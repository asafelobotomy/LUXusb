"""Cosign signature verification for container-based ISOs"""

import subprocess
import logging
import json
import tempfile
import re
from pathlib import Path
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CosignKey:
    """Cosign public key information for a distribution"""
    description: str
    key_url: str  # URL to download cosign.pub
    key_content: Optional[str] = None  # Cached key content
    container_registry: str = ""  # e.g., ghcr.io/ublue-os/bazzite
    note: Optional[str] = None


@dataclass
class CosignVerification:
    """Result of cosign verification"""
    verified: bool
    signature_info: Dict
    error_message: Optional[str] = None
    sha256: Optional[str] = None  # Extracted from signature if available


class CosignVerifier:
    """Verify cosign signatures for container-based distribution images"""
    
    def __init__(self):
        self.keys_file = Path(__file__).parent.parent / "data" / "cosign_keys.json"
        self.cosign_available = self._check_cosign_available()
        self.keys_data = self._load_keys()
    
    def _check_cosign_available(self) -> bool:
        """Check if cosign is available on the system"""
        try:
            result = subprocess.run(
                ['cosign', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Cosign is available: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("Cosign not available - signature verification disabled")
        logger.warning("Install cosign: https://docs.sigstore.dev/cosign/installation/")
        return False
    
    def _load_keys(self) -> Dict[str, CosignKey]:
        """Load cosign keys from JSON file"""
        if not self.keys_file.exists():
            logger.warning(f"Cosign keys file not found: {self.keys_file}")
            return {}
        
        try:
            with open(self.keys_file, 'r') as f:
                data = json.load(f)
            
            keys = {}
            for distro_id, key_info in data.items():
                keys[distro_id] = CosignKey(
                    description=key_info.get('description', ''),
                    key_url=key_info.get('key_url', ''),
                    key_content=key_info.get('key_content'),
                    container_registry=key_info.get('container_registry', ''),
                    note=key_info.get('note')
                )
            
            logger.info(f"Loaded {len(keys)} cosign keys")
            return keys
            
        except Exception as e:
            logger.error(f"Failed to load cosign keys: {e}")
            return {}
    
    def get_key(self, distro_id: str) -> Optional[CosignKey]:
        """Get cosign key for a distribution"""
        return self.keys_data.get(distro_id)
    
    def download_public_key(self, key_url: str) -> Optional[str]:
        """Download cosign public key from URL"""
        import requests
        
        try:
            logger.info(f"Downloading cosign public key from {key_url}")
            response = requests.get(key_url, timeout=10)
            response.raise_for_status()
            
            key_content = response.text.strip()
            
            # Validate it looks like a cosign public key
            if '-----BEGIN PUBLIC KEY-----' in key_content:
                logger.info("Successfully downloaded cosign public key")
                return key_content
            else:
                logger.warning("Downloaded content doesn't look like a cosign public key")
                return None
                
        except Exception as e:
            logger.error(f"Failed to download cosign public key: {e}")
            return None
    
    def verify_container_image(
        self,
        distro_id: str,
        container_image: str,
        key_content: Optional[str] = None
    ) -> CosignVerification:
        """
        Verify container image signature using cosign
        
        Args:
            distro_id: Distribution identifier (e.g., 'bazzite-desktop')
            container_image: Container registry path (e.g., 'ghcr.io/ublue-os/bazzite:stable')
            key_content: Optional public key content (downloads if not provided)
        
        Returns:
            CosignVerification object with results
        """
        if not self.cosign_available:
            return CosignVerification(
                verified=False,
                signature_info={},
                error_message="Cosign not installed on system"
            )
        
        # Get or download the public key
        if not key_content:
            key_info = self.get_key(distro_id)
            if not key_info:
                return CosignVerification(
                    verified=False,
                    signature_info={},
                    error_message=f"No cosign key configured for {distro_id}"
                )
            
            if key_info.key_content:
                key_content = key_info.key_content
            else:
                key_content = self.download_public_key(key_info.key_url)
                if not key_content:
                    return CosignVerification(
                        verified=False,
                        signature_info={},
                        error_message="Failed to download cosign public key"
                    )
        
        # Write key to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pub', delete=False) as key_file:
            key_file.write(key_content)
            key_path = key_file.name
        
        try:
            # Run cosign verify
            logger.info(f"Verifying container image: {container_image}")
            result = subprocess.run(
                ['cosign', 'verify', '--key', key_path, container_image],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ Cosign verification successful")
                
                # Parse the JSON output
                try:
                    signature_info = json.loads(result.stdout)
                    if isinstance(signature_info, list) and len(signature_info) > 0:
                        signature_info = signature_info[0]
                    
                    # Try to extract SHA256 from the signature
                    sha256 = self._extract_sha256_from_signature(signature_info)
                    
                    return CosignVerification(
                        verified=True,
                        signature_info=signature_info,
                        sha256=sha256
                    )
                except json.JSONDecodeError:
                    # Verification succeeded but couldn't parse output
                    return CosignVerification(
                        verified=True,
                        signature_info={'raw_output': result.stdout}
                    )
            else:
                logger.error(f"❌ Cosign verification failed: {result.stderr}")
                return CosignVerification(
                    verified=False,
                    signature_info={},
                    error_message=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            logger.error("Cosign verification timed out")
            return CosignVerification(
                verified=False,
                signature_info={},
                error_message="Verification timed out after 30 seconds"
            )
        except Exception as e:
            logger.error(f"Cosign verification error: {e}")
            return CosignVerification(
                verified=False,
                signature_info={},
                error_message=str(e)
            )
        finally:
            # Clean up temporary key file
            try:
                Path(key_path).unlink()
            except:
                pass
    
    def _extract_sha256_from_signature(self, signature_info: Dict) -> Optional[str]:
        """Try to extract SHA256 digest from signature metadata"""
        try:
            # Check various possible locations for the digest
            # Cosign stores digests in different places depending on the signature format
            
            # Try the critical section
            if 'critical' in signature_info:
                critical = signature_info['critical']
                if 'image' in critical and 'docker-manifest-digest' in critical['image']:
                    digest = critical['image']['docker-manifest-digest']
                    # Format: sha256:abc123...
                    if digest.startswith('sha256:'):
                        sha256 = digest.replace('sha256:', '')
                        logger.info(f"Extracted SHA256 from signature: {sha256[:16]}...")
                        return sha256
            
            # Try optional annotations
            if 'optional' in signature_info:
                optional = signature_info['optional']
                for key, value in optional.items():
                    if 'sha256' in key.lower() or 'digest' in key.lower():
                        # Try to extract hex string
                        match = re.search(r'([0-9a-f]{64})', str(value), re.IGNORECASE)
                        if match:
                            sha256 = match.group(1).lower()
                            logger.info(f"Extracted SHA256 from optional field: {sha256[:16]}...")
                            return sha256
            
            logger.debug("No SHA256 found in signature metadata")
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract SHA256: {e}")
            return None
    
    def verify_iso_file(
        self,
        distro_id: str,
        iso_path: Path,
        expected_sha256: Optional[str] = None
    ) -> CosignVerification:
        """
        Verify an ISO file using cosign (if the ISO has an associated signature)
        
        Note: This is less common - most distributions sign container images,
        not ISO files directly. Use verify_container_image() for most cases.
        
        Args:
            distro_id: Distribution identifier
            iso_path: Path to the ISO file
            expected_sha256: Optional expected SHA256 to verify against
        
        Returns:
            CosignVerification object
        """
        # Check for .sig file next to ISO
        sig_path = iso_path.with_suffix(iso_path.suffix + '.sig')
        
        if not sig_path.exists():
            return CosignVerification(
                verified=False,
                signature_info={},
                error_message=f"No signature file found: {sig_path}"
            )
        
        # TODO: Implement ISO file signature verification
        # This would require cosign verify-blob command
        logger.warning("ISO file signature verification not yet implemented")
        return CosignVerification(
            verified=False,
            signature_info={},
            error_message="ISO signature verification not implemented"
        )
    
    def get_container_digest(self, container_image: str) -> Optional[str]:
        """
        Get the SHA256 digest of a container image from the registry
        
        Args:
            container_image: Container registry path
        
        Returns:
            SHA256 digest or None if unavailable
        """
        try:
            # Use docker/podman to get the digest
            for tool in ['docker', 'podman']:
                try:
                    result = subprocess.run(
                        [tool, 'manifest', 'inspect', container_image],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    
                    if result.returncode == 0:
                        manifest = json.loads(result.stdout)
                        
                        # Extract digest from manifest
                        if 'config' in manifest and 'digest' in manifest['config']:
                            digest = manifest['config']['digest']
                            if digest.startswith('sha256:'):
                                sha256 = digest.replace('sha256:', '')
                                logger.info(f"Got container digest: {sha256[:16]}...")
                                return sha256
                        
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            logger.warning("Could not retrieve container digest (docker/podman not available)")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get container digest: {e}")
            return None
    
    def is_distro_cosign_signed(self, distro_id: str) -> bool:
        """Check if a distribution uses cosign signatures"""
        return distro_id in self.keys_data
    
    def install_instructions(self) -> str:
        """Return instructions for installing cosign"""
        return """
Cosign is not installed. To enable container signature verification:

Linux:
  # Binary installation
  wget https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
  sudo install cosign-linux-amd64 /usr/local/bin/cosign
  
  # Or via package manager
  sudo apt install cosign      # Debian/Ubuntu
  sudo dnf install cosign      # Fedora
  sudo pacman -S cosign        # Arch

More info: https://docs.sigstore.dev/cosign/installation/
"""


# Singleton instance
_verifier_instance = None


def get_cosign_verifier() -> CosignVerifier:
    """Get or create the global CosignVerifier instance"""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = CosignVerifier()
    return _verifier_instance

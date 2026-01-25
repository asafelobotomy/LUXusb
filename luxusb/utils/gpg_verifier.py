"""GPG signature verification for ISO authenticity checking"""

import subprocess
import logging
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GPGKey:
    """GPG key information for a distribution"""
    description: str
    key_id: str
    key_server: str
    key_url: str
    fingerprint: str
    signature_file: Optional[str]
    checksum_file: str
    note: Optional[str] = None


class GPGVerifier:
    """Verify GPG signatures for distribution ISOs and checksums"""
    
    def __init__(self):
        self.keys_file = Path(__file__).parent.parent / "data" / "gpg_keys.json"
        self.gpg_available = self._check_gpg_available()
        self.keys_data = self._load_keys()
    
    def _check_gpg_available(self) -> bool:
        """Check if GPG is available on the system"""
        try:
            result = subprocess.run(
                ['gpg', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("GPG is available for signature verification")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("GPG not available - signature verification disabled")
        return False
    
    def _load_keys(self) -> Dict[str, GPGKey]:
        """Load GPG key information from JSON"""
        try:
            with open(self.keys_file, 'r') as f:
                data = json.load(f)
            
            keys = {}
            for distro_id, key_data in data.items():
                keys[distro_id] = GPGKey(
                    description=key_data['description'],
                    key_id=key_data['key_id'],
                    key_server=key_data['key_server'],
                    key_url=key_data['key_url'],
                    fingerprint=key_data['fingerprint'],
                    signature_file=key_data.get('signature_file'),
                    checksum_file=key_data['checksum_file'],
                    note=key_data.get('note')
                )
            
            logger.info(f"Loaded GPG keys for {len(keys)} distributions")
            return keys
            
        except Exception as e:
            logger.error(f"Failed to load GPG keys: {e}")
            return {}
    
    def get_key_info(self, distro_id: str) -> Optional[GPGKey]:
        """Get GPG key information for a distribution"""
        return self.keys_data.get(distro_id)
    
    def import_key(self, distro_id: str) -> bool:
        """
        Import GPG key for a distribution
        
        Args:
            distro_id: Distribution identifier
            
        Returns:
            True if key imported successfully or already present
        """
        if not self.gpg_available:
            logger.debug("GPG not available, skipping key import")
            return False
        
        key_info = self.get_key_info(distro_id)
        if not key_info:
            logger.warning(f"No GPG key info for {distro_id}")
            return False
        
        # Check if key already imported
        if self._is_key_imported(key_info.key_id):
            logger.debug(f"Key {key_info.key_id} already imported")
            return True
        
        logger.info(f"Importing GPG key for {distro_id}: {key_info.description}")
        
        # Try importing from key server
        try:
            result = subprocess.run(
                ['gpg', '--keyserver', key_info.key_server, '--recv-keys', key_info.key_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully imported key {key_info.key_id}")
                return True
            else:
                logger.warning(f"Failed to import key from keyserver: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("Key import timed out")
        except Exception as e:
            logger.error(f"Key import failed: {e}")
        
        return False
    
    def _is_key_imported(self, key_id: str) -> bool:
        """Check if a GPG key is already imported"""
        try:
            result = subprocess.run(
                ['gpg', '--list-keys', key_id],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def verify_detached_signature(
        self,
        data_file: Path,
        signature_file: Path,
        distro_id: str
    ) -> Tuple[bool, str]:
        """
        Verify a detached GPG signature
        
        Args:
            data_file: Path to file being verified (e.g., SHA256SUMS)
            signature_file: Path to detached signature file (.gpg or .sig)
            distro_id: Distribution identifier
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.gpg_available:
            return False, "GPG not available on system"
        
        key_info = self.get_key_info(distro_id)
        if not key_info:
            return False, f"No GPG key info for {distro_id}"
        
        # Ensure key is imported
        if not self._is_key_imported(key_info.key_id):
            if not self.import_key(distro_id):
                return False, f"Failed to import GPG key for {distro_id}"
        
        try:
            logger.info(f"Verifying GPG signature: {signature_file.name}")
            result = subprocess.run(
                ['gpg', '--verify', str(signature_file), str(data_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check for "Good signature"
            output = result.stderr + result.stdout
            if 'Good signature' in output:
                logger.info(f"✓ Valid GPG signature from {distro_id}")
                return True, "Valid signature"
            elif 'BAD signature' in output:
                logger.error(f"✗ BAD GPG signature for {distro_id}!")
                return False, "BAD signature - file may be tampered!"
            else:
                logger.warning(f"GPG verification unclear: {output}")
                return False, f"Verification unclear: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "GPG verification timed out"
        except Exception as e:
            logger.error(f"GPG verification failed: {e}")
            return False, str(e)
    
    def verify_checksum_signature(
        self,
        checksum_content: str,
        signature_content: bytes,
        distro_id: str
    ) -> Tuple[bool, str]:
        """
        Verify GPG signature of checksum content (in-memory)
        
        Args:
            checksum_content: Content of checksum file (e.g., SHA256SUMS)
            signature_content: Content of signature file (.gpg)
            distro_id: Distribution identifier
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.gpg_available:
            return False, "GPG not available on system"
        
        # Write to temporary files for verification
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as data_file:
                data_file.write(checksum_content)
                data_path = Path(data_file.name)
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.gpg', delete=False) as sig_file:
                sig_file.write(signature_content)
                sig_path = Path(sig_file.name)
            
            # Verify signature
            success, message = self.verify_detached_signature(data_path, sig_path, distro_id)
            
            # Cleanup
            data_path.unlink()
            sig_path.unlink()
            
            return success, message
            
        except Exception as e:
            logger.error(f"Failed to verify signature: {e}")
            return False, str(e)
    
    def verify_embedded_signature(self, file_path: Path) -> Tuple[bool, str]:
        """
        Verify file with embedded GPG signature (e.g., Fedora CHECKSUM files)
        
        Args:
            file_path: Path to file with embedded signature
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.gpg_available:
            return False, "GPG not available on system"
        
        try:
            logger.info(f"Verifying embedded GPG signature: {file_path.name}")
            result = subprocess.run(
                ['gpg', '--verify', str(file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stderr + result.stdout
            if 'Good signature' in output:
                logger.info(f"✓ Valid embedded GPG signature")
                return True, "Valid signature"
            elif 'BAD signature' in output:
                logger.error(f"✗ BAD embedded GPG signature!")
                return False, "BAD signature - file may be tampered!"
            else:
                logger.warning(f"GPG verification unclear: {output}")
                return False, f"Verification unclear: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "GPG verification timed out"
        except Exception as e:
            logger.error(f"GPG verification failed: {e}")
            return False, str(e)
    
    def is_available(self) -> bool:
        """Check if GPG verification is available"""
        return self.gpg_available
    
    def get_supported_distros(self) -> list:
        """Get list of distributions with GPG key info"""
        return list(self.keys_data.keys())

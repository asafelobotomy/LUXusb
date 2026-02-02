"""
Secure Boot detection and bootloader signing
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SecureBootStatus:
    """Secure Boot status information"""
    enabled: bool
    setup_mode: bool
    available: bool
    error_message: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Check if Secure Boot is active (enabled and not in setup mode)"""
        return self.enabled and not self.setup_mode
    
    @property
    def requires_signing(self) -> bool:
        """Check if bootloader signing is required"""
        return self.enabled and not self.setup_mode


class SecureBootDetector:
    """Detect Secure Boot status and requirements"""
    
    def __init__(self):
        """Initialize Secure Boot detector"""
        self.logger = logging.getLogger(__name__)
    
    def detect_secure_boot(self) -> SecureBootStatus:
        """
        Detect current Secure Boot status
        
        Returns:
            SecureBootStatus object with detection results
        """
        # Check if running on EFI system
        efi_vars_path = Path('/sys/firmware/efi/efivars')
        if not efi_vars_path.exists():
            self.logger.info("Not an EFI system, Secure Boot not available")
            return SecureBootStatus(
                enabled=False,
                setup_mode=False,
                available=False,
                error_message="Not an EFI system"
            )
        
        # Try to read SecureBoot variable
        secure_boot_enabled = self._check_efi_variable('SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c')
        setup_mode = self._check_efi_variable('SetupMode-8be4df61-93ca-11d2-aa0d-00e098032b8c')
        
        if secure_boot_enabled is None:
            self.logger.warning("Could not determine Secure Boot status")
            return SecureBootStatus(
                enabled=False,
                setup_mode=False,
                available=True,
                error_message="Could not read Secure Boot status"
            )
        
        return SecureBootStatus(
            enabled=secure_boot_enabled,
            setup_mode=setup_mode if setup_mode is not None else False,
            available=True
        )
    
    def _check_efi_variable(self, var_name: str) -> Optional[bool]:
        """
        Check EFI variable value
        
        Args:
            var_name: EFI variable name with GUID
        
        Returns:
            True if enabled, False if disabled, None if unknown
        """
        var_path = Path(f'/sys/firmware/efi/efivars/{var_name}')
        
        if not var_path.exists():
            return None
        
        try:
            # Read variable (skip first 4 bytes which are attributes)
            with open(var_path, 'rb') as f:
                f.read(4)  # Skip attributes
                value = f.read(1)
                return value == b'\x01'
        except (PermissionError, OSError) as e:
            self.logger.debug(f"Could not read EFI variable {var_name}: {e}")
            return None
    
    def check_mokutil(self) -> bool:
        """
        Check if mokutil is available for MOK management
        
        Returns:
            True if mokutil is available, False otherwise
        """
        try:
            subprocess.run(
                ['which', 'mokutil'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, Exception):
            return False


class BootloaderSigner:
    """Sign bootloader for Secure Boot compatibility"""
    
    def __init__(self, keys_dir: Optional[Path] = None):
        """
        Initialize bootloader signer
        
        Args:
            keys_dir: Directory containing signing keys (default: /var/lib/shim-signed/mok)
        """
        self.keys_dir = keys_dir or Path('/var/lib/shim-signed/mok')
        self.logger = logging.getLogger(__name__)
    
    def sign_bootloader(self, bootloader_path: Path, output_path: Optional[Path] = None) -> bool:
        """
        Sign bootloader with MOK (Machine Owner Key)
        
        Args:
            bootloader_path: Path to bootloader file (e.g., grubx64.efi)
            output_path: Optional output path (defaults to overwriting original)
        
        Returns:
            True if signing successful, False otherwise
        """
        if not bootloader_path.exists():
            self.logger.error(f"Bootloader not found: {bootloader_path}")
            return False
        
        # Check if sbsign is available
        if not self._check_sbsign():
            self.logger.warning("sbsign not available, skipping bootloader signing")
            return False
        
        # Look for signing keys
        key_file, cert_file = self._find_signing_keys()
        if not key_file or not cert_file:
            self.logger.warning("Signing keys not found, skipping bootloader signing")
            return False
        
        output = output_path or bootloader_path
        
        try:
            # Sign the bootloader
            result = subprocess.run(
                [
                    'sbsign',
                    '--key', str(key_file),
                    '--cert', str(cert_file),
                    '--output', str(output),
                    str(bootloader_path)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"Successfully signed bootloader: {bootloader_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to sign bootloader: {e.stderr}")
            return False
    
    def _check_sbsign(self) -> bool:
        """
        Check if sbsign is available
        
        Returns:
            True if sbsign is available, False otherwise
        """
        try:
            subprocess.run(
                ['which', 'sbsign'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, Exception):
            return False
    
    def _find_signing_keys(self) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Find signing key and certificate
        
        Returns:
            Tuple of (key_file, cert_file) or (None, None) if not found
        """
        # Common key locations
        key_locations = [
            self.keys_dir / 'MOK.key',
            Path('/etc/pki/mok/MOK.key'),
            Path('/root/.mok/MOK.key'),
        ]
        
        cert_locations = [
            self.keys_dir / 'MOK.cer',
            self.keys_dir / 'MOK.crt',
            Path('/etc/pki/mok/MOK.cer'),
            Path('/etc/pki/mok/MOK.crt'),
            Path('/root/.mok/MOK.cer'),
            Path('/root/.mok/MOK.crt'),
        ]
        
        key_file = None
        cert_file = None
        
        # Find key
        for key_path in key_locations:
            if key_path.exists():
                key_file = key_path
                break
        
        # Find certificate
        for cert_path in cert_locations:
            if cert_path.exists():
                cert_file = cert_path
                break
        
        return key_file, cert_file
    
    def generate_mok_keys(self, output_dir: Path) -> bool:
        """
        Generate new MOK (Machine Owner Key) keys
        
        Args:
            output_dir: Directory to store generated keys
        
        Returns:
            True if successful, False otherwise
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        key_file = output_dir / 'MOK.key'
        cert_file = output_dir / 'MOK.cer'
        
        try:
            # Generate private key
            subprocess.run(
                [
                    'openssl', 'req', '-new', '-x509',
                    '-newkey', 'rsa:2048',
                    '-keyout', str(key_file),
                    '-out', str(cert_file),
                    '-days', '3650',
                    '-nodes',
                    '-subj', '/CN=LUXusb MOK/'
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"Generated MOK keys in {output_dir}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to generate MOK keys: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to generate MOK keys: {e}")
            return False
    
    def install_shim(self, efi_mount: Path) -> bool:
        """
        Install shim bootloader (for Secure Boot)
        
        Args:
            efi_mount: EFI partition mount point
        
        Returns:
            True if successful, False otherwise
        """
        # Look for system shim
        shim_locations = [
            Path('/usr/lib/shim/shimx64.efi.signed'),
            Path('/usr/lib/shim/shimx64.efi'),
            Path('/boot/efi/EFI/ubuntu/shimx64.efi'),
        ]
        
        shim_src = None
        for shim_path in shim_locations:
            if shim_path.exists():
                shim_src = shim_path
                break
        
        if not shim_src:
            self.logger.warning("Shim bootloader not found")
            self.logger.info("To enable Secure Boot support, install shim-signed:")
            self.logger.info("  Ubuntu/Debian: sudo apt install shim-signed")
            self.logger.info("  Fedora: sudo dnf install shim-x64")
            self.logger.info("  Arch: sudo pacman -S shim-signed")
            return False
        
        # Copy shim to EFI partition
        boot_dir = efi_mount / 'EFI' / 'BOOT'
        boot_dir.mkdir(parents=True, exist_ok=True)
        
        shim_dest = boot_dir / 'BOOTX64.EFI'
        
        try:
            subprocess.run(
                ['cp', str(shim_src), str(shim_dest)],
                capture_output=True,
                check=True
            )
            
            self.logger.info(f"Installed shim bootloader to {shim_dest}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install shim: {e.stderr}")
            return False
    
    def get_shim_install_instructions(self) -> str:
        """
        Get installation instructions for shim bootloader
        
        Returns:
            Formatted instructions string for display
        """
        return """Secure Boot support requires the 'shim-signed' package.

Install it using your package manager:

Ubuntu/Debian:
    sudo apt install shim-signed

Fedora:
    sudo dnf install shim-x64

Arch Linux:
    sudo pacman -S shim-signed

After installing, try creating the USB again with Secure Boot enabled."""


def detect_secure_boot() -> SecureBootStatus:
    """
    Convenience function to detect Secure Boot status
    
    Returns:
        SecureBootStatus object
    """
    detector = SecureBootDetector()
    return detector.detect_secure_boot()

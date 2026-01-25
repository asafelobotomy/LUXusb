"""
Custom ISO validation and management
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CustomISO:
    """Represents a custom ISO file"""
    path: Path
    name: str
    size_bytes: int
    is_valid: bool = False
    error_message: Optional[str] = None
    checksum_file: Optional[Path] = None
    gpg_signature: Optional[Path] = None
    gpg_key: Optional[Path] = None
    
    @property
    def size_mb(self) -> int:
        """Get size in megabytes"""
        return int(self.size_bytes / (1024 * 1024))
    
    @property
    def filename(self) -> str:
        """Get filename without path"""
        return self.path.name
    
    @property
    def display_name(self) -> str:
        """Get display-friendly name"""
        return self.name if self.name else self.filename
    
    @property
    def source_path(self) -> Path:
        """Get source path for duplicate checking"""
        return self.path
    
    @property
    def has_verification(self) -> bool:
        """Check if any verification files are attached"""
        return bool(self.checksum_file or self.gpg_signature or self.gpg_key)


class CustomISOValidator:
    """Validate custom ISO files"""
    
    # Minimum size for ISO file (10 MB)
    MIN_ISO_SIZE = 10 * 1024 * 1024
    
    # Maximum size for ISO file (10 GB)
    MAX_ISO_SIZE = 10 * 1024 * 1024 * 1024
    
    def __init__(self):
        """Initialize validator"""
        self.logger = logging.getLogger(__name__)
    
    def validate_iso_file(self, iso_path: Path, name: Optional[str] = None) -> CustomISO:
        """
        Validate a custom ISO file
        
        Args:
            iso_path: Path to ISO file
            name: Optional custom name (defaults to filename)
        
        Returns:
            CustomISO object with validation results
        """
        # Check if file exists
        if not iso_path.exists():
            return CustomISO(
                path=iso_path,
                name=name or iso_path.stem,
                size_bytes=0,
                is_valid=False,
                error_message="File does not exist"
            )
        
        # Check if it's a file (not directory)
        if not iso_path.is_file():
            return CustomISO(
                path=iso_path,
                name=name or iso_path.stem,
                size_bytes=0,
                is_valid=False,
                error_message="Path is not a file"
            )
        
        # Get file size
        size_bytes = iso_path.stat().st_size
        
        # Check size constraints
        if size_bytes < self.MIN_ISO_SIZE:
            return CustomISO(
                path=iso_path,
                name=name or iso_path.stem,
                size_bytes=size_bytes,
                is_valid=False,
                error_message=f"File too small (minimum {self.MIN_ISO_SIZE // (1024*1024)} MB)"
            )
        
        if size_bytes > self.MAX_ISO_SIZE:
            return CustomISO(
                path=iso_path,
                name=name or iso_path.stem,
                size_bytes=size_bytes,
                is_valid=False,
                error_message=f"File too large (maximum {self.MAX_ISO_SIZE // (1024*1024*1024)} GB)"
            )
        
        # Check file extension
        if iso_path.suffix.lower() not in ['.iso', '.img']:
            return CustomISO(
                path=iso_path,
                name=name or iso_path.stem,
                size_bytes=size_bytes,
                is_valid=False,
                error_message="Invalid file extension (must be .iso or .img)"
            )
        
        # Validate ISO format
        is_valid, error = self._validate_iso_format(iso_path)
        
        return CustomISO(
            path=iso_path,
            name=name or iso_path.stem,
            size_bytes=size_bytes,
            is_valid=is_valid,
            error_message=error
        )
    
    def _validate_iso_format(self, iso_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate ISO 9660 format using file command
        
        Args:
            iso_path: Path to ISO file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Use 'file' command to check ISO format
            result = subprocess.run(
                ['file', '-b', str(iso_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            
            # Check for ISO 9660 filesystem
            if 'iso 9660' in output or 'dos/mbr boot sector' in output or 'bootable' in output:
                self.logger.debug(f"Valid ISO format detected: {output.strip()}")
                return True, None
            
            # Also accept if 'file' says it's data (some ISOs report as "data")
            if 'data' in output:
                self.logger.warning(f"ISO file detected as 'data', assuming valid: {output.strip()}")
                return True, None
            
            return False, f"Not a valid ISO format: {output.strip()}"
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to validate ISO format: {e.stderr}")
            return False, "Failed to validate ISO format"
        except subprocess.TimeoutExpired:
            self.logger.error("ISO validation timed out")
            return False, "Validation timed out"
        except FileNotFoundError:
            # 'file' command not available, assume valid
            self.logger.warning("'file' command not found, skipping format validation")
            return True, None
    
    def check_bootable(self, iso_path: Path) -> bool:
        """
        Check if ISO is bootable
        
        Args:
            iso_path: Path to ISO file
        
        Returns:
            True if bootable, False otherwise
        """
        try:
            # Use isoinfo to check for bootable flag
            result = subprocess.run(
                ['isoinfo', '-d', '-i', str(iso_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check for boot catalog
            if 'Bootable' in result.stdout or 'El Torito' in result.stdout:
                return True
            
            return False
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            # If isoinfo not available or fails, assume bootable
            self.logger.warning("Could not check bootable status, assuming bootable")
            return True


def validate_custom_iso(iso_path: Path, name: Optional[str] = None) -> CustomISO:
    """
    Convenience function to validate a custom ISO
    
    Args:
        iso_path: Path to ISO file
        name: Optional custom name
    
    Returns:
        CustomISO object with validation results
    """
    validator = CustomISOValidator()
    return validator.validate_iso_file(iso_path, name)

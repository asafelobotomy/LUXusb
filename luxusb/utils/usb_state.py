"""
USB state detection and management for LUXusb-configured devices
"""

import json
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class USBState:
    """State information for a LUXusb-configured USB device"""
    device_path: str
    configured_date: str
    last_modified: str
    luxusb_version: str
    efi_partition: str
    data_partition: str
    installed_isos: List[str]  # List of ISO filenames
    grub_configured: bool
    secure_boot_enabled: bool = False  # Whether Secure Boot was enabled during creation
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'USBState':
        """Create from dictionary"""
        return cls(**data)


class USBStateManager:
    """Manage LUXusb USB device state"""
    
    CONFIG_FILENAME = ".luxusb-config"
    
    def __init__(self):
        """Initialize state manager"""
        pass
    
    def is_luxusb_device(self, mount_point: Path) -> bool:
        """
        Check if a mount point contains a LUXusb configuration
        
        Args:
            mount_point: Path to mounted filesystem
            
        Returns:
            True if LUXusb config exists
        """
        config_path = mount_point / self.CONFIG_FILENAME
        return config_path.exists()
    
    def read_state(self, mount_point: Path) -> Optional[USBState]:
        """
        Read USB state from config file
        
        Args:
            mount_point: Path to mounted filesystem
            
        Returns:
            USBState if config exists and valid, None otherwise
        """
        config_path = mount_point / self.CONFIG_FILENAME
        
        if not config_path.exists():
            logger.debug("No LUXusb config found at %s", config_path)
            return None
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            state = USBState.from_dict(data)
            
            # Always rescan ISOs from filesystem for accurate count
            state.installed_isos = self.scan_installed_isos(mount_point)
            logger.info("Found LUXusb-configured device: %s with %d ISOs", 
                       state.device_path, len(state.installed_isos))
            return state
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("Failed to read USB state from %s: %s", config_path, e)
            return None
    
    def write_state(
        self,
        mount_point: Path,
        device_path: str,
        efi_partition: str,
        data_partition: str,
        luxusb_version: str = "0.2.0",
        secure_boot_enabled: bool = False
    ) -> bool:
        """
        Write USB state configuration
        
        Args:
            mount_point: Path to mounted data partition
            device_path: Device path (e.g., /dev/sdb)
            efi_partition: EFI partition path
            data_partition: Data partition path
            luxusb_version: LUXusb version string
            secure_boot_enabled: Whether Secure Boot was enabled during creation
            
        Returns:
            True if successful
        """
        config_path = mount_point / self.CONFIG_FILENAME
        
        # Scan for existing ISOs
        iso_dir = mount_point / "isos"
        installed_isos = []
        if iso_dir.exists():
            installed_isos = [iso.name for iso in iso_dir.glob("*.iso")]
        
        # Check if GRUB is configured
        grub_cfg = mount_point / "boot" / "grub" / "grub.cfg"
        grub_configured = grub_cfg.exists()
        
        now = datetime.now().isoformat()
        
        state = USBState(
            device_path=device_path,
            configured_date=now,
            last_modified=now,
            luxusb_version=luxusb_version,
            efi_partition=efi_partition,
            data_partition=data_partition,
            installed_isos=installed_isos,
            grub_configured=grub_configured,
            secure_boot_enabled=secure_boot_enabled
        )
        
        try:
            with open(config_path, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            
            logger.info("Wrote LUXusb config to %s", config_path)
            return True
            
        except (OSError, IOError) as e:
            logger.error("Failed to write USB state: %s", e)
            return False
    
    def update_state(
        self,
        mount_point: Path,
        installed_isos: Optional[List[str]] = None,
        grub_configured: Optional[bool] = None,
        secure_boot_enabled: Optional[bool] = None
    ) -> bool:
        """
        Update existing USB state
        
        Args:
            mount_point: Path to mounted data partition
            installed_isos: Updated list of ISOs (if provided)
            grub_configured: Updated GRUB status (if provided)
            secure_boot_enabled: Updated Secure Boot status (if provided)
            
        Returns:
            True if successful
        """
        # Read existing state
        state = self.read_state(mount_point)
        if not state:
            logger.error("Cannot update state - no existing config found")
            return False
        
        # Update fields
        state.last_modified = datetime.now().isoformat()
        
        if installed_isos is not None:
            state.installed_isos = installed_isos
        
        if grub_configured is not None:
            state.grub_configured = grub_configured
        
        if secure_boot_enabled is not None:
            state.secure_boot_enabled = secure_boot_enabled
        
        # Write back
        config_path = mount_point / self.CONFIG_FILENAME
        try:
            with open(config_path, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            
            logger.info("Updated LUXusb config at %s", config_path)
            return True
            
        except (OSError, IOError) as e:
            logger.error("Failed to update USB state: %s", e)
            return False
    
    def scan_installed_isos(self, mount_point: Path) -> List[str]:
        """
        Scan for ISOs on USB (including subdirectories)
        
        Args:
            mount_point: Path to mounted data partition
            
        Returns:
            List of ISO filenames
        """
        iso_dir = mount_point / "isos"
        if not iso_dir.exists():
            return []
        
        # Use rglob to recursively search all subdirectories
        return [iso.name for iso in iso_dir.rglob("*.iso")]

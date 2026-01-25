"""
USB device detection and management
"""

import subprocess
import logging
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class USBDevice:
    """Represents a USB storage device"""
    device: str  # e.g., /dev/sdb
    size_bytes: int
    model: str
    vendor: str
    serial: str
    partitions: List[str]
    is_mounted: bool
    mount_points: List[str]
    is_luxusb_configured: bool = False  # Whether device has LUXusb config
    luxusb_state: Optional['USBState'] = None  # State info if configured
    
    @property
    def size_gb(self) -> float:
        """Get size in gigabytes"""
        return self.size_bytes / (1024 ** 3)
    
    @property
    def display_name(self) -> str:
        """Get human-readable device name"""
        vendor = self.vendor.strip() or "Unknown"
        model = self.model.strip() or "USB Device"
        size = f"{self.size_gb:.1f}GB"
        status = " [LUXusb Configured]" if self.is_luxusb_configured else ""
        return f"{vendor} {model} ({size}) - {self.device}{status}"
    
    def __str__(self) -> str:
        return self.display_name


class USBDetector:
    """Detect and manage USB storage devices"""
    
    def __init__(self) -> None:
        self.devices: List[USBDevice] = []
        
        # Lazy import to avoid circular dependency
        self._state_manager = None
    
    @property
    def state_manager(self):
        """Get USBStateManager instance (lazy loaded)"""
        if self._state_manager is None:
            from luxusb.utils.usb_state import USBStateManager
            self._state_manager = USBStateManager()
        return self._state_manager
    
    def scan_devices(self) -> List[USBDevice]:
        """
        Scan for USB storage devices
        
        Returns:
            List of USBDevice objects
        """
        logger.info("Scanning for USB devices...")
        self.devices = []
        
        try:
            # Use lsblk to get device information
            result = subprocess.run(
                [
                    'lsblk',
                    '-J',  # JSON output
                    '-o', 'NAME,SIZE,TYPE,TRAN,VENDOR,MODEL,SERIAL,MOUNTPOINT',
                    '-b'   # Bytes
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            data = json.loads(result.stdout)
            
            for device in data.get('blockdevices', []):
                # Filter only USB devices
                if device.get('tran') == 'usb' and device.get('type') == 'disk':
                    usb_dev = self._parse_device(device)
                    if usb_dev and usb_dev.size_bytes > 0:
                        # Check if device has LUXusb configuration
                        self._check_luxusb_state(usb_dev)
                        self.devices.append(usb_dev)
            
            logger.info("Found %d USB device(s)", len(self.devices))
            return self.devices
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to scan USB devices: %s", e)
            return []
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.exception("Error scanning USB devices: %s", e)
            return []
    
    def _parse_device(self, device_data: dict) -> Optional[USBDevice]:
        """Parse device data from lsblk output"""
        try:
            name = device_data.get('name', '')
            device_path = f"/dev/{name}"
            
            # Get partitions
            partitions = []
            mount_points = []
            is_mounted = False
            
            for child in device_data.get('children', []):
                if child.get('type') == 'part':
                    part_name = child.get('name', '')
                    partitions.append(f"/dev/{part_name}")
                    
                    mount_point = child.get('mountpoint')
                    if mount_point:
                        mount_points.append(mount_point)
                        is_mounted = True
            
            return USBDevice(
                device=device_path,
                size_bytes=int(device_data.get('size', 0)),
                model=device_data.get('model', '').strip(),
                vendor=device_data.get('vendor', '').strip(),
                serial=device_data.get('serial', '').strip(),
                partitions=partitions,
                is_mounted=is_mounted,
                mount_points=mount_points,
                is_luxusb_configured=False,
                luxusb_state=None
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning("Failed to parse device: %s", e)
            return None
    
    def _check_luxusb_state(self, device: USBDevice) -> None:
        """
        Check if device has LUXusb configuration
        
        Args:
            device: USBDevice to check (modified in place)
        """
        # Check each mount point for LUXusb config
        for mount_point in device.mount_points:
            mount_path = Path(mount_point)
            if self.state_manager.is_luxusb_device(mount_path):
                state = self.state_manager.read_state(mount_path)
                if state:
                    device.is_luxusb_configured = True
                    device.luxusb_state = state
                    logger.info("Detected LUXusb-configured device: %s", device.device)
                    return
        
        # If not mounted, try to temporarily mount and check
        if not device.is_mounted and len(device.partitions) >= 2:
            # Try mounting the second partition (data partition)
            data_partition = device.partitions[1] if len(device.partitions) > 1 else None
            if data_partition:
                temp_mount = self._temp_mount_partition(data_partition)
                if temp_mount:
                    try:
                        if self.state_manager.is_luxusb_device(temp_mount):
                            state = self.state_manager.read_state(temp_mount)
                            if state:
                                device.is_luxusb_configured = True
                                device.luxusb_state = state
                                logger.info("Detected LUXusb-configured device (temp mount): %s", device.device)
                    finally:
                        self._temp_unmount(temp_mount)
    
    def _temp_mount_partition(self, partition: str) -> Optional[Path]:
        """
        Temporarily mount a partition for checking
        
        Args:
            partition: Partition path (e.g., /dev/sdb2)
            
        Returns:
            Mount point Path if successful, None otherwise
        """
        temp_mount = Path(f"/tmp/luxusb-check-{Path(partition).name}")
        temp_mount.mkdir(parents=True, exist_ok=True)
        
        try:
            subprocess.run(
                ['mount', '-o', 'ro', partition, str(temp_mount)],
                capture_output=True,
                check=True,
                timeout=5
            )
            return temp_mount
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.debug("Could not temp mount %s: %s", partition, e)
            try:
                temp_mount.rmdir()
            except:
                pass
            return None
    
    def _temp_unmount(self, mount_point: Path) -> None:
        """Unmount and cleanup temp mount"""
        try:
            subprocess.run(
                ['umount', str(mount_point)],
                capture_output=True,
                check=False,
                timeout=5
            )
            mount_point.rmdir()
        except Exception as e:
            logger.debug("Error cleaning up temp mount: %s", e)
    
    def get_device_by_path(self, device_path: str) -> Optional[USBDevice]:
        """Get device by path"""
        for device in self.devices:
            if device.device == device_path:
                return device
        return None
    
    def unmount_device(self, device: USBDevice) -> bool:
        """
        Unmount all partitions of a device
        
        Args:
            device: USBDevice to unmount
            
        Returns:
            True if successful, False otherwise
        """
        if not device.is_mounted:
            logger.info("%s is not mounted", device.device)
            return True
        
        logger.info("Unmounting %s...", device.device)
        
        for partition in device.partitions:
            try:
                subprocess.run(
                    ['umount', partition],
                    capture_output=True,
                    check=True
                )
                logger.info("Unmounted %s", partition)
            except subprocess.CalledProcessError as e:
                logger.error("Failed to unmount %s: %s", partition, e)
                return False
        
        return True
    
    def is_system_disk(self, device: USBDevice) -> bool:
        """
        Check if device is the system disk (contains / or /boot)
        
        Args:
            device: USBDevice to check
            
        Returns:
            True if it's a system disk, False otherwise
        """
        critical_mounts = ['/', '/boot', '/boot/efi']
        
        for mount_point in device.mount_points:
            if mount_point in critical_mounts:
                logger.warning("%s is a system disk (mounted at %s)", device.device, mount_point)
                return True
        
        return False
    
    def validate_device(self, device: USBDevice, min_size_gb: float = 8.0) -> tuple[bool, str]:
        """
        Validate if device is suitable for use
        
        Args:
            device: USBDevice to validate
            min_size_gb: Minimum size in GB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if it's a system disk
        if self.is_system_disk(device):
            return False, "Cannot use system disk"
        
        # Check size
        if device.size_gb < min_size_gb:
            return False, f"Device too small (minimum {min_size_gb}GB required)"
        
        # Check if device exists
        if not Path(device.device).exists():
            return False, "Device not found"
        
        return True, ""


def get_usb_devices() -> List[USBDevice]:
    """
    Convenience function to get list of USB devices
    
    Returns:
        List of USBDevice objects
    """
    detector = USBDetector()
    return detector.scan_devices()

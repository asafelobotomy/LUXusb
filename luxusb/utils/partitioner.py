"""
USB partitioning and filesystem management
"""

import subprocess
import logging
import time
from typing import Optional, Tuple
from pathlib import Path

from luxusb.utils.usb_detector import USBDevice
from luxusb.constants import Size

logger = logging.getLogger(__name__)


class USBPartitioner:
    """Handle USB device partitioning and formatting"""
    
    def __init__(self, device: USBDevice):
        self.device = device
        self.bios_partition: Optional[str] = None
        self.efi_partition: Optional[str] = None
        self.data_partition: Optional[str] = None
    
    def create_partitions(self, efi_size_mb: int = Size.EFI_PARTITION_MB) -> bool:
        """
        Create partitions on USB device
        
        Layout (Hybrid BIOS/UEFI support):
        - Partition 1: BIOS Boot (1MB, unformatted) - for BIOS/Legacy systems
        - Partition 2: EFI System (FAT32) - for UEFI bootloader
        - Partition 3: Data (exFAT) - for ISOs
        
        Args:
            efi_size_mb: Size of EFI partition in MB
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Creating partitions on %s", self.device.device)
        
        try:
            # Unmount device first
            if not self._unmount_device():
                return False
            
            # Wipe existing partition table
            if not self._wipe_disk():
                return False
            
            # Create new GPT partition table
            if not self._create_gpt():
                return False
            
            # Create BIOS boot partition (1MB)
            if not self._create_bios_boot_partition():
                return False
            
            # Create EFI partition
            if not self._create_efi_partition(efi_size_mb):
                return False
            
            # Create data partition
            if not self._create_data_partition():
                return False
            
            # Inform kernel of partition changes
            self._reload_partition_table()
            
            # Wait for device nodes to be created
            time.sleep(2)
            
            # Set partition paths
            self.bios_partition = f"{self.device.device}1"
            self.efi_partition = f"{self.device.device}2"
            self.data_partition = f"{self.device.device}3"
            
            # Format partitions
            if not self._format_partitions():
                return False
            
            logger.info("Partitioning completed successfully")
            return True
            
        except (subprocess.CalledProcessError, OSError) as e:
            logger.exception("Failed to create partitions: %s", e)
            return False
    
    def _unmount_device(self) -> bool:
        """Unmount all partitions"""
        logger.info("Unmounting device...")
        
        for partition in self.device.partitions:
            try:
                subprocess.run(
                    ['umount', partition],
                    capture_output=True,
                    check=False  # Don't fail if not mounted
                )
            except (subprocess.CalledProcessError, OSError) as e:
                logger.warning("Failed to unmount %s: %s", partition, e)
        
        return True
    
    def _wipe_disk(self) -> bool:
        """Wipe partition table and first sectors"""
        logger.info("Wiping existing partition table...")
        
        try:
            # Use wipefs to remove all signatures
            subprocess.run(
                ['wipefs', '-a', self.device.device],
                capture_output=True,
                check=True
            )
            
            # Additionally, zero out first 10MB
            subprocess.run(
                ['dd', 'if=/dev/zero', f'of={self.device.device}', 
                 'bs=1M', 'count=10', 'status=none'],
                capture_output=True,
                check=True
            )
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to wipe disk: %s", e.stderr)
            return False
    
    def _create_gpt(self) -> bool:
        """Create new GPT partition table"""
        logger.info("Creating GPT partition table...")
        
        try:
            subprocess.run(
                ['parted', '-s', self.device.device, 'mklabel', 'gpt'],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create GPT: %s", e.stderr)
            return False
    
    def _create_bios_boot_partition(self) -> bool:
        """Create BIOS boot partition for Legacy/BIOS systems"""
        logger.info("Creating BIOS boot partition (1MB)...")
        
        try:
            # Create 1MB partition at the start
            subprocess.run(
                [
                    'parted', '-s', '-a', 'optimal', self.device.device,
                    'mkpart', 'BIOS', '1MiB', '2MiB'
                ],
                capture_output=True,
                check=True
            )
            
            # Set bios_grub flag (type EF02)
            subprocess.run(
                ['parted', '-s', self.device.device, 'set', '1', 'bios_grub', 'on'],
                capture_output=True,
                check=True
            )
            
            logger.info("BIOS boot partition created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create BIOS boot partition: %s", e.stderr)
            return False
    
    def _create_efi_partition(self, size_mb: int) -> bool:
        """Create EFI system partition"""
        logger.info("Creating EFI partition (%dMB)...", size_mb)
        
        try:
            # Create partition after BIOS boot partition (starts at 2MiB)
            # With optimal alignment, actual end will be aligned by parted
            end_mib = 2 + size_mb  # 2MiB start + 512MB = 514MiB nominal end
            subprocess.run(
                [
                    'parted', '-s', '-a', 'optimal', self.device.device,
                    'mkpart', 'EFI', 'fat32', '2MiB', f'{end_mib}MiB'
                ],
                capture_output=True,
                check=True
            )
            
            # Set ESP flag on partition 2
            subprocess.run(
                ['parted', '-s', self.device.device, 'set', '2', 'esp', 'on'],
                capture_output=True,
                check=True
            )
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create EFI partition: %s", e.stderr)
            return False
    
    def _create_data_partition(self) -> bool:
        """Create data partition for ISOs"""
        logger.info("Creating data partition...")
        
        try:
            # Create partition using remaining space
            # Start at 1.5GiB (1536MiB) to safely clear BIOS + EFI partitions
            # This provides buffer for any EFI partition size and alignment overhead
            # Parted with -a optimal will align both start and end properly
            # Note: Filesystem type omitted - actual formatting done later with mkfs.exfat
            subprocess.run(
                [
                    'parted', '-s', '-a', 'optimal', self.device.device,
                    'mkpart', 'DATA', '1536MiB', '100%'
                ],
                capture_output=True,
                check=True
            )
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create data partition: %s", e.stderr)
            return False
    
    def _reload_partition_table(self) -> bool:
        """Reload partition table"""
        logger.info("Reloading partition table...")
        
        try:
            subprocess.run(
                ['partprobe', self.device.device],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to reload partition table: %s", e.stderr)
            # Not critical, continue anyway
            return True
    
    def _format_partitions(self) -> bool:
        """Format both partitions"""
        logger.info("Formatting partitions...")
        
        # Format EFI partition (FAT32)
        if not self._format_efi():
            return False
        
        # Format data partition (ext4)
        if not self._format_data():
            return False
        
        return True
    
    def _format_efi(self) -> bool:
        """Format EFI partition as FAT32"""
        if not self.efi_partition:
            logger.error("EFI partition not set")
            return False
        
        logger.info("Formatting %s as FAT32...", self.efi_partition)
        
        try:
            subprocess.run(
                ['mkfs.vfat', '-F', '32', '-n', 'VMBOOT', self.efi_partition],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to format EFI partition: %s", e.stderr)
            return False
    
    def _format_data(self) -> bool:
        """Format data partition as ext4"""
        if not self.data_partition:
            logger.error("Data partition not set")
            return False
        
        logger.info("Formatting %s as ext4...", self.data_partition)
        
        try:
            subprocess.run(
                ['mkfs.ext4', '-L', 'LUXusb', '-F', self.data_partition],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to format data partition: %s", e.stderr)
            return False
    
    def mount_partitions(self, mount_base: Path) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Mount both partitions
        
        Args:
            mount_base: Base directory for mounting
            
        Returns:
            Tuple of (efi_mount_point, data_mount_point)
        """
        if not self.efi_partition or not self.data_partition:
            logger.error("Partitions not created yet")
            return None, None
        
        efi_mount = mount_base / "efi"
        data_mount = mount_base / "data"
        
        efi_mount.mkdir(parents=True, exist_ok=True)
        data_mount.mkdir(parents=True, exist_ok=True)
        
        try:
            # Mount EFI partition
            subprocess.run(
                ['mount', self.efi_partition, str(efi_mount)],
                capture_output=True,
                check=True
            )
            logger.info("Mounted %s at %s", self.efi_partition, efi_mount)
            
            # Mount data partition
            subprocess.run(
                ['mount', self.data_partition, str(data_mount)],
                capture_output=True,
                check=True
            )
            logger.info("Mounted %s at %s", self.data_partition, data_mount)
            
            return efi_mount, data_mount
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to mount partitions: %s", e.stderr)
            return None, None
    
    def unmount_partitions(self, efi_mount: Path, data_mount: Path) -> bool:
        """Unmount both partitions"""
        success = True
        
        for mount_point in [efi_mount, data_mount]:
            try:
                subprocess.run(
                    ['umount', str(mount_point)],
                    capture_output=True,
                    check=True
                )
                logger.info("Unmounted %s", mount_point)
            except subprocess.CalledProcessError as e:
                logger.error("Failed to unmount %s: %s", mount_point, e.stderr)
                success = False
        
        return success

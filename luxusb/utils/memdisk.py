"""
MEMDISK support for small ISO files

MEMDISK loads ISOs entirely into RAM, providing better compatibility
for utility ISOs that don't support loopback mounting.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# MEMDISK thresholds (in MB)
MEMDISK_MAX_SIZE = 512  # Max size for MEMDISK (RAM limitation)
MEMDISK_AUTO_SIZE = 128  # Auto-enable for ISOs smaller than this


class MEMDISKSupport:
    """Detect and configure MEMDISK support for ISOs"""
    
    def __init__(self):
        """Initialize MEMDISK support"""
        self.memdisk_binary = self._find_memdisk_binary()
    
    def _find_memdisk_binary(self) -> Optional[Path]:
        """
        Find MEMDISK binary on system
        
        Returns:
            Path to memdisk binary or None if not found
        """
        # Common locations for memdisk binary
        possible_paths = [
            Path('/usr/lib/syslinux/memdisk'),
            Path('/usr/lib/syslinux/bios/memdisk'),
            Path('/usr/share/syslinux/memdisk'),
            Path('/boot/memdisk'),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found MEMDISK binary at {path}")
                return path
        
        logger.warning("MEMDISK binary not found (install syslinux-common package)")
        return None
    
    def is_memdisk_available(self) -> bool:
        """
        Check if MEMDISK is available on system
        
        Returns:
            True if MEMDISK binary found
        """
        return self.memdisk_binary is not None
    
    def should_use_memdisk(self, iso_size_mb: int, force: bool = False) -> bool:
        """
        Determine if MEMDISK should be used for an ISO
        
        Args:
            iso_size_mb: ISO size in megabytes
            force: Force MEMDISK usage (ignores auto threshold)
        
        Returns:
            True if MEMDISK should be used
        """
        if not self.is_memdisk_available():
            return False
        
        # Auto-enable for small ISOs
        if iso_size_mb <= MEMDISK_AUTO_SIZE:
            logger.info(f"ISO size {iso_size_mb}MB <= {MEMDISK_AUTO_SIZE}MB: Using MEMDISK")
            return True
        
        # Optional for medium ISOs (user choice)
        if force and iso_size_mb <= MEMDISK_MAX_SIZE:
            logger.info(f"ISO size {iso_size_mb}MB, MEMDISK forced by user")
            return True
        
        # Too large for MEMDISK
        if iso_size_mb > MEMDISK_MAX_SIZE:
            logger.warning(f"ISO size {iso_size_mb}MB > {MEMDISK_MAX_SIZE}MB: Too large for MEMDISK")
            return False
        
        return False
    
    def is_windows_pe_iso(self, iso_path: Path) -> bool:
        """
        Detect if ISO is a Windows PE (Pre-installation Environment) image
        
        Args:
            iso_path: Path to ISO file
        
        Returns:
            True if ISO appears to be Windows PE
        """
        if not iso_path.exists():
            return False
        
        # Quick check: Windows PE ISOs typically have specific naming patterns
        name_lower = iso_path.name.lower()
        windows_keywords = ['winpe', 'windows pe', 'win10pe', 'win11pe', 'windowspe']
        
        if any(keyword in name_lower for keyword in windows_keywords):
            logger.info(f"Detected Windows PE ISO by name: {iso_path.name}")
            return True
        
        # TODO: Could add ISO filesystem analysis here if needed
        # (requires mounting ISO or parsing ISO9660 structure)
        
        return False
    
    def get_windows_pe_boot_commands(
        self,
        iso_path: str,
        memdisk_path: str = "/boot/memdisk"
    ) -> str:
        """
        Generate boot commands for Windows PE via MEMDISK (for use in submenus)
        
        Args:
            iso_path: Path to ISO file (relative to data partition)
            memdisk_path: Path to memdisk binary on USB
        
        Returns:
            Boot commands for embedding in submenu
        """
        return f"""    echo "========================================"
    echo "  Loading Windows PE into RAM"
    echo "========================================"
    echo ""
    echo "This may take 1-3 minutes..."
    echo "Please wait..."
    
    search --no-floppy --set=root --label LUXusb
    
    if [ "$root" = "" ]; then
      echo "ERROR: Could not find LUXusb data partition"
      echo "Press any key to return to menu..."
      read
    else
      linux16 {memdisk_path} iso raw
      initrd16 {iso_path}
    fi"""
    
    def get_memdisk_boot_commands(
        self,
        iso_path: str,
        memdisk_path: str = "/boot/memdisk"
    ) -> str:
        """
        Generate boot commands for MEMDISK (for use in submenus)
        
        Args:
            iso_path: Path to ISO file (relative to data partition)
            memdisk_path: Path to memdisk binary on USB
        
        Returns:
            Boot commands for embedding in submenu
        """
        return f"""    echo "Loading ISO into RAM via MEMDISK..."
    echo "This may take 30-60 seconds..."
    
    search --no-floppy --set=root --label LUXusb
    
    if [ "$root" = "" ]; then
      echo "ERROR: Could not find LUXusb data partition"
      echo "Press any key to return to menu..."
      read
    else
      linux16 {memdisk_path} iso raw
      initrd16 {iso_path}
    fi"""
    
    def get_windows_pe_boot_entry(
        self,
        iso_path: str,
        display_name: str,
        memdisk_path: str = "/boot/memdisk"
    ) -> str:
        """
        Generate GRUB menuentry for Windows PE booting via MEMDISK
        
        Windows PE requires special handling:
        - Must use MEMDISK 'iso' mode
        - Often requires additional time for RAM loading
        - May need specific boot parameters
        
        Args:
            iso_path: Path to ISO file (relative to data partition)
            display_name: Display name for menu entry
            memdisk_path: Path to memdisk binary on USB
        
        Returns:
            GRUB menuentry configuration
        """
        return f"""
menuentry '{display_name} (Windows PE - RAM Boot)' {{
    echo "========================================"
    echo "  Loading Windows PE into RAM"
    echo "========================================"
    echo ""
    echo "This may take 1-3 minutes depending on:"
    echo "  - ISO size"
    echo "  - Available RAM"
    echo "  - USB speed"
    echo ""
    echo "Please wait..."
    
    # Find data partition
    search --no-floppy --set=root --label LUXusb --hint hd0,gpt3
    if [ "$root" = "" ]; then
        search --no-floppy --set=root --label LUXusb --hint hd1,gpt3
    fi
    if [ "$root" = "" ]; then
        search --no-floppy --set=root --label LUXusb
    fi
    
    if [ "$root" = "" ]; then
        echo ""
        echo "ERROR: Could not find LUXusb data partition"
        echo "Press any key to return to menu..."
        read
    else
        # Load Windows PE ISO into RAM via MEMDISK
        # Note: Windows PE needs 'iso' mode for proper booting
        echo ""
        echo "Loading ISO: {iso_path}"
        linux16 {memdisk_path} iso raw
        initrd16 {iso_path}
    fi
}}
"""
    
    def get_memdisk_boot_entry(
        self,
        iso_path: str,
        display_name: str,
        memdisk_path: str = "/boot/memdisk"
    ) -> str:
        """
        Generate GRUB menuentry for MEMDISK booting
        
        Args:
            iso_path: Path to ISO file (relative to data partition)
            display_name: Display name for menu entry
            memdisk_path: Path to memdisk binary on USB
        
        Returns:
            GRUB menuentry configuration
        """
        return f"""
menuentry '{display_name} (RAM Boot - MEMDISK)' {{
    echo "Loading {display_name} into RAM..."
    echo "This may take 30-60 seconds..."
    
    # Find data partition
    search --no-floppy --set=root --label LUXusb --hint hd0,gpt3
    if [ "$root" = "" ]; then
        search --no-floppy --set=root --label LUXusb --hint hd1,gpt3
    fi
    if [ "$root" = "" ]; then
        search --no-floppy --set=root --label LUXusb
    fi
    
    if [ "$root" = "" ]; then
        echo "ERROR: Could not find LUXusb data partition"
        echo "Press any key to return to menu..."
        read
    else
        # Load ISO into RAM via MEMDISK
        linux16 {memdisk_path} iso raw
        initrd16 {iso_path}
    fi
}}
"""
    
    def copy_memdisk_to_usb(self, usb_boot_dir: Path) -> bool:
        """
        Copy MEMDISK binary to USB boot directory
        
        Args:
            usb_boot_dir: USB boot directory (e.g., /mnt/efi/boot)
        
        Returns:
            True if successful
        """
        if not self.memdisk_binary:
            logger.warning("MEMDISK binary not found, skipping copy")
            return False
        
        dest = usb_boot_dir / "memdisk"
        
        try:
            import shutil
            shutil.copy2(self.memdisk_binary, dest)
            logger.info(f"Copied MEMDISK to {dest}")
            return True
        except (OSError, IOError) as e:
            logger.error(f"Failed to copy MEMDISK: {e}")
            return False
    
    def get_install_instructions(self) -> str:
        """
        Get instructions for installing MEMDISK
        
        Returns:
            Installation instructions for user
        """
        return """
To enable MEMDISK support for small utility ISOs, install syslinux:

Ubuntu/Debian:
    sudo apt install syslinux-common

Fedora:
    sudo dnf install syslinux

Arch:
    sudo pacman -S syslinux

MEMDISK allows booting small ISOs (<512MB) by loading them entirely into RAM.
This provides better compatibility for:
- System rescue ISOs (SystemRescue, Super Grub2 Disk)
- Diagnostic tools (Memtest86+, HDAT2)
- Antivirus boot disks (Kaspersky Rescue Disk)
- Partition tools (GParted Live)
"""


def detect_small_isos(iso_paths: list[Path]) -> dict[Path, bool]:
    """
    Detect which ISOs are small enough for MEMDISK
    
    Args:
        iso_paths: List of ISO file paths
    
    Returns:
        Dictionary mapping ISO path to whether MEMDISK should be used
    """
    memdisk = MEMDISKSupport()
    results = {}
    
    for iso_path in iso_paths:
        if not iso_path.exists():
            results[iso_path] = False
            continue
        
        size_mb = iso_path.stat().st_size // (1024 * 1024)
        results[iso_path] = memdisk.should_use_memdisk(size_mb)
    
    return results

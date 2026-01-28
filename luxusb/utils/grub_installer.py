"""
GRUB bootloader installation and configuration
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional

from luxusb.utils.distro_manager import Distro
from luxusb.utils.custom_iso import CustomISO

logger = logging.getLogger(__name__)


class GRUBInstaller:
    """Install and configure GRUB2 bootloader"""
    
    def __init__(self, device: str, efi_mount: Path):
        """
        Initialize GRUB installer
        
        Args:
            device: Device path (e.g., /dev/sdb)
            efi_mount: Mount point of EFI partition
        """
        self.device = device
        self.efi_mount = efi_mount
        self.grub_dir = efi_mount / "EFI" / "BOOT"
    
    def install(self) -> bool:
        """
        Install GRUB bootloader for both BIOS and UEFI
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Installing GRUB to %s (BIOS + UEFI)", self.device)
        
        try:
            # Create GRUB directory
            self.grub_dir.mkdir(parents=True, exist_ok=True)
            
            # Install GRUB for BIOS (Legacy systems)
            if not self._install_grub_bios():
                logger.warning("BIOS GRUB installation failed, continuing with UEFI only")
            
            # Install GRUB for UEFI (modern systems)
            if not self._install_grub_efi():
                return False
            
            # Create default GRUB configuration
            if not self._create_default_config():
                return False
            
            logger.info("GRUB installation completed successfully")
            return True
            
        except (subprocess.CalledProcessError, OSError) as e:
            logger.exception("Failed to install GRUB: %s", e)
            return False
    
    def _install_grub_bios(self) -> bool:
        """Install GRUB for BIOS/Legacy systems"""
        logger.info("Installing GRUB for BIOS (i386-pc)...")
        
        try:
            # Install GRUB to MBR and BIOS boot partition
            subprocess.run(
                [
                    'grub-install',
                    '--target=i386-pc',
                    '--boot-directory=' + str(self.efi_mount / 'boot'),
                    '--recheck',
                    self.device
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("BIOS GRUB installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to install BIOS GRUB: %s", e.stderr)
            return False
        except FileNotFoundError:
            logger.error("grub-install not found - GRUB not installed on system")
            return False
    
    def _install_grub_efi(self) -> bool:
        """Install GRUB for UEFI systems"""
        logger.info("Installing GRUB for UEFI...")
        
        try:
            # Install GRUB to EFI partition
            subprocess.run(
                [
                    'grub-install',
                    '--target=x86_64-efi',
                    '--efi-directory=' + str(self.efi_mount),
                    '--boot-directory=' + str(self.efi_mount / 'boot'),
                    '--removable',  # Create fallback bootloader
                    '--recheck',
                    self.device
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("GRUB installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to install GRUB: %s", e.stderr)
            # Try alternative method with grub-mkimage
            return self._install_grub_manual()
    
    def _install_grub_manual(self) -> bool:
        """Manual GRUB installation (fallback method)"""
        logger.info("Trying manual GRUB installation...")
        
        try:
            # Create bootloader file manually with comprehensive module list
            subprocess.run(
                [
                    'grub-mkimage',
                    '-o', str(self.grub_dir / 'BOOTX64.EFI'),
                    '-O', 'x86_64-efi',
                    '-p', '/boot/grub',
                    # Partition support
                    'part_gpt', 'part_msdos',
                    # Filesystem support
                    'fat', 'ext2', 'ntfs', 'exfat',
                    # ISO/CD support
                    'iso9660', 'udf',
                    # Core boot modules
                    'normal', 'boot', 'linux', 'chain', 'configfile',
                    # Loopback for ISO booting (essential)
                    'loopback',
                    # Search and utilities
                    'search', 'search_fs_file', 'search_fs_uuid',
                    'search_label',
                    # Video/display
                    'all_video', 'gfxterm', 'gfxmenu',
                    # Other utilities
                    'echo', 'test', 'sleep', 'reboot', 'halt'
                ],
                capture_output=True,
                check=True
            )
            
            logger.info("Manual GRUB installation successful")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error("Manual GRUB installation failed: %s", e.stderr)
            return False
    
    def _create_default_config(self) -> bool:
        """Create default GRUB configuration"""
        grub_cfg_dir = self.efi_mount / "boot" / "grub"
        grub_cfg_dir.mkdir(parents=True, exist_ok=True)
        grub_cfg = grub_cfg_dir / "grub.cfg"
        
        config = """# GRUB Configuration for LUXusb
set timeout=30
set default=0

# Graphics configuration
set gfxmode=auto
set gfxpayload=keep

# Theme
set menu_color_normal=white/black
set menu_color_highlight=black/light-gray

# Pagination for long menus
set pager=1

# Load graphics modules
insmod all_video
insmod gfxterm

# Load font for better display
if loadfont unicode ; then
    set gfxmode=auto
    terminal_output gfxterm
else
    terminal_output console
fi

# Main menu
menuentry 'LUXusb - No ISOs Found' {
    echo "No bootable ISOs found on this device"
    echo "Please download ISOs using LUXusb application"
    echo "Press any key to reboot..."
    read
    reboot
}

menuentry 'Reboot' {
    reboot
}

menuentry 'Power Off' {
    halt
}
"""
        
        try:
            with open(grub_cfg, 'w', encoding='utf-8') as f:
                f.write(config)
            logger.info("Created GRUB config at %s", grub_cfg)
            return True
        except (OSError, IOError) as e:
            logger.error("Failed to create GRUB config: %s", e)
            return False
    
    def update_config_with_isos(
        self, 
        iso_paths: List[Path], 
        distros: List[Distro], 
        custom_isos: Optional[List[CustomISO]] = None,
        timeout: int = 30
    ) -> bool:
        """
        Update GRUB configuration with available ISOs
        
        Args:
            iso_paths: List of ISO file paths (relative to data partition root)
            distros: List of corresponding Distro objects
            custom_isos: Optional list of custom ISO objects (Phase 3.1)
            timeout: GRUB menu timeout in seconds (default: 30)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Updating GRUB configuration with %d ISOs", len(iso_paths))
        
        grub_cfg = self.efi_mount / "boot" / "grub" / "grub.cfg"
        
        # Generate menu entries for distribution ISOs
        entries = self._generate_iso_entries(iso_paths, distros)
        
        # Generate entries for custom ISOs
        if custom_isos:
            custom_entries = self._generate_custom_iso_entries(custom_isos)
            entries = f"{entries}\n\n# Custom ISOs\n{custom_entries}"
        
        total_count = len(iso_paths) + (len(custom_isos) if custom_isos else 0)
        
        config = f"""# GRUB Configuration for LUXusb
set timeout={timeout}
set default=0

# CRITICAL: Remove TPM module to fix GRUB 2.04+ loopback boot black screen
# See: https://bugs.launchpad.net/ubuntu/+source/grub2/+bug/1851311
rmmod tpm

# Graphics configuration
set gfxmode=auto
set gfxpayload=keep
set pager=1

# Load all required modules upfront
insmod part_gpt
insmod part_msdos
insmod fat
insmod ext2
insmod loopback
insmod iso9660
insmod udf
insmod linux
insmod search
insmod search_fs_file
insmod search_fs_uuid
insmod search_label
insmod regexp
insmod test
insmod all_video
insmod gfxterm

# Set up graphics and load font
if loadfont unicode ; then
    set gfxmode=auto
    terminal_output gfxterm
else
    terminal_output console
fi
set menu_color_normal=white/black
set menu_color_highlight=black/light-gray

# Diagnostic information
echo "LUXusb Multi-Boot Menu"
echo "======================"
echo "GRUB version: $grub_version"
echo "{total_count} distribution(s) available"
echo ""

{entries}

menuentry 'Reboot' {{
    reboot
}}

menuentry 'Power Off' {{
    halt
}}
"""
        
        try:
            with open(grub_cfg, 'w', encoding='utf-8') as f:
                f.write(config)
            logger.info("GRUB configuration updated successfully")
            return True
        except (OSError, IOError) as e:
            logger.error("Failed to update GRUB config: %s", e)
            return False
    
    def _generate_iso_entries(
        self, iso_paths: List[Path], distros: List[Distro]
    ) -> str:
        """Generate GRUB menu entries for ISOs"""
        entries = []
        # Hotkeys for quick access (avoid GRUB reserved keys: c, e)
        hotkeys = 'abdfghijklmnopqrstuvwxyz123456789'
        
        for idx, (iso_path, distro) in enumerate(zip(iso_paths, distros)):
            # Get relative path from data partition root
            # iso_path is absolute (e.g., /tmp/luxusb-mount/data/isos/arch/arch.iso)
            # We need to extract the path relative to the data partition
            # (e.g., /isos/arch/arch.iso for GRUB)
            iso_path_obj = Path(iso_path)
            
            # Find "isos" directory in path and construct relative path from there
            parts = iso_path_obj.parts
            try:
                isos_idx = parts.index('isos')
                # Reconstruct path from 'isos' onwards with leading slash
                iso_rel = '/' + '/'.join(parts[isos_idx:])
            except ValueError:
                # Fallback: if 'isos' not in path, use just the filename
                logger.warning(f"Could not find 'isos' in path {iso_path}, using filename only")
                iso_rel = f"/{iso_path_obj.name}"
            
            release = distro.latest_release
            if not release:
                continue
            
            # Determine boot parameters based on distro family
            boot_cmds = self._get_boot_commands(distro, iso_rel)
            
            # Add hotkey if available
            hotkey_attr = ''
            if idx < len(hotkeys):
                hotkey = hotkeys[idx]
                hotkey_attr = f" --hotkey={hotkey}"
                display_name = f"{distro.name} [{hotkey.upper()}]"
            else:
                display_name = distro.name
            
            entry = f"""
menuentry '{display_name} {release.version}'{hotkey_attr} {{
    echo "Loading {distro.name}..."
    
    # Find data partition (partition 3 on USB device)
    # Multi-method search with fallbacks for different hardware configurations
    search --no-floppy --set=root --label LUXusb --hint hd0,gpt3
    if [ "$root" = "" ]; then
        # Fallback: USB might be second drive (hd1)
        search --no-floppy --set=root --label LUXusb --hint hd1,gpt3
    fi
    if [ "$root" = "" ]; then
        # Fallback: Exhaustive search without hint
        search --no-floppy --set=root --label LUXusb
    fi
    
    # Verify partition was found
    if [ "$root" = "" ]; then
        echo "ERROR: Could not find LUXusb data partition"
        echo "Please check USB device is inserted correctly"
        echo "Press any key to return to menu..."
        read
        return
    fi
    echo "Found root partition: $root"
    
    # Verify TPM is unloaded (critical for GRUB 2.04+)
    # Note: Errors are automatically suppressed in GRUB
    rmmod tpm
    
    # Verify ISO file exists before attempting loopback
    set isopath="{iso_rel}"
    if [ ! -f "$isopath" ]; then
        echo "ERROR: ISO file not found: $isopath"
        echo "Partition: $root"
        echo "Contents of /isos/:"
        ls /isos/ || echo "Cannot list /isos/ directory"
        echo "Press any key to return to menu..."
        read
        return
    fi
    
    # Load ISO via loopback
    echo "Loading ISO: {iso_rel}"
    loopback loop "$isopath"
    
{boot_cmds}
}}
"""
            entries.append(entry)
        
        return '\n'.join(entries)
    
    def _get_boot_commands(self, distro: Distro, iso_path: str) -> str:
        """Get distro-specific boot commands"""
        family = getattr(distro, 'family', 'independent')
        distro_id = distro.id
        
        # Ubuntu-based (Ubuntu, Pop!_OS, Linux Mint, elementary)
        if (family == 'debian' or
                distro_id in ['ubuntu', 'popos', 'linuxmint',
                              'elementary']):
            return f"""    # Ubuntu/Debian style boot
    # Try loopback.cfg first (modern standard for Ubuntu 16.04+)
    if [ -f (loop)/boot/grub/loopback.cfg ]; then
        set iso_path="{iso_path}"
        export iso_path
        configfile (loop)/boot/grub/loopback.cfg
    # Try Debian Live (newer Debian ISOs)
    elif [ -f (loop)/live/vmlinuz ]; then
        echo "Booting Debian Live..."
        linux (loop)/live/vmlinuz boot=live findiso={iso_path} \
            components nomodeset noapic acpi=off
        initrd (loop)/live/initrd.img
    # Try Ubuntu/Mint casper
    elif [ -f (loop)/casper/vmlinuz ]; then
        echo "Booting Ubuntu/Casper..."
        linux (loop)/casper/vmlinuz boot=casper \
            iso-scan/filename={iso_path} noeject noprompt \
            rootdelay=10 usb-storage.delay_use=5 \
            nomodeset noapic acpi=off ---
        initrd (loop)/casper/initrd
    else
        echo "Error: Could not find kernel in ISO"
        echo "Searched: loopback.cfg, /live/vmlinuz, /casper/vmlinuz"
        echo "Press any key to return to menu..."
        read
    fi"""
        
        # Arch-based (Arch, Manjaro, CachyOS)
        elif family == 'arch' or distro_id in ['arch', 'manjaro', 'cachyos-desktop', 'cachyos-handheld']:
            return f"""    # Arch Linux style boot
    if [ -f (loop)/arch/boot/x86_64/vmlinuz-linux ]; then
        echo "Booting Arch Linux..."
        linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch img_dev=/dev/disk/by-label/LUXusb img_loop={iso_path} earlymodules=loop rootdelay=10 nomodeset noapic acpi=off
        initrd (loop)/arch/boot/x86_64/initramfs-linux.img
    elif [ -f (loop)/boot/vmlinuz-linux ]; then
        echo "Booting Arch Linux (alternate path)..."
        linux (loop)/boot/vmlinuz-linux archisobasedir=arch img_dev=/dev/disk/by-label/LUXusb img_loop={iso_path} earlymodules=loop rootdelay=10 nomodeset noapic acpi=off
        initrd (loop)/boot/initramfs-linux.img
    else
        echo "Error: Could not find Arch kernel in ISO"
        echo "Searched: /arch/boot/x86_64/vmlinuz-linux, /boot/vmlinuz-linux"
        echo "Press any key to return to menu..."
        read
    fi"""
        
        # Fedora-based (Fedora, Bazzite, Nobara)
        elif family == 'fedora' or distro_id in ['fedora', 'bazzite-desktop', 'bazzite-handheld', 'nobara']:
            return f"""    # Fedora style boot
    if [ -f (loop)/isolinux/vmlinuz ]; then
        echo "Booting Fedora..."
        linux (loop)/isolinux/vmlinuz iso-scan/filename={iso_path} root=live:LABEL=LUXusb rd.live.image nomodeset noapic acpi=off
        initrd (loop)/isolinux/initrd.img
    elif [ -f (loop)/images/pxeboot/vmlinuz ]; then
        echo "Booting Fedora (alternate path)..."
        linux (loop)/images/pxeboot/vmlinuz iso-scan/filename={iso_path} root=live:LABEL=LUXusb rd.live.image nomodeset noapic acpi=off
        initrd (loop)/images/pxeboot/initrd.img
    else
        echo "Error: Could not find Fedora kernel in ISO"
        echo "Searched: /isolinux/vmlinuz, /images/pxeboot/vmlinuz"
        echo "Press any key to return to menu..."
        read
    fi"""
        
        # openSUSE
        elif distro_id in ['opensuse-tumbleweed', 'opensuse-leap']:
            return f"""    # openSUSE style boot
    if [ -f (loop)/boot/x86_64/loader/linux ]; then
        echo "Booting openSUSE..."
        linux (loop)/boot/x86_64/loader/linux isofrom_device=/dev/disk/by-label/LUXusb isofrom_system={iso_path} nomodeset noapic acpi=off
        initrd (loop)/boot/x86_64/loader/initrd
    else
        echo "Error: Could not find openSUSE kernel in ISO"
        echo "Searched: /boot/x86_64/loader/linux"
        echo "Press any key to return to menu..."
        read
    fi"""
        
        # Generic fallback - try multiple common paths
        else:
            return f"""    # Generic multi-path boot attempt
    echo "Attempting generic boot..."
    # Try loopback.cfg first (best compatibility)
    if [ -f (loop)/boot/grub/loopback.cfg ]; then
        echo "Using loopback.cfg"
        set iso_path="{iso_path}"
        export iso_path
        configfile (loop)/boot/grub/loopback.cfg
    elif [ -f (loop)/casper/vmlinuz ]; then
        echo "Booting with casper (Ubuntu-style)..."
        linux (loop)/casper/vmlinuz boot=casper iso-scan/filename={iso_path} nomodeset noapic acpi=off noeject noprompt
        initrd (loop)/casper/initrd
    elif [ -f (loop)/isolinux/vmlinuz ]; then
        echo "Booting with isolinux..."
        linux (loop)/isolinux/vmlinuz iso-scan/filename={iso_path} nomodeset noapic acpi=off
        initrd (loop)/isolinux/initrd.img
    elif [ -f (loop)/arch/boot/x86_64/vmlinuz-linux ]; then
        echo "Booting with Arch kernel..."
        linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch img_loop={iso_path} nomodeset noapic acpi=off
        initrd (loop)/arch/boot/x86_64/initramfs-linux.img
    else
        echo "Error: Could not find bootable kernel in ISO"
        echo "Searched paths:"
        echo "  - /boot/grub/loopback.cfg"
        echo "  - /casper/vmlinuz"
        echo "  - /isolinux/vmlinuz"
        echo "  - /arch/boot/x86_64/vmlinuz-linux"
        echo "Press any key to return to menu..."
        read
    fi"""
    
    def _generate_custom_iso_entries(self, custom_isos: List[CustomISO]) -> str:
        """Generate GRUB menu entries for custom ISOs"""
        entries = []
        
        for custom_iso in custom_isos:
            # Get relative path from data partition
            iso_rel = f"/isos/custom/{custom_iso.filename}"
            
            entry = f"""
menuentry '{custom_iso.display_name} (Custom)' {{
    echo "Loading custom ISO: {custom_iso.display_name}"
    
    # Find data partition with fallbacks
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
        return
    fi
    echo "Found root partition: $root"
    
    # Verify TPM is unloaded
    rmmod tpm
    
    # Verify ISO exists
    set isopath="{iso_rel}"
    if [ ! -f "$isopath" ]; then
        echo "ERROR: Custom ISO not found: $isopath"
        echo "Press any key to return to menu..."
        read
        return
    fi
    
    # Load ISO via loopback
    echo "Loading ISO: {iso_rel}"
    loopback loop "$isopath"
    
    # Generic boot attempt
    # Try common boot paths
    echo "Attempting to boot {custom_iso.display_name}..."
    
    # Try Ubuntu/Debian style
    if [ -f (loop)/casper/vmlinuz ]; then
        echo "Using Ubuntu/Casper boot method..."
        linux (loop)/casper/vmlinuz boot=casper iso-scan/filename={iso_rel} nomodeset noapic acpi=off noeject noprompt
        initrd (loop)/casper/initrd
    # Try Fedora/CentOS style
    elif [ -f (loop)/isolinux/vmlinuz ]; then
        echo "Using Fedora/isolinux boot method..."
        linux (loop)/isolinux/vmlinuz iso-scan/filename={iso_rel} nomodeset noapic acpi=off
        initrd (loop)/isolinux/initrd.img
    # Try Arch style
    elif [ -f (loop)/arch/boot/x86_64/vmlinuz-linux ]; then
        echo "Using Arch boot method..."
        linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=ARCHISO nomodeset noapic acpi=off
        initrd (loop)/arch/boot/x86_64/initramfs-linux.img
    else
        echo "Could not find bootable kernel in ISO"
        echo "This ISO may not be bootable or uses an unsupported boot method"
        echo "Searched: /casper/vmlinuz, /isolinux/vmlinuz, /arch/boot/x86_64/vmlinuz-linux"
        echo "Press any key to return to menu..."
        read
    fi
}}
"""
            entries.append(entry)
        
        return '\n'.join(entries)


def install_grub(device: str, efi_mount: Path) -> bool:
    """
    Convenience function to install GRUB
    
    Args:
        device: Device path
        efi_mount: EFI partition mount point
        
    Returns:
        True if successful, False otherwise
    """
    installer = GRUBInstaller(device, efi_mount)
    return installer.install()

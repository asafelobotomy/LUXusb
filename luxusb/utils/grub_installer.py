"""
GRUB bootloader installation and configuration
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional

from luxusb._version import __version__
from luxusb.utils.distro_manager import Distro
from luxusb.utils.custom_iso import CustomISO
from luxusb.utils.memdisk import MEMDISKSupport
from luxusb.utils.persistence import PersistenceManager
from luxusb.utils.grub_theme import GRUBTheme

logger = logging.getLogger(__name__)


class GRUBInstaller:
    """Install and configure GRUB2 bootloader"""
    
    def __init__(self, device: str, efi_mount: Path, data_mount: Optional[Path] = None):
        """
        Initialize GRUB installer
        
        Args:
            device: Device path (e.g., /dev/sdb)
            efi_mount: Mount point of EFI partition
            data_mount: Mount point of data partition (for persistence)
        """
        self.device = device
        self.efi_mount = efi_mount
        self.data_mount = data_mount
        self.grub_dir = efi_mount / "EFI" / "BOOT"
        self.memdisk_support = MEMDISKSupport()
        self.theme_manager = GRUBTheme(efi_mount)
        
        # Initialize persistence manager if data partition provided
        self.persistence_manager = None
        if data_mount:
            self.persistence_manager = PersistenceManager(data_mount)
    
    def install(self) -> bool:
        """
        Install GRUB bootloader for BIOS and UEFI (64-bit + 32-bit)
        
        Installs:
        - i386-pc (BIOS/Legacy)
        - x86_64-efi (64-bit UEFI)
        - i386-efi (32-bit UEFI, optional)
        
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
            
            # Install MEMDISK for small ISO support (optional)
            self._install_memdisk()
            
            # Install GRUB theme (optional but recommended)
            self._install_theme()
            
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
        """Install GRUB for UEFI systems (64-bit and 32-bit)"""
        logger.info("Installing GRUB for UEFI...")
        
        # Install 64-bit UEFI (primary target)
        success_64 = self._install_grub_target('x86_64-efi')
        if not success_64:
            logger.error("Failed to install 64-bit UEFI GRUB")
            return self._install_grub_manual()
        
        # Try to install 32-bit UEFI (optional, for 2010-2012 tablets)
        # This is a best-effort installation - failure is acceptable
        success_32 = self._install_grub_target('i386-efi', optional=True)
        if success_32:
            logger.info("32-bit UEFI support enabled (Bay Trail/Cherry Trail tablets)")
        else:
            logger.info("32-bit UEFI not available (requires grub-efi-ia32-bin package)")
        
        return True
    
    def _install_grub_target(self, target: str, optional: bool = False) -> bool:
        """Install GRUB for a specific target architecture"""
        logger.info(f"Installing GRUB target: {target}...")
        
        try:
            subprocess.run(
                [
                    'grub-install',
                    f'--target={target}',
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
            
            logger.info(f"GRUB {target} installed successfully")
            
            # Verify font file exists (critical for menu visibility)
            font_path = self.efi_mount / "boot" / "grub" / "fonts" / "unicode.pf2"
            if not font_path.exists():
                logger.warning(f"Font file not found at {font_path}, trying to copy from system")
                # Try to find and copy system font
                system_font_paths = [
                    Path("/usr/share/grub/unicode.pf2"),
                    Path("/usr/share/grub2/unicode.pf2"),
                    Path("/boot/grub/fonts/unicode.pf2"),
                    Path("/boot/grub2/fonts/unicode.pf2")
                ]
                for sys_font in system_font_paths:
                    if sys_font.exists():
                        import shutil
                        font_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(sys_font, font_path)
                        logger.info(f"Copied font from {sys_font} to {font_path}")
                        break
                else:
                    logger.error("Could not find unicode.pf2 font file on system!")
                    logger.error("Menu may be invisible. Install grub-common or grub2-common package.")
            
            return True
            
        except subprocess.CalledProcessError as e:
            if optional:
                logger.debug(f"Optional {target} installation failed: {e.stderr}")
            else:
                logger.error(f"Failed to install GRUB {target}: {e.stderr}")
            return False
        except FileNotFoundError:
            if optional:
                logger.debug(f"grub-install not found for {target} (package not installed)")
            else:
                logger.error("grub-install not found - GRUB not installed on system")
            return False
    
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
    
    def _install_memdisk(self) -> bool:
        """
        Install MEMDISK binary for small ISO support (optional)
        
        Returns:
            True if successful or not available (non-critical)
        """
        if not self.memdisk_support.is_memdisk_available():
            logger.info("MEMDISK not available (install syslinux-common for utility ISO support)")
            return True  # Non-critical, continue anyway
        
        boot_dir = self.efi_mount / "boot"
        boot_dir.mkdir(parents=True, exist_ok=True)
        
        if self.memdisk_support.copy_memdisk_to_usb(boot_dir):
            logger.info("MEMDISK installed successfully (enables small ISO RAM booting)")
            return True
        else:
            logger.warning("MEMDISK installation failed (utility ISOs will use standard loopback)")
            return True  # Non-critical
    
    def _install_theme(self) -> bool:
        """
        Install GRUB theme (optional)
        
        Returns:
            True if successful or skipped (non-critical)
        """
        try:
            if self.theme_manager.install_default_theme():
                logger.info("✓ GRUB theme installed")
                return True
            else:
                logger.warning("Theme installation failed, using basic theme")
                return True  # Non-critical
        except Exception as e:
            logger.warning(f"Theme installation error: {e}")
            return True  # Non-critical
    
    def _create_default_config(self) -> bool:
        """Create default GRUB configuration"""
        grub_cfg_dir = self.efi_mount / "boot" / "grub"
        grub_cfg_dir.mkdir(parents=True, exist_ok=True)
        grub_cfg = grub_cfg_dir / "grub.cfg"
        
        # Check if theme is installed
        theme_line = ""
        if self.theme_manager.is_theme_installed():
            theme_path = self.theme_manager.get_theme_path()
            theme_line = f"\n# Load custom theme\nset theme={theme_path}"
        
        config = f"""# GRUB Configuration for LUXusb
set timeout=30
set timeout_style=menu
set default=0

# Graphics configuration
set gfxmode=auto
set gfxpayload=keep{theme_line}

# Basic theme colors (fallback if theme not available)
set menu_color_normal=white/black
set menu_color_highlight=black/light-gray

# Pagination for long menus
set pager=1

# Load graphics modules
insmod all_video
insmod gfxterm

# Load font for better display
load_video
if loadfont $prefix/fonts/unicode.pf2 ; then
    terminal_output gfxterm
else
    terminal_output console
fi

# Main menu
menuentry 'LUXusb - No ISOs Found' {{
    echo "No bootable ISOs found on this device"
    echo "Please download ISOs using LUXusb application"
    echo "Press any key to reboot..."
    read
    reboot
}}

menuentry 'Reboot' {{
    reboot
}}

menuentry 'Power Off' {{
    halt
}}
"""
        
        try:
            # Ensure directory exists (defensive coding)
            grub_cfg.parent.mkdir(parents=True, exist_ok=True)
            
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
        
        grub_cfg_dir = self.efi_mount / "boot" / "grub"
        grub_cfg_dir.mkdir(parents=True, exist_ok=True)
        grub_cfg = grub_cfg_dir / "grub.cfg"
        
        # Generate menu entries for distribution ISOs
        entries = self._generate_iso_entries(iso_paths, distros)
        
        # Generate entries for custom ISOs
        if custom_isos:
            custom_entries = self._generate_custom_iso_entries(custom_isos)
            entries = f"{entries}\n\n# Custom ISOs\n{custom_entries}"
        
        total_count = len(iso_paths) + (len(custom_isos) if custom_isos else 0)
        
        # Build help text with keyboard shortcuts as echo commands
        help_lines = [
            "╔═══════════════════════════════════════════════════════════════════════════╗",
            "║                         LUXusb Multiboot Menu                             ║",
            f"║                            Version {__version__}                                ║",
            "╠═══════════════════════════════════════════════════════════════════════════╣",
            f"║  {total_count} ISO{'s' if total_count != 1 else ''} available                                                           ║",
            "║                                                                           ║",
            "║  Navigation:                                                              ║",
            "║    ↑/↓     - Select menu item                                             ║",
            "║    Enter   - Boot selected item                                           ║",
            "║    [A-Z]   - Quick jump to ISO (hotkeys shown in [brackets])              ║",
            "║    Esc     - Return to previous menu / Exit submenu                       ║",
            "║                                                                           ║",
            "║  Boot Options (in ISO submenus):                                          ║",
            "║    Normal        - Standard boot with default kernel parameters           ║",
            "║    Safe Graphics - Disable GPU acceleration (nomodeset + vendor flags)    ║",
            "║    MEMDISK       - Load entire ISO into RAM (small ISOs only)             ║",
            "║                                                                           ║",
            "║  Advanced:                                                                ║",
            "║    Press 'c' for GRUB command line                                        ║",
            "║    Press 'e' to edit boot parameters                                      ║",
            "║                                                                           ║",
            "║  Timeout: Menu auto-boots first item in 30 seconds                        ║",
            "║           Press any key to stop countdown                                 ║",
            "╚═══════════════════════════════════════════════════════════════════════════╝",
            "",
            "Press ESC to return to menu..."
        ]
        
        # Convert to echo commands for GRUB
        help_text = '\n    '.join([f'echo "{line}"' for line in help_lines])
        
        config = f"""# ═══════════════════════════════════════════════════════════════════════════
# GRUB Configuration for LUXusb v{__version__}
# Generated: $(date)
# Total ISOs: {total_count}
# ═══════════════════════════════════════════════════════════════════════════

# ═══ MODULE LOADING ═══
# Load all required GRUB modules first
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

# ═══ GRAPHICS SETUP ═══
# Initialize video subsystem and load font
# CRITICAL: Font path must be explicit ($prefix/fonts/unicode.pf2)
# Without proper font, menu will be invisible (black screen)
set gfxmode=auto
set gfxpayload=keep
load_video
if loadfont $prefix/fonts/unicode.pf2 ; then
    # Font loaded successfully - use graphics terminal
    terminal_output gfxterm
else
    # Font loading failed - fall back to text console
    # This prevents invisible menu (black screen)
    terminal_output console
    echo "Warning: Font file not found, using text mode"
fi

# ═══ MENU APPEARANCE ═══
set menu_color_normal=white/black
set menu_color_highlight=black/light-gray
set pager=1

# ═══ MENU BEHAVIOR ═══
# Set timeout AFTER terminal is initialized
set timeout=30
set timeout_style=menu
set default=0

# ═══ STORAGE SETUP ═══
# Find LUXusb data partition by label
search --no-floppy --set=root --label LUXusb

# ═══ HELP & INFORMATION ═══
menuentry 'ℹ️  View Help & Keyboard Shortcuts' {{
    clear
    {help_text}
    sleep --interruptible 9999
}}

# ═══ BOOTABLE ISOS ═══

{entries}

# ═══ SYSTEM CONTROLS ═══

menuentry '🔄 Reboot System' {{
    echo "Rebooting..."
    reboot
}}

menuentry '⏻  Power Off' {{
    echo "Shutting down..."
    halt
}}

# ═══════════════════════════════════════════════════════════════════════════
# End of GRUB Configuration
# ═══════════════════════════════════════════════════════════════════════════
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
        """Generate hierarchical GRUB menu entries for ISOs with boot options"""
        entries = []
        # Hotkeys for quick access (avoid GRUB reserved keys: c, e)
        hotkeys = 'abdfghijklmnopqrstuvwxyz123456789'
        
        for idx, (iso_path, distro) in enumerate(zip(iso_paths, distros)):
            # Get relative path from data partition root
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
            
            # Add hotkey if available
            hotkey_attr = ''
            if idx < len(hotkeys):
                hotkey = hotkeys[idx]
                hotkey_attr = f"--hotkey={hotkey} "
                display_name = f"[{hotkey.upper()}] {distro.name} {release.version}"
            else:
                display_name = f"{distro.name} {release.version}"
            
            # Check if ISO is small enough for MEMDISK
            iso_size_mb = iso_path_obj.stat().st_size // (1024 * 1024) if iso_path_obj.exists() else 0
            use_memdisk = self.memdisk_support.should_use_memdisk(iso_size_mb)
            is_windows_pe = self.memdisk_support.is_windows_pe_iso(iso_path_obj)
            
            # Create submenu with boot options and descriptions
            submenu = f"""
submenu {hotkey_attr}'{display_name}' {{
  # ─── {distro.name} {release.version} ───
  # Description: {distro.description if hasattr(distro, 'description') else 'Linux Distribution'}
  # ISO Size: {iso_size_mb} MB
  # Architecture: {release.architecture if hasattr(release, 'architecture') else 'x86_64'}
  
  menuentry '▶ Boot Normally (Recommended)' {{
    # Standard boot with default kernel parameters
    set isofile="{iso_rel}"
    rmmod tpm
    loopback -d loop 2>/dev/null || true
    loopback loop "$isofile"
{self._get_boot_commands(distro, iso_rel, safe_mode=False)}
  }}
  
  menuentry '🛡️  Safe Graphics Mode (GPU Issues)' {{
    # Disables GPU acceleration for compatibility
    # Use if: Black screen, corrupted display, GPU hangs
    # Adds: nomodeset i915.modeset=0 nouveau.modeset=0 radeon.modeset=0
    set isofile="{iso_rel}"
    rmmod tpm
    loopback -d loop 2>/dev/null || true
    loopback loop "$isofile"
{self._get_boot_commands(distro, iso_rel, safe_mode=True)}
  }}"""
            
            # Add MEMDISK option if applicable
            if is_windows_pe and self.memdisk_support.is_memdisk_available():
                submenu += f"""
  
  menuentry '💾 MEMDISK Mode (Windows PE)' {{
    # Loads entire ISO into RAM for Windows PE environments
    # Requires: {iso_size_mb} MB of available RAM
    # Benefit: Faster, no CD emulation issues
    set isofile="{iso_rel}"
    loopback -d loop 2>/dev/null || true
{self.memdisk_support.get_windows_pe_boot_commands(iso_rel, "/boot/memdisk")}
  }}"""
                logger.info(f"Added Windows PE MEMDISK option for {distro.name}")
            elif use_memdisk and self.memdisk_support.is_memdisk_available():
                submenu += f"""
  
  menuentry '💾 MEMDISK Mode (Load to RAM)' {{
    # Loads entire ISO into system RAM
    # Requires: {iso_size_mb} MB of available RAM (ISO size)
    # Benefit: Faster boot, USB can be removed after loading
    # Warning: Slower initial load, uses RAM
    set isofile="{iso_rel}"
    loopback -d loop 2>/dev/null || true
{self.memdisk_support.get_memdisk_boot_commands(iso_rel, "/boot/memdisk")}
  }}"""
                logger.info(f"Added MEMDISK option for {distro.name} ({iso_size_mb}MB)")
            
            # Close submenu with return option
            submenu += f"""
  
  menuentry '←  Return to Main Menu' {{
    # Press ESC or select this to go back
    # Tip: ESC key works from anywhere in submenus
    true
  }}
}}
"""
            entries.append(submenu)
        
        return '\n'.join(entries)
    
    def _get_boot_commands(self, distro: Distro, iso_path: str, safe_mode: bool = False) -> str:
        """Get distro-specific boot commands with optional safe mode parameters
        
        Args:
            distro: Distribution object
            iso_path: Path to ISO file
            safe_mode: If True, add safe graphics parameters (nomodeset, etc.)
        """
        family = getattr(distro, 'family', 'independent')
        distro_id = distro.id
        
        # Safe mode kernel parameters
        # Based on research: nomodeset is critical, vendor-specific modeset=0 for compatibility
        # Avoid nolapic/nolapic_timer/acpi=off - they break newer systems
        safe_params = ""
        if safe_mode:
            safe_params = " nomodeset i915.modeset=0 nouveau.modeset=0 radeon.modeset=0 amdgpu.modeset=0"
        
        # Get persistence parameters if available
        persistence_params = ""
        if self.persistence_manager and self.persistence_manager.is_persistence_supported(distro_id):
            # Check if persistence file exists
            persistence_files = self.persistence_manager.list_persistence_files()
            if distro_id in persistence_files:
                kernel_params = self.persistence_manager.get_kernel_params(distro_id)
                if kernel_params:
                    persistence_params = " " + " ".join(kernel_params)
                    logger.info(f"Added persistence for {distro_id}: {persistence_params}")
        
        # Ubuntu-based (Ubuntu, Pop!_OS, Linux Mint, elementary)
        if (family == 'debian' or
                distro_id in ['ubuntu', 'popos', 'linuxmint',
                              'elementary']):
            return f"""    if [ -f (loop)/boot/grub/loopback.cfg ]; then
      set iso_path="{iso_path}"
      export iso_path
      configfile (loop)/boot/grub/loopback.cfg
    elif [ -f (loop)/live/vmlinuz ]; then
      linux (loop)/live/vmlinuz boot=live findiso={iso_path} components quiet splash{persistence_params}{safe_params}
      initrd (loop)/live/initrd.img
    elif [ -f (loop)/casper/vmlinuz ]; then
      linux (loop)/casper/vmlinuz boot=casper iso-scan/filename={iso_path} quiet splash{persistence_params}{safe_params}
      initrd (loop)/casper/initrd
    fi"""
        
        # Arch-based (Arch, Manjaro, CachyOS)
        elif family == 'arch' or distro_id in ['arch', 'manjaro', 'cachyos-desktop', 'cachyos-handheld']:
            return f"""    if [ -f (loop)/arch/boot/x86_64/vmlinuz-linux ]; then
      linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch img_dev=/dev/disk/by-label/LUXusb img_loop={iso_path} earlymodules=loop quiet{persistence_params}{safe_params}
      initrd (loop)/arch/boot/x86_64/initramfs-linux.img
    elif [ -f (loop)/boot/vmlinuz-linux ]; then
      linux (loop)/boot/vmlinuz-linux archisobasedir=arch img_dev=/dev/disk/by-label/LUXusb img_loop={iso_path} earlymodules=loop quiet{persistence_params}{safe_params}
      initrd (loop)/boot/initramfs-linux.img
    fi"""
        
        # Fedora-based (Fedora, Bazzite, Nobara)
        elif family == 'fedora' or distro_id in ['fedora', 'bazzite-desktop', 'bazzite-handheld', 'nobara']:
            return f"""    if [ -f (loop)/isolinux/vmlinuz ]; then
      linux (loop)/isolinux/vmlinuz iso-scan/filename={iso_path} root=live:LABEL=LUXusb rd.live.image quiet{persistence_params}{safe_params}
      initrd (loop)/isolinux/initrd.img
    elif [ -f (loop)/images/pxeboot/vmlinuz ]; then
      linux (loop)/images/pxeboot/vmlinuz iso-scan/filename={iso_path} root=live:LABEL=LUXusb rd.live.image quiet{persistence_params}{safe_params}
      initrd (loop)/images/pxeboot/initrd.img
    fi"""
        
        # openSUSE
        elif distro_id in ['opensuse-tumbleweed', 'opensuse-leap']:
            return f"""    if [ -f (loop)/boot/x86_64/loader/linux ]; then
      linux (loop)/boot/x86_64/loader/linux isofrom_device=/dev/disk/by-label/LUXusb isofrom_system={iso_path} quiet splash{safe_params}
      initrd (loop)/boot/x86_64/loader/initrd
    fi"""
        
        # Generic fallback - try multiple common paths
        else:
            return f"""    if [ -f (loop)/boot/grub/loopback.cfg ]; then
      set iso_path="{iso_path}"
      export iso_path
      configfile (loop)/boot/grub/loopback.cfg
    elif [ -f (loop)/casper/vmlinuz ]; then
      linux (loop)/casper/vmlinuz boot=casper iso-scan/filename={iso_path} quiet splash noeject noprompt{safe_params}
      initrd (loop)/casper/initrd
    elif [ -f (loop)/isolinux/vmlinuz ]; then
      linux (loop)/isolinux/vmlinuz iso-scan/filename={iso_path} quiet{safe_params}
      initrd (loop)/isolinux/initrd.img
    elif [ -f (loop)/arch/boot/x86_64/vmlinuz-linux ]; then
      linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch img_loop={iso_path} quiet{safe_params}
      initrd (loop)/arch/boot/x86_64/initramfs-linux.img
    fi"""
    
    def _generate_custom_iso_entries(self, custom_isos: List[CustomISO]) -> str:
        """Generate hierarchical GRUB menu entries for custom ISOs with boot options"""
        entries = []
        
        for custom_iso in custom_isos:
            # Get relative path from data partition
            iso_rel = f"/isos/custom/{custom_iso.filename}"
            
            # Create submenu with boot options
            submenu = f"""
submenu '{custom_iso.display_name} (Custom ISO)' {{
  
  menuentry 'Boot {custom_iso.display_name} (Normal)' {{
    set isofile="{iso_rel}"
    rmmod tpm
    loopback -d loop 2>/dev/null || true
    loopback loop "$isofile"
    
    # Try common boot paths - normal mode
    if [ -f (loop)/casper/vmlinuz ]; then
      linux (loop)/casper/vmlinuz boot=casper iso-scan/filename={iso_rel} quiet splash noeject noprompt
      initrd (loop)/casper/initrd
    elif [ -f (loop)/isolinux/vmlinuz ]; then
      linux (loop)/isolinux/vmlinuz iso-scan/filename={iso_rel} quiet
      initrd (loop)/isolinux/initrd.img
    elif [ -f (loop)/arch/boot/x86_64/vmlinuz-linux ]; then
      linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=ARCHISO
      initrd (loop)/arch/boot/x86_64/initramfs-linux.img
    fi
  }}
  
  menuentry 'Boot {custom_iso.display_name} (Safe Graphics)' {{
    set isofile="{iso_rel}"
    rmmod tpm
    loopback -d loop 2>/dev/null || true
    loopback loop "$isofile"
    
    # Try common boot paths - safe graphics mode
    if [ -f (loop)/casper/vmlinuz ]; then
      linux (loop)/casper/vmlinuz boot=casper iso-scan/filename={iso_rel} nomodeset i915.modeset=0 nouveau.modeset=0 noeject noprompt
      initrd (loop)/casper/initrd
    elif [ -f (loop)/isolinux/vmlinuz ]; then
      linux (loop)/isolinux/vmlinuz iso-scan/filename={iso_rel} nomodeset i915.modeset=0 nouveau.modeset=0
      initrd (loop)/isolinux/initrd.img
    elif [ -f (loop)/arch/boot/x86_64/vmlinuz-linux ]; then
      linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=ARCHISO nomodeset i915.modeset=0 nouveau.modeset=0
      initrd (loop)/arch/boot/x86_64/initramfs-linux.img
    fi
  }}
  
  menuentry 'Return to Main Menu' {{
    true
  }}
}}
"""
            entries.append(submenu)
        
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

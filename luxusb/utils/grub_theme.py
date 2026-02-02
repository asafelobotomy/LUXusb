"""
GRUB theme management for custom backgrounds and styling

Provides default LUXusb theme and supports custom theme installation.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class GRUBTheme:
    """Manage GRUB theme installation and configuration"""
    
    # Default theme configuration
    DEFAULT_THEME_CONFIG = """# LUXusb GRUB Theme
# Professional dark theme with LUXusb branding

# General settings
title-text: ""
desktop-image: "background.png"
desktop-color: "#000000"
terminal-font: "Unifont Regular 16"

# Boot menu
+ boot_menu {
    left = 15%
    top = 25%
    width = 70%
    height = 50%
    
    item_color = "#cccccc"
    selected_item_color = "#ffffff"
    item_height = 32
    item_padding = 8
    item_spacing = 4
    
    icon_width = 32
    icon_height = 32
    item_icon_space = 16
    
    # Menu box styling
    menu_pixmap_style = "boot_menu_*.png"
}

# Progress bar (for loading)
+ progress_bar {
    id = "__timeout__"
    left = 15%
    top = 80%
    width = 70%
    height = 24
    
    fg_color = "#4a90d9"
    bg_color = "#333333"
    border_color = "#666666"
    
    text = "Booting in %d seconds..."
    text_color = "#cccccc"
    font = "Unifont Regular 14"
}

# Help text
+ label {
    top = 90%
    left = 0
    width = 100%
    height = 20
    align = "center"
    color = "#888888"
    font = "Unifont Regular 12"
    text = "Press [E] to edit | [C] for command line | Use ↑↓ to select"
}
"""
    
    def __init__(self, efi_mount: Path):
        """
        Initialize GRUB theme manager
        
        Args:
            efi_mount: Mount point of EFI partition
        """
        self.efi_mount = efi_mount
        self.theme_dir = efi_mount / "boot" / "grub" / "themes" / "luxusb"
        self.logger = logging.getLogger(__name__)
    
    def install_default_theme(self) -> bool:
        """
        Install default LUXusb theme
        
        Creates theme directory and copies default theme files.
        Includes:
        - theme.txt configuration
        - background.png (generated gradient)
        - Optional distro icons
        
        Returns:
            True if installation successful, False otherwise
        """
        try:
            self.logger.info("Installing default GRUB theme...")
            
            # Create theme directory
            self.theme_dir.mkdir(parents=True, exist_ok=True)
            
            # Write theme configuration
            theme_file = self.theme_dir / "theme.txt"
            theme_file.write_text(self.DEFAULT_THEME_CONFIG)
            self.logger.info(f"✓ Theme config written: {theme_file}")
            
            # Create simple background (solid color or gradient)
            self._create_default_background()
            
            # Create menu box decorations (optional)
            self._create_menu_decorations()
            
            self.logger.info("✓ Default theme installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install theme: {e}")
            return False
    
    def _create_default_background(self) -> bool:
        """
        Create default background image
        
        Generates a simple gradient background using ImageMagick (if available)
        or creates a solid color PNG fallback.
        
        Returns:
            True if creation successful
        """
        background_file = self.theme_dir / "background.png"
        
        try:
            import subprocess
            
            # Try ImageMagick convert (best quality)
            try:
                subprocess.run(
                    [
                        'convert',
                        '-size', '1920x1080',
                        'gradient:#1a1a2e-#16213e',
                        str(background_file)
                    ],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                self.logger.info("✓ Background created with ImageMagick")
                return True
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass
            
            # Fallback: Use PIL/Pillow if available
            try:
                from PIL import Image, ImageDraw
                
                # Create gradient background
                img = Image.new('RGB', (1920, 1080))
                draw = ImageDraw.Draw(img)
                
                # Simple two-color gradient (dark blue theme)
                for y in range(1080):
                    # Interpolate between #1a1a2e and #16213e
                    r = int(0x1a + (0x16 - 0x1a) * y / 1080)
                    g = int(0x1a + (0x21 - 0x1a) * y / 1080)
                    b = int(0x2e + (0x3e - 0x2e) * y / 1080)
                    draw.line([(0, y), (1920, y)], fill=(r, g, b))
                
                img.save(str(background_file), 'PNG')
                self.logger.info("✓ Background created with PIL")
                return True
            except ImportError:
                pass
            
            # Final fallback: Create solid color PNG manually
            self.logger.warning("ImageMagick and PIL not available, using solid color")
            return self._create_solid_background()
            
        except Exception as e:
            self.logger.warning(f"Could not create gradient background: {e}")
            return self._create_solid_background()
    
    def _create_solid_background(self) -> bool:
        """
        Create minimal solid color PNG (fallback)
        
        Creates a tiny 1x1 PNG that GRUB will scale up.
        This ensures theme works even without external tools.
        
        Returns:
            True if creation successful
        """
        background_file = self.theme_dir / "background.png"
        
        try:
            # Minimal PNG: 1x1 dark blue pixel
            # PNG header + IHDR + IDAT (1x1 dark blue) + IEND
            png_data = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
                0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # RGB, no compression
                0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
                0x54, 0x08, 0x1D, 0x01, 0x01, 0x00, 0xFE, 0xFF,  # Compressed data
                0x1A, 0x1A, 0x2E, 0x00, 0x00, 0x18, 0x57, 0x00,  # Dark blue pixel
                0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
                0x42, 0x60, 0x82
            ])
            
            background_file.write_bytes(png_data)
            self.logger.info("✓ Solid color background created")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create fallback background: {e}")
            return False
    
    def _create_menu_decorations(self) -> bool:
        """
        Create menu box decoration files (optional)
        
        Creates minimal transparent PNGs for menu styling.
        These are optional - theme works without them.
        
        Returns:
            True if creation successful
        """
        try:
            # For simplicity, skip menu decorations in default theme
            # Can be added in future versions with proper PNG generation
            self.logger.info("Menu decorations skipped (optional)")
            return True
        except Exception as e:
            self.logger.warning(f"Could not create menu decorations: {e}")
            return True  # Non-critical
    
    def install_custom_theme(self, theme_dir_source: Path) -> bool:
        """
        Install custom theme from directory
        
        Args:
            theme_dir_source: Path to directory containing theme.txt and assets
        
        Returns:
            True if installation successful, False otherwise
        """
        if not theme_dir_source.exists():
            self.logger.error(f"Theme directory not found: {theme_dir_source}")
            return False
        
        theme_file = theme_dir_source / "theme.txt"
        if not theme_file.exists():
            self.logger.error(f"theme.txt not found in {theme_dir_source}")
            return False
        
        try:
            self.logger.info(f"Installing custom theme from {theme_dir_source}")
            
            # Remove old theme if exists
            if self.theme_dir.exists():
                shutil.rmtree(self.theme_dir)
            
            # Copy entire theme directory
            shutil.copytree(theme_dir_source, self.theme_dir)
            
            self.logger.info("✓ Custom theme installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install custom theme: {e}")
            return False
    
    def get_theme_path(self) -> str:
        """
        Get GRUB path to theme file
        
        Returns:
            Path string for use in grub.cfg (e.g., /boot/grub/themes/luxusb/theme.txt)
        """
        return "/boot/grub/themes/luxusb/theme.txt"
    
    def is_theme_installed(self) -> bool:
        """
        Check if theme is currently installed
        
        Returns:
            True if theme directory and theme.txt exist
        """
        theme_file = self.theme_dir / "theme.txt"
        return theme_file.exists()


def install_default_theme(efi_mount: Path) -> bool:
    """
    Convenience function to install default theme
    
    Args:
        efi_mount: Mount point of EFI partition
    
    Returns:
        True if installation successful
    """
    theme_manager = GRUBTheme(efi_mount)
    return theme_manager.install_default_theme()

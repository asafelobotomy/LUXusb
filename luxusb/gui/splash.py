"""
Splash screen for LUXusb application
"""

import logging
from pathlib import Path
from typing import Optional

from luxusb.gui import Gtk, Gdk, GdkPixbuf

logger = logging.getLogger(__name__)


class SplashWindow(Gtk.Window):
    """Splash screen window shown during application startup"""
    
    def __init__(self) -> None:
        super().__init__()
        
        # Window properties
        self.set_default_size(350, 280)
        self.set_decorated(False)  # No title bar
        self.set_modal(True)
        self.set_title("LUXusb")
        
        # Center window on screen
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(40)
        main_box.set_margin_end(40)
        main_box.set_valign(Gtk.Align.CENTER)
        main_box.set_halign(Gtk.Align.CENTER)
        
        # Load and display icon
        icon_path = self._find_icon()
        if icon_path and icon_path.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(icon_path),
                    180,  # width - reduced for narrower window
                    180,  # height - reduced for narrower window
                    True  # preserve aspect ratio
                )
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                icon_image = Gtk.Image.new_from_paintable(texture)
                icon_image.set_size_request(180, 180)  # Force minimum size
                icon_image.set_pixel_size(180)  # Set pixel size
                main_box.append(icon_image)
            except Exception as e:
                logger.warning(f"Failed to load icon for splash: {e}")
        
        # Load and display text logo
        text_logo_path = self._find_text_logo()
        if text_logo_path and text_logo_path.exists():
            try:
                # Text logo is 531x132, scale proportionally
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(text_logo_path),
                    300,  # width - reduced for narrower window
                    75,   # height - maintains aspect ratio
                    True  # preserve aspect ratio
                )
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                text_image = Gtk.Image.new_from_paintable(texture)
                text_image.set_size_request(300, 75)  # Force exact size
                text_image.set_pixel_size(300)  # Set pixel size (like icon)
                main_box.append(text_image)
            except Exception as e:
                logger.warning(f"Failed to load text logo for splash: {e}")
        else:
            # Fallback to text label
            label = Gtk.Label(label="LUXusb")
            label.add_css_class("title-1")
            main_box.append(label)
        
        # Version and tagline
        version_label = Gtk.Label(label="Version 0.2.1")
        version_label.add_css_class("caption")
        version_label.add_css_class("dim-label")
        main_box.append(version_label)
        
        tagline = Gtk.Label(label="Create bootable USB drives with multiple Linux distributions")
        tagline.add_css_class("caption")
        tagline.add_css_class("dim-label")
        tagline.set_wrap(True)
        tagline.set_justify(Gtk.Justification.CENTER)
        tagline.set_max_width_chars(50)
        main_box.append(tagline)
        
        # Loading spinner
        spinner = Gtk.Spinner()
        spinner.set_spinning(True)
        spinner.set_size_request(32, 32)
        main_box.append(spinner)
        
        loading_label = Gtk.Label(label="Loading...")
        loading_label.add_css_class("caption")
        loading_label.add_css_class("dim-label")
        main_box.append(loading_label)
        
        # Add dark mode styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window.splash {
                background: #1e1e1e;
                color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5);
            }
            window.splash label {
                color: #ffffff;
            }
        """)
        
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.add_css_class("splash")
        
        self.set_child(main_box)
    
    def _find_icon(self) -> Optional[Path]:
        """Find the application icon"""
        # Try multiple locations
        possible_paths = [
            Path(__file__).parent.parent / "data" / "icons" / "com.luxusb.LUXusb.png",
            Path.cwd() / "luxusb" / "data" / "icons" / "com.luxusb.LUXusb.png",
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found icon at: {path}")
                return path
        
        logger.warning("Could not find application icon for splash screen")
        return None
    
    def _find_text_logo(self) -> Optional[Path]:
        """Find the text logo (from archived sources if needed)"""
        possible_paths = [
            Path(__file__).parent.parent.parent / "archive" / "images-source" / "luxusb-text-source.png",
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found text logo at: {path}")
                return path
        
        logger.debug("Could not find text logo for splash screen")
        return None
    
    def close_splash(self) -> None:
        """Close the splash screen with a fade effect"""
        self.close()


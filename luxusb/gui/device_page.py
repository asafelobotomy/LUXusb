"""
USB device selection page
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GdkPixbuf, Gdk
import logging
from typing import Any
from pathlib import Path

from luxusb.utils.usb_detector import USBDevice

logger = logging.getLogger(__name__)


class DeviceSelectionPage(Adw.NavigationPage):
    """Page for selecting USB device"""
    
    def __init__(self, main_window: Any) -> None:
        super().__init__()
        self.main_window = main_window
        self.set_title("Select USB Device")
        
        # Create main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title and description
        title = Gtk.Label(label="Select USB Device")
        title.add_css_class("title-1")
        content.append(title)
        
        description = Gtk.Label(
            label="Choose the USB device you want to use.\n⚠️ All data on the selected device will be erased!"
        )
        description.add_css_class("dim-label")
        description.set_wrap(True)
        description.set_justify(Gtk.Justification.CENTER)
        content.append(description)
        
        # Refresh button
        refresh_btn = Gtk.Button(label="🔄 Scan for USB Devices")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        refresh_btn.add_css_class("suggested-action")
        content.append(refresh_btn)
        
        # Device list
        self.device_list = Gtk.ListBox()
        self.device_list.add_css_class("boxed-list")
        self.device_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.device_list)
        content.append(scrolled)
        
        # Continue button
        continue_btn = Gtk.Button(label="Continue")
        continue_btn.connect("clicked", self.on_continue_clicked)
        continue_btn.add_css_class("pill")
        continue_btn.add_css_class("suggested-action")
        content.append(continue_btn)
        
        self.set_child(content)
        
        # Scan on load
        GLib.idle_add(self.refresh_devices)
    
    def refresh_devices(self) -> bool:
        """Scan and display USB devices"""
        logger.info("Scanning for USB devices...")
        
        # Clear existing devices
        while True:
            row = self.device_list.get_row_at_index(0)
            if row is None:
                break
            self.device_list.remove(row)
        
        # Scan devices
        devices = self.main_window.get_application().usb_detector.scan_devices()
        
        if not devices:
            # Show "no devices" message
            no_devices = Gtk.Label(label="No USB devices found.\nPlease insert a USB drive and click Refresh.")
            no_devices.add_css_class("dim-label")
            no_devices.set_margin_top(20)
            no_devices.set_margin_bottom(20)
            self.device_list.append(no_devices)
        else:
            # Add device rows
            for device in devices:
                row = self.create_device_row(device)
                self.device_list.append(row)
        
        return False  # Don't repeat
    
    def create_device_row(self, device: USBDevice) -> Gtk.ListBoxRow:
        """Create a row for a device"""
        row = Gtk.ListBoxRow()
        row.device = device
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Icon - different for configured devices
        if device.is_luxusb_configured:
            # Use LUXusb icon for configured devices
            icon_path = self._find_luxusb_icon()
            if icon_path and icon_path.exists():
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        str(icon_path),
                        72,
                        72,
                        True
                    )
                    texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                    icon = Gtk.Image.new_from_paintable(texture)
                    icon.set_pixel_size(72)
                    icon.set_size_request(72, 72)
                except Exception as e:
                    logger.warning(f"Failed to load LUXusb icon: {e}")
                    icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                    icon.set_pixel_size(72)
            else:
                icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                icon.set_pixel_size(72)
        else:
            icon = Gtk.Image.new_from_icon_name("drive-removable-media")
            icon.set_pixel_size(72)
        box.append(icon)
        
        # Info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        # Device name
        name_label = Gtk.Label(label=device.display_name)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        info_box.append(name_label)
        
        # Size and status
        status = "Mounted" if device.is_mounted else "Not mounted"
        
        # Add LUXusb status if configured
        if device.is_luxusb_configured and device.luxusb_state:
            num_isos = len(device.luxusb_state.installed_isos)
            status_text = f"{device.size_gb:.1f} GB • {status} • {num_isos} ISO(s) installed"
        else:
            status_text = f"{device.size_gb:.1f} GB • {status}"
            
        size_label = Gtk.Label(label=status_text)
        size_label.set_halign(Gtk.Align.START)
        size_label.add_css_class("dim-label")
        info_box.append(size_label)
        
        # Show ISOs if configured
        if device.is_luxusb_configured and device.luxusb_state and device.luxusb_state.installed_isos:
            iso_label = Gtk.Label(label=f"ISOs: {', '.join(device.luxusb_state.installed_isos[:3])}")
            iso_label.set_halign(Gtk.Align.START)
            iso_label.add_css_class("caption")
            iso_label.add_css_class("dim-label")
            iso_label.set_ellipsize(3)  # Ellipsize at end
            info_box.append(iso_label)
        
        # Show Secure Boot status if configured
        if device.is_luxusb_configured and device.luxusb_state:
            sb_enabled = getattr(device.luxusb_state, 'secure_boot_enabled', False)
            if sb_enabled:
                sb_label = Gtk.Label(label="🔒 Secure Boot Enabled")
                sb_label.set_halign(Gtk.Align.START)
                sb_label.add_css_class("caption")
                sb_label.add_css_class("success")
                sb_label.set_tooltip_text("This USB was created with Secure Boot signing")
                info_box.append(sb_label)
            else:
                sb_label = Gtk.Label(label="Secure Boot: Disabled")
                sb_label.set_halign(Gtk.Align.START)
                sb_label.add_css_class("caption")
                sb_label.add_css_class("dim-label")
                sb_label.set_tooltip_text("This USB was created without Secure Boot signing")
                info_box.append(sb_label)
        
        box.append(info_box)
        
        # Badge for configured devices
        if device.is_luxusb_configured:
            badge = Gtk.Label(label="✓ Configured")
            badge.add_css_class("success")
            badge.add_css_class("pill")
            box.append(badge)
        
        # Warning if system disk
        if self.main_window.get_application().usb_detector.is_system_disk(device):
            warning = Gtk.Label(label="⚠️ System Disk")
            warning.add_css_class("error")
            box.append(warning)
        
        row.set_child(box)
        return row
    
    def _find_luxusb_icon(self) -> Path | None:
        """Find the LUXusb icon"""
        possible_paths = [
            Path(__file__).parent.parent / "data" / "icons" / "com.luxusb.LUXusb.png",
            Path("images") / "LUXusb - Logo - Icon.png",
            Path("/usr/share/icons/hicolor/256x256/apps/com.luxusb.LUXusb.png"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.debug(f"Found LUXusb icon at: {path}")
                return path
        
        logger.warning("LUXusb icon not found")
        return None
    
    def on_refresh_clicked(self, _button: Gtk.Button) -> None:
        """Handle refresh button click"""
        self.refresh_devices()
    
    def on_continue_clicked(self, _button: Gtk.Button) -> None:
        """Handle continue button click"""
        selected_row = self.device_list.get_selected_row()
        
        if not selected_row or not hasattr(selected_row, 'device'):
            self.main_window.show_error_dialog(
                "No Device Selected",
                "Please select a USB device to continue."
            )
            return
        
        device = selected_row.device
        
        # Validate device
        is_valid, error = self.main_window.get_application().usb_detector.validate_device(device)
        if not is_valid:
            self.main_window.show_error_dialog("Invalid Device", error)
            return
        
        # Store selected device
        self.main_window.get_application().selected_device = device
        
        # Check if device is already configured with LUXusb
        if device.is_luxusb_configured:
            # Show dialog asking if user wants to add more ISOs or erase
            self.main_window.show_configured_device_dialog(
                f"LUXusb Device Detected",
                f"{device.display_name} is already configured with LUXusb.\n\n"
                f"Installed ISOs: {len(device.luxusb_state.installed_isos)}\n\n"
                f"Would you like to add more distributions or erase and start fresh?",
                self.on_configured_device_response
            )
            return
        
        # Show warning dialog for new device
        self.main_window.show_warning_dialog(
            "⚠️ Warning: Data Will Be Erased",
            f"All data on {device.display_name} will be permanently erased.\n\n"
            f"Are you sure you want to continue?",
            self.on_warning_response
        )
    
    def on_configured_device_response(self, _dialog: Adw.MessageDialog, response: str) -> None:
        """Handle configured device dialog response"""
        if response == "add":
            # Navigate to family selection for organized distro browsing
            # Set append mode flag on app
            self.main_window.get_application().append_mode = True
            self.main_window.navigate_to_family_page()
        elif response == "erase":
            # Clear append mode flag
            self.main_window.get_application().append_mode = False
            # Show erase warning
            device = self.main_window.get_application().selected_device
            self.main_window.show_warning_dialog(
                "⚠️ Warning: Data Will Be Erased",
                f"All data on {device.display_name} will be permanently erased.\n\n"
                f"Are you sure you want to continue?",
                self.on_warning_response
            )
    
    def on_warning_response(self, _dialog: Adw.MessageDialog, response: str) -> None:
        """Handle warning dialog response"""
        if response == "continue":
            self.main_window.navigate_to_family_page()

"""
Custom ISO selection page
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio
import logging
from typing import Any
from pathlib import Path

from luxusb.utils.custom_iso import CustomISO, validate_custom_iso

logger = logging.getLogger(__name__)


class CustomISOPage(Adw.NavigationPage):
    """Page for adding custom ISO files"""
    
    def __init__(self, main_window: Any) -> None:
        super().__init__()
        self.main_window = main_window
        self.set_title("Add Custom ISO Files")
        self.custom_isos: list[CustomISO] = []
        
        # Create main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title
        title = Gtk.Label(label="Add Custom ISO Files")
        title.add_css_class("title-1")
        content.append(title)
        
        description = Gtk.Label(
            label="Select ISO files from your computer to add to your bootable USB drive.\n"
                  "Supported: Most Linux distribution ISO files."
        )
        description.add_css_class("dim-label")
        description.set_wrap(True)
        description.set_justify(Gtk.Justification.CENTER)
        content.append(description)
        
        # Custom ISO list
        self.custom_iso_list = Gtk.ListBox()
        self.custom_iso_list.add_css_class("boxed-list")
        self.custom_iso_list.set_selection_mode(Gtk.SelectionMode.NONE)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.custom_iso_list)
        content.append(scrolled)
        
        # Add ISO button
        add_iso_btn = Gtk.Button(label="📁 Browse for ISO File")
        add_iso_btn.connect("clicked", self.on_add_custom_iso_clicked)
        add_iso_btn.add_css_class("suggested-action")
        add_iso_btn.set_halign(Gtk.Align.CENTER)
        add_iso_btn.set_size_request(300, -1)
        content.append(add_iso_btn)
        
        # Selection summary
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        summary_box.set_margin_top(20)
        summary_box.add_css_class("card")
        summary_box.set_margin_top(16)
        summary_box.set_margin_bottom(16)
        summary_box.set_margin_start(16)
        summary_box.set_margin_end(16)
        
        self.summary_label = Gtk.Label()
        self.summary_label.add_css_class("heading")
        self.summary_label.set_halign(Gtk.Align.START)
        summary_box.append(self.summary_label)
        
        content.append(summary_box)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        
        back_btn = Gtk.Button(label="← Back")
        back_btn.connect("clicked", self.on_back_clicked)
        button_box.append(back_btn)
        
        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect("clicked", self.on_clear_clicked)
        button_box.append(clear_btn)
        
        self.continue_btn = Gtk.Button(label="Continue")
        self.continue_btn.connect("clicked", self.on_continue_clicked)
        self.continue_btn.add_css_class("suggested-action")
        self.continue_btn.set_sensitive(False)
        button_box.append(self.continue_btn)
        
        content.append(button_box)
        
        self.set_child(content)
        self.update_summary()
    
    def on_add_custom_iso_clicked(self, _button: Gtk.Button) -> None:
        """Handle add custom ISO button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select ISO File")
        
        # Set file filter for ISO files
        filter_iso = Gtk.FileFilter()
        filter_iso.set_name("ISO Images")
        filter_iso.add_pattern("*.iso")
        filter_iso.add_mime_type("application/x-iso9660-image")
        
        # Create filter list store
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_iso)
        dialog.set_filters(filters)
        
        dialog.open(self.main_window, None, self.on_iso_file_selected)
    
    def on_iso_file_selected(self, dialog: Gtk.FileDialog, result) -> None:
        """Handle ISO file selection"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                self.add_custom_iso(path)
        except Exception as e:
            if "dismissed" not in str(e).lower():
                logger.error("File selection error: %s", e)
    
    def add_custom_iso(self, path: str) -> None:
        """Add a custom ISO to the list"""
        # Validate ISO
        custom_iso = validate_custom_iso(Path(path))
        
        if not custom_iso.is_valid:
            self.main_window.show_error_dialog(
                "Invalid ISO File",
                custom_iso.error_message or "The selected file is not a valid ISO."
            )
            return
        
        # Check for duplicates
        if any(iso.source_path == custom_iso.source_path for iso in self.custom_isos):
            self.main_window.show_error_dialog(
                "Duplicate ISO",
                "This ISO file has already been added."
            )
            return
        
        # Add to list
        self.custom_isos.append(custom_iso)
        
        # Create row
        row = self.create_custom_iso_row(custom_iso)
        self.custom_iso_list.append(row)
        
        logger.info(f"Added custom ISO: {custom_iso.filename}")
        self.update_summary()
    
    def create_custom_iso_row(self, custom_iso: CustomISO) -> Gtk.ListBoxRow:
        """Create a row for a custom ISO"""
        row = Gtk.ListBoxRow()
        row.custom_iso = custom_iso
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        
        # Top row: Icon, Info, Remove button
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Icon
        icon = Gtk.Image.new_from_icon_name("media-optical-symbolic")
        icon.set_pixel_size(48)
        top_box.append(icon)
        
        # Info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        # Filename
        name_label = Gtk.Label(label=custom_iso.display_name)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        info_box.append(name_label)
        
        # Size and path
        size_mb = custom_iso.size_bytes / (1024 * 1024)
        path_label = Gtk.Label(label=f"{size_mb:.1f} MB • {custom_iso.source_path}")
        path_label.set_halign(Gtk.Align.START)
        path_label.add_css_class("dim-label")
        path_label.add_css_class("caption")
        path_label.set_ellipsize(3)  # Ellipsize at end
        info_box.append(path_label)
        
        # Verification status
        if custom_iso.has_verification:
            verif_parts = []
            if custom_iso.checksum_file:
                verif_parts.append("✓ Checksum")
            if custom_iso.gpg_signature:
                verif_parts.append("✓ GPG Signature")
            if custom_iso.gpg_key:
                verif_parts.append("✓ GPG Key")
            
            verif_label = Gtk.Label(label=" • ".join(verif_parts))
            verif_label.set_halign(Gtk.Align.START)
            verif_label.add_css_class("caption")
            verif_label.add_css_class("success")
            info_box.append(verif_label)
        
        top_box.append(info_box)
        
        # Remove button
        remove_btn = Gtk.Button()
        remove_btn.set_icon_name("user-trash-symbolic")
        remove_btn.connect("clicked", self.on_remove_iso_clicked, custom_iso)
        remove_btn.add_css_class("flat")
        remove_btn.set_valign(Gtk.Align.START)
        top_box.append(remove_btn)
        
        main_box.append(top_box)
        
        # Verification files section
        verif_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        verif_box.set_margin_start(60)  # Align with info text
        
        # Checksum button
        checksum_btn = Gtk.Button(label="📄 Add Checksum")
        checksum_btn.connect("clicked", self.on_add_checksum_clicked, custom_iso, row)
        checksum_btn.add_css_class("pill")
        checksum_btn.set_tooltip_text("Add SHA256/SHA512 checksum file for verification")
        if custom_iso.checksum_file:
            checksum_btn.set_label("✓ Checksum")
            checksum_btn.add_css_class("success")
        verif_box.append(checksum_btn)
        
        # GPG Signature button
        sig_btn = Gtk.Button(label="🔏 Add Signature")
        sig_btn.connect("clicked", self.on_add_signature_clicked, custom_iso, row)
        sig_btn.add_css_class("pill")
        sig_btn.set_tooltip_text("Add GPG signature file (.sig/.asc) for verification")
        if custom_iso.gpg_signature:
            sig_btn.set_label("✓ Signature")
            sig_btn.add_css_class("success")
        verif_box.append(sig_btn)
        
        # GPG Key button
        key_btn = Gtk.Button(label="🔑 Add GPG Key")
        key_btn.connect("clicked", self.on_add_gpg_key_clicked, custom_iso, row)
        key_btn.add_css_class("pill")
        key_btn.set_tooltip_text("Add GPG public key for signature verification")
        if custom_iso.gpg_key:
            key_btn.set_label("✓ GPG Key")
            key_btn.add_css_class("success")
        verif_box.append(key_btn)
        
        main_box.append(verif_box)
        
        row.set_child(main_box)
        return row
    
    def on_remove_iso_clicked(self, _button: Gtk.Button, custom_iso: CustomISO) -> None:
        """Handle remove ISO button click"""
        # Remove from list
        self.custom_isos.remove(custom_iso)
        
        # Remove row from UI
        for i in range(self.custom_iso_list.get_last_child() and 1000 or 0):
            row = self.custom_iso_list.get_row_at_index(i)
            if row and hasattr(row, 'custom_iso') and row.custom_iso == custom_iso:
                self.custom_iso_list.remove(row)
                break
        
        logger.info(f"Removed custom ISO: {custom_iso.filename}")
        self.update_summary()
    
    def on_add_checksum_clicked(self, _button: Gtk.Button, custom_iso: CustomISO, row: Gtk.ListBoxRow) -> None:
        """Handle add checksum button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Checksum File")
        
        # Set file filter for checksum files
        filter_checksum = Gtk.FileFilter()
        filter_checksum.set_name("Checksum Files")
        filter_checksum.add_pattern("*.sha256")
        filter_checksum.add_pattern("*.sha512")
        filter_checksum.add_pattern("*.sha1")
        filter_checksum.add_pattern("*.md5")
        filter_checksum.add_pattern("SHA256SUMS*")
        filter_checksum.add_pattern("*SUMS")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_checksum)
        dialog.set_filters(filters)
        
        dialog.open(self.main_window, None, self.on_checksum_file_selected, custom_iso, row)
    
    def on_checksum_file_selected(self, dialog: Gtk.FileDialog, result, custom_iso: CustomISO, row: Gtk.ListBoxRow) -> None:
        """Handle checksum file selection"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = Path(file.get_path())
                custom_iso.checksum_file = path
                logger.info(f"Added checksum file for {custom_iso.filename}: {path.name}")
                
                # Rebuild the row to show updated status
                self.rebuild_iso_row(custom_iso, row)
        except Exception as e:
            if "dismissed" not in str(e).lower():
                logger.error("Checksum file selection error: %s", e)
    
    def on_add_signature_clicked(self, _button: Gtk.Button, custom_iso: CustomISO, row: Gtk.ListBoxRow) -> None:
        """Handle add signature button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select GPG Signature File")
        
        # Set file filter for signature files
        filter_sig = Gtk.FileFilter()
        filter_sig.set_name("GPG Signature Files")
        filter_sig.add_pattern("*.sig")
        filter_sig.add_pattern("*.asc")
        filter_sig.add_pattern("*.gpg")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_sig)
        dialog.set_filters(filters)
        
        dialog.open(self.main_window, None, self.on_signature_file_selected, custom_iso, row)
    
    def on_signature_file_selected(self, dialog: Gtk.FileDialog, result, custom_iso: CustomISO, row: Gtk.ListBoxRow) -> None:
        """Handle signature file selection"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = Path(file.get_path())
                custom_iso.gpg_signature = path
                logger.info(f"Added GPG signature for {custom_iso.filename}: {path.name}")
                
                # Rebuild the row to show updated status
                self.rebuild_iso_row(custom_iso, row)
        except Exception as e:
            if "dismissed" not in str(e).lower():
                logger.error("Signature file selection error: %s", e)
    
    def on_add_gpg_key_clicked(self, _button: Gtk.Button, custom_iso: CustomISO, row: Gtk.ListBoxRow) -> None:
        """Handle add GPG key button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select GPG Public Key")
        
        # Set file filter for key files
        filter_key = Gtk.FileFilter()
        filter_key.set_name("GPG Key Files")
        filter_key.add_pattern("*.gpg")
        filter_key.add_pattern("*.asc")
        filter_key.add_pattern("*.key")
        filter_key.add_pattern("*.pub")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_key)
        dialog.set_filters(filters)
        
        dialog.open(self.main_window, None, self.on_gpg_key_file_selected, custom_iso, row)
    
    def on_gpg_key_file_selected(self, dialog: Gtk.FileDialog, result, custom_iso: CustomISO, row: Gtk.ListBoxRow) -> None:
        """Handle GPG key file selection"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = Path(file.get_path())
                custom_iso.gpg_key = path
                logger.info(f"Added GPG key for {custom_iso.filename}: {path.name}")
                
                # Rebuild the row to show updated status
                self.rebuild_iso_row(custom_iso, row)
        except Exception as e:
            if "dismissed" not in str(e).lower():
                logger.error("GPG key file selection error: %s", e)
    
    def rebuild_iso_row(self, custom_iso: CustomISO, old_row: Gtk.ListBoxRow) -> None:
        """Rebuild an ISO row to reflect updated verification status"""
        # Find the index of the old row
        index = -1
        for i in range(1000):
            row = self.custom_iso_list.get_row_at_index(i)
            if row == old_row:
                index = i
                break
        
        if index >= 0:
            # Remove old row
            self.custom_iso_list.remove(old_row)
            
            # Create new row
            new_row = self.create_custom_iso_row(custom_iso)
            
            # Insert at same position
            self.custom_iso_list.insert(new_row, index)
    
    def update_summary(self) -> None:
        """Update selection summary"""
        num_isos = len(self.custom_isos)
        total_size_gb = sum(iso.size_bytes for iso in self.custom_isos) / (1024 ** 3)
        
        self.summary_label.set_text(
            f"{num_isos} ISO{'s' if num_isos != 1 else ''} selected • {total_size_gb:.1f} GB total"
        )
        
        self.continue_btn.set_sensitive(num_isos > 0)
    
    def on_back_clicked(self, _button: Gtk.Button) -> None:
        """Handle back button click"""
        nav_view = self.main_window.nav_view
        nav_view.pop()
    
    def on_clear_clicked(self, _button: Gtk.Button) -> None:
        """Handle clear all button click"""
        self.custom_isos.clear()
        
        # Clear UI
        while True:
            row = self.custom_iso_list.get_first_child()
            if not row:
                break
            self.custom_iso_list.remove(row)
        
        self.update_summary()
    
    def on_continue_clicked(self, _button: Gtk.Button) -> None:
        """Handle continue button click"""
        # Save custom ISOs to application state
        app = self.main_window.get_application()
        app.custom_isos = self.custom_isos
        
        logger.info(f"Proceeding with {len(self.custom_isos)} custom ISO(s)")
        
        # Navigate to progress page
        self.main_window.navigate_to_progress_page(
            distro_selections=[],  # No distribution ISOs
            custom_isos=self.custom_isos
        )

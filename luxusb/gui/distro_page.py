"""
Distribution selection page
"""

import logging
from luxusb.gui import Gtk, Adw, GLib
from typing import Any

from luxusb.utils.distro_manager import get_distro_manager, Distro, DistroSelection
from luxusb.utils.custom_iso import CustomISO, validate_custom_iso
from luxusb.constants import DistroFamily

logger = logging.getLogger(__name__)


class DistroSelectionPage(Adw.NavigationPage):
    """Page for selecting Linux distribution(s)"""
    
    def __init__(self, main_window: Any, family_filter: str = None) -> None:
        super().__init__()
        self.main_window = main_window
        self.family_filter = family_filter
        self.selected_distros: dict[str, Distro] = {}  # distro_id -> Distro
        self.custom_isos: list[CustomISO] = []
        
        # Restore any pending selections from previous navigation
        app = main_window.get_application()
        if hasattr(app, 'pending_selections'):
            self.selected_distros = app.pending_selections.copy()
            logger.info(f"Restored {len(self.selected_distros)} pending selection(s)")
        
        # Set title based on family filter using DistroFamily enum
        if family_filter:
            try:
                family_enum = DistroFamily(family_filter)
                title = family_enum.display_name
            except ValueError:
                title = "Select Distribution"
        else:
            title = "Select Distributions"
        self.set_title(title)
        
        # Create main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title using DistroFamily enum
        if family_filter:
            try:
                family_enum = DistroFamily(family_filter)
                title_text = family_enum.display_name
            except ValueError:
                title_text = "Select Distributions"
        else:
            title_text = "Select Distributions"
        
        title = Gtk.Label(label=title_text)
        title.add_css_class("title-1")
        content.append(title)
        
        description = Gtk.Label(
            label="Select one or more Linux distributions to install. Space calculation shown on the right."
        )
        description.add_css_class("dim-label")
        description.set_wrap(True)
        description.set_justify(Gtk.Justification.CENTER)
        content.append(description)
        
        # Horizontal box for two-column layout
        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        columns_box.set_vexpand(True)
        
        # LEFT COLUMN: Distro list with search
        left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_column.set_hexpand(True)
        
        # Search entry
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search distributions...")
        search_entry.connect("search-changed", self.on_search_changed)
        left_column.append(search_entry)
        
        # Distribution list (no selection mode - we use checkboxes)
        self.distro_list = Gtk.ListBox()
        self.distro_list.add_css_class("boxed-list")
        self.distro_list.set_selection_mode(Gtk.SelectionMode.NONE)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.distro_list)
        left_column.append(scrolled)
        
        columns_box.append(left_column)
        
        # RIGHT COLUMN: Logo + USB information summary
        right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        right_column.set_size_request(350, -1)  # Fixed width for info panel
        right_column.set_vexpand(True)
        
        # LUXusb logo at top (compact)
        from pathlib import Path
        logo_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        logo_container.set_valign(Gtk.Align.START)
        logo_container.set_margin_top(20)
        
        icon_path = Path(__file__).parent.parent / "data" / "icons" / "com.luxusb.LUXusb.png"
        if icon_path.exists():
            logo_image = Gtk.Image.new_from_file(str(icon_path))
            logo_image.set_pixel_size(200)
            logo_image.set_opacity(0.3)  # Subtle watermark effect
            logo_container.append(logo_image)
        
        right_column.append(logo_container)
        
        # Wrap summary in scrolled window to prevent window resize
        summary_scroll = Gtk.ScrolledWindow()
        summary_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        summary_scroll.set_vexpand(True)  # Take remaining vertical space
        summary_scroll.set_propagate_natural_height(False)  # Don't let content expand window
        
        # Selection summary bar
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        summary_box.set_margin_top(16)
        summary_box.set_margin_bottom(16)
        summary_box.set_margin_start(16)
        summary_box.set_margin_end(16)
        
        # Current selection info
        selection_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        selection_title = Gtk.Label(label="📦 Current Selection")
        selection_title.add_css_class("heading")
        selection_title.set_halign(Gtk.Align.CENTER)
        selection_box.append(selection_title)
        
        # Container for selection summary and distro columns
        self.selection_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Summary label (count + size)
        self.selection_summary_label = Gtk.Label()
        self.selection_summary_label.add_css_class("dim-label")
        self.selection_summary_label.set_halign(Gtk.Align.CENTER)
        self.selection_summary_label.set_wrap(True)
        self.selection_summary_label.set_max_width_chars(40)
        self.selection_container.append(self.selection_summary_label)
        
        # Container for distro columns (will be populated dynamically)
        self.distro_columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.distro_columns_box.set_halign(Gtk.Align.CENTER)
        self.selection_container.append(self.distro_columns_box)
        
        selection_box.append(self.selection_container)
        
        summary_box.append(selection_box)
        
        # Separator
        separator1 = Gtk.Separator()
        summary_box.append(separator1)
        
        # USB free space info
        usb_space_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        usb_space_title = Gtk.Label(label="💾 USB Storage")
        usb_space_title.add_css_class("heading")
        usb_space_title.set_halign(Gtk.Align.CENTER)
        usb_space_box.append(usb_space_title)
        
        self.usb_space_label = Gtk.Label()
        self.usb_space_label.add_css_class("dim-label")
        self.usb_space_label.set_halign(Gtk.Align.CENTER)
        self.usb_space_label.set_wrap(True)
        self.usb_space_label.set_max_width_chars(40)
        usb_space_box.append(self.usb_space_label)
        
        # Space usage progress bar
        self.space_progress = Gtk.ProgressBar()
        self.space_progress.set_show_text(True)
        usb_space_box.append(self.space_progress)
        
        summary_box.append(usb_space_box)
        
        # Separator
        separator2 = Gtk.Separator()
        summary_box.append(separator2)
        
        # Current ISOs on USB
        current_isos_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        current_isos_title = Gtk.Label(label="📀 ISOs Already on USB")
        current_isos_title.add_css_class("heading")
        current_isos_title.set_halign(Gtk.Align.CENTER)
        current_isos_box.append(current_isos_title)
        
        self.current_isos_label = Gtk.Label()
        self.current_isos_label.add_css_class("dim-label")
        self.current_isos_label.set_halign(Gtk.Align.CENTER)
        self.current_isos_label.set_wrap(True)
        self.current_isos_label.set_max_width_chars(40)
        current_isos_box.append(self.current_isos_label)
        
        summary_box.append(current_isos_box)
        
        # Warning label (initially hidden)
        self.warning_label = Gtk.Label()
        self.warning_label.add_css_class("error")
        self.warning_label.set_wrap(True)
        self.warning_label.set_visible(False)
        summary_box.append(self.warning_label)
        
        summary_scroll.set_child(summary_box)
        right_column.append(summary_scroll)
        columns_box.append(right_column)
        
        content.append(columns_box)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        
        # Back button
        back_btn = Gtk.Button(label="← Back")
        back_btn.connect("clicked", self.on_back_clicked)
        button_box.append(back_btn)
        
        # Clear all button
        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect("clicked", self.on_clear_all_clicked)
        button_box.append(clear_btn)
        
        # Continue button
        self.continue_btn = Gtk.Button(label="Continue")
        self.continue_btn.connect("clicked", self.on_continue_clicked)
        self.continue_btn.add_css_class("suggested-action")
        self.continue_btn.set_sensitive(False)
        button_box.append(self.continue_btn)
        
        content.append(button_box)
        
        self.set_child(content)
        
        # Load distros
        self.refresh_distros()
        
        # Update summary initially
        self.update_selection_summary()
    
    def refresh_distros(self) -> None:
        """Load and display distributions"""
        logger.info("Loading distributions...")
        
        # Clear existing
        while True:
            row = self.distro_list.get_row_at_index(0)
            if row is None:
                break
            self.distro_list.remove(row)
        
        # Get all distros
        distros = get_distro_manager().get_all_distros()
        
        # Filter by family if specified
        if self.family_filter:
            distros = [d for d in distros if hasattr(d, 'family') and d.family == self.family_filter]
        
        # Remove incompatible distros from selection if Secure Boot is enabled
        app = self.main_window.get_application()
        if app.enable_secure_boot:
            # Auto-deselect incompatible distros
            distros_to_remove = [
                distro_id for distro_id, distro in self.selected_distros.items()
                if not getattr(distro, 'secure_boot_compatible', True)
            ]
            for distro_id in distros_to_remove:
                del self.selected_distros[distro_id]
                logger.info(f"Auto-deselected incompatible distro: {distro_id}")
        
        # Add rows
        for distro in distros:
            row = self.create_distro_row(distro)
            self.distro_list.append(row)
        
        # Update USB information display after distros are loaded
        self.update_selection_summary()
    
    def create_distro_row(self, distro: Distro) -> Gtk.ListBoxRow:
        """Create a row for a distribution with checkbox"""
        row = Gtk.ListBoxRow()
        row.distro = distro
        row.set_activatable(True)
        
        # Check Secure Boot compatibility
        app = self.main_window.get_application()
        secure_boot_enabled = app.enable_secure_boot
        is_compatible = distro.secure_boot_compatible if hasattr(distro, 'secure_boot_compatible') else True
        
        # Determine if distro should be disabled
        is_disabled = secure_boot_enabled and not is_compatible
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Checkbox
        checkbox = Gtk.CheckButton()
        checkbox.set_active(distro.id in self.selected_distros and not is_disabled)
        checkbox.set_sensitive(not is_disabled)  # Disable checkbox if incompatible
        checkbox.connect("toggled", self.on_distro_toggled, distro)
        row.checkbox = checkbox
        box.append(checkbox)
        
        # Icon from logo file
        from pathlib import Path
        icon_path = Path(__file__).parent.parent / "data" / "icons" / f"{distro.id}.png"
        if icon_path.exists():
            icon = Gtk.Image.new_from_file(str(icon_path))
            icon.set_pixel_size(48)
        else:
            # Fallback to generic icon
            icon = Gtk.Image.new_from_icon_name("application-x-cd-image")
            icon.set_pixel_size(48)
        box.append(icon)
        
        # Info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        # If disabled due to Secure Boot, apply grey styling
        if is_disabled:
            box.set_opacity(0.4)  # Grey out entire row
            row.set_sensitive(False)  # Prevent row activation
        
        # Name with Secure Boot warning if incompatible
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        name_label = Gtk.Label(label=distro.name)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        name_box.append(name_label)
        
        # Add Secure Boot incompatibility badge
        if is_disabled:
            sb_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
            sb_icon.add_css_class("error")
            sb_icon.set_tooltip_text("Not compatible with Secure Boot")
            name_box.append(sb_icon)
            
            sb_label = Gtk.Label(label="Incompatible with Secure Boot")
            sb_label.add_css_class("error")
            sb_label.add_css_class("caption")
            sb_label.set_tooltip_text("This distribution cannot be used when Secure Boot is enabled")
            name_box.append(sb_label)
        
        info_box.append(name_box)
        
        # Description
        desc_label = Gtk.Label(label=distro.description)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.set_max_width_chars(50)
        desc_label.add_css_class("dim-label")
        desc_label.add_css_class("caption")
        info_box.append(desc_label)
        
        # GPG verification badge
        gpg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        if distro.latest_release and hasattr(distro.latest_release, 'gpg_verified'):
            if distro.latest_release.gpg_verified:
                # Verified badge with shield icon
                gpg_icon = Gtk.Image.new_from_icon_name("security-high-symbolic")
                gpg_icon.add_css_class("success")
                gpg_box.append(gpg_icon)
                
                gpg_label = Gtk.Label(label="GPG Verified")
                gpg_label.add_css_class("success")
                gpg_label.add_css_class("caption")
                gpg_box.append(gpg_label)
                
                # Info button to show GPG details
                gpg_info_btn = Gtk.Button()
                gpg_info_btn.set_icon_name("help-about-symbolic")
                gpg_info_btn.set_tooltip_text("View GPG Key Details")
                gpg_info_btn.add_css_class("flat")
                gpg_info_btn.add_css_class("circular")
                gpg_info_btn.connect("clicked", self.show_gpg_info, distro)
                gpg_box.append(gpg_info_btn)
            else:
                # Warning badge for unverified
                gpg_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
                gpg_icon.add_css_class("warning")
                gpg_box.append(gpg_icon)
                
                gpg_label = Gtk.Label(label="Checksum Only")
                gpg_label.add_css_class("warning")
                gpg_label.add_css_class("caption")
                gpg_box.append(gpg_label)
        
        # Version and size
        if distro.latest_release:
            release = distro.latest_release
            version_label = Gtk.Label(
                label=f"Latest: {release.version} • {release.size_gb:.1f} GB"
            )
            version_label.set_halign(Gtk.Align.START)
            version_label.add_css_class("dim-label")
            version_label.add_css_class("caption")
            info_box.append(version_label)
            
            # Add GPG badge below version
            if gpg_box.get_first_child() is not None:  # Only add if has content
                info_box.append(gpg_box)
        
        box.append(info_box)
        
        row.set_child(box)
        
        # Make row activatable and connect to toggle checkbox
        row.set_activatable(True)
        def on_row_activated(row_widget):
            if hasattr(row_widget, 'checkbox'):
                row_widget.checkbox.set_active(not row_widget.checkbox.get_active())
        self.distro_list.connect("row-activated", lambda lb, r: on_row_activated(r))
        
        return row
    
    def on_distro_toggled(self, checkbox: Gtk.CheckButton, distro: Distro) -> None:
        """Handle distro selection toggle"""
        if checkbox.get_active():
            self.selected_distros[distro.id] = distro
            logger.info(f"Selected: {distro.name}")
        else:
            if distro.id in self.selected_distros:
                del self.selected_distros[distro.id]
                logger.info(f"Deselected: {distro.name}")
        
        self.update_selection_summary()
    
    def update_selection_summary(self) -> None:
        """Update the selection summary bar"""
        # Get USB device info from distro page (set in navigate_to_distro_page)
        usb_device = getattr(self, 'selected_usb_device', None)
        
        num_selected = len(self.selected_distros)
        total_size_mb = sum(
            d.latest_release.size_mb 
            for d in self.selected_distros.values() 
            if d.latest_release and d.latest_release.size_mb > 0
        )
        total_size_gb = total_size_mb / 1024
        
        # Calculate available space (USB size - EFI partition)
        EFI_SIZE_GB = 1.0
        SAFETY_MARGIN = 1.1  # 10% extra
        
        # Update current selection info with multi-column layout
        if num_selected > 0:
            distro_names = [d.name for d in self.selected_distros.values()]
            
            # Update summary
            self.selection_summary_label.set_text(
                f"{num_selected} distro{'s' if num_selected != 1 else ''} selected ({total_size_gb:.1f} GB)"
            )
            
            # Clear existing columns
            while True:
                child = self.distro_columns_box.get_first_child()
                if child is None:
                    break
                self.distro_columns_box.remove(child)
            
            # Create columns (max 5 items per column)
            ITEMS_PER_COLUMN = 5
            num_columns = (len(distro_names) + ITEMS_PER_COLUMN - 1) // ITEMS_PER_COLUMN
            
            for col_idx in range(num_columns):
                start_idx = col_idx * ITEMS_PER_COLUMN
                end_idx = min(start_idx + ITEMS_PER_COLUMN, len(distro_names))
                column_names = distro_names[start_idx:end_idx]
                
                # Create column
                column_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                column_label = Gtk.Label()
                column_label.add_css_class("dim-label")
                column_label.set_halign(Gtk.Align.START)
                column_label.set_text("\n".join(f"• {name}" for name in column_names))
                column_box.append(column_label)
                
                self.distro_columns_box.append(column_box)
        else:
            # No selection
            self.selection_summary_label.set_text("No distros selected yet")
            
            # Clear columns
            while True:
                child = self.distro_columns_box.get_first_child()
                if child is None:
                    break
                self.distro_columns_box.remove(child)
        
        if usb_device:
            available_gb = (usb_device.size_bytes / (1024**3)) - EFI_SIZE_GB
            required_gb = total_size_gb * SAFETY_MARGIN
            usage_fraction = min(required_gb / available_gb, 1.0) if available_gb > 0 else 0
            
            # Update USB space info
            used_gb = (usb_device.size_bytes / (1024**3)) - available_gb
            self.usb_space_label.set_text(
                f"Total: {usb_device.size_bytes / (1024**3):.1f} GB\n"
                f"Available: {available_gb:.1f} GB\n"
                f"Required: {required_gb:.1f} GB"
            )
            
            # Update progress bar
            self.space_progress.set_fraction(usage_fraction)
            self.space_progress.set_text(f"{usage_fraction*100:.0f}% of available space")
            
            # Update current ISOs on USB - show ALL ISOs
            if hasattr(usb_device, 'luxusb_state') and usb_device.luxusb_state:
                iso_list = usb_device.luxusb_state.installed_isos
                sb_enabled = getattr(usb_device.luxusb_state, 'secure_boot_enabled', False)
                
                # Build status text
                status_lines = []
                if iso_list:
                    status_lines.append(f"{len(iso_list)} ISO{'s' if len(iso_list) != 1 else ''} installed:")
                    status_lines.extend(f"• {iso}" for iso in iso_list)
                else:
                    status_lines.append("No ISOs currently on USB")
                
                # Add Secure Boot status
                if sb_enabled:
                    status_lines.append("\n🔒 Secure Boot: Enabled")
                else:
                    status_lines.append("\nSecure Boot: Disabled")
                
                self.current_isos_label.set_text("\n".join(status_lines))
            else:
                self.current_isos_label.set_text("USB not yet configured with LUXusb")
            
            # Show warning if exceeds capacity
            if required_gb > available_gb:
                self.warning_label.set_text(
                    f"⚠️ Selection too large! Exceeds capacity by {required_gb - available_gb:.1f} GB. "
                    f"Please remove some distributions."
                )
                self.warning_label.set_visible(True)
                self.continue_btn.set_sensitive(False)
                self.space_progress.add_css_class("error")
            else:
                self.warning_label.set_visible(False)
                self.continue_btn.set_sensitive(num_selected > 0 or len(self.custom_isos) > 0)
                self.space_progress.remove_css_class("error")
        else:
            # No USB selected yet
            self.usb_space_label.set_text("Please select a USB device first")
            self.current_isos_label.set_text("N/A")
            self.space_progress.set_fraction(0)
            self.space_progress.set_text("No USB device selected")
            self.continue_btn.set_sensitive(num_selected > 0 or len(self.custom_isos) > 0)
        
        # Update continue button text
        if num_selected > 0:
            self.continue_btn.set_label(f"Continue with {num_selected} Distro{'s' if num_selected != 1 else ''}")
        else:
            self.continue_btn.set_label("Continue")
    
    def on_back_clicked(self, _button: Gtk.Button) -> None:
        """Navigate back to family selection page"""
        # Store current selections in the application for persistence
        app = self.main_window.get_application()
        if not hasattr(app, 'pending_selections'):
            app.pending_selections = {}
        
        # Save current selections
        for distro_id, distro in self.selected_distros.items():
            app.pending_selections[distro_id] = distro
        
        logger.info(f"Going back with {len(app.pending_selections)} distro(s) already selected")
        
        # Pop current page to go back to family page
        nav_view = self.main_window.nav_view
        nav_view.pop()
    
    def on_clear_all_clicked(self, _button: Gtk.Button) -> None:
        """Clear all selections"""
        self.selected_distros.clear()
        
        # Uncheck all checkboxes - iterate using while loop
        row = self.distro_list.get_first_child()
        while row:
            if hasattr(row, 'checkbox'):
                row.checkbox.set_active(False)
            row = row.get_next_sibling()
        
        self.update_selection_summary()
        logger.info("Cleared all selections")
    
    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        """Handle search text change"""
        query = entry.get_text().lower()
        
        # Filter rows - iterate using while loop
        row = self.distro_list.get_first_child()
        while row:
            if hasattr(row, 'distro'):
                distro = row.distro
                visible = (query in distro.name.lower() or 
                          query in distro.description.lower())
                row.set_visible(visible)
            row = row.get_next_sibling()
    
    def on_add_custom_iso_clicked(self, _button: Gtk.Button) -> None:
        """Handle add custom ISO button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select ISO File")
        
        # Set file filter
        filter_iso = Gtk.FileFilter()
        filter_iso.set_name("ISO Images")
        filter_iso.add_pattern("*.iso")
        
        filters = Gtk.ListStore.new([Gtk.FileFilter])
        filters.append([filter_iso])
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
            logger.error("File selection error: %s", e)
    
    def add_custom_iso(self, path: str) -> None:
        """Add a custom ISO to the list"""
        from pathlib import Path
        
        # Validate ISO
        custom_iso = validate_custom_iso(Path(path))
        
        if not custom_iso.is_valid:
            self.main_window.show_error_dialog(
                "Invalid ISO File",
                custom_iso.error_message or "The selected file is not a valid ISO."
            )
            return
        
        # Add to list
        self.custom_isos.append(custom_iso)
        
        # Create row
        row = self.create_custom_iso_row(custom_iso)
        self.custom_iso_list.append(row)
        
        logger.info(f"Added custom ISO: {custom_iso.filename}")
    
    def create_custom_iso_row(self, custom_iso: CustomISO) -> Gtk.ListBoxRow:
        """Create a row for a custom ISO"""
        row = Gtk.ListBoxRow()
        row.custom_iso = custom_iso
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        # Filename
        name_label = Gtk.Label(label=custom_iso.display_name)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        info_box.append(name_label)
        
        # Size
        size_label = Gtk.Label(label=f"{custom_iso.size_mb:.1f} MB")
        size_label.set_halign(Gtk.Align.START)
        size_label.add_css_class("dim-label")
        info_box.append(size_label)
        
        box.append(info_box)
        
        # Remove button
        remove_btn = Gtk.Button(icon_name="user-trash-symbolic")
        remove_btn.add_css_class("flat")
        remove_btn.connect("clicked", lambda btn: self.remove_custom_iso(row))
        box.append(remove_btn)
        
        row.set_child(box)
        return row
    
    def remove_custom_iso(self, row: Gtk.ListBoxRow) -> None:
        """Remove a custom ISO"""
        if hasattr(row, 'custom_iso'):
            self.custom_isos.remove(row.custom_iso)
            self.custom_iso_list.remove(row)
    
    def on_continue_clicked(self, _button: Gtk.Button) -> None:
        """Handle continue button click"""
        # Get app reference for Secure Boot check
        app = self.main_window.get_application()
        
        # Build selections list from selected distros
        selections = []
        for idx, distro in enumerate(self.selected_distros.values()):
            # Safety check: Skip incompatible distros if Secure Boot is enabled
            if app.enable_secure_boot:
                is_compatible = getattr(distro, 'secure_boot_compatible', True)
                if not is_compatible:
                    logger.warning(f"Skipping incompatible distro with Secure Boot: {distro.name}")
                    continue
            
            if distro.latest_release:
                selection = DistroSelection(
                    distro=distro,
                    release=distro.latest_release,
                    priority=idx  # Priority based on selection order
                )
                selections.append(selection)
        
        # Must have at least distro selection or custom ISO
        if not selections and not self.custom_isos:
            self.main_window.show_error_dialog(
                "No Selection",
                "Please select at least one distribution or add a custom ISO to continue."
            )
            return
        
        # Store selections
        app = self.main_window.get_application()
        app.selections = selections
        app.custom_isos = self.custom_isos.copy()
        
        # Navigate to progress page
        self.main_window.navigate_to_progress_page()
    
    def show_gpg_info(self, _button: Gtk.Button, distro: Distro) -> None:
        """Show GPG key information dialog"""
        # Load GPG keys from config
        import json
        from pathlib import Path
        
        gpg_keys_file = Path(__file__).parent.parent / "data" / "gpg_keys.json"
        gpg_key_info = None
        
        try:
            with open(gpg_keys_file, 'r', encoding='utf-8') as f:
                gpg_keys = json.load(f)
                # Find GPG key for this distro
                for key_id, key_data in gpg_keys.items():
                    if distro.id.lower() in key_id.lower():
                        gpg_key_info = key_data
                        break
        except Exception as e:
            logger.error(f"Failed to load GPG keys: {e}")
        
        # Create dialog
        if gpg_key_info:
            fingerprint = gpg_key_info.get('fingerprint', 'Unknown')
            key_server = gpg_key_info.get('key_server', 'Unknown')
            
            # Format fingerprint with spaces for readability
            fingerprint_formatted = ' '.join([fingerprint[i:i+4] for i in range(0, len(fingerprint), 4)])
            
            message = (
                f"<b>{distro.name}</b> uses GPG signature verification for enhanced security.\n\n"
                f"<b>Key Fingerprint:</b>\n<tt>{fingerprint_formatted}</tt>\n\n"
                f"<b>Key Server:</b> {key_server}\n\n"
                "This ensures the ISO file is authentic and unmodified."
            )
        else:
            message = (
                f"<b>{distro.name}</b> uses GPG signature verification.\n\n"
                "The distribution's GPG key will be verified during download."
            )
        
        dialog = Adw.MessageDialog.new(
            self.main_window,
            "GPG Verification Details",
            None
        )
        dialog.set_body_use_markup(True)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.present()
        # Clear pending selections since user is proceeding
        if hasattr(app, 'pending_selections'):
            app.pending_selections.clear()
        
        logger.info(f"Proceeding with {len(selections)} distro(s) and {len(self.custom_isos)} custom ISO(s)")
        
        # Navigate to progress page
        self.main_window.navigate_to_progress_page()

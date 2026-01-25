"""
Preferences dialog for update settings (Phase 3)
"""

import logging
from datetime import datetime
from typing import Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from luxusb.utils.update_scheduler import UpdateScheduler

logger = logging.getLogger(__name__)


class PreferencesDialog(Adw.PreferencesWindow):
    """Preferences dialog for update settings"""
    
    def __init__(self, parent: Gtk.Window):
        super().__init__()
        
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(600, 500)
        
        self.scheduler = UpdateScheduler()
        
        self._build_ui()
        self._load_preferences()
    
    def _build_ui(self) -> None:
        """Build preference pages"""
        
        # Updates page
        updates_page = Adw.PreferencesPage.new()
        updates_page.set_title("Updates")
        updates_page.set_icon_name("software-update-available-symbolic")
        
        # Automatic checks group
        auto_group = Adw.PreferencesGroup.new()
        auto_group.set_title("Automatic Checks")
        auto_group.set_description("Configure when LUXusb checks for distribution metadata updates")
        
        # Enable auto-check switch
        self.auto_check_row = Adw.SwitchRow.new()
        self.auto_check_row.set_title("Check for updates on startup")
        self.auto_check_row.set_subtitle("Automatically check for new distribution metadata when LUXusb starts")
        self.auto_check_row.connect("notify::active", self._on_auto_check_changed)
        auto_group.add(self.auto_check_row)
        
        # Check interval spin button
        self.interval_row = Adw.SpinRow.new_with_range(1, 30, 1)
        self.interval_row.set_title("Check interval (days)")
        self.interval_row.set_subtitle("How often to check for updates")
        self.interval_row.connect("changed", self._on_interval_changed)
        auto_group.add(self.interval_row)
        
        updates_page.add(auto_group)
        
        # Status group
        status_group = Adw.PreferencesGroup.new()
        status_group.set_title("Status")
        status_group.set_description("Current update check status")
        
        # Last check row
        self.last_check_row = Adw.ActionRow.new()
        self.last_check_row.set_title("Last check")
        self.last_check_row.set_subtitle("Never")
        status_group.add(self.last_check_row)
        
        # Next check row
        self.next_check_row = Adw.ActionRow.new()
        self.next_check_row.set_title("Next check")
        self.next_check_row.set_subtitle("On next startup")
        status_group.add(self.next_check_row)
        
        updates_page.add(status_group)
        
        # Skipped versions group
        skip_group = Adw.PreferencesGroup.new()
        skip_group.set_title("Skipped Versions")
        skip_group.set_description("Distributions you've chosen not to update")
        
        # Skip list box
        self.skip_listbox = Gtk.ListBox.new()
        self.skip_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.skip_listbox.add_css_class("boxed-list")
        skip_group.add(self.skip_listbox)
        
        # Clear skip list button
        clear_button = Gtk.Button.new_with_label("Clear Skip List")
        clear_button.add_css_class("destructive-action")
        clear_button.connect("clicked", self._on_clear_skip_list)
        
        clear_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        clear_box.set_halign(Gtk.Align.CENTER)
        clear_box.set_margin_top(12)
        clear_box.append(clear_button)
        skip_group.add(clear_box)
        
        updates_page.add(skip_group)
        
        # Actions group
        actions_group = Adw.PreferencesGroup.new()
        actions_group.set_title("Actions")
        
        # Check now button
        check_now_button = Gtk.Button.new_with_label("Check for Updates Now")
        check_now_button.add_css_class("suggested-action")
        check_now_button.connect("clicked", self._on_check_now)
        
        check_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        check_box.set_halign(Gtk.Align.CENTER)
        check_box.set_margin_top(12)
        check_box.append(check_now_button)
        actions_group.add(check_box)
        
        updates_page.add(actions_group)
        
        self.add(updates_page)
    
    def _load_preferences(self) -> None:
        """Load current preferences from scheduler"""
        prefs = self.scheduler.preferences
        stats = self.scheduler.get_statistics()
        
        # Auto-check setting
        self.auto_check_row.set_active(prefs.get('auto_check_on_startup', True))
        
        # Check interval
        interval = prefs.get('check_interval_days', 7)
        self.interval_row.set_value(interval)
        
        # Last check time
        last_check = stats.get('last_check')
        if last_check and last_check != "Never":
            try:
                last_dt = datetime.fromisoformat(last_check)
                self.last_check_row.set_subtitle(last_dt.strftime("%B %d, %Y at %I:%M %p"))
            except (ValueError, TypeError):
                self.last_check_row.set_subtitle("Never")
        else:
            self.last_check_row.set_subtitle("Never")
        
        # Next check time
        next_check = stats.get('next_check')
        if next_check and next_check != "On next startup":
            try:
                next_dt = datetime.fromisoformat(next_check)
                self.next_check_row.set_subtitle(next_dt.strftime("%B %d, %Y at %I:%M %p"))
            except (ValueError, TypeError):
                self.next_check_row.set_subtitle("On next startup")
        else:
            self.next_check_row.set_subtitle("On next startup")
        
        # Skip list
        self._update_skip_list()
    
    def _update_skip_list(self) -> None:
        """Update skip list display"""
        # Clear existing rows
        while True:
            row = self.skip_listbox.get_first_child()
            if row is None:
                break
            self.skip_listbox.remove(row)
        
        # Get skip versions
        skip_versions = self.scheduler.preferences.get('skip_versions', [])
        
        if not skip_versions:
            # Show empty state
            empty_row = Adw.ActionRow.new()
            empty_row.set_title("No skipped versions")
            empty_row.set_subtitle("You haven't skipped any distribution updates")
            self.skip_listbox.append(empty_row)
        else:
            # Add rows for each skip version
            for entry in skip_versions:
                distro_id = entry.get('distro_id', 'Unknown')
                version = entry.get('version', 'Unknown')
                
                row = Adw.ActionRow.new()
                row.set_title(f"{distro_id}")
                row.set_subtitle(f"Version: {version}")
                
                # Remove button
                remove_btn = Gtk.Button.new_from_icon_name("user-trash-symbolic")
                remove_btn.set_valign(Gtk.Align.CENTER)
                remove_btn.add_css_class("flat")
                remove_btn.set_tooltip_text("Remove from skip list")
                remove_btn.connect("clicked", self._on_remove_skip, entry)
                row.add_suffix(remove_btn)
                
                self.skip_listbox.append(row)
    
    def _on_auto_check_changed(self, switch: Adw.SwitchRow, _param) -> None:
        """Handle auto-check toggle"""
        enabled = switch.get_active()
        
        # Update scheduler
        prefs = self.scheduler.preferences
        prefs['auto_check_on_startup'] = enabled
        self.scheduler.save_preferences()
        
        logger.info(f"Auto-check on startup: {enabled}")
    
    def _on_interval_changed(self, spin: Adw.SpinRow) -> None:
        """Handle interval change"""
        interval = int(spin.get_value())
        
        # Update scheduler
        prefs = self.scheduler.preferences
        prefs['check_interval_days'] = interval
        self.scheduler.save_preferences()
        
        logger.info(f"Check interval set to {interval} days")
    
    def _on_check_now(self, _button: Gtk.Button) -> None:
        """Handle check now button"""
        # Close preferences and trigger update check
        self.close()
        
        # Emit signal to parent to run update check
        # For now, just show toast
        toast = Adw.Toast.new("Checking for updates...")
        toast.set_timeout(2)
        if self.get_transient_for():
            parent = self.get_transient_for()
            if hasattr(parent, 'add_toast'):
                parent.add_toast(toast)
    
    def _on_clear_skip_list(self, _button: Gtk.Button) -> None:
        """Handle clear skip list button"""
        # Confirmation dialog
        dialog = Adw.MessageDialog.new(
            self,
            "Clear Skip List?",
            "This will remove all distributions from the skip list. You will be notified of updates for them again."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("clear", "Clear List")
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        
        def on_response(_dialog, response):
            if response == "clear":
                prefs = self.scheduler.preferences
                prefs['skip_versions'] = []
                prefs['skip_until_date'] = None
                self.scheduler.save_preferences()
                self._update_skip_list()
                logger.info("Skip list cleared")
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_remove_skip(self, _button: Gtk.Button, entry: dict) -> None:
        """Handle remove skip entry"""
        distro_id = entry.get('distro_id')
        version = entry.get('version')
        
        # Remove from skip list
        prefs = self.scheduler.preferences
        skip_versions = prefs.get('skip_versions', [])
        skip_versions = [s for s in skip_versions if not (s.get('distro_id') == distro_id and s.get('version') == version)]
        prefs['skip_versions'] = skip_versions
        self.scheduler.save_preferences()
        
        # Update display
        self._update_skip_list()
        logger.info(f"Removed {distro_id} {version} from skip list")

"""
Main GTK4 application window
"""

import logging
from typing import Optional, Callable, Any
from threading import Thread

from luxusb.gui import Gtk, Adw, GLib, Gio

from luxusb import APP_NAME, APP_ID
from luxusb.utils.usb_detector import USBDetector, USBDevice
from luxusb.utils.distro_manager import DistroSelection
from luxusb.utils.custom_iso import CustomISO
from luxusb.utils.secure_boot import detect_secure_boot
from luxusb.gui.splash import SplashWindow
from luxusb.gui.device_page import DeviceSelectionPage
from luxusb.gui.family_page import FamilySelectionPage
from luxusb.gui.distro_page import DistroSelectionPage
from luxusb.gui.progress_page import ProgressPage
from luxusb.constants import ConfigKeys, Interval, PathPattern

logger = logging.getLogger(__name__)


class LUXusbApplication(Adw.Application):
    """Main application class"""
    
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)
        self.window: Optional[MainWindow] = None
        self.splash: Optional[SplashWindow] = None
        self.usb_detector = USBDetector()
        self.selected_device: Optional[USBDevice] = None
        self.selections: list[DistroSelection] = []
        self.custom_isos: list[CustomISO] = []
        self.enable_secure_boot = False
        self.append_mode = False  # Whether to append to existing USB or create fresh
        
        # Detect Secure Boot status
        self.secure_boot_status = detect_secure_boot()
        if self.secure_boot_status.is_active:
            logger.info("Secure Boot is active on this system")
            self.enable_secure_boot = True
        
        # Register actions
        self._setup_actions()
    
    def do_activate(self) -> None:
        """Called when application is activated"""
        if not self.window:
            # Show splash screen
            self.splash = SplashWindow()
            self.splash.set_application(self)
            self.splash.present()
            
            # Start background metadata check
            Thread(target=self._check_metadata_updates, daemon=True).start()
            
            # Load main window after a short delay (simulates loading time)
            GLib.timeout_add(1500, self._show_main_window)
    
    def _show_main_window(self) -> bool:
        """Show main window and close splash screen"""
        # Create and show main window
        self.window = MainWindow(application=self)
        self.window.present()
        
        # Close splash screen
        if self.splash:
            self.splash.close_splash()
            self.splash = None
        
        return False  # Don't repeat
    
    def _check_metadata_updates(self) -> None:
        """Check for metadata updates in background thread (Phase 3 enhanced)"""
        try:
            from luxusb.utils.update_scheduler import UpdateScheduler
            from luxusb.utils.network_detector import is_network_available
            from luxusb.utils.distro_validator import DistroValidator
            
            # Initialize scheduler
            scheduler = UpdateScheduler()
            
            # Check if auto-check is enabled
            if not scheduler.is_auto_check_enabled():
                logger.info("Automatic update checks disabled")
                return
            
            # Check network connectivity
            if not is_network_available(timeout=2.0):
                logger.info("Network unavailable - skipping update check")
                return
            
            # Check if we should run update check
            should_check, reason = scheduler.should_check_for_updates()
            if not should_check:
                logger.info(f"Skipping update check: {reason}")
                return
            
            logger.info(f"Running update check: {reason}")
            
            # Run validation
            validator = DistroValidator()
            stale_distros, unverified = validator.check_metadata_freshness()
            
            # Filter out skipped versions
            filtered_distros = []
            for distro_id in stale_distros:
                # Simplified - in real implementation, would parse version from metadata
                if not scheduler.should_skip_version(distro_id, "unknown"):
                    filtered_distros.append(distro_id)
            
            if filtered_distros:
                # Show update notification on main thread
                GLib.idle_add(self._show_update_notification, filtered_distros)
            else:
                logger.info("All metadata up to date")
                # Still mark check as completed even if nothing to update
                scheduler.mark_check_completed()
        
        except Exception as e:
            logger.exception(f"Metadata check failed: {e}")
    
    def _show_update_notification(self, stale_distros: list[str]) -> bool:
        """Show update notification dialog (runs on main thread)"""
        if not self.window:
            return False
        
        from luxusb.gui.update_dialog import UpdateNotificationDialog, UpdateWorkflow
        
        dialog = UpdateNotificationDialog(self.window, stale_distros)
        dialog.connect("response", lambda d, response: self._handle_update_response(d, response, stale_distros))
        dialog.present()
        
        return False  # Don't repeat
    
    def _handle_update_response(self, dialog: Adw.MessageDialog, response: str, stale_distros: list[str]) -> None:
        """Handle user response to update notification (Phase 3 enhanced)"""
        from luxusb.utils.update_scheduler import UpdateScheduler
        
        scheduler = UpdateScheduler()
        
        if response == "update":
            # User wants to update now
            dialog.close()
            self._start_update_workflow(stale_distros)
            
            # Mark check as completed (clears remind_later, updates timestamp)
            scheduler.mark_check_completed()
        
        elif response == "later":
            # Remind in 24 hours
            scheduler.set_remind_later(hours=24)
            logger.info("Update reminder set for 24 hours")
            dialog.close()
        
        elif response == "skip":
            # Skip for 30 days
            scheduler.set_skip_date(days=30)
            
            # Also add these specific versions to skip list
            for distro_id in stale_distros:
                scheduler.add_skip_version(distro_id, "latest")
            
            logger.info(f"Skipped updates for 30 days and versions: {stale_distros}")
            dialog.close()
            
            logger.info("User skipped update notification")
            dialog.close()
    
    def _start_update_workflow(self, stale_distros: list[str]) -> None:
        """Start update workflow with progress dialog"""
        from luxusb.gui.update_dialog import UpdateWorkflow
        
        def on_complete(success_count: int, error_count: int):
            """Called when updates complete"""
            if error_count == 0:
                # Show success toast
                toast = Adw.Toast.new(f"✅ {success_count} distribution(s) updated")
                toast.set_timeout(3)
                if hasattr(self.window, 'add_toast'):
                    self.window.add_toast(toast)
            else:
                # Show warning toast
                toast = Adw.Toast.new(f"⚠️ {success_count} updated, {error_count} failed")
                toast.set_timeout(5)
                if hasattr(self.window, 'add_toast'):
                    self.window.add_toast(toast)
        
        workflow = UpdateWorkflow(self.window, stale_distros, on_complete)
        workflow.start()
    
    def _setup_actions(self) -> None:
        """Setup application actions"""
        # Check for updates action
        check_updates_action = Gio.SimpleAction.new("check_updates", None)
        check_updates_action.connect("activate", self.on_check_updates)
        self.add_action(check_updates_action)
        
        # Preferences action
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)
        
        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
    
    def on_check_updates(self, _action, _param) -> None:
        """Handle Check for Updates menu item"""
        if not self.window:
            return
        
        # Show progress dialog
        dialog = Adw.MessageDialog.new(
            self.window,
            "Checking for Updates",
            "Fetching latest distribution information from official sources..."
        )
        dialog.add_response("cancel", "Cancel")
        
        # Create spinner
        spinner = Gtk.Spinner()
        spinner.set_spinning(True)
        spinner.set_margin_top(12)
        spinner.set_margin_bottom(12)
        dialog.set_extra_child(spinner)
        
        dialog.present()
        
        # Run update check in background thread
        def check_updates_thread():
            try:
                from luxusb.utils.distro_updater import DistroUpdater
                updater = DistroUpdater()
                results = updater.update_all()
                
                # Update UI on main thread
                GLib.idle_add(lambda: self._show_update_results(dialog, results))
            except Exception as e:
                logger.exception(f"Update check failed: {e}")
                GLib.idle_add(lambda: self._show_update_error(dialog, str(e)))
        
        Thread(target=check_updates_thread, daemon=True).start()
    
    def _show_update_results(self, dialog: Adw.MessageDialog, results: dict) -> None:
        """Show update check results"""
        dialog.close()
        
        if not self.window:
            return
        
        success_count = sum(1 for v in results.values() if v)
        total = len(results)
        
        # Show toast notification
        if success_count > 0:
            toast_msg = f"✓ Updated {success_count} of {total} distributions"
            toast = Adw.Toast.new(toast_msg)
            toast.set_timeout(5)
            self.toast_overlay.add_toast(toast)
            logger.info(toast_msg)
            
            # Hot-reload distros in the UI without restart
            self._reload_distro_lists()
            
            # Clear update indicator
            self._show_update_indicator(False)
        
        # Show detailed dialog
        result_msg = f"Updated {success_count} of {total} distributions."
        if success_count > 0:
            result_msg += "\n\nDistribution list has been refreshed."
        
        result_dialog = Adw.MessageDialog.new(
            self.window,
            "Updates Complete",
            result_msg
        )
        result_dialog.add_response("ok", "OK")
        result_dialog.present()
    
    def _show_update_error(self, dialog: Adw.MessageDialog, error: str) -> None:
        """Show update error"""
        dialog.close()
        
        if not self.window:
            return
        
        error_dialog = Adw.MessageDialog.new(
            self.window,
            "Update Failed",
            f"Failed to check for updates:\n{error}"
        )
        error_dialog.add_response("ok", "OK")
        error_dialog.present()
    
    def on_preferences(self, _action, _param) -> None:
        """Show preferences dialog"""
        if not self.window:
            return
        
        from luxusb.gui.preferences_dialog import PreferencesDialog
        
        prefs = PreferencesDialog(self.window)
        prefs.present()
    
    def on_about(self, _action, _param) -> None:
        """Show about dialog"""
        if not self.window:
            return
        
        about = Adw.AboutWindow(
            transient_for=self.window,
            modal=True,
            application_name=APP_NAME,
            application_icon=APP_ID,
            developer_name="LUXusb Contributors",
            version="0.2.0",
            website="https://github.com/solon/luxusb",
            issue_url="https://github.com/solon/luxusb/issues",
            license_type=Gtk.License.GPL_3_0,
            comments="Create bootable USB drives with multiple Linux distributions"
        )
        about.present()


class MainWindow(Adw.ApplicationWindow):
    """Main application window"""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        
        self.set_title(APP_NAME)
        self.set_default_size(900, 700)
        
        # Get style manager for theme switching
        self.style_manager = Adw.StyleManager.get_default()
        
        # Load and apply saved theme preference
        self._load_theme_preference()
        
        # Create header bar
        header = Adw.HeaderBar()
        
        # Menu button with options
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Menu")
        menu_button.add_css_class("flat")
        self.menu_button = menu_button  # Store reference for badge updates
        
        # Create menu
        menu = Gio.Menu()
        menu.append("Check for Updates", "app.check_updates")
        menu.append("About", "app.about")
        menu_button.set_menu_model(menu)
        
        header.pack_end(menu_button)
        
        # Check if updates are needed (show indicator)
        GLib.timeout_add_seconds(2, self._check_update_status)
        
        # Light/Dark mode toggle button
        theme_button = Gtk.Button()
        theme_button.set_icon_name("weather-clear-night-symbolic")
        theme_button.set_tooltip_text("Toggle Light/Dark Mode")
        theme_button.connect("clicked", self.on_theme_toggle_clicked)
        theme_button.add_css_class("flat")
        header.pack_start(theme_button)
        self.theme_button = theme_button
        
        # Update icon based on current theme
        self.update_theme_icon()
        
        # Secure Boot toggle (if available)
        app = self.get_application()
        if app.secure_boot_status.available:
            secure_boot_switch = Gtk.Switch()
            secure_boot_switch.set_active(app.enable_secure_boot)
            secure_boot_switch.connect(
                "notify::active",
                self.on_secure_boot_toggled
            )
            secure_boot_switch.set_tooltip_text(
                "Enable Secure Boot signing for bootloader"
            )
            
            secure_boot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            secure_boot_label = Gtk.Label(label="Secure Boot")
            secure_boot_box.append(secure_boot_label)
            secure_boot_box.append(secure_boot_switch)
            
            header.pack_end(secure_boot_box)
        
        # Create navigation view
        self.nav_view = Adw.NavigationView()
        
        # Create pages
        self.device_page = DeviceSelectionPage(self)
        self.family_page = FamilySelectionPage(self)
        self.progress_page = ProgressPage(self)
        
        # Note: distro_page is created on-demand with family filter
        
        # Add pages to navigation
        self.nav_view.add(self.device_page)
        
        # Create toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.nav_view)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header)
        main_box.append(self.toast_overlay)
        
        self.set_content(main_box)
        
        # Start periodic update checker using interval constant
        GLib.timeout_add_seconds(Interval.PERIODIC_UPDATE_CHECK, self._periodic_update_check)
        logger.info(f"Started periodic update checker (every {Interval.PERIODIC_UPDATE_CHECK // 3600} hours)")
    
    def navigate_to_family_page(self) -> None:
        """Navigate to family selection page"""
        self.nav_view.push(self.family_page)
    
    def navigate_to_distro_page(self, family_filter: str = None) -> None:
        """Navigate to distro selection page with optional family filter"""
        # Create new distro page with family filter
        distro_page = DistroSelectionPage(self, family_filter=family_filter)
        
        # Store USB device reference for space calculation
        app = self.get_application()
        distro_page.selected_usb_device = app.selected_device
        
        self.nav_view.push(distro_page)
        distro_page.refresh_distros()
    
    def navigate_to_progress_page(self) -> None:
        """Navigate to progress page"""
        self.nav_view.push(self.progress_page)
        self.progress_page.start_installation()
    
    def show_error_dialog(self, title: str, message: str) -> None:
        """Show error dialog"""
        dialog = Adw.MessageDialog.new(self, title, message)
        dialog.add_response("ok", "OK")
        dialog.present()
    
    def show_warning_dialog(self, title: str, message: str, callback: Optional[Callable] = None) -> None:
        """Show warning dialog with confirmation"""
        dialog = Adw.MessageDialog.new(self, title, message)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("continue", "Continue")
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        
        if callback:
            dialog.connect("response", callback)
        
        dialog.present()
    
    def show_configured_device_dialog(self, title: str, message: str, callback: Optional[Callable] = None) -> None:
        """Show dialog for already-configured LUXusb devices"""
        dialog = Adw.MessageDialog.new(self, title, message)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("add", "Add More ISOs")
        dialog.add_response("erase", "Erase and Start Fresh")
        dialog.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_response_appearance("erase", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("add")
        
        if callback:
            dialog.connect("response", callback)
        
        dialog.present()
    
    def on_secure_boot_toggled(self, switch: Gtk.Switch, _param) -> None:
        """Handle Secure Boot toggle"""
        app = self.get_application()
        app.enable_secure_boot = switch.get_active()
        status = 'enabled' if app.enable_secure_boot else 'disabled'
        logger.info("Secure Boot signing: %s", status)
        
        # Refresh distro page if currently visible to update incompatible distros
        current_page = self.nav_view.get_visible_page()
        if current_page and hasattr(current_page, 'refresh_distros'):
            # This is a distro page - refresh it to grey out incompatible distros
            logger.info("Refreshing distro list to reflect Secure Boot change")
            current_page.refresh_distros()
    
    def _load_theme_preference(self) -> None:
        """Load theme preference from config and apply it"""
        from luxusb.config import config
        
        theme = config.get(ConfigKeys.UI.THEME, default='dark')
        
        if theme == 'dark':
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            logger.info("Loaded dark mode from preferences")
        elif theme == 'light':
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            logger.info("Loaded light mode from preferences")
        else:
            # 'auto' or unknown - use system preference
            self.style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
            logger.info("Using system theme preference")
    
    def _save_theme_preference(self, theme: str) -> None:
        """Save theme preference to config"""
        from luxusb.config import config
        
        config.set('ui.theme', theme)
        config.save()
        logger.info(f"Saved theme preference: {theme}")
    
    def on_theme_toggle_clicked(self, _button: Gtk.Button) -> None:
        """Toggle between light and dark themes"""
        current_scheme = self.style_manager.get_color_scheme()
        
        # Toggle between light and dark (skip 'default'/system preference)
        if current_scheme == Adw.ColorScheme.FORCE_LIGHT:
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            logger.info("Switched to dark mode")
            self._save_theme_preference('dark')
        else:
            self.style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            logger.info("Switched to light mode")
            self._save_theme_preference('light')
        
        # Update button icon
        self.update_theme_icon()
    
    def update_theme_icon(self) -> None:
        """Update theme button icon based on current theme"""
        current_scheme = self.style_manager.get_color_scheme()
        
        # Show sun icon in dark mode (clicking will go to light)
        # Show moon icon in light mode (clicking will go to dark)
        if current_scheme == Adw.ColorScheme.FORCE_DARK:
            self.theme_button.set_icon_name("weather-clear-symbolic")  # Sun icon
            self.theme_button.set_tooltip_text("Switch to Light Mode")
        else:
            self.theme_button.set_icon_name("weather-clear-night-symbolic")  # Moon icon
            self.theme_button.set_tooltip_text("Switch to Dark Mode")
    
    def _periodic_update_check(self) -> bool:
        """Periodically check for updates in the background"""
        try:
            from luxusb.config import Config
            config = Config()
            
            # Check if auto-update is enabled using constant
            if not config.get(ConfigKeys.Metadata.AUTO_UPDATE_ON_STARTUP, default=True):
                return True  # Keep timer running
            
            # Run update check silently
            def silent_update_thread():
                try:
                    from luxusb.utils.distro_updater import DistroUpdater
                    updater = DistroUpdater()
                    results = updater.update_all()
                    
                    success_count = sum(1 for v in results.values() if v)
                    if success_count > 0:
                        # Show subtle notification
                        GLib.idle_add(
                            lambda: self._show_silent_update_notification(
                                success_count
                            )
                        )
                except Exception as e:
                    logger.debug(f"Periodic update check failed: {e}")
            
            Thread(target=silent_update_thread, daemon=True).start()
            
        except Exception as e:
            logger.debug(f"Periodic update check error: {e}")
        
        return True  # Keep timer running
    
    def _show_silent_update_notification(self, count: int) -> None:
        """Show notification for background updates"""
        toast = Adw.Toast.new(
            f"🔄 {count} distribution(s) updated in background"
        )
        toast.set_timeout(4)
        self.toast_overlay.add_toast(toast)
        
        # Hot-reload distros
        self._reload_distro_lists()
        logger.info(f"Background update completed: {count} distros updated")
    
    def _reload_distro_lists(self) -> None:
        """Reload distribution lists in all pages without restart"""
        try:
            # Reload family page
            if hasattr(self, 'family_page'):
                self.family_page.load_families()
                logger.debug("Reloaded family page")
            
            # Reload distro page if it exists and is visible
            if hasattr(self, 'distro_page'):
                self.distro_page.refresh_distros()
                logger.debug("Reloaded distro page")
                
        except Exception as e:
            logger.warning(f"Failed to reload distro lists: {e}")
    
    def _check_update_status(self) -> bool:
        """Check if updates are available and show indicator"""
        try:
            from luxusb.config import Config
            from pathlib import Path
            import json
            from datetime import datetime, timedelta
            
            config = Config()
            update_frequency_days = config.get(
                ConfigKeys.Metadata.UPDATE_FREQUENCY_DAYS, default=7
            )
            
            if update_frequency_days == 0:
                # Always update, no indicator needed
                return False
            
            cache_dir = Path.home() / PathPattern.CACHE_DIR
            update_marker = cache_dir / PathPattern.UPDATE_MARKER_FILE
            
            if update_marker.exists():
                with open(update_marker, 'r') as f:
                    data = json.load(f)
                    last_update = datetime.fromisoformat(data['timestamp'])
                    days_since = (datetime.now() - last_update).days
                    
                    if days_since >= update_frequency_days:
                        # Updates available
                        self._show_update_indicator(True)
                        logger.info(
                            f"Updates available "
                            f"({days_since} days since last update)"
                        )
            else:
                # Never updated
                self._show_update_indicator(True)
                logger.info("First run - updates recommended")
                
        except Exception as e:
            logger.debug(f"Update status check failed: {e}")
        
        return False  # Don't repeat
    
    def _show_update_indicator(self, show: bool) -> None:
        """Show or hide update available indicator"""
        if show:
            # Add suggested-action style class for visual indicator
            self.menu_button.add_css_class("suggested-action")
            self.menu_button.set_tooltip_text("Menu (Updates Available!)")
            
            # Show toast notification
            toast = Adw.Toast.new(
                "🔔 Distribution updates available - Check Menu"
            )
            toast.set_timeout(6)
            toast.set_priority(Adw.ToastPriority.HIGH)
            self.toast_overlay.add_toast(toast)
        else:
            # Remove indicator
            self.menu_button.remove_css_class("suggested-action")
            self.menu_button.set_tooltip_text("Menu")
    

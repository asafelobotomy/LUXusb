"""
Progress and installation page
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import logging
import threading
from pathlib import Path

from luxusb.constants import StatusIcon
from luxusb.utils.partitioner import USBPartitioner
from luxusb.utils.downloader import ISODownloader, DownloadProgress
from luxusb.utils.grub_installer import GRUBInstaller
from luxusb.core.workflow import LUXusbWorkflow, WorkflowProgress
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ProgressPage(Adw.NavigationPage):
    """Page showing installation progress"""
    
    def __init__(self, main_window: Any) -> None:
        super().__init__()
        self.main_window = main_window
        self.set_title("Installing")
        self.set_can_pop(False)  # Prevent going back during installation
        
        # Create main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(40)
        content.set_margin_end(40)
        content.set_valign(Gtk.Align.CENTER)
        
        # Status label
        self.status_label = Gtk.Label(label="Preparing installation...")
        self.status_label.add_css_class("title-2")
        content.append(self.status_label)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        content.append(self.progress_bar)
        
        # Details label
        self.details_label = Gtk.Label(label="")
        self.details_label.add_css_class("dim-label")
        self.details_label.set_wrap(True)
        self.details_label.set_justify(Gtk.Justification.CENTER)
        content.append(self.details_label)
        
        # Pause/Resume button (hidden initially, shown during download)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.pause_resume_btn = Gtk.Button(label="⏸️ Pause")
        self.pause_resume_btn.connect("clicked", self.on_pause_resume_clicked)
        self.pause_resume_btn.add_css_class("pill")
        self.pause_resume_btn.set_visible(False)
        button_box.append(self.pause_resume_btn)
        
        content.append(button_box)
        
        # Log view
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_buffer = self.log_view.get_buffer()
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.log_view)
        scrolled.set_min_content_height(200)
        content.append(scrolled)
        
        # Done button (hidden initially)
        self.done_btn = Gtk.Button(label="Done")
        self.done_btn.connect("clicked", self.on_done_clicked)
        self.done_btn.add_css_class("pill")
        self.done_btn.add_css_class("suggested-action")
        self.done_btn.set_visible(False)
        content.append(self.done_btn)
        
        # Store workflow reference
        self.workflow: Optional[LUXusbWorkflow] = None
        self.is_downloading = False
        
        self.set_child(content)
    
    def start_installation(self) -> None:
        """Start the installation process"""
        logger.info("Starting installation process...")
        
        # Run installation in background thread
        thread = threading.Thread(target=self._install_worker, daemon=True)
        thread.start()
    
    def _install_worker(self) -> None:
        """Worker thread for installation"""
        app = self.main_window.get_application()
        device = app.selected_device
        selections = app.selections
        custom_isos = app.custom_isos
        enable_secure_boot = app.enable_secure_boot
        
        try:
            # Create workflow instance with Phase 3 features
            append_mode = app.append_mode if hasattr(app, 'append_mode') else False
            self.workflow = LUXusbWorkflow(
                device=device,
                selections=selections if selections else None,
                custom_isos=custom_isos if custom_isos else None,
                progress_callback=self.on_workflow_progress,
                enable_secure_boot=enable_secure_boot,
                append_mode=append_mode
            )
            
            # Set callback for outdated ISO detection
            self.workflow.outdated_iso_callback = self.on_outdated_isos_detected
            
            # Show pause/resume button during download stage
            GLib.idle_add(self._show_pause_button)
            
            # Execute workflow
            success = self.workflow.execute()
            
            # Hide pause/resume button after completion
            GLib.idle_add(self._hide_pause_button)
            
            if success:
                self.update_status("✓ Installation Complete!", 1.0)
                self.log("USB device is ready to boot!")
                self.log(f"You can now boot from {device.display_name}")
                GLib.idle_add(self.show_done_button)
            else:
                self.update_status(f"{StatusIcon.FAILURE} Installation Failed", 0.0)
                self.log("Installation failed. Check the logs above for details.")
                GLib.idle_add(self.show_done_button)
                
        except Exception as e:
            logger.exception("Unexpected installation error: %s", e)
            self.update_status(f"{StatusIcon.FAILURE} Installation Failed", 0.0)
            self.log(f"ERROR: {str(e)}")
            GLib.idle_add(self._hide_pause_button)
            GLib.idle_add(self.show_done_button)
    
    def on_workflow_progress(self, progress: WorkflowProgress):
        """Handle workflow progress updates"""
        # Update progress bar and status
        self.update_status(progress.details, progress.percentage / 100.0)
        
        # Log stage changes
        if progress.current_stage:
            # Only log new stages, not every progress update
            if not hasattr(self, '_last_stage') or self._last_stage != progress.current_stage:
                self.log(f"=== {progress.current_stage} ===")
                self._last_stage = progress.current_stage
        
        # Show/hide pause button based on stage
        if progress.current_stage and "download" in progress.current_stage.lower():
            GLib.idle_add(self._show_pause_button)
        elif progress.current_stage and self.is_downloading:
            GLib.idle_add(self._hide_pause_button)
    
    def _show_pause_button(self):
        """Show pause/resume button"""
        self.is_downloading = True
        self.pause_resume_btn.set_visible(True)
        return False
    
    def _hide_pause_button(self):
        """Hide pause/resume button"""
        self.is_downloading = False
        self.pause_resume_btn.set_visible(False)
        return False
    
    def update_status(self, text: str, progress: float):
        """Update status label and progress bar"""
        GLib.idle_add(self._update_status_ui, text, progress)
    
    def _update_status_ui(self, text: str, progress: float):
        """Update status UI (GTK main thread)"""
        self.status_label.set_text(text)
        self.progress_bar.set_fraction(progress)
        return False
    
    def log(self, message: str):
        """Add message to log"""
        GLib.idle_add(self._append_log, message)
    
    def _append_log(self, message: str):
        """Append to log buffer (GTK main thread)"""
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, message + "\n", -1)
        
        # Auto-scroll to bottom
        mark = self.log_buffer.create_mark(None, end_iter, False)
        self.log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        self.log_buffer.delete_mark(mark)
        return False
    
    def _update_status_ui(self, text: str, progress: float):
        """UI update for status (must run in main thread)"""
        self.status_label.set_text(text)
        self.progress_bar.set_fraction(progress)
        return False
    
    def log(self, message: str):
        """Add log message"""
        GLib.idle_add(self._log_ui, message)
    
    def _log_ui(self, message: str):
        """UI update for log (must run in main thread)"""
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, message + "\n")
        
        # Scroll to bottom
        mark = self.log_buffer.get_insert()
        self.log_view.scroll_to_mark(mark, 0.0, False, 0.0, 0.0)
        
        return False
    
    def show_done_button(self) -> bool:
        """Show done button"""
        self.done_btn.set_visible(True)
        return False
    
    def on_done_clicked(self, _button: Gtk.Button) -> None:
        """Handle done button click"""
        # Close application or restart
        self.main_window.close()
    
    def on_pause_resume_clicked(self, button):
        """Handle pause/resume button click"""
        if not self.workflow:
            return
        
        if self.workflow.is_download_paused():
            # Resume download
            self.workflow.resume_download()
            self.pause_resume_btn.set_label("⏸️ Pause")
            self.log("Download resumed")
        else:
            # Pause download
            self.workflow.pause_download()
            self.pause_resume_btn.set_label("▶️ Resume")
            self.log("Download paused")
    
    def on_outdated_isos_detected(self, outdated_isos: list) -> None:
        """
        Handle detection of outdated ISOs on USB
        Called from workflow when mounting existing USB in append mode
        """
        def show_dialog():
            from luxusb.gui.stale_iso_dialog import StaleISODialog, ISOUpdateWorkflow
            
            dialog = StaleISODialog(self.main_window, outdated_isos)
            dialog.connect("response", lambda d, response: self._handle_stale_iso_response(d, response, outdated_isos))
            dialog.present()
        
        # Show dialog on main thread
        GLib.idle_add(show_dialog)
    
    def _handle_stale_iso_response(self, dialog: Adw.MessageDialog, response: str, outdated_isos: list) -> None:
        """Handle user response to stale ISO notification"""
        dialog.close()
        
        if response == "update":
            # User wants to update ISOs
            self.log("Starting ISO update process...")
            
            from luxusb.gui.stale_iso_dialog import ISOUpdateWorkflow
            
            def on_complete(success_count: int, error_count: int):
                if error_count == 0:
                    self.log(f"✓ {success_count} ISO(s) updated successfully")
                    # Auto-refresh GRUB config
                    self.log("Auto-refreshing GRUB configuration...")
                    if hasattr(self.workflow, '_auto_refresh_grub_if_needed'):
                        self.workflow._auto_refresh_grub_if_needed()
                else:
                    self.log(f"⚠️ {success_count} updated, {error_count} failed")
            
            # Get data mount from workflow
            data_mount = str(self.workflow.data_mount) if self.workflow and self.workflow.data_mount else None
            
            if data_mount:
                workflow = ISOUpdateWorkflow(
                    self.main_window,
                    outdated_isos,
                    data_mount,
                    on_complete
                )
                workflow.start()
            else:
                self.log("ERROR: Could not determine data mount point")
        
        elif response == "keep":
            # User wants to keep current ISOs
            self.log("Keeping current ISO versions")


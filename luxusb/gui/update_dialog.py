"""
Update notification and progress dialogs
"""

import logging
from typing import Callable, List, Optional
from threading import Thread

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

logger = logging.getLogger(__name__)


class UpdateNotificationDialog(Adw.MessageDialog):
    """Dialog to notify user about available updates"""
    
    def __init__(self, parent: Gtk.Window, stale_distros: List[str]) -> None:
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        
        # Dialog content
        self.set_heading("🔄 New Distribution Updates Available")
        
        # Build message
        if len(stale_distros) == 1:
            message = f"Updates found for:\n• {stale_distros[0]}"
        elif len(stale_distros) <= 5:
            distro_list = "\n• ".join(stale_distros)
            message = f"Updates found for:\n• {distro_list}"
        else:
            distro_list = "\n• ".join(stale_distros[:5])
            remaining = len(stale_distros) - 5
            message = f"Updates found for:\n• {distro_list}\n...and {remaining} more"
        
        message += f"\n\n📦 {len(stale_distros)} distribution(s) with updates"
        self.set_body(message)
        
        # Add responses
        self.add_response("skip", "Skip This Version")
        self.add_response("later", "Update Later")
        self.add_response("update", "Update Now")
        
        # Style update button as suggested
        self.set_response_appearance("update", Adw.ResponseAppearance.SUGGESTED)
        
        # Set default response
        self.set_default_response("update")
        self.set_close_response("later")


class UpdateProgressDialog(Gtk.Window):
    """Dialog showing update progress"""
    
    def __init__(self, parent: Gtk.Window, distros: List[str]) -> None:
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title("Updating Distributions")
        self.set_default_size(500, 300)
        self.set_resizable(False)
        
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<big><b>Updating Distribution Metadata</b></big>")
        box.append(title)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("Starting...")
        box.append(self.progress_bar)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_wrap(True)
        self.status_label.set_max_width_chars(50)
        self.status_label.set_xalign(0.0)
        box.append(self.status_label)
        
        # Scrolled window for log messages
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(150)
        
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_view.set_monospace(True)
        self.log_buffer = self.log_view.get_buffer()
        scrolled.set_child(self.log_view)
        box.append(scrolled)
        
        # Close button (initially disabled)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        
        self.close_button = Gtk.Button(label="Close")
        self.close_button.set_sensitive(False)
        self.close_button.connect("clicked", lambda _: self.close())
        button_box.append(self.close_button)
        
        box.append(button_box)
        
        self.set_child(box)
        
        # Store distro list
        self.distros = distros
        self.total_distros = len(distros)
        self.current_index = 0
    
    def update_progress(self, fraction: float, text: str) -> None:
        """Update progress bar (call from main thread via GLib.idle_add)"""
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(text)
    
    def update_status(self, status: str) -> None:
        """Update status label"""
        self.status_label.set_text(status)
    
    def append_log(self, message: str, style: str = "normal") -> None:
        """Append message to log view"""
        end_iter = self.log_buffer.get_end_iter()
        
        # Style markers
        if style == "success":
            message = f"✅ {message}"
        elif style == "error":
            message = f"❌ {message}"
        elif style == "info":
            message = f"ℹ️  {message}"
        elif style == "progress":
            message = f"🔄 {message}"
        
        self.log_buffer.insert(end_iter, f"{message}\n")
        
        # Auto-scroll to bottom
        end_mark = self.log_buffer.create_mark(None, end_iter, False)
        self.log_view.scroll_to_mark(end_mark, 0.0, True, 0.0, 1.0)
    
    def mark_complete(self, success_count: int, error_count: int) -> None:
        """Mark update process as complete"""
        if error_count == 0:
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text(f"✅ Complete ({success_count} updated)")
            self.update_status("All distributions updated successfully!")
        else:
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text(f"⚠️ Complete with errors")
            self.update_status(f"{success_count} updated, {error_count} failed")
        
        # Enable close button
        self.close_button.set_sensitive(True)


class UpdateWorkflow:
    """Handle background update workflow"""
    
    def __init__(
        self,
        parent: Gtk.Window,
        distros: List[str],
        on_complete: Optional[Callable[[int, int], None]] = None
    ) -> None:
        self.parent = parent
        self.distros = distros
        self.on_complete = on_complete
        
        # Progress dialog
        self.dialog: Optional[UpdateProgressDialog] = None
        
        # Results
        self.success_count = 0
        self.error_count = 0
    
    def start(self) -> None:
        """Start update workflow (shows dialog and runs in background)"""
        # Create and show progress dialog
        self.dialog = UpdateProgressDialog(self.parent, self.distros)
        self.dialog.present()
        
        # Start background thread
        thread = Thread(target=self._run_updates, daemon=True)
        thread.start()
    
    def _run_updates(self) -> None:
        """Run updates in background thread"""
        from luxusb.utils.distro_updater import DistroUpdater
        
        updater = DistroUpdater()
        total = len(self.distros)
        
        for index, distro_id in enumerate(self.distros, 1):
            # Update progress
            fraction = (index - 1) / total
            GLib.idle_add(
                self.dialog.update_progress,
                fraction,
                f"{index}/{total} distributions"
            )
            GLib.idle_add(
                self.dialog.update_status,
                f"Updating {distro_id}..."
            )
            GLib.idle_add(
                self.dialog.append_log,
                f"Updating {distro_id}...",
                "progress"
            )
            
            # Run update
            try:
                success, message = updater.update_distro(distro_id)
                
                if success:
                    self.success_count += 1
                    GLib.idle_add(
                        self.dialog.append_log,
                        f"{distro_id}: {message}",
                        "success"
                    )
                else:
                    self.error_count += 1
                    GLib.idle_add(
                        self.dialog.append_log,
                        f"{distro_id}: {message}",
                        "error"
                    )
            except Exception as e:
                self.error_count += 1
                logger.exception(f"Error updating {distro_id}")
                GLib.idle_add(
                    self.dialog.append_log,
                    f"{distro_id}: {str(e)}",
                    "error"
                )
        
        # Mark complete
        GLib.idle_add(
            self.dialog.mark_complete,
            self.success_count,
            self.error_count
        )
        
        # Call completion callback
        if self.on_complete:
            GLib.idle_add(
                self.on_complete,
                self.success_count,
                self.error_count
            )

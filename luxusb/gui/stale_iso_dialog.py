"""
Stale ISO notification dialog
"""

import logging
from typing import Callable, List, Optional
from threading import Thread

from luxusb.gui import Gtk, Adw, GLib

from luxusb.utils.grub_refresher import OutdatedISO

logger = logging.getLogger(__name__)


class StaleISODialog(Adw.MessageDialog):
    """Dialog to notify user about outdated ISOs on USB"""
    
    def __init__(self, parent: Gtk.Window, outdated_isos: List[OutdatedISO]) -> None:
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        
        # Dialog content
        self.set_heading("ℹ️ Outdated ISOs Detected")
        
        # Build message
        message = "The following ISOs have newer versions available:\n\n"
        
        for iso_info in outdated_isos[:5]:  # Show first 5
            message += f"• {iso_info.upgrade_description}\n"
        
        if len(outdated_isos) > 5:
            remaining = len(outdated_isos) - 5
            message += f"\n...and {remaining} more"
        
        message += f"\n\n📦 {len(outdated_isos)} update(s) available"
        
        self.set_body(message)
        
        # Add responses
        self.add_response("keep", "Keep Current")
        self.add_response("update", "Download Updates")
        
        # Style update button as suggested
        self.set_response_appearance("update", Adw.ResponseAppearance.SUGGESTED)
        
        # Set default response
        self.set_default_response("update")
        self.set_close_response("keep")
        
        # Store outdated ISOs
        self.outdated_isos = outdated_isos


class ISOUpdateProgressDialog(Gtk.Window):
    """Dialog showing ISO update progress"""
    
    def __init__(self, parent: Gtk.Window, outdated_isos: List[OutdatedISO]) -> None:
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title("Updating ISOs")
        self.set_default_size(550, 350)
        self.set_resizable(False)
        
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<big><b>Updating Distribution ISOs</b></big>")
        box.append(title)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("Starting...")
        box.append(self.progress_bar)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_wrap(True)
        self.status_label.set_max_width_chars(60)
        self.status_label.set_xalign(0.0)
        box.append(self.status_label)
        
        # Scrolled window for log messages
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(180)
        
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
        
        # Store ISO list
        self.outdated_isos = outdated_isos
        self.total_isos = len(outdated_isos)
        self.success_count = 0
        self.error_count = 0
    
    def update_progress(self, fraction: float, text: str) -> None:
        """Update progress bar"""
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
    
    def mark_complete(self) -> None:
        """Mark update process as complete"""
        if self.error_count == 0:
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text(f"✅ Complete ({self.success_count} updated)")
            self.update_status("All ISOs updated successfully!")
        else:
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text(f"⚠️ Complete with errors")
            self.update_status(f"{self.success_count} updated, {self.error_count} failed")
        
        # Enable close button
        self.close_button.set_sensitive(True)


class ISOUpdateWorkflow:
    """Handle ISO update workflow"""
    
    def __init__(
        self,
        parent: Gtk.Window,
        outdated_isos: List[OutdatedISO],
        data_mount: str,
        on_complete: Optional[Callable[[int, int], None]] = None
    ) -> None:
        self.parent = parent
        self.outdated_isos = outdated_isos
        self.data_mount = data_mount
        self.on_complete = on_complete
        self.dialog: Optional[ISOUpdateProgressDialog] = None
    
    def start(self) -> None:
        """Start ISO update workflow"""
        # Create and show progress dialog
        self.dialog = ISOUpdateProgressDialog(self.parent, self.outdated_isos)
        self.dialog.present()
        
        # Start background thread
        thread = Thread(target=self._run_updates, daemon=True)
        thread.start()
    
    def _run_updates(self) -> None:
        """Run ISO updates in background thread"""
        from luxusb.utils.downloader import ISODownloader
        from luxusb.config import Config
        import shutil
        
        config = Config()
        total = len(self.outdated_isos)
        
        for index, iso_info in enumerate(self.outdated_isos, 1):
            distro = iso_info.distro
            available = iso_info.available_version
            current_path = iso_info.current_path
            
            # Update progress
            fraction = (index - 1) / total
            GLib.idle_add(
                self.dialog.update_progress,
                fraction,
                f"{index}/{total} ISOs"
            )
            GLib.idle_add(
                self.dialog.update_status,
                f"Downloading {distro.name} {available.version}..."
            )
            GLib.idle_add(
                self.dialog.append_log,
                f"Updating {distro.name}...",
                "progress"
            )
            
            try:
                # Find matching release
                matching_release = None
                for release in distro.releases:
                    if release.iso_url:
                        filename = release.iso_url.split('/')[-1]
                        parsed = self.dialog.outdated_isos[0].available_version.__class__.__name__
                        # Simplified: just check if version is in filename
                        if available.version in filename:
                            matching_release = release
                            break
                
                if not matching_release:
                    raise Exception(f"Could not find release for version {available.version}")
                
                # Download new ISO
                downloader = ISODownloader(config)
                temp_path = current_path.parent / f"{available.filename}.tmp"
                
                GLib.idle_add(
                    self.dialog.append_log,
                    f"Downloading from: {matching_release.iso_url[:50]}...",
                    "info"
                )
                
                # Simple download (no progress callback for now)
                success = downloader.download(
                    matching_release.iso_url,
                    temp_path,
                    matching_release.sha256
                )
                
                if not success:
                    raise Exception("Download failed")
                
                # Backup old ISO
                backup_path = current_path.parent / f"{current_path.name}.backup"
                shutil.move(str(current_path), str(backup_path))
                
                # Move new ISO to place
                final_path = current_path.parent / available.filename
                shutil.move(str(temp_path), str(final_path))
                
                # Success!
                self.dialog.success_count += 1
                GLib.idle_add(
                    self.dialog.append_log,
                    f"{distro.name}: Updated to {available.version}",
                    "success"
                )
                
                # Remove backup
                backup_path.unlink()
                
            except Exception as e:
                self.dialog.error_count += 1
                logger.exception(f"Error updating {distro.name}")
                GLib.idle_add(
                    self.dialog.append_log,
                    f"{distro.name}: {str(e)}",
                    "error"
                )
        
        # Mark complete
        GLib.idle_add(self.dialog.mark_complete)
        
        # Call completion callback
        if self.on_complete:
            GLib.idle_add(
                self.on_complete,
                self.dialog.success_count,
                self.dialog.error_count
            )

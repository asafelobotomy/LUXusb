"""
Main orchestrator for USB creation workflow
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

from luxusb.utils.usb_detector import USBDevice
from luxusb.utils.distro_manager import Distro, DistroSelection, calculate_required_space
from luxusb.utils.partitioner import USBPartitioner
from luxusb.utils.downloader import ISODownloader, DownloadProgress
from luxusb.utils.grub_installer import GRUBInstaller
from luxusb.utils.custom_iso import CustomISO
from luxusb.utils.secure_boot import SecureBootDetector, BootloaderSigner
from luxusb.config import Config
from luxusb.constants import WorkflowStage

logger = logging.getLogger(__name__)


@dataclass
class WorkflowProgress:
    """Overall workflow progress"""
    stage: str
    stage_progress: float
    overall_progress: float
    message: str
    current_iso: Optional[int] = None  # Which ISO is being processed (1-based)
    total_isos: Optional[int] = None  # Total number of ISOs
    
    @property
    def percentage(self) -> float:
        """Get overall progress as percentage (0-100)"""
        return self.overall_progress * 100
    
    @property
    def details(self) -> str:
        """Get detailed progress string"""
        if self.current_iso and self.total_isos:
            return f"{self.message} ({self.current_iso}/{self.total_isos})"
        return self.message
    
    @property
    def current_stage(self) -> str:
        """Get current stage name"""
        return self.stage


class LUXusbWorkflow:
    """
    Orchestrates the complete workflow for creating a bootable USB
    """
    
    def __init__(
        self,
        device: USBDevice,
        selections: Optional[list[DistroSelection]] = None,
        custom_isos: Optional[list[CustomISO]] = None,
        progress_callback: Optional[Callable[[WorkflowProgress], None]] = None,
        enable_secure_boot: bool = False,
        append_mode: bool = False
    ):
        """
        Initialize workflow
        
        Args:
            device: Target USB device
            selections: List of distribution selections to install
            custom_isos: List of custom ISO files to include
            progress_callback: Optional callback for progress updates
            enable_secure_boot: Enable Secure Boot signing
            append_mode: If True, append ISOs to existing USB instead of erasing
        """
        self.device = device
        self.progress_callback = progress_callback
        self.custom_isos = custom_isos or []
        self.selections = selections or []
        self.enable_secure_boot = enable_secure_boot
        self.append_mode = append_mode
        
        # Require at least one ISO source
        if not self.selections and not self.custom_isos:
            raise ValueError("Must provide either 'selections' or 'custom_isos'")
        
        self.mount_base = Path("/tmp/luxusb-mount")
        self.efi_mount: Optional[Path] = None
        self.data_mount: Optional[Path] = None
        self.iso_paths: list[Path] = []  # Multiple ISOs
        
        # Downloader instance for pause/resume control
        self.downloader = ISODownloader()
        self.config = Config()
        
        # Secure Boot components
        self.secure_boot_detector = SecureBootDetector()
        self.bootloader_signer = BootloaderSigner()
        
    @property
    def is_multi_iso(self) -> bool:
        """Check if this is a multi-ISO installation"""
        return len(self.selections) + len(self.custom_isos) > 1
    
    @property
    def total_isos(self) -> int:
        """Get total number of ISOs (distros + custom)"""
        return len(self.selections) + len(self.custom_isos)
        
    def pause_download(self) -> None:
        """Pause the current download"""
        self.downloader.pause()
        logger.info("Download paused by user")
    
    def resume_download(self) -> None:
        """Resume the paused download"""
        self.downloader.resume()
        logger.info("Download resumed by user")
    
    def is_download_paused(self) -> bool:
        """Check if download is paused"""
        return self.downloader.is_paused()
    
    def execute(self) -> bool:
        """
        Execute complete workflow
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.append_mode:
                logger.info("Running in APPEND mode - preserving existing data")
                
                # Stage 1: Skip partitioning (0-20%)
                self._update_progress(WorkflowStage.MOUNT.value, 0.0, 0.0, "Mounting existing partitions...")
                
                # Stage 2: Mount existing partitions (0-25%)
                if not self._mount_existing_partitions():
                    return False
                
                # Stage 3: Skip GRUB installation (already installed)
                self._update_progress(WorkflowStage.GRUB_INSTALL.value, 1.0, 0.35, "Using existing bootloader")
                
                # Stage 4: Download new ISOs (35-85%)
                if not self._download_iso():
                    return False
                
                # Stage 5: Update GRUB config with new ISOs (85-95%)
                if not self._configure_bootloader():
                    return False
                
                # Stage 6: Cleanup (95-100%)
                self._cleanup()
                
                self._update_progress(WorkflowStage.COMPLETE.value, 1.0, 1.0, "ISOs added successfully!")
                return True
            else:
                logger.info("Running in ERASE mode - creating fresh USB")
                
                # Stage 1: Partition (0-20%)
                if not self._partition_usb():
                    return False
                
                # Stage 2: Mount (20-25%)
                if not self._mount_partitions():
                    return False
                
                # Stage 3: Install GRUB (25-35%)
                if not self._install_bootloader():
                    return False
                
                # Stage 4: Download ISO (35-85%)
                if not self._download_iso():
                    return False
                
                # Stage 5: Configure (85-95%)
                if not self._configure_bootloader():
                    return False
                
                # Stage 6: Cleanup (95-100%)
                self._cleanup()
                
                self._update_progress(WorkflowStage.COMPLETE.value, 1.0, 1.0, "Installation complete!")
                return True
            
        except (subprocess.CalledProcessError, OSError, IOError, RuntimeError) as e:
            logger.exception("Workflow failed: %s", e)
            self._cleanup()
            return False
        except Exception as e:
            # Catch any unexpected errors to ensure cleanup runs
            logger.exception("Unexpected workflow error: %s", e)
            self._cleanup()
            return False
    
    def _partition_usb(self) -> bool:
        """Stage 1: Partition USB device"""
        self._update_progress(WorkflowStage.PARTITION.value, 0.0, 0.0, "Partitioning USB device...")
        
        partitioner = USBPartitioner(self.device)
        
        if not partitioner.create_partitions():
            logger.error("Failed to create partitions")
            return False
        
        self._update_progress(WorkflowStage.PARTITION.value, 1.0, 0.2, "Partitions created")
        return True
    
    def _mount_partitions(self) -> bool:
        """Stage 2: Mount partitions"""
        self._update_progress(WorkflowStage.MOUNT.value, 0.0, 0.2, "Mounting partitions...")
        
        partitioner = USBPartitioner(self.device)
        partitioner.bios_partition = f"{self.device.device}1"
        partitioner.efi_partition = f"{self.device.device}2"
        partitioner.data_partition = f"{self.device.device}3"
        
        self.efi_mount, self.data_mount = partitioner.mount_partitions(self.mount_base)
        
        if not self.efi_mount or not self.data_mount:
            logger.error("Failed to mount partitions")
            return False
        
        self._update_progress(WorkflowStage.MOUNT.value, 1.0, 0.25, "Partitions mounted")
        return True
    
    def _mount_existing_partitions(self) -> bool:
        """Mount existing partitions without reformatting (for append mode)"""
        self._update_progress(WorkflowStage.MOUNT.value, 0.0, 0.0, "Mounting existing partitions...")
        
        # Use existing partition paths (new 3-partition layout)
        bios_partition = f"{self.device.device}1"
        efi_partition = f"{self.device.device}2"
        data_partition = f"{self.device.device}3"
        
        partitioner = USBPartitioner(self.device)
        partitioner.bios_partition = bios_partition
        partitioner.efi_partition = efi_partition
        partitioner.data_partition = data_partition
        
        # Mount without formatting
        self.efi_mount, self.data_mount = partitioner.mount_partitions(self.mount_base)
        
        if not self.efi_mount or not self.data_mount:
            logger.error("Failed to mount existing partitions")
            return False
        
        logger.info("Mounted existing partitions for append mode")
        
        # Auto-detect and refresh GRUB config if ISOs have changed
        self._auto_refresh_grub_if_needed()
        
        # Check for outdated ISOs and offer to update
        self._check_outdated_isos()
        
        self._update_progress(WorkflowStage.MOUNT.value, 1.0, 0.25, "Existing partitions mounted")
        return True
    
    def _install_bootloader(self) -> bool:
        """Stage 3: Install GRUB bootloader"""
        self._update_progress(WorkflowStage.GRUB_INSTALL.value, 0.0, 0.25, "Installing bootloader...")
        
        if not self.efi_mount:
            logger.error("EFI mount point not available")
            return False
        
        # Check Secure Boot status
        secure_boot_status = self.secure_boot_detector.detect_secure_boot()
        if secure_boot_status.is_active:
            logger.info("Secure Boot is active")
            if self.enable_secure_boot:
                # Install shim for Secure Boot
                self._update_progress(WorkflowStage.GRUB_INSTALL.value, 0.2, 0.27, "Installing Secure Boot shim...")
                if not self.bootloader_signer.install_shim(self.efi_mount):
                    logger.warning("Failed to install shim, continuing without Secure Boot support")
        
        installer = GRUBInstaller(self.device.device, self.efi_mount)
        
        if not installer.install():
            logger.error("Failed to install GRUB")
            return False
        
        # Sign bootloader if Secure Boot is enabled
        if self.enable_secure_boot and secure_boot_status.requires_signing:
            self._update_progress(WorkflowStage.GRUB_INSTALL.value, 0.8, 0.33, "Signing bootloader...")
            grub_efi = self.efi_mount / "EFI" / "BOOT" / "grubx64.efi"
            if grub_efi.exists():
                if not self.bootloader_signer.sign_bootloader(grub_efi):
                    logger.warning("Failed to sign bootloader, USB may not boot with Secure Boot")
        
        self._update_progress(WorkflowStage.GRUB_INSTALL.value, 1.0, 0.35, "Bootloader installed")
        return True
    
    def _download_iso(self) -> bool:
        """Stage 4: Download ISO(s) and copy custom ISOs"""
        if not self.data_mount:
            logger.error("Data mount point not available")
            return False
        
        total_isos = len(self.selections) + len(self.custom_isos)
        iso_dir = self.data_mount / "isos"
        iso_dir.mkdir(exist_ok=True)
        
        # Get config options for download
        auto_select = self.config.get('download.auto_select_mirror', default=True)
        allow_resume = self.config.get('download.allow_resume', default=True)
        abort_on_failure = self.config.get('multi_iso.abort_on_failure', default=False)
        
        current_idx = 1
        
        # Download distribution ISOs
        for selection in self.selections:
            distro = selection.distro
            release = selection.release
            
            # Check GPG strict mode before downloading
            gpg_strict = self.config.get('download.gpg_strict_mode', default=False)
            if gpg_strict and hasattr(release, 'gpg_verified') and not release.gpg_verified:
                logger.error(f"GPG strict mode enabled: Cannot download {distro.name} (not GPG verified)")
                if abort_on_failure:
                    return False
                logger.warning(f"Skipping {distro.name} due to missing GPG verification")
                current_idx += 1
                continue
            
            # Log GPG verification warning if not verified
            if not gpg_strict and hasattr(release, 'gpg_verified') and not release.gpg_verified:
                logger.warning(f"⚠️  {distro.name}: GPG verification unavailable - proceeding with SHA256 only")
            
            # Create distro-specific subdirectory
            distro_dir = iso_dir / distro.id
            distro_dir.mkdir(exist_ok=True)
            
            iso_path = distro_dir / selection.iso_filename
            
            # Skip if ISO already exists and is valid
            if iso_path.exists():
                logger.info(f"ISO already exists: {iso_path}")
                self.iso_paths.append(iso_path)
                current_idx += 1
                continue
            
            self._update_progress(
                WorkflowStage.DOWNLOAD.value, 0.0, 0.35,
                f"Downloading {distro.name} {release.version}",
                current_iso=current_idx,
                total_isos=total_isos
            )
            
            def download_progress(progress: DownloadProgress) -> None:
                # Map download progress to 35-85% of overall
                # Divide range equally among ISOs
                iso_range = 0.5 / total_isos
                iso_start = 0.35 + (current_idx - 1) * iso_range
                overall = iso_start + (progress.percentage / 100 * iso_range)
                
                # Include pause/resume status in message
                if progress.is_paused:
                    status_msg = f"⏸️ Paused: {distro.name}"
                elif progress.is_resumable:
                    status_msg = f"{distro.name}: {progress.percentage:.1f}% @ {progress.speed_mb_per_sec:.1f} MB/s (resumable)"
                else:
                    status_msg = f"{distro.name}: {progress.percentage:.1f}% @ {progress.speed_mb_per_sec:.1f} MB/s"
                
                self._update_progress(
                    WorkflowStage.DOWNLOAD.value,
                    progress.percentage / 100,
                    overall,
                    status_msg,
                    current_iso=current_idx,
                    total_isos=total_isos
                )
            
            # Use mirror failover with resume and auto-select
            if release.mirrors and len(release.mirrors) > 0:
                success = self.downloader.download_with_mirrors(
                    primary_url=release.iso_url,
                    mirrors=release.mirrors,
                    destination=iso_path,
                    expected_sha256=release.sha256,
                    progress_callback=download_progress,
                    auto_select_best=auto_select,
                    allow_resume=allow_resume
                )
            else:
                # Single URL - use resume-capable download
                success = self.downloader.download_with_resume(
                    url=release.iso_url,
                    destination=iso_path,
                    expected_sha256=release.sha256,
                    progress_callback=download_progress,
                    allow_resume=allow_resume
                )
            
            if not success:
                logger.error(f"Failed to download ISO: {distro.name}")
                if abort_on_failure:
                    return False
                # Continue with other ISOs
                logger.warning(f"Skipping {distro.name}, continuing with other ISOs")
                current_idx += 1
                continue
            
            self.iso_paths.append(iso_path)
            logger.info(f"Downloaded: {iso_path}")
            current_idx += 1
        
        # Copy custom ISOs
        for custom_iso in self.custom_isos:
            self._update_progress(
                WorkflowStage.DOWNLOAD.value, 0.0, 0.35,
                f"Copying custom ISO: {custom_iso.display_name}",
                current_iso=current_idx,
                total_isos=total_isos
            )
            
            # Create custom subdirectory
            custom_dir = iso_dir / "custom"
            custom_dir.mkdir(exist_ok=True)
            
            dest_path = custom_dir / custom_iso.filename
            
            # Copy ISO file
            try:
                import shutil
                shutil.copy2(custom_iso.path, dest_path)
                self.iso_paths.append(dest_path)
                logger.info(f"Copied custom ISO: {dest_path}")
            except (OSError, IOError) as e:
                logger.error(f"Failed to copy custom ISO: {e}")
                if abort_on_failure:
                    return False
            
            current_idx += 1
        
        if len(self.iso_paths) == 0:
            logger.error("No ISOs available")
            return False
        
        self._update_progress(WorkflowStage.DOWNLOAD.value, 1.0, 0.85, 
                            f"Prepared {len(self.iso_paths)}/{total_isos} ISOs")
        return True
    
    def _configure_bootloader(self) -> bool:
        """Stage 5: Configure GRUB with ISO(s)"""
        self._update_progress(WorkflowStage.CONFIGURE.value, 0.0, 0.85, "Configuring bootloader...")
        
        if not self.efi_mount:
            logger.error("EFI mount point not available")
            return False
        
        if len(self.iso_paths) == 0:
            logger.error("No ISO paths available")
            return False
        
        installer = GRUBInstaller(self.device.device, self.efi_mount)
        
        # Extract distros from selections
        distros = [sel.distro for sel in self.selections]
        
        # Set GRUB timeout from config
        timeout = self.config.get('multi_iso.default_boot_timeout', default=10)
        
        if not installer.update_config_with_isos(
            self.iso_paths[:len(distros)],  # Only distro ISOs
            distros,
            custom_isos=self.custom_isos if self.custom_isos else None,
            timeout=timeout
        ):
            logger.error("Failed to configure bootloader")
            return False
        
        # Write LUXusb state file
        self._update_progress(WorkflowStage.CONFIGURE.value, 0.8, 0.92, "Writing USB configuration...")
        self._write_state_file()
        
        self._update_progress(WorkflowStage.CONFIGURE.value, 1.0, 0.95, "Bootloader configured")
        return True
    
    def _write_state_file(self) -> None:
        """Write LUXusb state configuration to USB"""
        if not self.data_mount:
            logger.warning("Cannot write state file - no data mount")
            return
        
        try:
            from luxusb.utils.usb_state import USBStateManager
            from luxusb import __version__
            
            state_manager = USBStateManager()
            
            efi_partition = f"{self.device.device}1"
            data_partition = f"{self.device.device}2"
            
            success = state_manager.write_state(
                mount_point=self.data_mount,
                device_path=self.device.device,
                efi_partition=efi_partition,
                data_partition=data_partition,
                luxusb_version=__version__,
                secure_boot_enabled=self.enable_secure_boot
            )
            
            if success:
                logger.info("LUXusb configuration written successfully")
            else:
                logger.warning("Failed to write LUXusb configuration")
                
        except Exception as e:
            logger.exception(f"Error writing state file: {e}")
    
    def _auto_refresh_grub_if_needed(self) -> None:
        """
        Automatically detect if GRUB config needs refresh and update it
        
        This ensures the config stays in sync with actual ISO files on disk,
        handling scenarios like:
        - User manually updated ISOs (e.g., arch-2026.01.01.iso -> arch-2026.07.01.iso)
        - ISOs were deleted
        - New ISOs were manually added
        
        Runs silently - users don't need to know about GRUB config management
        """
        if not self.efi_mount or not self.data_mount:
            return
        
        try:
            from luxusb.utils.grub_refresher import GRUBConfigRefresher
            
            logger.info("Checking if GRUB config needs refresh...")
            refresher = GRUBConfigRefresher(self.efi_mount, self.data_mount)
            
            # Check if config matches actual ISOs
            is_fresh, message = refresher.verify_config_freshness()
            
            if not is_fresh:
                logger.info(f"GRUB config outdated: {message}")
                logger.info("Auto-refreshing GRUB configuration...")
                
                # Get GRUB timeout from config
                timeout = self.config.get('multi_iso.default_boot_timeout', default=10)
                
                # Refresh config
                if refresher.refresh_config(self.device.device, timeout=timeout):
                    logger.info("✓ GRUB config automatically refreshed")
                else:
                    logger.warning("Failed to auto-refresh GRUB config")
            else:
                logger.info(f"GRUB config is up to date: {message}")
                
        except Exception as e:
            logger.warning(f"Could not auto-refresh GRUB config: {e}")
            # Don't fail the workflow - just log the warning
    
    def _check_outdated_isos(self) -> None:
        """
        Check for outdated ISOs on USB and offer to update them
        
        This runs when mounting existing USB in append mode.
        Compares ISO versions with latest available in metadata.
        """
        if not self.efi_mount or not self.data_mount:
            return
        
        try:
            from luxusb.utils.grub_refresher import GRUBConfigRefresher
            
            logger.info("Checking for outdated ISOs...")
            refresher = GRUBConfigRefresher(self.efi_mount, self.data_mount)
            
            # Check for outdated ISOs
            outdated = refresher.check_outdated_isos()
            
            if outdated:
                logger.info(f"Found {len(outdated)} outdated ISO(s)")
                
                # Notify via callback if available
                if hasattr(self, 'outdated_iso_callback') and self.outdated_iso_callback:
                    self.outdated_iso_callback(outdated)
                else:
                    # Just log for now
                    for iso_info in outdated:
                        logger.info(f"  • {iso_info.upgrade_description}")
            else:
                logger.info("All ISOs are up to date")
                
        except Exception as e:
            logger.warning(f"Could not check for outdated ISOs: {e}")
            # Don't fail the workflow - just log the warning
    
    def _cleanup(self) -> None:
        """Stage 6: Cleanup and unmount"""
        self._update_progress(WorkflowStage.CLEANUP.value, 0.0, 0.95, "Cleaning up...")
        
        if self.efi_mount and self.data_mount:
            partitioner = USBPartitioner(self.device)
            partitioner.unmount_partitions(self.efi_mount, self.data_mount)
        
        self._update_progress(WorkflowStage.CLEANUP.value, 1.0, 1.0, "Cleanup complete")
    
    def _update_progress(
        self,
        stage: str,
        stage_progress: float,
        overall_progress: float,
        message: str,
        current_iso: Optional[int] = None,
        total_isos: Optional[int] = None
    ) -> None:
        """Update progress via callback"""
        if self.progress_callback:
            progress = WorkflowProgress(
                stage=stage,
                stage_progress=stage_progress,
                overall_progress=overall_progress,
                message=message,
                current_iso=current_iso,
                total_isos=total_isos
            )
            self.progress_callback(progress)

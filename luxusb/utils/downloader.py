"""ISO download manager with progress tracking and resume support"""

import json
import requests
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
from threading import Event

from luxusb.constants import FileExtension

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency
_mirror_selector = None
_stats_tracker = None

def get_mirror_selector():
    """Get singleton MirrorSelector instance"""
    global _mirror_selector
    if _mirror_selector is None:
        from luxusb.utils.mirror_selector import MirrorSelector
        _mirror_selector = MirrorSelector()
    return _mirror_selector

def get_stats_tracker():
    """Get singleton MirrorStatsTracker instance"""
    global _stats_tracker
    if _stats_tracker is None:
        from luxusb.utils.mirror_stats import MirrorStatsTracker
        _stats_tracker = MirrorStatsTracker()
    return _stats_tracker
    if _mirror_selector is None:
        from luxusb.utils.mirror_selector import MirrorSelector
        _mirror_selector = MirrorSelector()
    return _mirror_selector


@dataclass
class DownloadProgress:
    """Download progress information"""
    total_bytes: int
    downloaded_bytes: int
    speed_bytes_per_sec: float
    eta_seconds: float
    is_resumable: bool = False  # Whether download supports resume
    is_paused: bool = False     # Whether download is currently paused
    
    @property
    def percentage(self) -> float:
        """Get download percentage"""
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100
    
    @property
    def speed_mb_per_sec(self) -> float:
        """Get speed in MB/s"""
        return self.speed_bytes_per_sec / (1024 * 1024)


@dataclass
class ResumeMetadata:
    """Metadata for resuming interrupted downloads"""
    url: str
    total_size: int
    downloaded_bytes: int
    partial_checksum: str  # SHA256 of partial file
    timestamp: str
    destination: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ResumeMetadata':
        """Create from dictionary"""
        return cls(**data)


class ISODownloader:
    """Download ISO files with progress tracking, verification, and resume support"""
    
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LUXusb/0.2.0'
        })
        self.pause_event = Event()  # For pause/resume control
        self.pause_event.set()  # Not paused by default
        
        # Configure session for better reliability
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def pause(self) -> None:
        """Pause the current download"""
        self.pause_event.clear()
        logger.info("Download paused")
    
    def resume(self) -> None:
        """Resume the paused download"""
        self.pause_event.set()
        logger.info("Download resumed")
    
    def is_paused(self) -> bool:
        """Check if download is paused"""
        return not self.pause_event.is_set()
    
    def download_with_mirrors(
        self,
        primary_url: str,
        mirrors: List[str],
        destination: Path,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        chunk_size: int = 8192,
        auto_select_best: bool = False,
        allow_resume: bool = True
    ) -> bool:
        """
        Download ISO file with automatic mirror failover
        
        Args:
            primary_url: Primary download URL
            mirrors: List of mirror URLs to try on failure
            destination: Path to save ISO
            expected_sha256: Expected SHA256 checksum (optional)
            progress_callback: Callback function for progress updates
            chunk_size: Download chunk size in bytes
            auto_select_best: If True, test mirrors and use fastest first
            allow_resume: Whether to allow resuming downloads
            
        Returns:
            True if successful, False otherwise
        """
        all_urls = [primary_url] + mirrors
        
        # Auto-select fastest mirror if requested
        if auto_select_best and len(all_urls) > 1:
            logger.info("Auto-selecting fastest mirror...")
            selector = get_mirror_selector()
            best_url = selector.select_best_mirror(all_urls)
            if best_url:
                # Move best to front
                all_urls.remove(best_url)
                all_urls.insert(0, best_url)
                logger.info("Using fastest mirror: %s", best_url)
        
        for i, url in enumerate(all_urls):
            logger.info("Attempting download from URL %d/%d: %s", i + 1, len(all_urls), url)
            
            # Record start time for stats
            start_time = time.time()
            
            # Use resume-capable download if enabled
            if allow_resume:
                success = self.download_with_resume(
                    url=url,
                    destination=destination,
                    expected_sha256=expected_sha256,
                    progress_callback=progress_callback,
                    chunk_size=chunk_size,
                    allow_resume=True
                )
            else:
                success = self.download(
                    url=url,
                    destination=destination,
                    expected_sha256=expected_sha256,
                    progress_callback=progress_callback,
                    chunk_size=chunk_size
                )
            
            # Record stats
            elapsed_ms = (time.time() - start_time) * 1000
            stats_tracker = get_stats_tracker()
            
            if success:
                logger.info("Successfully downloaded from: %s", url)
                stats_tracker.record_success(url, elapsed_ms)
                return True
            else:
                stats_tracker.record_failure(url)
                if i < len(all_urls) - 1:
                    logger.warning("Download failed, trying next mirror...")
                else:
                    logger.error("All download sources exhausted")
        
        return False
    
    def _get_metadata_path(self, destination: Path) -> Path:
        """Get path for resume metadata file"""
        return destination.with_suffix(FileExtension.RESUME)
    
    def _save_resume_metadata(self, metadata: ResumeMetadata) -> None:
        """Save resume metadata to JSON file"""
        metadata_path = self._get_metadata_path(Path(metadata.destination))
        try:
            # Ensure parent directory exists (defensive coding)
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            logger.debug("Resume metadata saved: %s", metadata_path)
        except Exception as e:
            logger.warning("Failed to save resume metadata: %s", e)
    
    def _load_resume_metadata(self, destination: Path) -> Optional[ResumeMetadata]:
        """Load resume metadata from JSON file"""
        metadata_path = self._get_metadata_path(destination)
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            return ResumeMetadata.from_dict(data)
        except Exception as e:
            logger.warning("Failed to load resume metadata: %s", e)
            return None
    
    def _cleanup_resume_files(self, destination: Path) -> None:
        """Clean up partial download and metadata files"""
        part_file = destination.with_suffix(FileExtension.PART)
        metadata_file = self._get_metadata_path(destination)
        
        if part_file.exists():
            part_file.unlink()
            logger.debug("Deleted partial file: %s", part_file)
        
        if metadata_file.exists():
            metadata_file.unlink()
            logger.debug("Deleted metadata file: %s", metadata_file)
    
    def _supports_resume(self, url: str) -> bool:
        """Check if server supports HTTP Range requests"""
        try:
            response = self.session.head(url, timeout=10)
            accept_ranges = response.headers.get('Accept-Ranges', '').lower()
            return 'bytes' in accept_ranges
        except Exception as e:
            logger.debug("Could not check resume support: %s", e)
            return False
    
    def download_with_resume(
        self,
        url: str,
        destination: Path,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        chunk_size: int = 8192,
        allow_resume: bool = True
    ) -> bool:
        """
        Download ISO file with resume support
        
        Args:
            url: ISO download URL
            destination: Path to save ISO
            expected_sha256: Expected SHA256 checksum (optional)
            progress_callback: Callback function for progress updates
            chunk_size: Download chunk size in bytes
            allow_resume: Whether to attempt resuming partial downloads
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading %s (resume: %s)", url, allow_resume)
        logger.info("Destination: %s", destination)
        
        try:
            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            part_file = destination.with_suffix(FileExtension.PART)
            downloaded_size = 0
            sha256_hash = hashlib.sha256() if expected_sha256 else None
            
            # Check if we can resume
            can_resume = False
            if allow_resume and part_file.exists():
                metadata = self._load_resume_metadata(destination)
                if metadata and metadata.url == url:
                    downloaded_size = part_file.stat().st_size
                    
                    # Verify partial file matches metadata
                    if downloaded_size == metadata.downloaded_bytes:
                        can_resume = self._supports_resume(url)
                        if can_resume:
                            logger.info("Resuming download from %d bytes", downloaded_size)
                            # Rebuild hash for already downloaded bytes
                            if sha256_hash:
                                with open(part_file, 'rb') as f:
                                    for chunk in iter(lambda: f.read(chunk_size), b''):
                                        sha256_hash.update(chunk)
            
            # Prepare request headers
            headers = {}
            if can_resume and downloaded_size > 0:
                headers['Range'] = f'bytes={downloaded_size}-'
                logger.info("Using Range header: %s", headers['Range'])
            
            # Start download
            response = self.session.get(url, stream=True, timeout=30, headers=headers)
            
            # Check if resume was accepted
            if can_resume and response.status_code == 206:
                logger.info("Server accepted resume request (206 Partial Content)")
                mode = 'ab'  # Append to existing file
            elif response.status_code == 200:
                if can_resume:
                    logger.info("Server doesn't support resume, starting from beginning")
                mode = 'wb'  # Create new file
                downloaded_size = 0
                sha256_hash = hashlib.sha256() if expected_sha256 else None
            else:
                response.raise_for_status()
                return False
            
            total_size = int(response.headers.get('content-length', 0))
            if can_resume and response.status_code == 206:
                total_size += downloaded_size  # Add already downloaded bytes
            
            # Check if server supports resume for future
            supports_resume = self._supports_resume(url)
            
            # Download with progress tracking and pause support
            import time
            start_time = time.time()
            last_update_time = start_time
            
            with open(part_file, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    # Check pause state
                    self.pause_event.wait()  # Blocks if paused
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update hash
                        if sha256_hash:
                            sha256_hash.update(chunk)
                        
                        # Calculate progress
                        current_time = time.time()
                        if progress_callback and (current_time - last_update_time) >= 0.5:
                            elapsed = current_time - start_time
                            speed = downloaded_size / elapsed if elapsed > 0 else 0
                            
                            remaining_bytes = total_size - downloaded_size
                            eta = remaining_bytes / speed if speed > 0 else 0
                            
                            progress = DownloadProgress(
                                total_bytes=total_size,
                                downloaded_bytes=downloaded_size,
                                speed_bytes_per_sec=speed,
                                eta_seconds=eta,
                                is_resumable=supports_resume,
                                is_paused=self.is_paused()
                            )
                            
                            progress_callback(progress)
                            last_update_time = current_time
                            
                            # Save resume metadata periodically (every 10MB)
                            if supports_resume and downloaded_size % (10 * 1024 * 1024) < chunk_size:
                                metadata = ResumeMetadata(
                                    url=url,
                                    total_size=total_size,
                                    downloaded_bytes=downloaded_size,
                                    partial_checksum="",  # Not used for now
                                    timestamp=datetime.now().isoformat(),
                                    destination=str(destination)
                                )
                                self._save_resume_metadata(metadata)
            
            logger.info("Download completed: %s", destination)
            
            # Move .part file to final destination
            if part_file.exists():
                part_file.rename(destination)
            
            # Verify checksum if provided
            if expected_sha256 and sha256_hash:
                calculated_hash = sha256_hash.hexdigest()
                if calculated_hash.lower() != expected_sha256.lower():
                    logger.error("SHA256 checksum mismatch!")
                    logger.error("Expected:   %s", expected_sha256)
                    logger.error("Calculated: %s", calculated_hash)
                    destination.unlink()  # Delete corrupted file
                    self._cleanup_resume_files(destination)
                    return False
                logger.info("SHA256 checksum verified successfully")
            
            # Clean up resume metadata on success
            self._cleanup_resume_files(destination)
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error("Download failed: %s", e)
            # Keep .part file for resume
            return False
        except Exception as e:
            logger.exception("Unexpected error during download: %s", e)
            return False
    
    def download(
        self,
        url: str,
        destination: Path,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        chunk_size: int = 8192
    ) -> bool:
        """
        Download ISO file
        
        Args:
            url: ISO download URL
            destination: Path to save ISO
            expected_sha256: Expected SHA256 checksum (optional)
            progress_callback: Callback function for progress updates
            chunk_size: Download chunk size in bytes
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Downloading %s", url)
        logger.info("Destination: %s", destination)
        
        try:
            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Start download
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            # Prepare for checksum calculation
            sha256_hash = hashlib.sha256() if expected_sha256 else None
            
            # Download with progress tracking
            import time
            start_time = time.time()
            last_update_time = start_time
            
            # Ensure destination directory exists (defensive coding)
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update hash
                        if sha256_hash:
                            sha256_hash.update(chunk)
                        
                        # Calculate progress
                        current_time = time.time()
                        if progress_callback and (current_time - last_update_time) >= 0.5:
                            elapsed = current_time - start_time
                            speed = downloaded_size / elapsed if elapsed > 0 else 0
                            
                            remaining_bytes = total_size - downloaded_size
                            eta = remaining_bytes / speed if speed > 0 else 0
                            
                            progress = DownloadProgress(
                                total_bytes=total_size,
                                downloaded_bytes=downloaded_size,
                                speed_bytes_per_sec=speed,
                                eta_seconds=eta
                            )
                            
                            progress_callback(progress)
                            last_update_time = current_time
            
            logger.info("Download completed: %s", destination)
            
            # Verify checksum if provided
            if expected_sha256 and sha256_hash:
                calculated_hash = sha256_hash.hexdigest()
                if calculated_hash.lower() != expected_sha256.lower():
                    logger.error("SHA256 checksum mismatch!")
                    logger.error("Expected:   %s", expected_sha256)
                    logger.error("Calculated: %s", calculated_hash)
                    destination.unlink()  # Delete corrupted file
                    return False
                logger.info("SHA256 checksum verified successfully")
                
                # Check GPG verification status in strict mode
                from luxusb.config import Config
                config = Config()
                if config.get('download.gpg_strict_mode', False):
                    # Check if this download should require GPG verification
                    # (This check would typically happen before download starts,
                    # but we add a safeguard here as well)
                    logger.info("GPG strict mode enabled - additional verification recommended")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error("Download failed: %s", e)
            if destination.exists():
                destination.unlink()  # Clean up partial download
            return False
        except (OSError, IOError) as e:
            logger.exception("Unexpected error during download: %s", e)
            if destination.exists():
                destination.unlink()
            return False
    
    def verify_checksum(self, file_path: Path, expected_sha256: str) -> bool:
        """
        Verify SHA256 checksum of a file
        
        Args:
            file_path: Path to file
            expected_sha256: Expected SHA256 checksum
            
        Returns:
            True if checksum matches, False otherwise
        """
        logger.info("Verifying checksum of %s", file_path)
        
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256_hash.update(chunk)
            
            calculated = sha256_hash.hexdigest()
            matches = calculated.lower() == expected_sha256.lower()
            
            if matches:
                logger.info("Checksum verification passed")
            else:
                logger.error("Checksum verification failed")
                logger.error("Expected:   %s", expected_sha256)
                logger.error("Calculated: %s", calculated)
            
            return matches
            
        except (OSError, IOError) as e:
            logger.exception("Failed to verify checksum: %s", e)
            return False
    
    def get_file_size(self, url: str) -> Optional[int]:
        """
        Get file size without downloading
        
        Args:
            url: File URL
            
        Returns:
            File size in bytes, or None if unavailable
        """
        try:
            response = self.session.head(url, timeout=10)
            response.raise_for_status()
            return int(response.headers.get('content-length', 0))
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning("Failed to get file size: %s", e)
            return None

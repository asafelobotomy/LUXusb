"""
Centralized constants and enums for LUXusb application

This module provides a single source of truth for all string literals,
magic numbers, and enumerated values used across the application.
"""

from enum import Enum, IntEnum
from typing import Final


# ============================================================================
# Distribution Families
# ============================================================================

class DistroFamily(str, Enum):
    """Linux distribution family identifiers"""
    ARCH = "arch"
    DEBIAN = "debian"
    FEDORA = "fedora"
    INDEPENDENT = "independent"
    
    @property
    def display_name(self) -> str:
        """Get human-readable family name"""
        return {
            self.ARCH: "Arch-based Distributions",
            self.DEBIAN: "Debian-based Distributions",
            self.FEDORA: "Fedora-based Distributions",
            self.INDEPENDENT: "Independent Distributions"
        }[self]


# ============================================================================
# Distribution Categories
# ============================================================================

class DistroCategory(str, Enum):
    """Distribution category types"""
    DESKTOP = "Desktop"
    SERVER = "Server"
    GAMING = "Gaming"
    SECURITY = "Security"
    LIGHTWEIGHT = "Lightweight"
    EDUCATION = "Education"


# ============================================================================
# Verification Status
# ============================================================================

class VerificationStatus(str, Enum):
    """Verification tier levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    UNVERIFIED = "unverified"


class HealthStatus(str, Enum):
    """Mirror/service health status"""
    GOOD = "good"
    WARNING = "warning"
    POOR = "poor"


# ============================================================================
# Field Names (JSON/Dict Keys)
# ============================================================================

class DistroFields:
    """Field names for distribution metadata"""
    ID: Final = "id"
    NAME: Final = "name"
    DESCRIPTION: Final = "description"
    HOMEPAGE: Final = "homepage"
    LOGO_URL: Final = "logo_url"
    CATEGORY: Final = "category"
    FAMILY: Final = "family"
    BASE_DISTRO: Final = "base_distro"
    POPULARITY_RANK: Final = "popularity_rank"
    RELEASES: Final = "releases"
    METADATA: Final = "metadata"


class ReleaseFields:
    """Field names for release metadata"""
    VERSION: Final = "version"
    RELEASE_DATE: Final = "release_date"
    ISO_URL: Final = "iso_url"
    SHA256: Final = "sha256"
    SIZE_MB: Final = "size_mb"
    ARCHITECTURE: Final = "architecture"
    MIRRORS: Final = "mirrors"
    GPG_VERIFIED: Final = "gpg_verified"
    COSIGN_AVAILABLE: Final = "cosign_available"
    NOTES: Final = "notes"


class MetadataFields:
    """Field names for metadata sections"""
    LAST_UPDATED: Final = "last_updated"
    MAINTAINER: Final = "maintainer"
    VERIFIED: Final = "verified"
    VERIFICATION_TIER: Final = "verification_tier"


# ============================================================================
# Configuration Keys
# ============================================================================

class ConfigKeys:
    """Configuration key paths (dot-notation)"""
    
    class Download:
        """Download configuration keys"""
        VERIFY_CHECKSUMS: Final = "download.verify_checksums"
        MAX_RETRIES: Final = "download.max_retries"
        TIMEOUT: Final = "download.timeout"
        PREFERRED_MIRROR: Final = "download.preferred_mirror"
        AUTO_SELECT_MIRROR: Final = "download.auto_select_mirror"
        ALLOW_RESUME: Final = "download.allow_resume"
        CLEANUP_PARTIAL_FILES: Final = "download.cleanup_partial_files"
        VERIFY_GPG_SIGNATURES: Final = "download.verify_gpg_signatures"
        GPG_STRICT_MODE: Final = "download.gpg_strict_mode"
        AUTO_IMPORT_GPG_KEYS: Final = "download.auto_import_gpg_keys"
    
    class Metadata:
        """Metadata update configuration keys"""
        AUTO_UPDATE_ON_STARTUP: Final = "metadata.auto_update_on_startup"
        UPDATE_FREQUENCY_DAYS: Final = "metadata.update_frequency_days"
        UPDATE_TIMEOUT: Final = "metadata.update_timeout"
    
    class USB:
        """USB configuration keys"""
        EFI_PARTITION_SIZE_MB: Final = "usb.efi_partition_size_mb"
        VERIFY_BEFORE_WRITE: Final = "usb.verify_before_write"
        CONFIRM_BEFORE_FORMAT: Final = "usb.confirm_before_format"
    
    class UI:
        """UI configuration keys"""
        THEME: Final = "ui.theme"
        SHOW_ADVANCED_OPTIONS: Final = "ui.show_advanced_options"
        REMEMBER_LAST_DISTRO: Final = "ui.remember_last_distro"
    
    class Safety:
        """Safety configuration keys"""
        REQUIRE_CONFIRMATION: Final = "safety.require_confirmation"
        ENABLE_LOGGING: Final = "safety.enable_logging"
        CHECK_UPDATES: Final = "safety.check_updates"
    
    class MultiISO:
        """Multi-ISO configuration keys"""
        ENABLED: Final = "multi_iso.enabled"
        MAX_ISOS: Final = "multi_iso.max_isos"
        DEFAULT_BOOT_TIMEOUT: Final = "multi_iso.default_boot_timeout"
        SEQUENTIAL_DOWNLOADS: Final = "multi_iso.sequential_downloads"
        ABORT_ON_FAILURE: Final = "multi_iso.abort_on_failure"


# ============================================================================
# Status Icons & Symbols
# ============================================================================

class StatusIcon:
    """Unicode symbols for status display"""
    SUCCESS: Final = "✅"
    FAILURE: Final = "❌"
    WARNING: Final = "⚠️"
    INFO: Final = "ℹ️"
    REFRESH: Final = "🔄"
    DOWNLOAD: Final = "📥"
    CHECKMARK: Final = "✓"
    CROSS: Final = "✗"
    PAUSE: Final = "⏸️"
    BELL: Final = "🔔"
    LOCK: Final = "🔒"
    SHIELD: Final = "🛡️"


# ============================================================================
# Workflow Stages
# ============================================================================

class WorkflowStage(str, Enum):
    """Workflow execution stages"""
    INIT = "init"
    PARTITION = "partition"
    MOUNT = "mount"
    GRUB_INSTALL = "grub"
    DOWNLOAD = "download"
    CONFIGURE = "configure"
    CLEANUP = "cleanup"
    COMPLETE = "complete"
    
    @property
    def display_name(self) -> str:
        """Get display name for UI"""
        return {
            self.INIT: "Initializing",
            self.PARTITION: "Partitioning USB",
            self.MOUNT: "Mounting partitions",
            self.GRUB_INSTALL: "Installing GRUB",
            self.DOWNLOAD: "Downloading ISOs",
            self.CONFIGURE: "Configuring bootloader",
            self.CLEANUP: "Cleaning up",
            self.COMPLETE: "Complete"
        }[self]


# ============================================================================
# File Extensions & Patterns
# ============================================================================

class FileExtension:
    """Common file extensions"""
    ISO: Final = ".iso"
    JSON: Final = ".json"
    PART: Final = ".part"
    RESUME: Final = ".resume"
    GPG: Final = ".gpg"
    SIG: Final = ".sig"
    ASC: Final = ".asc"
    TMP: Final = ".tmp"
    SHA256: Final = ".sha256"


# ============================================================================
# Magic Numbers
# ============================================================================

class Size:
    """Size constants in bytes"""
    KB: Final = 1024
    MB: Final = 1024 * 1024
    GB: Final = 1024 * 1024 * 1024
    
    # Common partition sizes
    EFI_PARTITION_MB: Final = 1024  # 1 GB for EFI
    MIN_USB_SIZE_GB: Final = 8  # Minimum 8GB USB


class Timeout:
    """Timeout values in seconds"""
    HTTP_REQUEST: Final = 30
    MIRROR_TEST: Final = 10
    DOWNLOAD_DEFAULT: Final = 3600  # 1 hour
    UPDATE_CHECK: Final = 30


class Interval:
    """Time intervals in seconds"""
    PERIODIC_UPDATE_CHECK: Final = 6 * 3600  # 6 hours
    PROGRESS_UPDATE_MS: Final = 100  # 100ms for smooth progress
    TOAST_TIMEOUT: Final = 5  # 5 seconds
    CACHE_TTL_HOURS: Final = 24


# ============================================================================
# Paths & Directories
# ============================================================================

class PathPattern:
    """Path patterns and directory names"""
    CONFIG_DIR: Final = ".config/luxusb"
    DATA_DIR: Final = ".local/share/luxusb"
    CACHE_DIR: Final = ".cache/luxusb"
    LOG_DIR: Final = ".local/share/luxusb/logs"
    
    # File names
    CONFIG_FILE: Final = "config.yaml"
    LOG_FILE: Final = "luxusb.log"
    MIRROR_STATS_FILE: Final = "mirror_stats.json"
    UPDATE_MARKER_FILE: Final = "last_metadata_update.json"


# ============================================================================
# HTTP & Network
# ============================================================================

class HTTPHeader:
    """HTTP headers"""
    USER_AGENT: Final = "User-Agent"
    CONTENT_LENGTH: Final = "Content-Length"
    ACCEPT_RANGES: Final = "Accept-Ranges"
    RANGE: Final = "Range"


class MimeType:
    """MIME types"""
    JSON: Final = "application/json"
    ISO: Final = "application/x-iso9660-image"
    TEXT: Final = "text/plain"


# ============================================================================
# Validation
# ============================================================================

class Validation:
    """Validation thresholds and patterns"""
    MIN_SHA256_LENGTH: Final = 64
    MAX_SHA256_LENGTH: Final = 64
    MIN_VERSION_LENGTH: Final = 1
    MAX_DISTRO_NAME_LENGTH: Final = 100
    
    # Success rate thresholds for mirror health
    MIRROR_HEALTH_GOOD: Final = 0.8  # 80%+
    MIRROR_HEALTH_WARNING: Final = 0.5  # 50-80%
    # Below 50% = poor


# ============================================================================
# Error Messages
# ============================================================================

class ErrorMessage:
    """Common error message templates"""
    USB_NOT_FOUND: Final = "No USB devices found"
    INSUFFICIENT_SPACE: Final = "Insufficient space on USB device"
    DOWNLOAD_FAILED: Final = "Download failed"
    CHECKSUM_MISMATCH: Final = "Checksum verification failed"
    GPG_VERIFICATION_FAILED: Final = "GPG signature verification failed"
    PERMISSION_DENIED: Final = "Permission denied - run with sudo"
    NETWORK_ERROR: Final = "Network error - check your connection"
    INVALID_DISTRO: Final = "Invalid distribution selected"


# ============================================================================
# Success Messages
# ============================================================================

class SuccessMessage:
    """Common success message templates"""
    DOWNLOAD_COMPLETE: Final = "Download completed successfully"
    USB_CREATED: Final = "Bootable USB created successfully"
    UPDATE_COMPLETE: Final = "Update completed"
    VERIFICATION_PASSED: Final = "Verification passed"


# ============================================================================
# Architecture
# ============================================================================

class Architecture(str, Enum):
    """System architecture types"""
    X86_64 = "x86_64"
    AARCH64 = "aarch64"
    ARM = "arm"
    I686 = "i686"


# ============================================================================
# Theme
# ============================================================================

class Theme(str, Enum):
    """UI theme options"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

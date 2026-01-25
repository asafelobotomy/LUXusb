"""
Linux distribution metadata and management
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DistroRelease:
    """Represents a specific release of a Linux distribution"""
    version: str
    release_date: str
    iso_url: str
    sha256: str
    size_mb: int
    architecture: str = "x86_64"
    mirrors: Optional[List[str]] = None  # List of mirror URLs for failover
    
    def __post_init__(self) -> None:
        """Initialize mirrors list if not provided"""
        if self.mirrors is None:
            self.mirrors = []
    
    @property
    def size_gb(self) -> float:
        """Get size in gigabytes"""
        return self.size_mb / 1024.0


@dataclass
class Distro:
    """Represents a Linux distribution"""
    id: str
    name: str
    description: str
    homepage: str
    logo_url: str
    category: str
    popularity_rank: int
    releases: List[DistroRelease]
    # Distribution family (arch, debian, fedora, independent)
    family: Optional[str] = None
    base_distro: Optional[str] = None  # Specific base distribution
    secure_boot_compatible: bool = False  # Whether compatible with Secure Boot
    
    @property
    def latest_release(self) -> Optional[DistroRelease]:
        """Get the latest release"""
        return self.releases[0] if self.releases else None


@dataclass
class DistroSelection:
    """Represents a user-selected distribution for installation"""
    distro: Distro
    release: DistroRelease
    priority: int = 0  # Boot menu order (0 = default boot)
    
    @property
    def display_name(self) -> str:
        """Get display name for UI"""
        return f"{self.distro.name} {self.release.version}"
    
    @property
    def iso_filename(self) -> str:
        """Get ISO filename for storage"""
        return f"{self.distro.id}-{self.release.version}.iso"
    
    @property
    def size_bytes(self) -> int:
        """Get ISO size in bytes"""
        return self.release.size_mb * 1024 * 1024


def calculate_required_space(selections: List[DistroSelection]) -> int:
    """
    Calculate total space needed for all selected ISOs
    
    Args:
        selections: List of selected distributions
        
    Returns:
        Total bytes required (including EFI partition and overhead)
    """
    efi_size = 1024 * 1024 * 1024  # 1GB for EFI partition
    iso_total = sum(s.size_bytes for s in selections)
    overhead = 512 * 1024 * 1024  # 512MB overhead for filesystem
    return efi_size + iso_total + overhead


def format_size(bytes_size: int) -> str:
    """
    Format byte size as human-readable string
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "4.7 GB")
    """
    gb = bytes_size / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.1f} GB"
    mb = bytes_size / (1024 ** 2)
    return f"{mb:.0f} MB"


def validate_usb_capacity(
    usb_size_bytes: int, selections: List[DistroSelection]
) -> tuple[bool, str]:
    """
    Validate if USB has enough space for selected ISOs
    
    Args:
        usb_size_bytes: USB device capacity in bytes
        selections: List of selected distributions
        
    Returns:
        Tuple of (is_valid, message)
    """
    required = calculate_required_space(selections)
    
    if usb_size_bytes >= required:
        available = usb_size_bytes - required
        return True, f"Space available: {format_size(available)}"
    
    deficit = required - usb_size_bytes
    return (
        False,
        f"Need {format_size(required)}, only "
        f"{format_size(usb_size_bytes)} available "
        f"(short by {format_size(deficit)})"
    )


class DistroManager:
    """Manage Linux distribution metadata"""
    
    def __init__(self) -> None:
        """
        Initialize distro manager
        
        Loads distributions from JSON files in luxusb/data/distros/
        """
        self.distros: List[Distro] = []
        self._load_distros()
    
    def _load_distros(self) -> None:
        """Load distribution metadata from JSON files"""
        from luxusb.utils.distro_json_loader import load_all_distros
        
        self.distros = load_all_distros()
        
        if not self.distros:
            raise RuntimeError("No distributions found. Please ensure JSON files exist in luxusb/data/distros/")
        
        logger.info("Loaded %d distributions from JSON", len(self.distros))
    
    def get_all_distros(self) -> List[Distro]:
        """Get all available distributions"""
        return self.distros
    
    def get_distro_by_id(self, distro_id: str) -> Optional[Distro]:
        """Get distribution by ID"""
        for distro in self.distros:
            if distro.id == distro_id:
                return distro
        return None
    
    def get_popular_distros(self, limit: int = 10) -> List[Distro]:
        """Get most popular distributions"""
        sorted_distros = sorted(self.distros, key=lambda d: d.popularity_rank)
        return sorted_distros[:limit]
    
    def search_distros(self, query: str) -> List[Distro]:
        """Search distributions by name or description"""
        query = query.lower()
        results = []

        for distro in self.distros:
            if (query in distro.name.lower() or
                    query in distro.description.lower()):
                results.append(distro)
        
        return results


# Global instance (lazy initialization to avoid circular import)
_distro_manager_instance: Optional['DistroManager'] = None


def get_distro_manager() -> 'DistroManager':
    """Get or create the global DistroManager singleton"""
    global _distro_manager_instance
    if _distro_manager_instance is None:
        _distro_manager_instance = DistroManager()
    return _distro_manager_instance


# For backward compatibility
distro_manager = None  # Will be initialized on first access

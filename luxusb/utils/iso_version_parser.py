"""
ISO filename parsing and version comparison utility
"""

import re
import logging
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ISOVersion:
    """Parsed ISO version information"""
    distro_id: str           # e.g., "ubuntu", "fedora", "arch"
    version: str             # e.g., "24.04", "41", "2026.01.01"
    variant: Optional[str]   # e.g., "desktop", "server", "workstation"
    architecture: str        # e.g., "x86_64", "amd64", "i686"
    filename: str            # Original filename
    
    def __str__(self) -> str:
        if self.variant:
            return f"{self.distro_id}-{self.version}-{self.variant}"
        return f"{self.distro_id}-{self.version}"
    
    @property
    def sort_key(self) -> str:
        """Generate sortable version key for comparison"""
        # Convert version to sortable format
        # Handle different version formats:
        # - Semantic: 24.04, 11.0.1
        # - Date: 2026.01.01
        # - Number: 41, 42
        parts = re.split(r'[.\-]', self.version)
        
        # Pad each part to 8 digits for proper sorting
        return '.'.join(part.zfill(8) for part in parts)


class ISOVersionParser:
    """Parse ISO filenames and extract version information"""
    
    # Distro-specific patterns
    PATTERNS = [
        # Ubuntu: ubuntu-24.04-desktop-amd64.iso, ubuntu-24.04.1-live-server-amd64.iso
        {
            'distro': 'ubuntu',
            'pattern': r'ubuntu-(?P<version>[\d.]+)(-(?P<variant>desktop|server|live-server))?-(?P<arch>amd64|i386)\.iso',
        },
        # Fedora: Fedora-Workstation-Live-x86_64-41-1.4.iso
        {
            'distro': 'fedora',
            'pattern': r'Fedora-(?P<variant>Workstation|Server|Silverblue)?-?(?:Live-)?(?P<arch>x86_64|i686)-(?P<version>[\d]+(?:-[\d.]+)?)\.iso',
        },
        # Fedora (simple): fedora-40-x86_64.iso
        {
            'distro': 'fedora',
            'pattern': r'fedora-(?P<version>\d+)-(?P<arch>x86_64|i686)\.iso',
        },
        # Arch: archlinux-2026.01.01-x86_64.iso
        {
            'distro': 'arch',
            'pattern': r'arch(?:linux)?-(?P<version>\d{4}\.\d{2}\.\d{2})-(?P<arch>x86_64|i686)\.iso',
        },
        # Linux Mint: linuxmint-22-cinnamon-64bit.iso, linuxmint-22.1-xfce-64bit.iso
        {
            'distro': 'linuxmint',
            'pattern': r'linuxmint-(?P<version>[\d.]+)-(?P<variant>cinnamon|mate|xfce)-(?P<arch>64bit|32bit)\.iso',
        },
        # Debian: debian-12.4.0-amd64-netinst.iso, debian-live-12.4.0-amd64-kde.iso
        {
            'distro': 'debian',
            'pattern': r'debian(?:-live)?-(?P<version>[\d.]+)-(?P<arch>amd64|i386)(?:-(?P<variant>netinst|kde|gnome|xfce))?\.iso',
        },
        # Kali: kali-linux-2024.1-installer-amd64.iso
        {
            'distro': 'kali',
            'pattern': r'kali-linux-(?P<version>[\d.]+)-(?P<variant>installer|live)?-(?P<arch>amd64|i386)\.iso',
        },
        # Manjaro: manjaro-kde-24.0-240113-linux66.iso
        {
            'distro': 'manjaro',
            'pattern': r'manjaro-(?P<variant>kde|gnome|xfce)?-?(?P<version>[\d.]+)-[\d]+-linux\d+\.iso',
        },
        # Pop!_OS: pop-os_22.04_amd64_intel_8.iso
        {
            'distro': 'popos',
            'pattern': r'pop-os_(?P<version>[\d.]+)_(?P<arch>amd64|i386)_(?P<variant>intel|nvidia|nvidia_3050|nvidia_old)_\d+\.iso',
        },
    ]
    
    def parse(self, filename: str) -> Optional[ISOVersion]:
        """
        Parse ISO filename and extract version information
        
        Args:
            filename: ISO filename (e.g., "ubuntu-24.04-desktop-amd64.iso")
            
        Returns:
            ISOVersion object or None if parsing failed
        """
        filename_lower = filename.lower()
        
        for pattern_info in self.PATTERNS:
            distro = pattern_info['distro']
            pattern = pattern_info['pattern']
            
            match = re.match(pattern, filename_lower, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                
                version = groups.get('version', '')
                variant = groups.get('variant')
                arch = groups.get('arch', 'x86_64')
                
                # Normalize architecture
                if arch in ('amd64', '64bit'):
                    arch = 'x86_64'
                elif arch in ('i386', '32bit'):
                    arch = 'i686'
                
                # Normalize variant (lowercase)
                if variant:
                    variant = variant.lower()
                
                return ISOVersion(
                    distro_id=distro,
                    version=version,
                    variant=variant,
                    architecture=arch,
                    filename=filename
                )
        
        # No pattern matched
        logger.warning(f"Could not parse ISO filename: {filename}")
        return None
    
    def compare_versions(self, v1: ISOVersion, v2: ISOVersion) -> int:
        """
        Compare two ISO versions
        
        Args:
            v1: First version
            v2: Second version
            
        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        # Must be same distro and variant to compare
        if v1.distro_id != v2.distro_id:
            raise ValueError(f"Cannot compare different distros: {v1.distro_id} vs {v2.distro_id}")
        
        if v1.variant != v2.variant:
            raise ValueError(f"Cannot compare different variants: {v1.variant} vs {v2.variant}")
        
        # Compare using sort keys
        key1 = v1.sort_key
        key2 = v2.sort_key
        
        if key1 < key2:
            return -1
        elif key1 > key2:
            return 1
        else:
            return 0
    
    def is_newer(self, v1: ISOVersion, v2: ISOVersion) -> bool:
        """Check if v1 is newer than v2"""
        try:
            return self.compare_versions(v1, v2) > 0
        except ValueError:
            return False
    
    def find_latest_version(self, versions: list[ISOVersion]) -> Optional[ISOVersion]:
        """
        Find the latest version from a list
        
        Args:
            versions: List of ISOVersion objects
            
        Returns:
            Latest version or None if list is empty
        """
        if not versions:
            return None
        
        # Group by distro and variant
        groups = {}
        for v in versions:
            key = (v.distro_id, v.variant)
            if key not in groups:
                groups[key] = []
            groups[key].append(v)
        
        # Find latest in each group
        latest_versions = []
        for group_versions in groups.values():
            latest = max(group_versions, key=lambda v: v.sort_key)
            latest_versions.append(latest)
        
        return latest_versions if len(latest_versions) > 1 else latest_versions[0]


def parse_iso_filename(filename: str) -> Optional[ISOVersion]:
    """
    Convenience function to parse ISO filename
    
    Args:
        filename: ISO filename
        
    Returns:
        ISOVersion object or None
    """
    parser = ISOVersionParser()
    return parser.parse(filename)


def compare_iso_versions(filename1: str, filename2: str) -> Optional[int]:
    """
    Convenience function to compare two ISO filenames
    
    Args:
        filename1: First ISO filename
        filename2: Second ISO filename
        
    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2, None if cannot compare
    """
    parser = ISOVersionParser()
    v1 = parser.parse(filename1)
    v2 = parser.parse(filename2)
    
    if not v1 or not v2:
        return None
    
    try:
        return parser.compare_versions(v1, v2)
    except ValueError:
        return None

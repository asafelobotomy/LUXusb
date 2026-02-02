"""
Persistence support for live Linux distributions

Allows live USBs to save changes (files, settings, packages) across reboots.
Supports multiple distributions with different persistence mechanisms.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PersistenceType(Enum):
    """Type of persistence mechanism used by distribution"""
    CASPER = "casper"              # Ubuntu/Debian (casper-rw)
    OVERLAY = "overlay"            # Fedora (rd.live.overlay)
    COW = "cow"                    # Arch (cow_spacesize)
    PERSISTENCE_FILE = "file"      # Generic persistence file
    NONE = "none"                  # No persistence support


@dataclass
class PersistenceConfig:
    """Configuration for distribution persistence"""
    distro_id: str
    persistence_type: PersistenceType
    file_name: str                 # e.g., "ubuntu-persistence.dat"
    file_size_mb: int              # Size in MB
    kernel_params: List[str]       # Additional boot parameters
    label: Optional[str] = None    # Filesystem label if needed


class PersistenceManager:
    """Manage persistence storage for live Linux distributions"""
    
    # Default persistence configurations per distro family
    DISTRO_CONFIGS: Dict[str, PersistenceConfig] = {
        'ubuntu': PersistenceConfig(
            distro_id='ubuntu',
            persistence_type=PersistenceType.CASPER,
            file_name='ubuntu-persistence.dat',
            file_size_mb=4096,  # 4GB default
            kernel_params=['persistent', 'persistent-path=/persistence/ubuntu-persistence.dat'],
            label='casper-rw'
        ),
        'debian': PersistenceConfig(
            distro_id='debian',
            persistence_type=PersistenceType.CASPER,
            file_name='debian-persistence.dat',
            file_size_mb=4096,
            kernel_params=['persistent', 'persistent-path=/persistence/debian-persistence.dat'],
            label='persistence'
        ),
        'fedora': PersistenceConfig(
            distro_id='fedora',
            persistence_type=PersistenceType.OVERLAY,
            file_name='fedora-overlay.img',
            file_size_mb=4096,
            kernel_params=['rd.live.overlay=/dev/disk/by-label/FEDORA-OVERLAY'],
            label='FEDORA-OVERLAY'
        ),
        'arch': PersistenceConfig(
            distro_id='arch',
            persistence_type=PersistenceType.COW,
            file_name='arch-cow.img',
            file_size_mb=4096,
            kernel_params=['cow_spacesize=4096M', 'cow_device=/dev/disk/by-label/ARCH-COW'],
            label='ARCH-COW'
        ),
        'linuxmint': PersistenceConfig(
            distro_id='linuxmint',
            persistence_type=PersistenceType.CASPER,
            file_name='mint-persistence.dat',
            file_size_mb=4096,
            kernel_params=['persistent', 'persistent-path=/persistence/mint-persistence.dat'],
            label='casper-rw'
        ),
        'kali': PersistenceConfig(
            distro_id='kali',
            persistence_type=PersistenceType.CASPER,
            file_name='kali-persistence.dat',
            file_size_mb=4096,
            kernel_params=['persistent', 'persistent-path=/persistence/kali-persistence.dat'],
            label='persistence'
        ),
    }
    
    def __init__(self, data_partition_path: Path):
        """
        Initialize persistence manager
        
        Args:
            data_partition_path: Mount point of USB data partition
        """
        self.data_partition = data_partition_path
        self.persistence_dir = data_partition_path / 'persistence'
        self.persistence_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def is_persistence_supported(self, distro_id: str) -> bool:
        """
        Check if distro supports persistence
        
        Args:
            distro_id: Distribution identifier (e.g., 'ubuntu', 'fedora')
        
        Returns:
            True if persistence is supported for this distro
        """
        return distro_id.lower() in self.DISTRO_CONFIGS
    
    def get_config(self, distro_id: str) -> Optional[PersistenceConfig]:
        """
        Get persistence configuration for distro
        
        Args:
            distro_id: Distribution identifier
        
        Returns:
            PersistenceConfig or None if not supported
        """
        return self.DISTRO_CONFIGS.get(distro_id.lower())
    
    def create_persistence_file(
        self,
        distro_id: str,
        size_mb: Optional[int] = None,
        force: bool = False
    ) -> bool:
        """
        Create persistence file for distribution
        
        Args:
            distro_id: Distribution identifier
            size_mb: Override default size in MB (optional)
            force: Overwrite existing file if present
        
        Returns:
            True if creation successful, False otherwise
        """
        config = self.get_config(distro_id)
        if not config:
            self.logger.error(f"Persistence not supported for {distro_id}")
            return False
        
        # Use custom size or default
        file_size = size_mb or config.file_size_mb
        persistence_file = self.persistence_dir / config.file_name
        
        # Check if file already exists
        if persistence_file.exists() and not force:
            self.logger.info(f"Persistence file already exists: {persistence_file}")
            return True
        
        try:
            self.logger.info(f"Creating {file_size}MB persistence file for {distro_id}")
            
            # Create sparse file (much faster than dd)
            # truncate -s 4G file.dat
            subprocess.run(
                ['truncate', '-s', f'{file_size}M', str(persistence_file)],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Format with ext4
            self.logger.info(f"Formatting persistence file with ext4...")
            subprocess.run(
                ['mkfs.ext4', '-F', '-L', config.label or 'persistence', str(persistence_file)],
                check=True,
                capture_output=True,
                text=True
            )
            
            self.logger.info(f"✓ Persistence file created: {persistence_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create persistence file: {e.stderr}")
            return False
        except Exception as e:
            self.logger.exception(f"Unexpected error creating persistence: {e}")
            return False
    
    def delete_persistence_file(self, distro_id: str) -> bool:
        """
        Delete persistence file for distribution
        
        Args:
            distro_id: Distribution identifier
        
        Returns:
            True if deletion successful, False otherwise
        """
        config = self.get_config(distro_id)
        if not config:
            self.logger.error(f"Unknown distro: {distro_id}")
            return False
        
        persistence_file = self.persistence_dir / config.file_name
        
        if not persistence_file.exists():
            self.logger.warning(f"Persistence file does not exist: {persistence_file}")
            return True  # Already deleted
        
        try:
            persistence_file.unlink()
            self.logger.info(f"✓ Deleted persistence file: {persistence_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete persistence file: {e}")
            return False
    
    def get_kernel_params(self, distro_id: str) -> List[str]:
        """
        Get kernel parameters for persistence boot
        
        Args:
            distro_id: Distribution identifier
        
        Returns:
            List of kernel parameters to add to boot entry
        """
        config = self.get_config(distro_id)
        if not config:
            return []
        
        return config.kernel_params
    
    def list_persistence_files(self) -> Dict[str, Dict]:
        """
        List all existing persistence files
        
        Returns:
            Dict mapping distro_id to file info {path, size_mb, exists}
        """
        results = {}
        
        for distro_id, config in self.DISTRO_CONFIGS.items():
            persistence_file = self.persistence_dir / config.file_name
            
            if persistence_file.exists():
                try:
                    size_bytes = persistence_file.stat().st_size
                    size_mb = size_bytes // (1024 * 1024)
                    
                    results[distro_id] = {
                        'path': persistence_file,
                        'size_mb': size_mb,
                        'exists': True,
                        'label': config.label
                    }
                except Exception as e:
                    self.logger.warning(f"Error reading {persistence_file}: {e}")
        
        return results
    
    def get_supported_distros(self) -> List[str]:
        """
        Get list of distributions that support persistence
        
        Returns:
            List of distro IDs
        """
        return list(self.DISTRO_CONFIGS.keys())
    
    def estimate_space_used(self) -> int:
        """
        Calculate total space used by persistence files
        
        Returns:
            Total size in MB
        """
        total_mb = 0
        
        for persistence_info in self.list_persistence_files().values():
            total_mb += persistence_info['size_mb']
        
        return total_mb


def is_persistence_supported(distro_id: str) -> bool:
    """
    Convenience function to check persistence support
    
    Args:
        distro_id: Distribution identifier
    
    Returns:
        True if persistence is supported
    """
    return distro_id.lower() in PersistenceManager.DISTRO_CONFIGS


def get_persistence_help(distro_id: str) -> str:
    """
    Get help text for enabling persistence
    
    Args:
        distro_id: Distribution identifier
    
    Returns:
        Help text explaining how to use persistence
    """
    config = PersistenceManager.DISTRO_CONFIGS.get(distro_id.lower())
    
    if not config:
        return f"Persistence is not supported for {distro_id}."
    
    help_text = f"""
Persistence for {distro_id.title()}
{'='*50}

Persistence allows you to save changes (files, settings, packages) 
across reboots when using the live USB.

Configuration:
- Type: {config.persistence_type.value}
- File: {config.file_name}
- Default size: {config.file_size_mb}MB ({config.file_size_mb / 1024:.1f}GB)
- Label: {config.label or 'N/A'}

How it works:
1. LUXusb creates a persistence file on the USB
2. The live system mounts this file as an overlay filesystem
3. All changes are saved to this file instead of RAM
4. On next boot, changes persist automatically

Note: Larger persistence files allow more changes but use more USB space.
Recommended: 4GB for basic use, 8GB+ for package installations.
"""
    return help_text

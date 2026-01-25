"""
Configuration management for LUXusb
"""

import os
from pathlib import Path
from typing import Optional
import yaml
import logging

from luxusb.constants import (
    PathPattern,
    Timeout,
    Size,
    Theme,
    Interval
)

logger = logging.getLogger(__name__)


class Config:
    """Application configuration manager"""
    
    def __init__(self):
        self.config_dir = Path.home() / PathPattern.CONFIG_DIR
        self.data_dir = Path.home() / PathPattern.DATA_DIR
        self.cache_dir = Path.home() / PathPattern.CACHE_DIR
        
        # Create directories
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / PathPattern.CONFIG_FILE
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
                return self._default_config()
        return self._default_config()
    
    def _default_config(self) -> dict:
        """Return default configuration"""
        return {
            'download': {
                'verify_checksums': True,
                'max_retries': 3,
                'timeout': Timeout.HTTP_REQUEST,
                'preferred_mirror': 'auto',
                # Phase 2 features
                'auto_select_mirror': True,  # Automatically select fastest mirror
                'allow_resume': True,  # Allow resuming interrupted downloads
                'cleanup_partial_files': True,  # Remove .part files after successful download
                # GPG verification (Phase 4)
                'verify_gpg_signatures': True,  # Verify GPG signatures when available
                'gpg_strict_mode': False,  # Fail downloads if GPG verification fails (False = warn only)
                'auto_import_gpg_keys': True,  # Automatically import distro GPG keys from keyservers
            },
            'metadata': {
                'auto_update_on_startup': True,  # Automatically update distro metadata with GPG verification
                'update_frequency_days': 7,  # Update metadata every N days (0 = always, 999 = never)
                'update_timeout': Timeout.UPDATE_CHECK,  # Timeout for metadata update requests (seconds)
            },
            'usb': {
                'efi_partition_size_mb': Size.EFI_PARTITION_MB,  # 1GB for EFI
                'verify_before_write': True,
                'confirm_before_format': True,
            },
            'ui': {
                'theme': Theme.DARK.value,  # Default to dark mode
                'show_advanced_options': False,
                'remember_last_distro': True,
            },
            'safety': {
                'require_confirmation': True,
                'enable_logging': True,
                'check_updates': True,
            },
            'multi_iso': {
                'enabled': True,  # Allow multiple ISO selection
                'max_isos': 10,  # Maximum number of ISOs per USB
                'default_boot_timeout': 10,  # GRUB menu timeout (seconds)
                'sequential_downloads': True,  # Download one at a time
                'abort_on_failure': False,  # Continue with successful ISOs if one fails
            }
        }
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Optional[any] = None) -> any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


# Global config instance
config = Config()

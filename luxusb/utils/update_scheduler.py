"""
Update scheduler for managing metadata update timing and preferences
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class UpdateScheduler:
    """Manage update check scheduling and user preferences"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize scheduler
        
        Args:
            config_dir: Configuration directory (defaults to ~/.config/luxusb)
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "luxusb"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.prefs_file = self.config_dir / "update_preferences.json"
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> dict:
        """Load update preferences from disk"""
        if not self.prefs_file.exists():
            return self._default_preferences()
        
        try:
            with open(self.prefs_file, 'r') as f:
                prefs = json.load(f)
                logger.debug(f"Loaded update preferences: {prefs}")
                return prefs
        except Exception as e:
            logger.warning(f"Could not load preferences: {e}")
            return self._default_preferences()
    
    def _save_preferences(self) -> None:
        """Save update preferences to disk"""
        try:
            with open(self.prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            logger.debug("Saved update preferences")
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def save_preferences(self) -> None:
        """Public method to save preferences (used by GUI)"""
        self._save_preferences()
    
    def _default_preferences(self) -> dict:
        """Get default preferences"""
        return {
            "enabled": True,
            "check_interval_days": 7,
            "last_check_timestamp": None,
            "remind_later_until": None,
            "skip_versions": [],
            "skip_until_date": None,
            "auto_check_on_startup": True,
            "show_changelog": True
        }
    
    def should_check_for_updates(self) -> Tuple[bool, str]:
        """
        Determine if we should check for updates
        
        Returns:
            Tuple of (should_check, reason)
        """
        if not self.preferences.get("enabled", True):
            return (False, "Update checks disabled")
        
        # Check if auto-check on startup is disabled
        if not self.preferences.get("auto_check_on_startup", True):
            return (False, "Auto-check on startup disabled")
        
        # Check if user clicked "Update Later" recently
        remind_later = self.preferences.get("remind_later_until")
        if remind_later:
            try:
                remind_time = datetime.fromisoformat(remind_later)
                if datetime.now() < remind_time:
                    remaining = remind_time - datetime.now()
                    hours = int(remaining.total_seconds() / 3600)
                    return (False, f"User requested to remind later ({hours}h remaining)")
            except (ValueError, TypeError):
                # Invalid timestamp - clear it
                self.clear_remind_later()
        
        # Check if user clicked "Skip" with a date
        skip_until = self.preferences.get("skip_until_date")
        if skip_until:
            try:
                skip_date = datetime.fromisoformat(skip_until)
                if datetime.now() < skip_date:
                    days = (skip_date - datetime.now()).days
                    return (False, f"User skipped updates ({days} days remaining)")
            except (ValueError, TypeError):
                self.clear_skip_date()
        
        # Check last update timestamp
        last_check = self.preferences.get("last_check_timestamp")
        check_interval_days = self.preferences.get("check_interval_days", 7)
        
        if last_check:
            try:
                last_check_time = datetime.fromisoformat(last_check)
                next_check_time = last_check_time + timedelta(days=check_interval_days)
                
                if datetime.now() < next_check_time:
                    remaining = next_check_time - datetime.now()
                    hours = int(remaining.total_seconds() / 3600)
                    return (False, f"Checked recently ({hours}h until next check)")
                else:
                    days_since = (datetime.now() - last_check_time).days
                    return (True, f"Last checked {days_since} days ago")
            except (ValueError, TypeError):
                # Invalid timestamp - allow check
                return (True, "Invalid last check timestamp")
        else:
            return (True, "Never checked before")
    
    def mark_check_completed(self) -> None:
        """Mark that an update check was completed"""
        self.preferences["last_check_timestamp"] = datetime.now().isoformat()
        self.preferences["remind_later_until"] = None
        self._save_preferences()
        logger.info("Update check completed and recorded")
    
    def set_remind_later(self, hours: int = 24) -> None:
        """
        Set reminder for later
        
        Args:
            hours: Hours until next reminder (default: 24)
        """
        remind_time = datetime.now() + timedelta(hours=hours)
        self.preferences["remind_later_until"] = remind_time.isoformat()
        self._save_preferences()
        logger.info(f"Set reminder for {remind_time}")
    
    def clear_remind_later(self) -> None:
        """Clear reminder setting"""
        self.preferences["remind_later_until"] = None
        self._save_preferences()
    
    def set_skip_date(self, days: int = 30) -> None:
        """
        Skip updates for a period
        
        Args:
            days: Days to skip (default: 30)
        """
        skip_date = datetime.now() + timedelta(days=days)
        self.preferences["skip_until_date"] = skip_date.isoformat()
        self._save_preferences()
        logger.info(f"Skipping updates until {skip_date}")
    
    def clear_skip_date(self) -> None:
        """Clear skip date setting"""
        self.preferences["skip_until_date"] = None
        self._save_preferences()
    
    def add_skip_version(self, distro_id: str, version: str) -> None:
        """
        Add a specific version to skip list
        
        Args:
            distro_id: Distribution ID (e.g., 'ubuntu')
            version: Version to skip (e.g., '25.04')
        """
        skip_versions = self.preferences.get("skip_versions", [])
        skip_key = f"{distro_id}-{version}"
        
        if skip_key not in skip_versions:
            skip_versions.append(skip_key)
            self.preferences["skip_versions"] = skip_versions
            self._save_preferences()
            logger.info(f"Added {skip_key} to skip list")
    
    def should_skip_version(self, distro_id: str, version: str) -> bool:
        """
        Check if a specific version should be skipped
        
        Args:
            distro_id: Distribution ID
            version: Version to check
            
        Returns:
            True if version should be skipped
        """
        skip_versions = self.preferences.get("skip_versions", [])
        skip_key = f"{distro_id}-{version}"
        return skip_key in skip_versions
    
    def clear_skip_versions(self) -> None:
        """Clear all skipped versions"""
        self.preferences["skip_versions"] = []
        self._save_preferences()
        logger.info("Cleared skip versions list")
    
    def get_check_interval_days(self) -> int:
        """Get configured check interval in days"""
        return self.preferences.get("check_interval_days", 7)
    
    def set_check_interval_days(self, days: int) -> None:
        """
        Set check interval
        
        Args:
            days: Days between checks (minimum: 1, maximum: 365)
        """
        days = max(1, min(365, days))
        self.preferences["check_interval_days"] = days
        self._save_preferences()
        logger.info(f"Set check interval to {days} days")
    
    def get_last_check_date(self) -> Optional[datetime]:
        """Get last check datetime"""
        last_check = self.preferences.get("last_check_timestamp")
        if last_check:
            try:
                return datetime.fromisoformat(last_check)
            except (ValueError, TypeError):
                return None
        return None
    
    def get_next_check_date(self) -> Optional[datetime]:
        """Get next scheduled check datetime"""
        last_check = self.get_last_check_date()
        if last_check:
            interval = self.get_check_interval_days()
            return last_check + timedelta(days=interval)
        return None
    
    def is_auto_check_enabled(self) -> bool:
        """Check if automatic checking on startup is enabled"""
        return self.preferences.get("auto_check_on_startup", True)
    
    def set_auto_check_enabled(self, enabled: bool) -> None:
        """Enable/disable automatic checking on startup"""
        self.preferences["auto_check_on_startup"] = enabled
        self._save_preferences()
        logger.info(f"Auto-check on startup: {enabled}")
    
    def get_statistics(self) -> dict:
        """Get update check statistics"""
        last_check = self.get_last_check_date()
        next_check = self.get_next_check_date()
        
        return {
            "enabled": self.preferences.get("enabled", True),
            "check_interval_days": self.get_check_interval_days(),
            "last_check": last_check.isoformat() if last_check else "Never",
            "next_check": next_check.isoformat() if next_check else "On next startup",
            "remind_later_active": self.preferences.get("remind_later_until") is not None,
            "skip_period_active": self.preferences.get("skip_until_date") is not None,
            "skipped_versions_count": len(self.preferences.get("skip_versions", [])),
            "auto_check_enabled": self.is_auto_check_enabled()
        }

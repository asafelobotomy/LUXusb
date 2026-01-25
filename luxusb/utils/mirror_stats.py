"""
Mirror statistics tracker for monitoring mirror health and reliability
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class MirrorStats:
    """Statistics for a single mirror"""
    url: str
    success_count: int = 0
    failure_count: int = 0
    total_response_time_ms: float = 0.0
    last_used: Optional[str] = None
    last_updated: Optional[str] = None
    
    @property
    def average_response_time_ms(self) -> float:
        """Calculate average response time"""
        if self.success_count == 0:
            return 0.0
        return self.total_response_time_ms / self.success_count
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        total_attempts = self.success_count + self.failure_count
        if total_attempts == 0:
            return 100.0  # No attempts yet, assume good
        return (self.success_count / total_attempts) * 100.0
    
    @property
    def health_status(self) -> str:
        """Get health status: good, warning, or poor"""
        rate = self.success_rate
        if rate >= 80.0:
            return "good"
        elif rate >= 50.0:
            return "warning"
        else:
            return "poor"


class MirrorStatsTracker:
    """Track and persist mirror statistics"""
    
    def __init__(self):
        self._stats_file = self._get_stats_file()
        self._stats: Dict[str, MirrorStats] = {}
        self._lock = Lock()
        self._load_stats()
    
    def _get_stats_file(self) -> Path:
        """Get path to mirror stats file"""
        cache_dir = Path.home() / ".cache" / "luxusb"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "mirror_stats.json"
    
    def _load_stats(self) -> None:
        """Load statistics from disk"""
        if not self._stats_file.exists():
            logger.debug("No existing mirror stats file found")
            return
        
        try:
            with open(self._stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict to MirrorStats objects
            for url, stats_dict in data.items():
                self._stats[url] = MirrorStats(**stats_dict)
            
            logger.info(f"Loaded stats for {len(self._stats)} mirrors")
        except Exception as e:
            logger.exception(f"Failed to load mirror stats: {e}")
    
    def _save_stats(self) -> None:
        """Save statistics to disk"""
        try:
            # Convert MirrorStats objects to dicts
            data = {url: asdict(stats) for url, stats in self._stats.items()}
            
            with open(self._stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved stats for {len(self._stats)} mirrors")
        except Exception as e:
            logger.exception(f"Failed to save mirror stats: {e}")
    
    def record_success(self, mirror_url: str, response_time_ms: float) -> None:
        """Record successful download from mirror"""
        with self._lock:
            if mirror_url not in self._stats:
                self._stats[mirror_url] = MirrorStats(url=mirror_url)
            
            stats = self._stats[mirror_url]
            stats.success_count += 1
            stats.total_response_time_ms += response_time_ms
            stats.last_used = datetime.now().isoformat()
            stats.last_updated = datetime.now().isoformat()
            
            self._save_stats()
            logger.debug(f"Recorded success for {mirror_url}: {response_time_ms:.0f}ms")
    
    def record_failure(self, mirror_url: str) -> None:
        """Record failed download from mirror"""
        with self._lock:
            if mirror_url not in self._stats:
                self._stats[mirror_url] = MirrorStats(url=mirror_url)
            
            stats = self._stats[mirror_url]
            stats.failure_count += 1
            stats.last_updated = datetime.now().isoformat()
            
            self._save_stats()
            logger.debug(f"Recorded failure for {mirror_url}")
    
    def get_stats(self, mirror_url: str) -> Optional[MirrorStats]:
        """Get statistics for a specific mirror"""
        with self._lock:
            return self._stats.get(mirror_url)
    
    def get_all_stats(self) -> Dict[str, MirrorStats]:
        """Get statistics for all mirrors"""
        with self._lock:
            return self._stats.copy()
    
    def rank_mirrors(self, mirror_urls: List[str]) -> List[str]:
        """
        Rank mirrors by health and performance
        
        Returns mirrors sorted by:
        1. Success rate (higher is better)
        2. Average response time (lower is better)
        """
        with self._lock:
            # Get stats for each mirror
            mirror_data = []
            for url in mirror_urls:
                stats = self._stats.get(url)
                if stats is None:
                    # New mirror, give it priority
                    mirror_data.append((url, 100.0, 0.0))
                else:
                    mirror_data.append((
                        url,
                        stats.success_rate,
                        stats.average_response_time_ms
                    ))
            
            # Sort by success rate (desc), then response time (asc)
            mirror_data.sort(key=lambda x: (-x[1], x[2]))
            
            return [url for url, _, _ in mirror_data]
    
    def get_healthy_mirrors(self, mirror_urls: List[str], min_success_rate: float = 50.0) -> List[str]:
        """Filter mirrors by minimum success rate"""
        with self._lock:
            healthy = []
            for url in mirror_urls:
                stats = self._stats.get(url)
                if stats is None or stats.success_rate >= min_success_rate:
                    healthy.append(url)
            return healthy
    
    def cleanup_old_stats(self, days: int = 30) -> int:
        """Remove statistics older than specified days"""
        with self._lock:
            cutoff = datetime.now() - timedelta(days=days)
            to_remove = []
            
            for url, stats in self._stats.items():
                if stats.last_updated:
                    last_updated = datetime.fromisoformat(stats.last_updated)
                    if last_updated < cutoff:
                        to_remove.append(url)
            
            for url in to_remove:
                del self._stats[url]
            
            if to_remove:
                self._save_stats()
                logger.info(f"Cleaned up {len(to_remove)} old mirror stats")
            
            return len(to_remove)

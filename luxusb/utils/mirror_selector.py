"""Mirror selection and speed testing for downloads"""

import time
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from luxusb.utils.mirror_stats import MirrorStatsTracker
from luxusb.constants import Timeout

logger = logging.getLogger(__name__)


@dataclass
class MirrorInfo:
    """Information about a mirror"""
    url: str
    location: str = "Unknown"
    speed_ms: Optional[int] = None
    reliability_score: float = 1.0
    is_available: bool = True
    
    @property
    def display_name(self) -> str:
        """Get display name for UI"""
        if self.speed_ms is not None:
            return f"{self.location} ({self.speed_ms}ms)"
        return self.location


class MirrorSelector:
    """Select and test mirrors for optimal download performance"""
    
    def __init__(self, timeout: int = Timeout.MIRROR_TEST, use_stats: bool = True):
        """
        Initialize mirror selector
        
        Args:
            timeout: Timeout in seconds for mirror tests
            use_stats: Whether to use historical statistics for ranking
        """
        self.timeout = timeout
        self.use_stats = use_stats
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LUXusb/0.1.0'
        })
        
        # Initialize statistics tracker
        if use_stats:
            self.stats_tracker = MirrorStatsTracker()
        else:
            self.stats_tracker = None
    
    def test_mirror_speed(self, mirror_url: str, test_size_kb: int = 100) -> Optional[int]:
        """
        Test mirror response time
        
        Args:
            mirror_url: Mirror URL to test
            test_size_kb: Size in KB to download for test (0 = HEAD request only)
            
        Returns:
            Response time in milliseconds, or None if unavailable
        """
        try:
            start = time.time()
            
            if test_size_kb > 0:
                # Download small chunk to test actual speed
                response = self.session.get(
                    mirror_url,
                    stream=True,
                    timeout=self.timeout,
                    headers={'Range': f'bytes=0-{test_size_kb * 1024 - 1}'}
                )
            else:
                # Just HEAD request for availability
                response = self.session.head(mirror_url, timeout=self.timeout)
            
            response.raise_for_status()
            elapsed_ms = int((time.time() - start) * 1000)
            
            logger.debug("Mirror %s responded in %dms", mirror_url, elapsed_ms)
            return elapsed_ms
            
        except requests.exceptions.Timeout:
            logger.warning("Mirror timed out: %s", mirror_url)
            return None
        except requests.exceptions.RequestException as e:
            logger.warning("Mirror unavailable: %s - %s", mirror_url, e)
            return None
        except Exception as e:
            logger.error("Error testing mirror %s: %s", mirror_url, e)
            return None
    
    def test_mirrors_parallel(
        self,
        mirror_urls: List[str],
        max_workers: int = 5
    ) -> Dict[str, Optional[int]]:
        """
        Test multiple mirrors in parallel
        
        Args:
            mirror_urls: List of mirror URLs to test
            max_workers: Maximum number of parallel tests
            
        Returns:
            Dictionary mapping URL to response time in ms (None if failed)
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tests
            future_to_url = {
                executor.submit(self.test_mirror_speed, url): url
                for url in mirror_urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    speed_ms = future.result()
                    results[url] = speed_ms
                except Exception as e:
                    logger.error("Error testing mirror %s: %s", url, e)
                    results[url] = None
        
        return results
    
    def select_best_mirror(
        self,
        mirrors: List[str],
        test_parallel: bool = True
    ) -> Optional[str]:
        """
        Choose fastest available mirror
        
        Args:
            mirrors: List of mirror URLs
            test_parallel: Whether to test mirrors in parallel
            
        Returns:
            URL of fastest mirror, or None if all failed
        """
        if not mirrors:
            return None
        
        # If using stats, pre-rank mirrors by historical performance
        if self.use_stats and self.stats_tracker:
            # Filter out poor-performing mirrors (success rate < 50%)
            healthy_mirrors = self.stats_tracker.get_healthy_mirrors(mirrors, min_success_rate=50.0)
            if healthy_mirrors:
                mirrors = healthy_mirrors
                logger.info(f"Filtered to {len(mirrors)} healthy mirrors based on history")
            
            # Rank by historical performance
            mirrors = self.stats_tracker.rank_mirrors(mirrors)
            logger.debug(f"Pre-ranked mirrors by stats: {mirrors[:3]}")
        
        logger.info("Testing %d mirrors...", len(mirrors))
        
        if test_parallel and len(mirrors) > 1:
            results = self.test_mirrors_parallel(mirrors)
        else:
            results = {url: self.test_mirror_speed(url) for url in mirrors}
        
        # Filter available mirrors and sort by speed
        available = [(url, speed) for url, speed in results.items() if speed is not None]
        
        if not available:
            logger.warning("No mirrors available")
            return None
        
        # Sort by speed (lowest ms first)
        available.sort(key=lambda x: x[1])
        
        best_url, best_speed = available[0]
        logger.info("Selected fastest mirror: %s (%dms)", best_url, best_speed)
        
        return best_url
    
    def rank_mirrors(
        self,
        mirrors: List[str],
        test_parallel: bool = True
    ) -> List[Tuple[str, int]]:
        """
        Get ranked list of mirrors by speed
        
        Args:
            mirrors: List of mirror URLs
            test_parallel: Whether to test mirrors in parallel
            
        Returns:
            List of (url, speed_ms) tuples, sorted by speed
        """
        if test_parallel and len(mirrors) > 1:
            results = self.test_mirrors_parallel(mirrors)
        else:
            results = {url: self.test_mirror_speed(url) for url in mirrors}
        
        # Filter and sort
        ranked = [(url, speed) for url, speed in results.items() if speed is not None]
        ranked.sort(key=lambda x: x[1])
        
        return ranked
    
    def get_mirror_info(self, url: str, location: str = "Unknown") -> MirrorInfo:
        """
        Get detailed information about a mirror
        
        Args:
            url: Mirror URL
            location: Geographic location or description
            
        Returns:
            MirrorInfo object with test results
        """
        speed_ms = self.test_mirror_speed(url)
        
        return MirrorInfo(
            url=url,
            location=location,
            speed_ms=speed_ms,
            is_available=speed_ms is not None
        )
    
    def validate_mirror(self, url: str) -> bool:
        """
        Validate that a mirror is accessible
        
        Args:
            url: Mirror URL to validate
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            response = self.session.head(url, timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception:
            return False

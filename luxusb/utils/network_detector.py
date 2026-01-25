"""
Network connectivity detection and handling
"""

import logging
import socket
from typing import Tuple

logger = logging.getLogger(__name__)


class NetworkDetector:
    """Detect network connectivity for graceful offline handling"""
    
    # Well-known DNS servers for connectivity testing
    TEST_HOSTS = [
        ("8.8.8.8", 53),      # Google DNS
        ("1.1.1.1", 53),      # Cloudflare DNS
        ("208.67.222.222", 53), # OpenDNS
    ]
    
    def __init__(self, timeout: float = 3.0):
        """
        Initialize network detector
        
        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout
    
    def is_online(self) -> Tuple[bool, str]:
        """
        Check if network is available
        
        Returns:
            Tuple of (is_online, message)
        """
        # Try each test host
        for host, port in self.TEST_HOSTS:
            try:
                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                
                # Try to connect
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    logger.debug(f"Network check passed: {host}:{port}")
                    return (True, "Network available")
            
            except socket.error as e:
                logger.debug(f"Network check failed for {host}:{port}: {e}")
                continue
        
        # All hosts failed
        logger.info("No network connectivity detected")
        return (False, "Network unavailable")
    
    def check_url_accessible(self, url: str) -> Tuple[bool, str]:
        """
        Check if a specific URL is accessible
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (is_accessible, message)
        """
        import urllib.parse
        
        # Parse URL to get host
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        if not host:
            return (False, "Invalid URL")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return (True, f"{host} is accessible")
            else:
                return (False, f"{host} is not accessible (error: {result})")
        
        except socket.gaierror:
            return (False, f"Could not resolve {host}")
        except socket.error as e:
            return (False, f"Connection error: {e}")
    
    def get_connectivity_status(self) -> dict:
        """
        Get detailed connectivity status
        
        Returns:
            Dictionary with connectivity information
        """
        is_online, message = self.is_online()
        
        status = {
            "online": is_online,
            "message": message,
            "test_hosts_checked": len(self.TEST_HOSTS)
        }
        
        # If online, try to check some common package repositories
        if is_online:
            test_urls = [
                "https://releases.ubuntu.com",
                "https://download.fedoraproject.org",
                "https://mirrors.kernel.org"
            ]
            
            accessible = []
            for url in test_urls:
                is_accessible, _ = self.check_url_accessible(url)
                if is_accessible:
                    accessible.append(url)
            
            status["repositories_accessible"] = len(accessible)
            status["repositories_tested"] = len(test_urls)
        
        return status


def is_network_available(timeout: float = 3.0) -> bool:
    """
    Convenience function to quickly check network availability
    
    Args:
        timeout: Connection timeout in seconds
        
    Returns:
        True if network is available
    """
    detector = NetworkDetector(timeout=timeout)
    is_online, _ = detector.is_online()
    return is_online

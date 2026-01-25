"""Validate distro metadata on app startup"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DistroValidator:
    """Validate distro metadata freshness and integrity"""
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "distros"
        self.data_dir = Path(data_dir)
        self.stale_threshold_days = 90  # Warn if data is older than 90 days
    
    def check_metadata_freshness(self) -> Tuple[List[str], List[str]]:
        """
        Check if distro metadata is fresh
        Returns: (stale_distros, unverified_distros)
        """
        stale_distros = []
        unverified_distros = []
        
        json_files = list(self.data_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                distro_id = data['id']
                metadata = data.get('metadata', {})
                
                # Check if verified
                if not metadata.get('verified', False):
                    unverified_distros.append(distro_id)
                    logger.warning(f"{distro_id}: Not verified")
                
                # Check freshness
                last_updated = metadata.get('last_updated')
                if last_updated:
                    try:
                        update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        age_days = (datetime.now(update_date.tzinfo) - update_date).days
                        
                        if age_days > self.stale_threshold_days:
                            stale_distros.append(distro_id)
                            logger.warning(f"{distro_id}: Data is {age_days} days old")
                    except Exception as e:
                        logger.warning(f"{distro_id}: Could not parse date: {e}")
                
            except Exception as e:
                logger.error(f"Error checking {json_file.name}: {e}")
        
        return stale_distros, unverified_distros
    
    def check_placeholder_checksums(self) -> List[str]:
        """Check for placeholder/fake SHA256 checksums"""
        suspicious_distros = []
        
        # Common patterns in fake checksums
        fake_patterns = [
            'a1b2c3d4e5f6',  # Sequential hex
            '0123456789ab',  # Sequential
            '00000000',      # Zeros
            'ffffffff',      # All F's
        ]
        
        json_files = list(self.data_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                distro_id = data['id']
                
                for release in data.get('releases', []):
                    sha256 = release.get('sha256', '')
                    
                    # Check for patterns
                    for pattern in fake_patterns:
                        if pattern in sha256.lower():
                            suspicious_distros.append(f"{distro_id} ({release.get('version')})")
                            logger.warning(f"{distro_id}: Suspicious checksum pattern detected")
                            break
                    
            except Exception as e:
                logger.error(f"Error checking {json_file.name}: {e}")
        
        return suspicious_distros
    
    def validate_all(self) -> Dict[str, any]:
        """Run all validation checks"""
        stale, unverified = self.check_metadata_freshness()
        suspicious = self.check_placeholder_checksums()
        
        results = {
            'stale_distros': stale,
            'unverified_distros': unverified,
            'suspicious_checksums': suspicious,
            'needs_update': len(stale) > 0 or len(unverified) > 0 or len(suspicious) > 0
        }
        
        if results['needs_update']:
            logger.info("Some distro metadata needs updating")
            logger.info(f"  Stale: {len(stale)}")
            logger.info(f"  Unverified: {len(unverified)}")
            logger.info(f"  Suspicious checksums: {len(suspicious)}")
        else:
            logger.info("All distro metadata is up-to-date")
        
        return results


def validate_on_startup() -> bool:
    """
    Quick validation check to run on app startup
    Returns True if updates are recommended
    """
    try:
        validator = DistroValidator()
        results = validator.validate_all()
        return results['needs_update']
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False

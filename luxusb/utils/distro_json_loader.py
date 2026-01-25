"""
JSON-based distribution metadata loader
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

from luxusb.utils.distro_manager import Distro, DistroRelease

logger = logging.getLogger(__name__)


class DistroJSONLoader:
    """Load distribution metadata from JSON files"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize loader
        
        Args:
            data_dir: Directory containing distro JSON files (default: luxusb/data/distros)
        """
        if data_dir is None:
            # Default to package data directory
            package_dir = Path(__file__).parent.parent
            self.data_dir = package_dir / "data" / "distros"
        else:
            self.data_dir = Path(data_dir)
        
        self.schema_path = self.data_dir.parent / "distro-schema.json"
        self._cache: Dict[str, Distro] = {}
    
    def load_all(self) -> List[Distro]:
        """
        Load all distributions from JSON files
        
        Returns:
            List of Distro objects
        """
        distros = []
        
        if not self.data_dir.exists():
            logger.warning(f"Distro data directory not found: {self.data_dir}")
            return distros
        
        # Find all JSON files
        json_files = list(self.data_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} distro JSON files")
        
        for json_file in json_files:
            try:
                distro = self.load_distro(json_file)
                if distro:
                    distros.append(distro)
            except Exception as e:
                logger.error(f"Failed to load {json_file.name}: {e}")
                continue
        
        # Sort by popularity rank
        distros.sort(key=lambda d: d.popularity_rank)
        
        logger.info(f"Loaded {len(distros)} distributions")
        return distros
    
    def load_distro(self, file_path: Path) -> Optional[Distro]:
        """
        Load a single distribution from JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Distro object or None if loading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            required = ['id', 'name', 'description', 'homepage', 'category', 
                       'popularity_rank', 'releases']
            for field in required:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in {file_path.name}")
                    return None
            
            # Parse releases
            releases = []
            for rel_data in data['releases']:
                try:
                    release = self._parse_release(rel_data)
                    releases.append(release)
                except Exception as e:
                    logger.error(f"Failed to parse release in {file_path.name}: {e}")
                    continue
            
            if not releases:
                logger.warning(f"No valid releases found in {file_path.name}")
                return None
            
            # Create Distro object
            distro = Distro(
                id=data['id'],
                name=data['name'],
                description=data['description'],
                homepage=data['homepage'],
                logo_url=data.get('logo_url', ''),
                category=data['category'],
                popularity_rank=data['popularity_rank'],
                releases=releases,
                family=data.get('family'),  # Optional family field
                base_distro=data.get('base_distro'),  # Optional base_distro field
                secure_boot_compatible=data.get('secure_boot_compatible', False)  # Secure Boot compatibility
            )
            
            logger.debug(f"Loaded distro: {distro.name} ({len(releases)} releases)")
            return distro
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            return None
    
    def _parse_release(self, data: dict) -> DistroRelease:
        """
        Parse a release from JSON data
        
        Args:
            data: Release JSON data
            
        Returns:
            DistroRelease object
            
        Raises:
            ValueError: If required fields are missing
        """
        required = ['version', 'release_date', 'iso_url', 'sha256', 'size_mb']
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate SHA256 format (allow special placeholder for manual verification)
        sha256 = data['sha256']
        if not isinstance(sha256, str):
            raise ValueError(f"Invalid SHA256 checksum: {sha256}")
        
        # Allow either 64-char hex or special manual verification placeholder
        if sha256 != "REQUIRES_MANUAL_VERIFICATION" and len(sha256) != 64:
            raise ValueError(f"Invalid SHA256 checksum: {sha256}")
        
        # Parse mirrors (optional)
        mirrors = data.get('mirrors', [])
        if not isinstance(mirrors, list):
            mirrors = []
        
        return DistroRelease(
            version=data['version'],
            release_date=data['release_date'],
            iso_url=data['iso_url'],
            sha256=sha256,
            size_mb=data['size_mb'],
            architecture=data.get('architecture', 'x86_64'),
            mirrors=mirrors
        )
    
    def get_distro_by_id(self, distro_id: str) -> Optional[Distro]:
        """
        Get a specific distribution by ID
        
        Args:
            distro_id: Distribution ID (e.g., 'ubuntu')
            
        Returns:
            Distro object or None if not found
        """
        # Check cache first
        if distro_id in self._cache:
            return self._cache[distro_id]
        
        # Load from file
        json_file = self.data_dir / f"{distro_id}.json"
        if not json_file.exists():
            logger.warning(f"Distro file not found: {json_file}")
            return None
        
        distro = self.load_distro(json_file)
        if distro:
            self._cache[distro_id] = distro
        
        return distro
    
    def validate_schema(self, file_path: Path) -> bool:
        """
        Validate a distro JSON file against the schema
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            True if valid, False otherwise
            
        Note:
            Requires jsonschema package for validation
        """
        try:
            import jsonschema
        except ImportError:
            logger.warning("jsonschema package not available, skipping validation")
            return True
        
        try:
            # Load schema
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Load distro data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate
            jsonschema.validate(data, schema)
            logger.debug(f"Schema validation passed: {file_path.name}")
            return True
            
        except jsonschema.ValidationError as e:
            logger.error(f"Schema validation failed for {file_path.name}: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Validation error for {file_path.name}: {e}")
            return False


# Global loader instance
_loader = None


def get_distro_loader() -> DistroJSONLoader:
    """Get singleton distro loader instance"""
    global _loader
    if _loader is None:
        _loader = DistroJSONLoader()
    return _loader


def load_all_distros() -> List[Distro]:
    """
    Load all distributions from JSON files
    
    Returns:
        List of Distro objects sorted by popularity
    """
    loader = get_distro_loader()
    return loader.load_all()


def get_distro_by_id(distro_id: str) -> Optional[Distro]:
    """
    Get a specific distribution by ID
    
    Args:
        distro_id: Distribution ID (e.g., 'ubuntu')
        
    Returns:
        Distro object or None if not found
    """
    loader = get_distro_loader()
    return loader.get_distro_by_id(distro_id)

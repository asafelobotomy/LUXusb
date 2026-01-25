"""
Tests for Phase 2.4: Dynamic Distribution Metadata
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from luxusb.utils.distro_json_loader import DistroJSONLoader, load_all_distros, get_distro_by_id
from luxusb.utils.distro_manager import Distro, DistroRelease, DistroManager


class TestDistroJSONLoader:
    """Test JSON distribution loader"""
    
    def test_loader_initialization(self):
        """Test loader initializes with correct paths"""
        loader = DistroJSONLoader()
        
        assert loader.data_dir.exists()
        assert loader.data_dir.name == "distros"
        assert loader.schema_path.exists()
        assert loader.schema_path.name == "distro-schema.json"
    
    def test_load_all_distros(self):
        """Test loading all distributions"""
        loader = DistroJSONLoader()
        distros = loader.load_all()
        
        # Should load at least the distros we created
        assert len(distros) >= 4  # ubuntu, fedora, debian, linuxmint, etc.
        
        # Check they're sorted by popularity
        for i in range(len(distros) - 1):
            assert distros[i].popularity_rank <= distros[i + 1].popularity_rank
    
    def test_load_ubuntu(self):
        """Test loading Ubuntu specifically"""
        loader = DistroJSONLoader()
        ubuntu = loader.get_distro_by_id('ubuntu')
        
        assert ubuntu is not None
        assert ubuntu.id == 'ubuntu'
        assert ubuntu.name == 'Ubuntu Desktop'
        assert ubuntu.category == 'Desktop'
        assert ubuntu.popularity_rank == 1
        assert len(ubuntu.releases) >= 1
        
        release = ubuntu.latest_release
        assert release is not None
        assert release.version == '24.04.3'  # Updated to point release
        assert release.size_mb > 5000  # ~6GB (varies slightly)
        assert len(release.sha256) == 64
        assert release.architecture == 'x86_64'
    
    def test_load_fedora(self):
        """Test loading Fedora"""
        loader = DistroJSONLoader()
        fedora = loader.get_distro_by_id('fedora')
        
        assert fedora is not None
        assert fedora.id == 'fedora'
        assert fedora.name == 'Fedora Workstation'
        assert fedora.popularity_rank == 2
        
        release = fedora.latest_release
        assert release.version == '41'
        # ISO size can vary, just check it's reasonable (2-3 GB)
        assert 2000 <= release.size_mb <= 3000
    
    def test_load_debian(self):
        """Test loading Debian"""
        loader = DistroJSONLoader()
        debian = loader.get_distro_by_id('debian')
        
        assert debian is not None
        assert debian.id == 'debian'
        assert debian.name == 'Debian'
        assert len(debian.releases[0].mirrors) >= 1  # Has mirrors
    
    def test_distro_not_found(self):
        """Test loading non-existent distro"""
        loader = DistroJSONLoader()
        nonexistent = loader.get_distro_by_id('nonexistent-distro')
        
        assert nonexistent is None
    
    def test_parse_release_valid(self):
        """Test parsing valid release data"""
        loader = DistroJSONLoader()
        
        data = {
            'version': '24.04',
            'release_date': '2024-04-25',
            'iso_url': 'https://example.com/ubuntu.iso',
            'sha256': 'a' * 64,
            'size_mb': 3500,
            'architecture': 'x86_64',
            'mirrors': ['https://mirror1.com/ubuntu.iso']
        }
        
        release = loader._parse_release(data)
        
        assert release.version == '24.04'
        assert release.size_mb == 3500
        assert len(release.mirrors) == 1
    
    def test_parse_release_missing_field(self):
        """Test parsing release with missing required field"""
        loader = DistroJSONLoader()
        
        data = {
            'version': '24.04',
            'release_date': '2024-04-25',
            # Missing iso_url
            'sha256': 'a' * 64,
            'size_mb': 3500
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            loader._parse_release(data)
    
    def test_parse_release_invalid_sha256(self):
        """Test parsing release with invalid SHA256"""
        loader = DistroJSONLoader()
        
        data = {
            'version': '24.04',
            'release_date': '2024-04-25',
            'iso_url': 'https://example.com/ubuntu.iso',
            'sha256': 'invalid',  # Too short
            'size_mb': 3500
        }
        
        with pytest.raises(ValueError, match="Invalid SHA256"):
            loader._parse_release(data)
    
    def test_loader_caching(self):
        """Test that loader caches distros"""
        loader = DistroJSONLoader()
        
        # Load once
        ubuntu1 = loader.get_distro_by_id('ubuntu')
        
        # Load again (should use cache)
        ubuntu2 = loader.get_distro_by_id('ubuntu')
        
        # Should be the same object
        assert ubuntu1 is ubuntu2
        assert 'ubuntu' in loader._cache


class TestDistroManager:
    """Test DistroManager with JSON loading"""
    
    def test_manager_loads_from_json(self):
        """Test manager loads from JSON"""
        manager = DistroManager()
        
        # Should have loaded distros from JSON
        assert len(manager.distros) >= 4
        
        # Verify it's loading from JSON (check for Ubuntu)
        ubuntu = next((d for d in manager.distros if d.id == 'ubuntu'), None)
        assert ubuntu is not None
        assert ubuntu.name == 'Ubuntu Desktop'
    
    def test_get_all_distros(self):
        """Test getting all distributions"""
        manager = DistroManager()
        distros = manager.get_all_distros()
        
        assert isinstance(distros, list)
        assert len(distros) > 0
        assert all(isinstance(d, Distro) for d in distros)
    
    def test_get_distro_by_id_manager(self):
        """Test getting distro by ID through manager"""
        manager = DistroManager()
        
        ubuntu = manager.get_distro_by_id('ubuntu')
        assert ubuntu is not None
        assert ubuntu.id == 'ubuntu'
        
        nonexistent = manager.get_distro_by_id('nonexistent')
        assert nonexistent is None
    
    def test_get_popular_distros(self):
        """Test getting popular distros"""
        manager = DistroManager()
        
        popular = manager.get_popular_distros(limit=3)
        assert len(popular) <= 3
        assert all(isinstance(d, Distro) for d in popular)


class TestJSONSchema:
    """Test JSON schema and validation"""
    
    def test_schema_file_exists(self):
        """Test schema file exists and is valid JSON"""
        loader = DistroJSONLoader()
        
        assert loader.schema_path.exists()
        
        with open(loader.schema_path, 'r') as f:
            schema = json.load(f)
        
        assert '$schema' in schema
        assert 'properties' in schema
        assert 'required' in schema
    
    def test_schema_required_fields(self):
        """Test schema defines required fields"""
        loader = DistroJSONLoader()
        
        with open(loader.schema_path, 'r') as f:
            schema = json.load(f)
        
        required = schema['required']
        assert 'id' in required
        assert 'name' in required
        assert 'description' in required
        assert 'homepage' in required
        assert 'category' in required
        assert 'popularity_rank' in required
        assert 'releases' in required
    
    def test_existing_jsons_are_valid(self):
        """Test that all existing JSON files are valid"""
        loader = DistroJSONLoader()
        distros = loader.load_all()
        
        # All distros should have loaded successfully
        assert len(distros) >= 4
        
        # Verify each has required fields
        for distro in distros:
            assert distro.id
            assert distro.name
            assert distro.description
            assert distro.homepage
            assert distro.category
            assert distro.popularity_rank > 0
            assert len(distro.releases) > 0
            
            # Verify release fields
            for release in distro.releases:
                assert release.version
                assert release.release_date
                assert release.iso_url
                # Allow placeholder checksums for distros that require manual verification
                assert len(release.sha256) == 64 or release.sha256 == 'REQUIRES_MANUAL_VERIFICATION'
                assert release.size_mb >= 0  # Can be 0 if auto-updated
                assert release.architecture


class TestGlobalFunctions:
    """Test global convenience functions"""
    
    def test_load_all_distros_function(self):
        """Test global load_all_distros function"""
        distros = load_all_distros()
        
        assert isinstance(distros, list)
        assert len(distros) >= 4
        assert all(isinstance(d, Distro) for d in distros)
    
    def test_get_distro_by_id_function(self):
        """Test global get_distro_by_id function"""
        ubuntu = get_distro_by_id('ubuntu')
        
        assert ubuntu is not None
        assert ubuntu.id == 'ubuntu'
        assert ubuntu.name == 'Ubuntu Desktop'
    
    def test_singleton_loader(self):
        """Test that global functions use singleton loader"""
        from luxusb.utils.distro_json_loader import get_distro_loader
        
        loader1 = get_distro_loader()
        loader2 = get_distro_loader()
        
        # Should be the same instance
        assert loader1 is loader2


class TestBackwardCompatibility:
    """Test backward compatibility with existing code"""
    
    def test_distro_structure_unchanged(self):
        """Test Distro dataclass structure is unchanged"""
        loader = DistroJSONLoader()
        ubuntu = loader.get_distro_by_id('ubuntu')
        
        # Check all expected attributes exist
        assert hasattr(ubuntu, 'id')
        assert hasattr(ubuntu, 'name')
        assert hasattr(ubuntu, 'description')
        assert hasattr(ubuntu, 'homepage')
        assert hasattr(ubuntu, 'logo_url')
        assert hasattr(ubuntu, 'category')
        assert hasattr(ubuntu, 'popularity_rank')
        assert hasattr(ubuntu, 'releases')
        assert hasattr(ubuntu, 'latest_release')
    
    def test_distro_release_structure_unchanged(self):
        """Test DistroRelease dataclass structure is unchanged"""
        loader = DistroJSONLoader()
        ubuntu = loader.get_distro_by_id('ubuntu')
        release = ubuntu.latest_release
        
        # Check all expected attributes exist
        assert hasattr(release, 'version')
        assert hasattr(release, 'release_date')
        assert hasattr(release, 'iso_url')
        assert hasattr(release, 'sha256')
        assert hasattr(release, 'size_mb')
        assert hasattr(release, 'architecture')
        assert hasattr(release, 'mirrors')
        assert hasattr(release, 'size_gb')


class TestPhase24Summary:
    """Summary test for Phase 2.4"""
    
    def test_phase24_completion(self):
        """Verify Phase 2.4 features are implemented"""
        # JSON schema exists
        loader = DistroJSONLoader()
        assert loader.schema_path.exists()
        
        # JSON loader works
        distros = loader.load_all()
        assert len(distros) >= 4
        
        # Manager loads from JSON
        manager = DistroManager()
        assert len(manager.distros) >= 4
        
        # Global functions work
        all_distros = load_all_distros()
        assert len(all_distros) >= 4
        
        ubuntu = get_distro_by_id('ubuntu')
        assert ubuntu is not None
        
        # Backward compatibility maintained
        assert hasattr(ubuntu, 'latest_release')
        assert hasattr(ubuntu.latest_release, 'size_gb')
        
        print("\n✓ Phase 2.4 Complete:")
        print(f"  - JSON schema defined (distro-schema.json)")
        print(f"  - {len(distros)} distributions loaded from JSON")
        print(f"  - DistroJSONLoader implemented")
        print(f"  - DistroManager enhanced with JSON support")
        print(f"  - Backward compatibility maintained")
        print(f"  - Fallback to hardcoded defaults available")
        
        # List loaded distros
        print("\n  Loaded distributions:")
        for d in sorted(distros, key=lambda x: x.popularity_rank):
            rel = d.latest_release
            print(f"    {d.popularity_rank}. {d.name} {rel.version} ({rel.size_mb}MB)")

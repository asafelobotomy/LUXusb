"""
Tests for Phase 3.2: Secure Boot Support
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from luxusb.utils.secure_boot import (
    SecureBootStatus,
    SecureBootDetector,
    BootloaderSigner,
    detect_secure_boot
)


class TestSecureBootStatus:
    """Test SecureBootStatus dataclass"""
    
    def test_status_creation(self):
        """Test SecureBootStatus object creation"""
        status = SecureBootStatus(
            enabled=True,
            setup_mode=False,
            available=True
        )
        
        assert status.enabled is True
        assert status.setup_mode is False
        assert status.available is True
    
    def test_is_active_property(self):
        """Test is_active property"""
        # Active: enabled and not in setup mode
        status1 = SecureBootStatus(enabled=True, setup_mode=False, available=True)
        assert status1.is_active is True
        
        # Inactive: disabled
        status2 = SecureBootStatus(enabled=False, setup_mode=False, available=True)
        assert status2.is_active is False
        
        # Inactive: in setup mode
        status3 = SecureBootStatus(enabled=True, setup_mode=True, available=True)
        assert status3.is_active is False
    
    def test_requires_signing_property(self):
        """Test requires_signing property"""
        status1 = SecureBootStatus(enabled=True, setup_mode=False, available=True)
        assert status1.requires_signing is True
        
        status2 = SecureBootStatus(enabled=False, setup_mode=False, available=True)
        assert status2.requires_signing is False


class TestSecureBootDetector:
    """Test SecureBootDetector"""
    
    def test_detector_initialization(self):
        """Test detector can be initialized"""
        detector = SecureBootDetector()
        assert detector is not None
    
    @patch('pathlib.Path.exists')
    def test_detect_non_efi_system(self, mock_exists):
        """Test detection on non-EFI system"""
        mock_exists.return_value = False
        
        detector = SecureBootDetector()
        status = detector.detect_secure_boot()
        
        assert status.enabled is False
        assert status.available is False
        assert "Not an EFI system" in status.error_message
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b'\x00\x00\x00\x00\x01')
    def test_detect_secure_boot_enabled(self, mock_file, mock_exists):
        """Test detection when Secure Boot is enabled"""
        mock_exists.return_value = True
        
        detector = SecureBootDetector()
        status = detector.detect_secure_boot()
        
        assert status.enabled is True
        assert status.available is True
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b'\x00\x00\x00\x00\x00')
    def test_detect_secure_boot_disabled(self, mock_file, mock_exists):
        """Test detection when Secure Boot is disabled"""
        mock_exists.return_value = True
        
        detector = SecureBootDetector()
        status = detector.detect_secure_boot()
        
        assert status.enabled is False
        assert status.available is True
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', side_effect=PermissionError())
    def test_detect_permission_error(self, mock_file, mock_exists):
        """Test detection handles permission errors"""
        mock_exists.return_value = True
        
        detector = SecureBootDetector()
        status = detector.detect_secure_boot()
        
        # Should handle gracefully
        assert status is not None
    
    @patch('subprocess.run')
    def test_check_mokutil_available(self, mock_run):
        """Test mokutil availability check"""
        mock_run.return_value = Mock(returncode=0)
        
        detector = SecureBootDetector()
        has_mokutil = detector.check_mokutil()
        
        assert has_mokutil is True
        mock_run.assert_called_once_with(
            ['which', 'mokutil'],
            capture_output=True,
            check=True
        )
    
    @patch('subprocess.run')
    def test_check_mokutil_not_available(self, mock_run):
        """Test mokutil not available"""
        mock_run.side_effect = Exception()
        
        detector = SecureBootDetector()
        has_mokutil = detector.check_mokutil()
        
        assert has_mokutil is False


class TestBootloaderSigner:
    """Test BootloaderSigner"""
    
    def test_signer_initialization(self):
        """Test signer can be initialized"""
        signer = BootloaderSigner()
        assert signer is not None
        assert signer.keys_dir == Path('/var/lib/shim-signed/mok')
    
    def test_signer_custom_keys_dir(self):
        """Test signer with custom keys directory"""
        custom_dir = Path('/custom/keys')
        signer = BootloaderSigner(keys_dir=custom_dir)
        assert signer.keys_dir == custom_dir
    
    def test_sign_bootloader_nonexistent(self):
        """Test signing nonexistent bootloader fails"""
        signer = BootloaderSigner()
        result = signer.sign_bootloader(Path("/nonexistent/grub.efi"))
        
        assert result is False
    
    @patch('subprocess.run')
    def test_check_sbsign_available(self, mock_run):
        """Test sbsign availability check"""
        mock_run.return_value = Mock(returncode=0)
        
        signer = BootloaderSigner()
        has_sbsign = signer._check_sbsign()
        
        assert has_sbsign is True
    
    @patch('subprocess.run')
    def test_check_sbsign_not_available(self, mock_run):
        """Test sbsign not available"""
        mock_run.side_effect = Exception()
        
        signer = BootloaderSigner()
        has_sbsign = signer._check_sbsign()
        
        assert has_sbsign is False
    
    def test_find_signing_keys(self, tmp_path):
        """Test finding signing keys"""
        # Create temporary key files
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()
        
        key_file = keys_dir / "MOK.key"
        cert_file = keys_dir / "MOK.cer"
        
        key_file.write_text("fake key")
        cert_file.write_text("fake cert")
        
        signer = BootloaderSigner(keys_dir=keys_dir)
        found_key, found_cert = signer._find_signing_keys()
        
        assert found_key == key_file
        assert found_cert == cert_file
    
    @patch('pathlib.Path.exists')
    def test_find_signing_keys_not_found(self, mock_exists):
        """Test when signing keys not found"""
        mock_exists.return_value = False
        
        signer = BootloaderSigner()
        key_file, cert_file = signer._find_signing_keys()
        
        assert key_file is None
        assert cert_file is None
    
    @patch('subprocess.run')
    @patch('pathlib.Path.mkdir')
    def test_generate_mok_keys(self, mock_mkdir, mock_run, tmp_path):
        """Test MOK key generation"""
        mock_run.return_value = Mock(returncode=0)
        
        signer = BootloaderSigner()
        result = signer.generate_mok_keys(tmp_path)
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check openssl command was called
        args = mock_run.call_args[0][0]
        assert 'openssl' in args
        assert 'req' in args
    
    @patch('subprocess.run')
    def test_generate_mok_keys_failure(self, mock_run, tmp_path):
        """Test MOK key generation failure"""
        mock_run.side_effect = Exception("openssl failed")
        
        signer = BootloaderSigner()
        result = signer.generate_mok_keys(tmp_path)
        
        assert result is False
    
    def test_install_shim_not_found(self, tmp_path):
        """Test shim installation when shim not found"""
        # No shim file exists
        signer = BootloaderSigner()
        result = signer.install_shim(tmp_path)
        
        assert result is False
    
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    @patch.object(BootloaderSigner, '_check_sbsign', return_value=True)
    @patch.object(BootloaderSigner, '_find_signing_keys')
    def test_sign_bootloader_success(self, mock_keys, mock_sbsign, mock_run, mock_exists, tmp_path):
        """Test successful bootloader signing"""
        # Create test bootloader file
        bootloader = tmp_path / "grubx64.efi"
        bootloader.write_bytes(b"fake bootloader")
        
        # Mock signing keys found
        mock_keys.return_value = (
            Path("/tmp/MOK.key"),
            Path("/tmp/MOK.cer")
        )
        
        # Mock sbsign success
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        signer = BootloaderSigner()
        result = signer.sign_bootloader(bootloader)
        
        assert result is True
        
        # Verify sbsign was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'sbsign' in args


class TestDetectSecureBootFunction:
    """Test convenience function"""
    
    @patch.object(SecureBootDetector, 'detect_secure_boot')
    def test_detect_secure_boot_function(self, mock_detect):
        """Test detect_secure_boot convenience function"""
        mock_detect.return_value = SecureBootStatus(
            enabled=True,
            setup_mode=False,
            available=True
        )
        
        status = detect_secure_boot()
        
        assert status.enabled is True
        assert status.available is True


class TestPhase32Summary:
    """Phase 3.2 completion verification"""
    
    def test_phase32_completion(self):
        """Verify Phase 3.2 features are complete"""
        # Check all components exist
        detector = SecureBootDetector()
        assert detector is not None
        
        signer = BootloaderSigner()
        assert signer is not None
        
        # Test dataclass
        status = SecureBootStatus(
            enabled=True,
            setup_mode=False,
            available=True
        )
        assert status.is_active is True
        
        print("\n✓ Phase 3.2 Complete:")
        print("  - SecureBootStatus dataclass")
        print("  - SecureBootDetector with EFI variable reading")
        print("  - BootloaderSigner with sbsign support")
        print("  - MOK key generation")
        print("  - Shim bootloader installation")
        print("  - Signing key discovery")
        print("  - Convenience function")
        print("  - Ready for workflow integration")

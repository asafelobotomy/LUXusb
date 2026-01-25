"""
Unit tests for USB device detection
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from luxusb.utils.usb_detector import USBDevice, USBDetector


class TestUSBDevice:
    """Test USBDevice dataclass"""
    
    def test_size_gb_calculation(self):
        """Test size conversion to GB"""
        device = USBDevice(
            device="/dev/sdb",
            size_bytes=16_000_000_000,  # 16 GB
            model="Test USB",
            vendor="TestVendor",
            serial="12345",
            partitions=[],
            is_mounted=False,
            mount_points=[]
        )
        
        assert device.size_gb == pytest.approx(14.90, rel=0.1)
    
    def test_display_name(self):
        """Test display name generation"""
        device = USBDevice(
            device="/dev/sdb",
            size_bytes=16_000_000_000,
            model="Flash Drive",
            vendor="SanDisk",
            serial="ABC123",
            partitions=[],
            is_mounted=False,
            mount_points=[]
        )
        
        name = device.display_name
        assert "SanDisk" in name
        assert "Flash Drive" in name
        assert "/dev/sdb" in name
        assert "GB" in name


class TestUSBDetector:
    """Test USBDetector class"""
    
    @patch('subprocess.run')
    def test_scan_devices_success(self, mock_run):
        """Test successful device scanning"""
        # Mock lsblk output
        mock_run.return_value = Mock(
            stdout="""{
                "blockdevices": [
                    {
                        "name": "sdb",
                        "size": 16000000000,
                        "type": "disk",
                        "tran": "usb",
                        "vendor": "SanDisk",
                        "model": "Ultra",
                        "serial": "123456",
                        "mountpoint": null,
                        "children": []
                    }
                ]
            }""",
            returncode=0
        )
        
        detector = USBDetector()
        devices = detector.scan_devices()
        
        assert len(devices) == 1
        assert devices[0].device == "/dev/sdb"
        assert devices[0].vendor == "SanDisk"
        assert devices[0].model == "Ultra"
    
    @patch('subprocess.run')
    def test_scan_devices_filters_non_usb(self, mock_run):
        """Test that non-USB devices are filtered out"""
        mock_run.return_value = Mock(
            stdout="""{
                "blockdevices": [
                    {
                        "name": "sda",
                        "size": 500000000000,
                        "type": "disk",
                        "tran": "sata",
                        "vendor": "Samsung",
                        "model": "SSD 860",
                        "serial": "789",
                        "mountpoint": null,
                        "children": []
                    }
                ]
            }""",
            returncode=0
        )
        
        detector = USBDetector()
        devices = detector.scan_devices()
        
        assert len(devices) == 0
    
    def test_is_system_disk(self):
        """Test system disk detection"""
        detector = USBDetector()
        
        # System disk (mounted at /)
        system_device = USBDevice(
            device="/dev/sda",
            size_bytes=500_000_000_000,
            model="System SSD",
            vendor="Samsung",
            serial="SYS123",
            partitions=["/dev/sda1", "/dev/sda2"],
            is_mounted=True,
            mount_points=["/", "/boot"]
        )
        
        assert detector.is_system_disk(system_device) is True
        
        # Regular USB (not system disk)
        usb_device = USBDevice(
            device="/dev/sdb",
            size_bytes=16_000_000_000,
            model="USB Drive",
            vendor="SanDisk",
            serial="USB123",
            partitions=[],
            is_mounted=False,
            mount_points=[]
        )
        
        assert detector.is_system_disk(usb_device) is False
    
    def test_validate_device(self):
        """Test device validation"""
        detector = USBDetector()
        
        # Valid device
        valid_device = USBDevice(
            device="/dev/sdb",
            size_bytes=16_000_000_000,
            model="USB Drive",
            vendor="SanDisk",
            serial="USB123",
            partitions=[],
            is_mounted=False,
            mount_points=[]
        )
        
        with patch('pathlib.Path.exists', return_value=True):
            is_valid, error = detector.validate_device(valid_device)
            assert is_valid is True
            assert error == ""
        
        # Too small device
        small_device = USBDevice(
            device="/dev/sdb",
            size_bytes=4_000_000_000,  # 4 GB
            model="Small USB",
            vendor="Generic",
            serial="SMALL123",
            partitions=[],
            is_mounted=False,
            mount_points=[]
        )
        
        is_valid, error = detector.validate_device(small_device)
        assert is_valid is False
        assert "too small" in error.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

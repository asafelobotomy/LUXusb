# Test fixtures and configuration
import pytest


@pytest.fixture
def mock_usb_device():
    """Create a mock USB device for testing"""
    from luxusb.utils.usb_detector import USBDevice
    
    return USBDevice(
        device="/dev/sdb",
        size_bytes=16_000_000_000,
        model="Test USB Drive",
        vendor="TestVendor",
        serial="TEST123",
        partitions=[],
        is_mounted=False,
        mount_points=[]
    )


@pytest.fixture
def mock_distro():
    """Create a mock distribution for testing"""
    from luxusb.utils.distro_manager import Distro, DistroRelease
    
    return Distro(
        id="testdistro",
        name="Test Linux",
        description="A test distribution",
        homepage="https://test.linux",
        logo_url="https://test.linux/logo.png",
        category="Test",
        popularity_rank=999,
        releases=[
            DistroRelease(
                version="1.0",
                release_date="2024-01-01",
                iso_url="https://test.linux/test-1.0.iso",
                sha256="0" * 64,
                size_mb=1000,
            )
        ]
    )

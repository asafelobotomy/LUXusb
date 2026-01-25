"""
LUXusb - Create bootable USB drives with multiple Linux distributions
"""

from luxusb._version import __version__, get_version_string, get_full_version_info

__author__ = "LUXusb Team"
__license__ = "GPL-3.0"

# Application metadata
APP_NAME = "LUXusb"
APP_ID = "org.luxusb.LUXusb"
APP_DESCRIPTION = "Create bootable USB drives with multiple Linux distributions"

# Minimum requirements
MIN_USB_SIZE_GB = 8
MIN_PYTHON_VERSION = (3, 10)

# Supported architectures
SUPPORTED_ARCHS = ["x86_64", "amd64"]

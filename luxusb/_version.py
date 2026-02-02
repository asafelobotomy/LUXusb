"""
LUXusb Version Information

This is the single source of truth for version information.
All other files should import from here.
"""

__version__ = "0.6.3"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# Version metadata
VERSION_MAJOR = __version_info__[0]
VERSION_MINOR = __version_info__[1]
VERSION_PATCH = __version_info__[2]

# Release information
RELEASE_DATE = "2026-01-23"
RELEASE_NAME = "Logo Enhancement Release"
IS_DEV = False  # Set to True for development versions

def get_version_string(include_dev: bool = True) -> str:
    """Get formatted version string"""
    version = __version__
    if IS_DEV and include_dev:
        version += "-dev"
    return version

def get_full_version_info() -> dict:
    """Get complete version information as dictionary"""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "release_date": RELEASE_DATE,
        "release_name": RELEASE_NAME,
        "is_dev": IS_DEV,
        "version_string": get_version_string(),
    }

#!/usr/bin/env python3
"""
Version Management Utility

Usage:
    python scripts/version.py                    # Show current version
    python scripts/version.py --bump major       # Bump major version (1.0.0 -> 2.0.0)
    python scripts/version.py --bump minor       # Bump minor version (1.0.0 -> 1.1.0)
    python scripts/version.py --bump patch       # Bump patch version (1.0.0 -> 1.0.1)
    python scripts/version.py --set 1.2.3        # Set specific version
    python scripts/version.py --dev              # Toggle dev status
    python scripts/version.py --release "Name"   # Set release name
"""

import argparse
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from luxusb._version import (
    __version__,
    __version_info__,
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
    RELEASE_DATE,
    RELEASE_NAME,
    IS_DEV,
    get_version_string,
    get_full_version_info
)


def read_version_file() -> str:
    """Read the _version.py file"""
    version_file = Path(__file__).parent.parent / "luxusb" / "_version.py"
    return version_file.read_text()


def write_version_file(content: str) -> None:
    """Write updated content to _version.py"""
    version_file = Path(__file__).parent.parent / "luxusb" / "_version.py"
    version_file.write_text(content)
    print(f"✅ Updated {version_file}")


def update_version(new_version: str, release_name: str = None, is_dev: bool = None) -> None:
    """Update version in _version.py"""
    content = read_version_file()
    
    # Update version
    content = content.replace(
        f'__version__ = "{__version__}"',
        f'__version__ = "{new_version}"'
    )
    
    # Update release date to today
    today = date.today().isoformat()
    content = content.replace(
        f'RELEASE_DATE = "{RELEASE_DATE}"',
        f'RELEASE_DATE = "{today}"'
    )
    
    # Update release name if provided
    if release_name:
        content = content.replace(
            f'RELEASE_NAME = "{RELEASE_NAME}"',
            f'RELEASE_NAME = "{release_name}"'
        )
    
    # Update dev status if provided
    if is_dev is not None:
        content = content.replace(
            f'IS_DEV = {IS_DEV}',
            f'IS_DEV = {is_dev}'
        )
    
    write_version_file(content)


def bump_version(component: str) -> str:
    """Bump version component (major, minor, or patch)"""
    major, minor, patch = VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
    
    if component == "major":
        major += 1
        minor = 0
        patch = 0
    elif component == "minor":
        minor += 1
        patch = 0
    elif component == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid component: {component}")
    
    return f"{major}.{minor}.{patch}"


def toggle_dev() -> None:
    """Toggle development status"""
    content = read_version_file()
    new_status = not IS_DEV
    content = content.replace(
        f'IS_DEV = {IS_DEV}',
        f'IS_DEV = {new_status}'
    )
    write_version_file(content)
    print(f"Dev status: {IS_DEV} -> {new_status}")


def show_version() -> None:
    """Display current version information"""
    info = get_full_version_info()
    
    print("╔═══════════════════════════════════════════╗")
    print("║         LUXusb Version Information        ║")
    print("╚═══════════════════════════════════════════╝")
    print()
    print(f"  Version:      {info['version_string']}")
    print(f"  Release Date: {info['release_date']}")
    print(f"  Release Name: {info['release_name']}")
    print(f"  Development:  {'Yes' if info['is_dev'] else 'No'}")
    print()
    print(f"  Major: {info['major']}")
    print(f"  Minor: {info['minor']}")
    print(f"  Patch: {info['patch']}")


def main():
    parser = argparse.ArgumentParser(description="LUXusb Version Management")
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Bump version component"
    )
    group.add_argument(
        "--set",
        metavar="VERSION",
        help="Set specific version (e.g., 1.2.3)"
    )
    group.add_argument(
        "--dev",
        action="store_true",
        help="Toggle development status"
    )
    
    parser.add_argument(
        "--release",
        metavar="NAME",
        help="Set release name"
    )
    
    args = parser.parse_args()
    
    if args.bump:
        new_version = bump_version(args.bump)
        update_version(new_version, args.release)
        print(f"✅ Version bumped: {__version__} -> {new_version}")
        if args.release:
            print(f"✅ Release name: {args.release}")
    
    elif args.set:
        # Validate version format
        parts = args.set.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            print("❌ Error: Version must be in format X.Y.Z (e.g., 1.2.3)")
            sys.exit(1)
        
        update_version(args.set, args.release)
        print(f"✅ Version set: {__version__} -> {args.set}")
        if args.release:
            print(f"✅ Release name: {args.release}")
    
    elif args.dev:
        toggle_dev()
    
    elif args.release:
        update_version(__version__, args.release)
        print(f"✅ Release name updated: {args.release}")
    
    else:
        show_version()


if __name__ == "__main__":
    main()

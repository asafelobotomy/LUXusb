# Version Management Guide

## Overview

LUXusb uses a centralized version management system. All version information is stored in `luxusb/_version.py` as the single source of truth.

## Version Format

We follow [Semantic Versioning](https://semver.org/):
- **Major.Minor.Patch** (e.g., 1.2.3)
- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

## How It Works

### Single Source of Truth

**`luxusb/_version.py`** - Contains:
- `__version__` - Version string (e.g., "0.2.0")
- `__version_info__` - Version tuple (e.g., (0, 2, 0))
- `VERSION_MAJOR`, `VERSION_MINOR`, `VERSION_PATCH` - Individual components
- `RELEASE_DATE` - Release date (ISO format)
- `RELEASE_NAME` - Human-readable release name
- `IS_DEV` - Development status flag

### Files That Use Version

1. **`luxusb/__init__.py`** - Imports and exposes version
2. **`pyproject.toml`** - Reads version dynamically via setuptools
3. **`scripts/build-appimage.sh`** - Extracts version for AppImage filename
4. **Any Python code** - Can import from `luxusb._version`

## Usage

### View Current Version

```bash
python scripts/version.py
```

Output:
```
╔═══════════════════════════════════════════╗
║         LUXusb Version Information        ║
╚═══════════════════════════════════════════╝

  Version:      0.2.0
  Release Date: 2026-01-23
  Release Name: Logo Enhancement Release
  Development:  No

  Major: 0
  Minor: 2
  Patch: 0
```

### Bump Version

```bash
# Bump patch version (0.2.0 -> 0.2.1)
python scripts/version.py --bump patch

# Bump minor version (0.2.0 -> 0.3.0)
python scripts/version.py --bump minor

# Bump major version (0.2.0 -> 1.0.0)
python scripts/version.py --bump major
```

### Set Specific Version

```bash
python scripts/version.py --set 1.2.3
```

### Update Release Name

```bash
python scripts/version.py --release "Awesome Feature Release"

# Can combine with version bump
python scripts/version.py --bump minor --release "Multi-ISO Enhancement"
```

### Toggle Development Status

```bash
python scripts/version.py --dev
```

This toggles `IS_DEV` flag. When `True`, version string includes "-dev" suffix.

## In Python Code

### Import Version

```python
# Import full version info
from luxusb._version import __version__, get_version_string, get_full_version_info

# Get version string
version = __version__  # "0.2.0"

# Get version with dev suffix if applicable
version_str = get_version_string()  # "0.2.0" or "0.2.0-dev"

# Get complete version info
info = get_full_version_info()
# Returns:
# {
#     "version": "0.2.0",
#     "version_info": (0, 2, 0),
#     "major": 0,
#     "minor": 2,
#     "patch": 0,
#     "release_date": "2026-01-23",
#     "release_name": "Logo Enhancement Release",
#     "is_dev": False,
#     "version_string": "0.2.0"
# }
```

### Version Comparison

```python
from luxusb._version import __version_info__

# Check minimum version
if __version_info__ >= (0, 2, 0):
    # Use new feature
    pass
```

## Release Workflow

### 1. Start Development Phase

```bash
# Enable dev status
python scripts/version.py --dev
```

Version string becomes "0.2.0-dev"

### 2. Complete Features

Commit changes throughout development phase.

### 3. Prepare Release

```bash
# Bump version and set release name
python scripts/version.py --bump minor --release "Feature Name Release"

# Disable dev status
python scripts/version.py --dev
```

### 4. Update CHANGELOG

Edit `CHANGELOG.md` to move items from `[Unreleased]` to new version section.

### 5. Build Release

```bash
# Build AppImage (automatically uses new version)
./scripts/build-appimage.sh

# Build boot environment
./scripts/build-boot-env.sh
```

### 6. Tag Release

```bash
git tag -a v0.3.0 -m "Release version 0.3.0"
git push origin v0.3.0
```

## Benefits

✅ **Single Source of Truth** - Update version once, reflected everywhere
✅ **No Manual Edits** - Automated version bumping prevents errors
✅ **Consistent Versioning** - All files use same version
✅ **Easy to Track** - Clear version history in git
✅ **Build Automation** - Scripts automatically use correct version
✅ **Development Tracking** - Dev flag distinguishes releases from WIP

## File Structure

```
luxusb/
├── _version.py          # ← Single source of truth
├── __init__.py          # Imports and exposes version
└── ...

pyproject.toml           # Reads version dynamically
scripts/
├── version.py           # Version management CLI
└── build-appimage.sh    # Extracts version for builds
```

## Examples

### Patch Release (Bug Fix)

```bash
# Fix bugs...
python scripts/version.py --bump patch --release "Bug Fix Release"
# 0.2.0 -> 0.2.1
```

### Minor Release (New Features)

```bash
# Add features...
python scripts/version.py --bump minor --release "Custom ISO Support"
# 0.2.0 -> 0.3.0
```

### Major Release (Breaking Changes)

```bash
# Redesign architecture...
python scripts/version.py --bump major --release "Major Rewrite"
# 0.2.0 -> 1.0.0
```

## Troubleshooting

### Version Not Updating in Build

Ensure build scripts import version correctly:
```bash
VERSION=$(python3 -c "from luxusb._version import __version__; print(__version__)")
```

### Import Errors

Make sure `luxusb/_version.py` is in Python path:
```python
import sys
sys.path.insert(0, "luxusb")
from _version import __version__
```

### Version Mismatch

If you see different versions in different places, check:
1. `luxusb/_version.py` - Is this the source of truth?
2. `pyproject.toml` - Does it have `dynamic = ["version"]`?
3. Cached imports - Restart Python interpreter

## Best Practices

1. ✅ Always use `scripts/version.py` to update versions
2. ✅ Never manually edit `_version.py` version string
3. ✅ Update release name when bumping version
4. ✅ Use dev mode during development
5. ✅ Tag git commits with version numbers
6. ✅ Update CHANGELOG before each release
7. ✅ Test builds before releasing

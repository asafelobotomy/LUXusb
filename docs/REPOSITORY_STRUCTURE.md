# LUXusb Repository Structure

This document describes the organization of the LUXusb repository after Phase 4 reorganization (January 2026).

## Overview

The repository follows a clean, hierarchical structure designed for:
- **Discoverability**: Intuitive navigation and file locations
- **Maintainability**: Clear separation of concerns
- **Scalability**: Easy addition of new features and documentation
- **Historical Preservation**: Archive strategy for completed work

## Root Directory Layout

```
LUXusb/
├── luxusb/              # Main application package
├── tests/               # Test suite (production tests)
├── scripts/             # Utility scripts (maintenance, validation, build)
├── docs/                # Comprehensive documentation (organized by category)
├── archive/             # Historical documents, phase docs, archived tests
├── pyproject.toml       # Project metadata and dependencies (PEP 621)
├── requirements.txt     # Python dependencies
├── README.md            # Project overview and quick start
├── LICENSE              # GNU GPL-3.0 license
├── CHANGELOG.md         # Version history and release notes
├── CONTRIBUTING.md      # Contribution guidelines
└── ROADMAP.md           # Future development plans
```

---

## Main Package (`luxusb/`)

### Package Structure
```
luxusb/
├── __init__.py           # Package initialization
├── __main__.py          # Application entry point (python -m luxusb)
├── config.py            # Configuration management (XDG directories, YAML)
│
├── core/                # Core workflow orchestration
│   ├── __init__.py
│   └── workflow.py      # LUXusbWorkflow - multi-stage operations
│
├── gui/                 # GTK4/Libadwaita interface
│   ├── __init__.py
│   ├── main_window.py   # ApplicationWindow, navigation
│   ├── device_page.py   # USB device selection
│   ├── distro_page.py   # Distribution selection
│   ├── family_page.py   # Distribution family browsing
│   └── progress_page.py # Installation progress tracking
│
├── utils/               # Utility modules (single-responsibility)
│   ├── __init__.py
│   ├── usb_detector.py     # USB device detection (lsblk)
│   ├── partitioner.py      # USB partitioning (parted, mkfs)
│   ├── grub_installer.py   # GRUB installation
│   ├── downloader.py       # ISO downloader (resume, mirrors)
│   ├── mirror_selector.py  # Mirror speed testing
│   ├── distro_json_loader.py  # JSON-based distro loading
│   ├── distro_manager.py   # Distribution metadata management
│   ├── distro_updater.py   # Distro update checking
│   ├── distro_validator.py # Distro data validation
│   ├── gpg_verifier.py     # GPG signature verification
│   ├── secure_boot.py      # Secure Boot support
│   └── custom_iso.py       # Custom ISO validation
│
└── data/                # Static data files
    ├── distro-schema.json  # JSON Schema v7 for distros
    ├── families.json       # Distribution families metadata
    ├── gpg_keys.json       # GPG key fingerprints
    ├── distros/            # Distribution JSON files
    │   ├── arch.json
    │   ├── debian.json
    │   ├── fedora.json
    │   ├── kali.json
    │   ├── linuxmint.json
    │   ├── manjaro.json
    │   ├── popos.json
    │   └── ubuntu.json
    └── icons/              # Application icons
```

### Key Design Patterns
- **Three-layer architecture**: GUI → Core → Utils
- **Dataclass-based models**: `USBDevice`, `Distro`, `DistroRelease`, `WorkflowProgress`
- **JSON-driven data**: Distribution metadata loaded from `data/distros/*.json`
- **Subprocess execution**: All system commands via `subprocess.run()`
- **Progress callbacks**: Real-time UI updates via `WorkflowProgress`

---

## Tests (`tests/`)

### Test Structure
```
tests/
├── __init__.py
├── conftest.py                  # Pytest fixtures
├── test_usb_detector.py         # USB detection unit tests
├── test_all_phases.py           # Comprehensive Phase 1-3 tests (18 tests)
├── test_phase1_enhancements.py  # Phase 1: Startup metadata check
├── test_phase2_3.py             # Phase 2.3: JSON-based distro loading
├── test_phase2_4.py             # Phase 2.4: Stale ISO detection
├── test_phase2_integration.py  # Phase 2 integration tests
├── test_phase3_1.py             # Phase 3.1: Update scheduling
└── test_phase3_2.py             # Phase 3.2: Smart update logic
```

### Test Coverage
- **43 tests total** (100% passing as of Jan 2026)
- **Mock-based unit tests**: Safe testing without USB devices
- **Integration tests**: Workflow orchestration
- **Phase tests**: Automation feature validation

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_all_phases.py

# With coverage
pytest --cov=luxusb --cov-report=html
```

---

## Scripts (`scripts/`)

### Directory Structure
```
scripts/
├── maintenance/              # Maintenance utilities
│   ├── fix_grub_config.py   # GRUB configuration repair
│   └── refresh_grub.py      # GRUB menu regeneration
│
├── validation/               # Validation utilities
│   └── validate_partition_layout.py  # Partition layout verification
│
├── build-appimage.sh         # AppImage build script
├── build-boot-env.sh         # Boot environment builder
├── run-dev.sh                # Development mode runner
├── fetch_checksums.py        # Checksum fetcher for ISOs
└── verify-distros.py         # Distro JSON validation
```

### Usage Examples
```bash
# Development run
./scripts/run-dev.sh

# Build AppImage
./scripts/build-appimage.sh

# Validate distros
python3 scripts/verify-distros.py

# Fetch checksums
python3 scripts/fetch_checksums.py --distro ubuntu
```

---

## Documentation (`docs/`)

### Comprehensive Structure
```
docs/
├── README.md                    # Navigation index
├── AUTOMATION_CHECKLIST.md     # Phase 1-3 completion status
├── PROJECT_OVERVIEW.md          # High-level project info
├── REPOSITORY_STRUCTURE.md     # This file
├── QUICK_FIX_REFERENCE.md      # Common issues and solutions
│
├── architecture/               # System design
│   ├── ARCHITECTURE.md         # Component overview
│   ├── GRUB_IMPLEMENTATION_REVIEW.md
│   └── MULTIBOOT_REVIEW.md
│
├── automation/                 # Automation strategy
│   └── AUTOMATION_STRATEGY.md  # Phase 1-3 comprehensive docs
│
├── development/                # Developer guides
│   ├── DEVELOPMENT.md          # Setup and workflow
│   ├── NEW_DISTROS_GUIDE.md    # Adding distributions
│   ├── VERSION_MANAGEMENT.md   # Release management
│   ├── DISTRO_MANAGEMENT.md    # Distro metadata management
│   └── TESTING_CHECKLIST.md    # Testing procedures
│
├── user-guides/                # User documentation
│   ├── USER_GUIDE.md           # Complete user guide
│   ├── SECURE_BOOT_UI_GUIDE.md # Secure Boot feature
│   └── GPG_UX_ENHANCEMENTS.md  # GPG verification UI
│
├── features/                   # Feature documentation
│   ├── SECURE_BOOT_COMPATIBILITY_FEATURE.md
│   ├── SECURE_BOOT_IMPLEMENTATION_PLAN.md
│   ├── PHASE3_5_BIOS_SUPPORT.md
│   ├── MAXIMUM_COMPATIBILITY_ENHANCEMENTS.md
│   ├── ISO_UPDATE_STRATEGY.md
│   └── LINK_MANAGEMENT_ENHANCEMENT.md
│
├── fixes/                      # Problem solutions
│   ├── BLACK_SCREEN_FIX_SUMMARY.md
│   ├── BOOT_BLACK_SCREEN_FIX.md
│   ├── GRUB_TPM_BLACK_SCREEN_FIX.md
│   └── ALIGNMENT_FIX.md
│
├── reference/                  # Reference materials
│   ├── CONSTANTS_MIGRATION.md
│   ├── CONSTANTS_QUICKREF.md
│   ├── GPG_VERIFICATION.md
│   ├── COSIGN_VERIFICATION.md
│   └── DEPENDENCY_RESOLUTION.md
│
└── archive/                    # Archived audit reports
    ├── AUDIT_REPORT.md
    └── FINAL_AUDIT_SUMMARY.md
```

### Documentation Strategy
- **Categorization by purpose**: Architecture, development, user guides, features, fixes
- **Progressive disclosure**: Quick start → User guide → Developer guide → Architecture
- **Discoverability**: README.md indexes at each level
- **Maintenance**: Archive old docs, keep active docs current

---

## Archive (`archive/`)

### Archive Structure
```
archive/
├── test-scripts/            # Old test scripts (pre-organization)
│   ├── test_auto_grub_refresh.py
│   ├── test_auto_update.py
│   ├── test_phase2_iso_detection.py
│   └── test_secure_boot_feature.py
│
├── old-reviews/             # Historical review documents
│   ├── TEST_RESULTS.md
│   └── REPO_REVIEW_2026-01-23.md
│
├── phase-docs/              # Phase 1-3 completion documents
│   ├── PHASE1_COMPLETE.md
│   ├── PHASE2_1_COMPLETE.md
│   ├── PHASE2_INTEGRATION.md
│   ├── PHASE2_PLAN.md
│   ├── PHASE2_PROGRESS.md
│   ├── PHASE2.3_COMPLETE.md
│   ├── PHASE2.3_DESIGN.md
│   ├── PHASE2.4_COMPLETION.md
│   ├── PHASE3_COMPLETION.md
│   ├── PHASE3_GUI_INTEGRATION.md
│   ├── BUILD_COMPLETE.md
│   ├── CHECKSUMS_ENHANCED.md
│   ├── ENHANCEMENTS_COMPLETE.md
│   ├── MODERNIZATION_SUMMARY.md
│   ├── QUICKREF_CHECKSUMS.md
│   └── README_CHECKSUMS.md
│
├── implementation-docs/     # Historical implementation docs
├── research-docs/           # Research and planning docs
├── summaries/               # Historical summaries
├── tests-archived/          # Archived test files
└── verification-docs/       # Historical verification docs
```

### Archive Policy
- **Completed phases**: Phase docs moved to `archive/phase-docs/`
- **Old tests**: Superseded tests moved to `archive/test-scripts/`
- **Historical reviews**: Old review docs in `archive/old-reviews/`
- **Preservation**: Keep for historical context, don't delete

---

## Configuration Files

### `pyproject.toml`
```toml
[project]
name = "luxusb"
version = "0.1.0"
description = "GTK4-based Linux bootable USB creator"
requires-python = ">=3.10"
dependencies = [
    "PyGObject>=3.42.0",
    "requests>=2.28.0",
    "psutil>=5.9.0",
    "pyudev>=0.24.0",
]

[build-system]
requires = ["setuptools>=65.0"]
build-backend = "setuptools.build_meta"
```

### `requirements.txt`
Python package dependencies (mirrors `pyproject.toml` dependencies)

---

## File Naming Conventions

### Python Files
- **Snake case**: `usb_detector.py`, `distro_manager.py`
- **Descriptive names**: Indicate module purpose
- **Single responsibility**: One main class/function per file

### Documentation
- **UPPERCASE.md**: Root-level important docs (`README.md`, `CONTRIBUTING.md`)
- **Title Case**: Feature docs (`Secure_Boot_Implementation.md`)
- **Snake case**: Utility docs (`new_distros_guide.md`)
- **Prefixes**: `PHASE*`, `TEST_*`, `AUDIT_*` for categorization

### Data Files
- **JSON**: `.json` extension for all data files
- **Lowercase**: `arch.json`, `ubuntu.json`, `families.json`
- **Schema**: `distro-schema.json` for validation

---

## Import Path Examples

```python
# Application entry
python -m luxusb

# Core imports
from luxusb.core.workflow import LUXusbWorkflow
from luxusb.config import Config

# GUI imports
from luxusb.gui.main_window import MainWindow
from luxusb.gui.device_page import DevicePage

# Utils imports
from luxusb.utils.usb_detector import USBDetector
from luxusb.utils.downloader import ISODownloader
from luxusb.utils.distro_json_loader import DistroJSONLoader

# Data loading
from luxusb.utils.distro_json_loader import DistroJSONLoader
loader = DistroJSONLoader()
distros = loader.load_all()
```

---

## Development Workflow

### Adding New Features
1. **Plan**: Create design doc in `docs/features/`
2. **Implement**: Add code to `luxusb/utils/` or `luxusb/gui/`
3. **Test**: Create tests in `tests/`
4. **Document**: Update `docs/` and `CHANGELOG.md`
5. **Review**: Run `pytest` and validation scripts

### Adding New Distributions
1. **Create JSON**: `luxusb/data/distros/newdistro.json`
2. **Validate**: `python3 scripts/verify-distros.py`
3. **Test**: Run application, verify detection
4. **Document**: No code changes needed (JSON-driven)

### Repository Organization
1. **Preserve history**: Use `archive/` for completed work
2. **Clear categorization**: Place files in appropriate directories
3. **Update docs**: Reflect changes in `REPOSITORY_STRUCTURE.md`
4. **Test after moves**: Ensure imports still work

---

## Quick Reference

### Key Files
- **Entry point**: `luxusb/__main__.py`
- **Main workflow**: `luxusb/core/workflow.py`
- **Configuration**: `luxusb/config.py`
- **Distro data**: `luxusb/data/distros/*.json`
- **Tests**: `tests/test_all_phases.py`

### Key Directories
- **Production code**: `luxusb/`
- **Tests**: `tests/`
- **Documentation**: `docs/`
- **Build scripts**: `scripts/`
- **Historical**: `archive/`

### Navigation
- **Project overview**: [README.md](../README.md)
- **User guide**: [docs/user-guides/USER_GUIDE.md](user-guides/USER_GUIDE.md)
- **Developer guide**: [docs/development/DEVELOPMENT.md](development/DEVELOPMENT.md)
- **Architecture**: [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- **Documentation index**: [docs/README.md](README.md)

---

**Last Updated**: January 24, 2026  
**Organization Phase**: Phase 4 Complete  
**Test Coverage**: 43/43 passing (100%)

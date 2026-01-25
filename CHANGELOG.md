# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 4: Repository Organization
- **Comprehensive Documentation Navigation** - docs/README.md with task-based navigation
- **Repository Structure Guide** - Complete docs/REPOSITORY_STRUCTURE.md with examples
- **Organized Scripts Directory** - Maintenance and validation subdirectories
- **Archive Strategy** - Historical documents preserved in archive/
- **Documentation Categories** - 8 organized subdirectories (architecture, development, user-guides, automation, features, fixes, reference, archive)
- Phase 4 completion document with metrics and impact analysis

### Added - Automation & Features
- **BIOS/Legacy Boot Support** - Full support for older systems via 3-partition layout
- **Hybrid Boot Configuration** - Single USB works on both BIOS and UEFI systems
- **BIOS Boot Partition** - 1MB dedicated partition for Legacy/BIOS systems
- **Enhanced Graphics Configuration** - Auto resolution, smooth kernel handoff, pagination
- **Universal Compatibility** - Works on any computer from the last 20 years
- **Phase 1-3 Automation** - 60%+ workflow automation (startup checks, stale detection, smart scheduling)
- High-resolution distribution logos (512x512 PNG)
- Logo quality upgrade for all 14 distributions
- Organized icon management system with standardized naming

### Changed - Phase 4: Repository Organization
- **Root Directory** - Cleaned from 20+ files to 7 essential files (65% reduction)
- **Documentation Structure** - Hierarchical categorization with navigation indexes
- **Scripts Organization** - Separated by purpose (maintenance/validation)
- **Test Suite** - Moved archived tests to archive/test-scripts/, kept production tests in tests/
- **Documentation Discoverability** - Clear categorization and progressive disclosure
- Repository organization follows clean architecture principles

### Changed - Technical Improvements
- **Partition Layout** - Changed from 2 to 3 partitions (BIOS Boot + EFI + Data)
- **GRUB Installation** - Now installs both i386-pc (BIOS) and x86_64-efi (UEFI)
- **Graphics Mode** - Enhanced with gfxmode=auto, gfxpayload=keep, unicode fonts
- **Partition Hints** - Updated to gpt3 for better reliability with new layout
- Updated all distribution logos to official high-quality versions
- Improved aspect ratio preservation for distro icons
- Standardized file naming conventions across repository

### Testing
- **107 tests passing** (100% pass rate) after Phase 4 reorganization
- **Zero regressions** - All imports and functionality intact
- Comprehensive phase testing for automation features

### Breaking Changes
- ⚠️ **USB drives created with v0.1.0-0.2.0 must be recreated** due to partition layout change
- Partition numbering changed: Data is now partition 3 (was partition 2)

### Technical Details
- BIOS boot via MBR → core.img → GRUB config
- UEFI boot via BOOTX64.EFI → GRUB config
- Both modes share same grub.cfg configuration
- Menu pagination for >20 distributions
- Graceful fallback for graphics failures

### Planned
- Persistent storage support
- Ventoy integration
- Advanced GRUB theming
- Distribution categories and ratings
- Encryption support

## [0.2.0] - 2026-01-21

### Added
- **Custom ISO Support** - Add any bootable ISO file
  - ISO format validation (ISO 9660)
  - Bootable detection using isoinfo
  - Size constraints (10 MB - 10 GB)
  - Custom ISO file chooser in GUI
- **Secure Boot Signing** - Sign bootloader for Secure Boot compatibility
  - EFI variable detection
  - MOK key generation and management
  - Shim bootloader installation
  - sbsign integration
  - Secure Boot toggle in GUI header
- **Multiple ISO Support** - Create multi-boot USB drives
  - DistroSelection dataclass
  - Space calculation utilities
  - GRUB multi-boot configuration
- **Pause/Resume Downloads** - Control download process
  - HTTP Range request support
  - Resume metadata tracking (.resume files)
  - Pause/Resume button in GUI
- **Mirror Selection** - Automatic mirror selection
  - Parallel mirror speed testing
  - Auto-select fastest mirror
  - Mirror failover on errors
- **JSON-based Distribution Metadata** - Dynamic distribution updates
  - 8+ curated distributions with real checksums
  - JSON Schema validation
  - DistroJSONLoader with caching
  - Easy updates without code changes

### Changed
- Modernized API - Removed all backward compatibility code
  - `LUXusbWorkflow` now requires `selections` or `custom_isos` parameters
  - `DistroManager` always loads from JSON (no hardcoded fallback)
  - Clean, forward-looking parameter signatures
- Updated documentation with Phase 3 features
- Enhanced error handling and validation

### Removed
- Backward compatibility parameters (`distro`, `release`, `use_json`)
- 200+ lines of hardcoded distribution definitions
- Fallback to hardcoded distro metadata

## [0.1.0] - 2024-11-XX

### Added
- Initial GTK4 interface with Libadwaita
- USB device detection and validation
- System disk protection
- Distribution selection (8 popular distros)
- ISO download with progress tracking
- SHA256 checksum verification
- GPT partitioning (EFI + Data)
- GRUB2 bootloader installation
- Secure privilege handling via pkexec
- Real checksums for distributions
- Mirror support with failover

### Security
- SHA256 checksum verification for all downloads
- Protection against system disk formatting
- Privilege escalation via pkexec (PolicyKit)

---

## Version History Summary

- **v0.2.0** (2026-01-21) - Custom ISO + Secure Boot + Multi-ISO + Advanced Downloads
- **v0.1.0** (2024-11-XX) - Initial release with core functionality

---

For detailed phase-by-phase development history, see [archive/phase-docs/](archive/phase-docs/).

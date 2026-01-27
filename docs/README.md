# LUXusb Documentation

Complete documentation for LUXusb - A GTK4-based Linux application for creating bootable USB drives with multiple Linux distributions.

## 📚 Documentation Structure

### Quick Start
- [Main README](../README.md) - Project overview and quick start
- [User Guide](user-guides/USER_GUIDE.md) - End-user documentation
- [Installation & Setup](development/DEVELOPMENT.md) - Developer setup guide

### Core Documentation

#### 📐 Architecture
- [Architecture Overview](architecture/ARCHITECTURE.md) - System design and component structure
- [GRUB Implementation](architecture/GRUB_IMPLEMENTATION_REVIEW.md) - GRUB configuration and boot system
- [Multiboot Review](architecture/MULTIBOOT_REVIEW.md) - Multi-distribution boot support

#### 🚀 Automation
- [Automation Strategy](automation/AUTOMATION_STRATEGY.md) - Comprehensive automation implementation
- [Automation Checklist](AUTOMATION_CHECKLIST.md) - Phase 1-3 completion status

#### 🛠️ Development
- [Development Guide](development/DEVELOPMENT.md) - Contributing and development workflow
- [Adding New Distributions](development/NEW_DISTROS_GUIDE.md) - How to add Linux distributions
- [Version Management](development/VERSION_MANAGEMENT.md) - Release and version control
- [Distribution Management](development/DISTRO_MANAGEMENT.md) - Managing distro metadata
- [Testing Checklist](development/TESTING_CHECKLIST.md) - Testing procedures

#### 👤 User Guides
- [User Guide](user-guides/USER_GUIDE.md) - Complete user documentation
- [Secure Boot UI Guide](user-guides/SECURE_BOOT_UI_GUIDE.md) - Secure Boot feature usage
- [GPG UX Enhancements](user-guides/GPG_UX_ENHANCEMENTS.md) - GPG verification interface

#### ⚡ Features
- [Secure Boot Compatibility](features/SECURE_BOOT_COMPATIBILITY_FEATURE.md) - Secure Boot support
- [Secure Boot Implementation Plan](features/SECURE_BOOT_IMPLEMENTATION_PLAN.md) - Technical implementation
- [Maximum Compatibility Enhancements](features/MAXIMUM_COMPATIBILITY_ENHANCEMENTS.md) - Broad hardware support
- [Phase 3.5 BIOS Support](features/PHASE3_5_BIOS_SUPPORT.md) - Legacy BIOS compatibility

#### 🔧 Fixes & Solutions
- [Black Screen Fix Summary](fixes/BLACK_SCREEN_FIX_SUMMARY.md) - Boot black screen resolution
- [Boot Black Screen Fix](fixes/BOOT_BLACK_SCREEN_FIX.md) - Detailed fix procedures
- [GRUB TPM Black Screen Fix](fixes/GRUB_TPM_BLACK_SCREEN_FIX.md) - TPM-related fixes
- [Alignment Fix](fixes/ALIGNMENT_FIX.md) - Partition alignment issues

#### 📖 Reference
- [Constants Migration](reference/CONSTANTS_MIGRATION.md) - Configuration constants
- [Constants Quick Reference](reference/CONSTANTS_QUICKREF.md) - Quick reference guide
- [GPG Verification](reference/GPG_VERIFICATION.md) - GPG signature verification
- [Cosign Verification](reference/COSIGN_VERIFICATION.md) - Cosign verification system
- [Dependency Resolution](reference/DEPENDENCY_RESOLUTION.md) - Package dependencies
- [Library & Naming Review (2026-01-27)](reference/LIBRARY_NAMING_REVIEW_2026-01-27.md) - Comprehensive library and naming convention analysis

#### 📝 Project Management
- [Project Overview](PROJECT_OVERVIEW.md) - High-level project information
- [Repository Structure](REPOSITORY_STRUCTURE.md) - Codebase organization
- [Quick Fix Reference](QUICK_FIX_REFERENCE.md) - Common issues and solutions
- [ISO Update Strategy](ISO_UPDATE_STRATEGY.md) - ISO management approach
- [Link Management Enhancement](LINK_MANAGEMENT_ENHANCEMENT.md) - URL management

#### 📦 Archive
- [Audit Reports](archive/) - Historical audit documents
- [Phase Documentation](../archive/phase-docs/) - Phase 1-3 completion docs
- [Old Reviews](../archive/old-reviews/) - Historical review documents

---

## 🎯 Quick Navigation by Task

### I want to...
- **Use LUXusb**: Start with [User Guide](user-guides/USER_GUIDE.md)
- **Contribute**: Read [Development Guide](development/DEVELOPMENT.md) and [CONTRIBUTING](../CONTRIBUTING.md)
- **Add a new distribution**: Follow [New Distros Guide](development/NEW_DISTROS_GUIDE.md)
- **Understand the architecture**: See [Architecture Overview](architecture/ARCHITECTURE.md)
- **Enable Secure Boot**: Check [Secure Boot UI Guide](user-guides/SECURE_BOOT_UI_GUIDE.md)
- **Fix boot issues**: Browse [Fixes & Solutions](fixes/)
- **Learn about automation**: Read [Automation Strategy](automation/AUTOMATION_STRATEGY.md)

---

## 📊 Project Status

### Automation Phases
- ✅ **Phase 1**: Startup Metadata Check - COMPLETE
- ✅ **Phase 2**: Stale ISO Detection - COMPLETE
- ✅ **Phase 3**: Smart Update Scheduling - COMPLETE

**Achievement**: 60%+ automation coverage | Zero-maintenance user experience

### Recent Enhancements
- GPG signature verification
- Cosign verification support
- Secure Boot compatibility
- Maximum hardware compatibility
- Comprehensive test coverage (43/43 tests passing)

---

## 🔍 Search Tips

- **Architecture questions**: Check `architecture/` directory
- **How-to guides**: Browse `user-guides/` and `development/`
- **Feature documentation**: Look in `features/`
- **Troubleshooting**: See `fixes/` and `QUICK_FIX_REFERENCE.md`
- **API/Reference**: Check `reference/` directory
- **Historical context**: Browse `archive/` directories

---

## 📄 License
GNU General Public License v3.0 - See [LICENSE](../LICENSE) for details

## 🤝 Contributing
Contributions welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md) and [Development Guide](development/DEVELOPMENT.md)

---

**Last Updated**: January 24, 2026

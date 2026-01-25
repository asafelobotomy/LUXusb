# Archive

This directory contains historical development documentation and phase completion records.

## Phase Documentation

All phase completion documents have been archived here to keep the root directory clean:

- **PHASE1_COMPLETE.md** - Real checksums and mirror support
- **PHASE2_1_COMPLETE.md** - Resume downloads
- **PHASE2_PLAN.md** - Phase 2 planning
- **PHASE2_PROGRESS.md** - Phase 2 progress tracking
- **PHASE2_INTEGRATION.md** - Phase 2 integration testing
- **PHASE2.3_COMPLETE.md** - Multiple ISO support
- **PHASE2.3_DESIGN.md** - Multiple ISO design document
- **PHASE2.4_COMPLETION.md** - JSON-based distribution metadata
- **PHASE3_COMPLETION.md** - Custom ISO + Secure Boot features
- **PHASE3_GUI_INTEGRATION.md** - GUI integration for Phase 3
- **MODERNIZATION_SUMMARY.md** - Backward compatibility removal
- **BUILD_COMPLETE.md** - Initial build completion

## Scripts Documentation

- **CHECKSUMS_ENHANCED.md** - Checksum enhancement details
- **ENHANCEMENTS_COMPLETE.md** - Enhancement completion summary
- **QUICKREF_CHECKSUMS.md** - Quick reference for checksums
- **README_CHECKSUMS.md** - Checksum README

## Archived Tests

**tests-archived/** - Phase-specific development tests (3 files, 52 tests)

Phase-specific tests were valuable during development but became redundant after features were integrated:
- **test_phase1_enhancements.py** - Checksums and mirrors (now in test_distro_metadata.py)
- **test_phase2_3.py** - Multiple ISO support (now core functionality)
- **test_phase2_integration.py** - Integration tests (now standard behavior)

See [tests-archived/README.md](tests-archived/README.md) for details.

## Purpose

These documents track the development history and are kept for reference but are not needed for daily development or deployment.

For current documentation, see:
- [README.md](../README.md) - Project overview
- [docs/](../docs/) - User guides and architecture
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [tests/](../tests/) - Active test suite (4 files, 44 tests)

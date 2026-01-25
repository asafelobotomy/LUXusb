# Archived Test Files

**Archive Date**: January 23, 2026  
**Reason**: Phase-specific development tests no longer needed after feature integration

---

## Archived Files

### test_phase1_enhancements.py
- **Purpose**: Tested Phase 1 enhancements (real checksums and mirror support)
- **Status**: Phase 1 completed and features integrated
- **Archived Because**: Checksum validation now part of core distro metadata tests
- **Tests**: Real checksums, uniqueness, specific checksums, mirror functionality

### test_phase2_3.py
- **Purpose**: Tested Phase 2.3 features (multiple ISO support)
- **Status**: Phase 2.3 completed and features integrated
- **Archived Because**: Multiple ISO support is now standard functionality
- **Tests**: DistroSelection, space calculations, USB capacity validation, workflow handling

### test_phase2_integration.py
- **Purpose**: Tested Phase 2 feature integration (pause/resume, mirrors, checksums)
- **Status**: Phase 2 completed and features integrated
- **Archived Because**: Integration complete, features are now standard
- **Tests**: Workflow pause/resume, config integration, download verification

---

## Current Active Tests

The following tests remain active as they test ongoing core functionality:

- **test_usb_detector.py** - USB device detection (core functionality)
- **test_distro_metadata.py** - JSON metadata loading (renamed from test_phase2_4.py)
- **test_custom_iso.py** - Custom ISO support (renamed from test_phase3_1.py)
- **test_secure_boot.py** - Secure Boot support (renamed from test_phase3_2.py)

---

## Test Count Summary

**Before Cleanup**: 96 tests across 7 files  
**After Cleanup**: 44 tests across 4 files (+ conftest.py)  
**Archived Tests**: 52 phase-specific development tests

---

## Philosophy

Phase-specific tests were valuable during development to validate new features as they were being built. Once a phase is complete and its features are integrated into the core application, these tests become redundant with the core functionality tests.

The remaining tests focus on:
1. **Core system components** (USB detection)
2. **Active features** (custom ISO, Secure Boot, metadata loading)
3. **Ongoing functionality** (not one-time development milestones)

This keeps the test suite focused, maintainable, and relevant to the current codebase state.

---

## Restoration

If these tests are needed for historical reference or to verify old behavior:

```bash
# Restore a specific test file
cp archive/tests-archived/test_phase1_enhancements.py tests/

# Restore all archived tests
cp archive/tests-archived/test_*.py tests/
```

---

**Archived as part of**: Code quality audit and test suite modernization  
**Related Documentation**: docs/AUDIT_REPORT.md, docs/FINAL_AUDIT_SUMMARY.md

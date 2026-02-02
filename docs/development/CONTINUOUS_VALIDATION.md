# Continuous Validation Checklist for LUXusb

**Purpose**: Prevent regression of GRUB boot errors and similar bugs  
**Date Created**: 2026-01-29  
**Last Updated**: 2026-01-29

## Quick Reference

Run these checks before **every** commit to catch issues early:

```bash
# 1. Run full test suite
python3 -m pytest tests/ -v

# 2. Check file operations safety
python3 scripts/validation/check_file_operations.py

# 3. GRUB configuration validation (creates temp USB simulation)
python3 -c "from tests.test_grub_validation import test_grub_config; test_grub_config()"

# 4. Check for common GRUB syntax errors
grep -r "{{" luxusb/ --include="*.py" | grep -v "function.*{{" | grep -v "menuentry.*{{"
```

## Validation Categories

### 1. File Operation Safety ✅

**What It Checks**: Directory creation before file writes

**Tool**: [`scripts/validation/check_file_operations.py`](../../scripts/validation/check_file_operations.py)

**Run Frequency**: Every commit

**Expected Result**: 0 critical issues, <10 warnings

**Command**:
```bash
python3 scripts/validation/check_file_operations.py
```

**Fixes Common Issues**:
- Missing `mkdir()` before `open(w)`
- Missing `parent.mkdir()` before `.write_text()`
- Directory assumptions on USB partitions

### 2. GRUB Configuration Validation ✅

**What It Checks**:
- Module loading order (insmod before rmmod)
- Helper function syntax
- Menuentry structure (indentation)
- Required sections present
- No syntax errors (double braces, etc.)

**Tool**: Inline validation script (can be extracted to `scripts/validation/`)

**Run Frequency**: After any GRUB-related code changes

**Expected Result**: All tests pass

**Command**:
```bash
cd /home/solon/Documents/LUXusb && python3 << 'EOF'
"""GRUB Configuration Validation"""
import tempfile, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from luxusb.utils.grub_installer import GRUBInstaller
from luxusb.utils.usb_detector import USBDevice
from luxusb.utils.distro_json_loader import DistroJSONLoader

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)
    efi_mount = tmp_path / "efi"
    data_mount = tmp_path / "data"
    efi_mount.mkdir()
    data_mount.mkdir()
    
    device = USBDevice("/dev/sdX", 16000000000, "Test", "Test", "TEST", [], False, [])
    installer = GRUBInstaller(device, efi_mount, data_mount)
    
    loader = DistroJSONLoader()
    distros_list = loader.load_all()
    
    isos_dir = data_mount / "isos"
    isos_dir.mkdir()
    
    iso_paths, distros_matched = [], []
    for distro in distros_list[:3]:
        if distro.releases:
            iso_path = isos_dir / f"{distro.id}-{distro.releases[0].version}.iso"
            iso_path.write_text("mock")
            iso_paths.append(iso_path)
            distros_matched.append(distro)
    
    success = installer.update_config_with_isos(iso_paths, distros_matched, timeout=10)
    grub_cfg = efi_mount / "boot" / "grub" / "grub.cfg"
    
    if not success or not grub_cfg.exists():
        print("❌ Config generation failed")
        sys.exit(1)
    
    config = grub_cfg.read_text()
    
    # Validate structure
    required = ["set timeout=", "insmod part_gpt", "insmod loopback", 
                "function loop {", "function find_partition {", "find_partition || halt"]
    missing = [s for s in required if s not in config]
    if missing:
        print(f"❌ Missing: {missing}")
        sys.exit(1)
    
    # Validate module order
    if config.find("insmod part_gpt") >= config.find("rmmod tpm"):
        print("❌ Module order wrong")
        sys.exit(1)
    
    print("✅ GRUB configuration validation passed")
EOF
```

**Fixes Common Issues**:
- Module loading order errors
- Syntax errors in generated configs
- Missing helper functions
- Incorrect indentation

### 3. Unit Test Suite ✅

**What It Checks**: All application functionality

**Tool**: pytest

**Run Frequency**: Every commit

**Expected Result**: 107/107 tests passing

**Command**:
```bash
python3 -m pytest tests/ -v
```

**Key Test Files**:
- `tests/test_all_phases.py` - Integration tests
- `tests/test_usb_detector.py` - USB detection
- `tests/test_distro_metadata.py` - Distro loading
- `tests/test_custom_iso.py` - Custom ISO support
- `tests/test_secure_boot.py` - Secure Boot

### 4. Syntax Pattern Checks

**What It Checks**: Common syntax errors in code

**Tool**: grep-based pattern matching

**Run Frequency**: Pre-commit

**Expected Result**: 0 matches (or only in function definitions)

**Commands**:

#### Check for Double Braces (Should Only Be in Function Definitions)
```bash
# Find any {{ that's not in function definitions
grep -rn "{{" luxusb/ --include="*.py" | grep -v "function.*{{" | grep -v "menuentry.*{{"
```

**Expected**: Empty output or only in f-string function definitions

#### Check for Directory Creation Before File Writes
```bash
# Find open(w) calls
grep -rn "open(.*'w'" luxusb/ --include="*.py"

# Manually verify each has mkdir() before it
```

#### Check for Unsafe Path Operations
```bash
# Find .write_text() and .write_bytes()
grep -rn "\.write_text\(\|\.write_bytes\(" luxusb/ --include="*.py"

# Verify each has parent.mkdir() before it
```

### 5. Static Code Analysis

**What It Checks**: Code quality, type hints, unused imports

**Tool**: ruff (modern Python linter)

**Run Frequency**: Pre-commit (optional)

**Command**:
```bash
# Install ruff if not already installed
pip install ruff

# Run linter
ruff check luxusb/

# Run formatter check
ruff format --check luxusb/
```

### 6. Type Checking

**What It Checks**: Type hint correctness

**Tool**: mypy or pyright

**Run Frequency**: Weekly or before major releases

**Command**:
```bash
# Install mypy
pip install mypy

# Run type checker
mypy luxusb/ --ignore-missing-imports
```

## Pre-Commit Checklist

Before committing GRUB-related changes:

- [ ] Run GRUB configuration validation
- [ ] Run file operation safety check
- [ ] Run full test suite
- [ ] Check for double braces in generated code
- [ ] Manually test on loop device (if changing boot logic)

Before committing any code:

- [ ] Run test suite
- [ ] Run file operation safety check
- [ ] Check for linter warnings
- [ ] Update CHANGELOG.md
- [ ] Update version if needed

## Hardware Testing Checklist

Before releasing new version:

- [ ] Create USB with latest code
- [ ] Test BIOS boot (legacy systems)
- [ ] Test UEFI boot (modern systems)
- [ ] Test with multiple distros (Ubuntu, Fedora, Arch)
- [ ] Test helper functions (error messages, partition search)
- [ ] Test on different hardware (if possible)
- [ ] Verify no boot errors
- [ ] Verify GRUB menu displays correctly

## Common Issues & Quick Fixes

### Issue: Module Loading Order Error

**Symptom**: `error: no such module 'tpm'` on boot

**Check**:
```bash
# Verify insmod comes before rmmod
grep -A 30 "insmod part_gpt" luxusb/utils/grub_installer.py | grep -B 5 "rmmod tpm"
```

**Fix**: Ensure all `insmod` commands are before `rmmod tpm`

### Issue: Directory Not Found Error

**Symptom**: `FileNotFoundError` when writing config

**Check**:
```bash
# Run file operation safety check
python3 scripts/validation/check_file_operations.py
```

**Fix**: Add `path.parent.mkdir(parents=True, exist_ok=True)` before file write

### Issue: Double Braces in GRUB Config

**Symptom**: GRUB syntax error with `{{`

**Check**:
```bash
# Generate config and check
python3 -c "from luxusb.utils.grub_installer import GRUBInstaller; ..." | grep "{{"
```

**Fix**: Escape braces in f-strings: use `{{` for literal `{` in function definitions

### Issue: Test Failures

**Symptom**: pytest shows failing tests

**Check**:
```bash
# Run tests with verbose output
python3 -m pytest tests/ -xvs
```

**Fix**: Review error messages, check for missing dependencies or broken imports

## Automation Opportunities

### GitHub Actions (Future)

```yaml
# .github/workflows/validate.yml
name: Validation
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python3 -m pytest tests/ -v
      - name: Check file operations
        run: python3 scripts/validation/check_file_operations.py
      - name: GRUB validation
        run: python3 scripts/validation/validate_grub.py
```

### Pre-commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running pre-commit validation..."

# Run tests
python3 -m pytest tests/ -q || exit 1

# Check file operations
python3 scripts/validation/check_file_operations.py || exit 1

echo "✅ All checks passed"
```

## Resources

### Documentation

- [V0.5.2_COMPREHENSIVE_VALIDATION.md](V0.5.2_COMPREHENSIVE_VALIDATION.md) - Latest validation report
- [FILE_OPERATION_SAFETY_AUDIT.md](FILE_OPERATION_SAFETY_AUDIT.md) - Detailed audit results
- [V0.5.0_HYBRID_IMPLEMENTATION.md](V0.5.0_HYBRID_IMPLEMENTATION.md) - GRUB structure refactor

### Tools

- **File Operation Checker**: `scripts/validation/check_file_operations.py`
- **Test Suite**: `tests/`
- **GRUB Installer**: `luxusb/utils/grub_installer.py`

### External References

- [GRUB Manual](https://www.gnu.org/software/grub/manual/)
- [GLIM Project](https://github.com/thias/glim) - Reference implementation
- [Python Path Documentation](https://docs.python.org/3/library/pathlib.html)

## Metrics to Track

### Code Quality

- Test coverage: 107 tests passing
- Static analysis warnings: 0 critical
- Type hint coverage: Partial (improving)

### GRUB Boot Success

- Boot success rate: Target 100%
- Module loading errors: 0
- Syntax errors: 0
- Partition search failures: 0

### File Operations

- Directory creation bugs: 0
- File write failures: 0
- Path handling errors: 0

---

**Last Updated**: 2026-01-29  
**Version**: 1.0  
**Status**: Active monitoring

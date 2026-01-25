# Checksum Fetcher - Quick Reference

## Installation

```bash
pip install beautifulsoup4  # Already in requirements.txt
```

## Common Commands

```bash
# Check all distributions (shows differences)
python3 scripts/fetch_checksums.py

# Check specific distribution
python3 scripts/fetch_checksums.py --distro ubuntu

# Clear cache and fetch fresh
python3 scripts/fetch_checksums.py --no-cache

# Update distro_manager.py automatically
python3 scripts/fetch_checksums.py --update

# Update specific distribution
python3 scripts/fetch_checksums.py --distro fedora --update
```

## Distribution IDs

| ID | Name | Reliability |
|----|------|-------------|
| `ubuntu` | Ubuntu Desktop | ✅ Excellent |
| `fedora` | Fedora Workstation | ✅ Excellent |
| `linuxmint` | Linux Mint | ✅ Excellent |
| `popos` | Pop!_OS | ✅ Excellent |
| `manjaro` | Manjaro | ✅ Excellent (fastest) |
| `debian` | Debian | ✅ Good (with fallback) |
| `zorin` | Zorin OS | ⚠️ Fair (HTML parsing) |
| `elementary` | elementary OS | ⚠️ Fair (version drift) |

## Cache Management

```bash
# View cache
ls -lh ~/.cache/luxusb/checksums/

# Clear all cache
rm -rf ~/.cache/luxusb/checksums

# Clear specific distro
rm ~/.cache/luxusb/checksums/ubuntu.json
```

## Typical Workflows

### Weekly Checksum Verification

```bash
python3 scripts/fetch_checksums.py
```

### Pre-Release Preparation

```bash
# Clear cache
rm -rf ~/.cache/luxusb/checksums

# Fetch fresh checksums
python3 scripts/fetch_checksums.py --no-cache

# Review differences
cat checksum_report.txt

# Apply updates
python3 scripts/fetch_checksums.py --update
```

### After Distribution Release

```bash
# Clear cache for updated distro
rm ~/.cache/luxusb/checksums/ubuntu.json

# Fetch new checksum
python3 scripts/fetch_checksums.py --distro ubuntu

# Update if different
python3 scripts/fetch_checksums.py --distro ubuntu --update
```

## Troubleshooting

### Network Timeout

```bash
# Try with cache disabled
python3 scripts/fetch_checksums.py --distro debian --no-cache
```

### Version Mismatch

```bash
# Check what's actually available
curl -s https://releases.ubuntu.com/24.04/SHA256SUMS | grep desktop
```

### Update Failed

```bash
# Restore from backup
cp luxusb/utils/distro_manager.py.bak luxusb/utils/distro_manager.py
```

## Output Interpretation

### ✅ MATCH
Checksum is current and correct. No action needed.

### ⚠️ DIFFERENT
Checksum has changed. Review and consider updating:
```bash
python3 scripts/fetch_checksums.py --distro <id> --update
```

### ❌ Error
Fetching failed. Check network connection or source availability.

## Performance

- **With cache**: <0.1s per distribution ⚡
- **Without cache**: 0.5s - 4s depending on source
- **Full scan (8 distros)**: ~1-2s with cache, ~20s without

## Safety Features

✅ Automatic backup before updates  
✅ Pattern-based replacement (no arbitrary code)  
✅ HTTPS-only sources  
✅ SHA256 format validation  
✅ Detailed change reporting  

## More Information

- **scripts/README_CHECKSUMS.md** - Basic usage guide
- **scripts/CHECKSUMS_ENHANCED.md** - Detailed feature documentation
- **scripts/ENHANCEMENTS_COMPLETE.md** - Implementation summary

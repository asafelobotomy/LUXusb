# Checksum Fetcher - Optional Enhancements

## Overview

The checksum fetcher has been enhanced with production-ready features for automated maintenance of distribution checksums in LUXusb.

## Implemented Enhancements

### 1. Caching System ✅

**Feature**: 24-hour TTL cache for checksum results

**Location**: `~/.cache/luxusb/checksums/`

**Benefits**:
- Reduces repeated network requests
- Faster verification during development
- Respects distribution server bandwidth

**Usage**:
```bash
# Use cache (default)
python3 scripts/fetch_checksums.py --distro ubuntu

# Bypass cache
python3 scripts/fetch_checksums.py --distro ubuntu --no-cache
```

**Cache Structure**:
```json
{
  "distro_id": "ubuntu",
  "iso_url": "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso",
  "checksum": "faabcf33ae53976d2b8207a001ff32f4e5daae013505ac7188c9ea63988f8328",
  "timestamp": "2026-01-21T12:42:40.818386"
}
```

### 2. --update Flag ✅

**Feature**: Automatically update `distro_manager.py` with fetched checksums

**Safety Features**:
- Creates backup (`distro_manager.py.bak`) before modifications
- Only updates checksums that differ
- Reports all changes made

**Usage**:
```bash
# Check for updates (no modifications)
python3 scripts/fetch_checksums.py

# Apply updates
python3 scripts/fetch_checksums.py --update

# Update specific distro
python3 scripts/fetch_checksums.py --distro ubuntu --update
```

**Example Output**:
```
======================================================================
  UPDATING distro_manager.py
======================================================================
✅ Created backup: distro_manager.py.bak
✅ Updated Ubuntu Desktop checksum

✅ Successfully updated 1 checksum(s) in distro_manager.py

✅ Update complete! Please review the changes.
```

### 3. Improved Version Matching ✅

**Feature**: Intelligent version fallback for distributions with changing release paths

**Implemented For**:
- **Ubuntu**: Tries version-specific path (24.04.1), then base version (24.04)
- **Debian**: Similar fallback logic with archive support

**Pattern Matching**:
- Matches by edition (desktop/server) and architecture (amd64/arm64)
- Handles version suffixes (24.04 → 24.04.3)
- Finds best match when exact filename not available

**Example**:
```
📥 Fetching: https://releases.ubuntu.com/24.04/SHA256SUMS
✅ Found checksum (pattern match): faabcf33ae53976d...
ℹ️  Matched line: faabcf33ae53976d... *ubuntu-24.04.3-desktop-amd64.iso
```

### 4. Enhanced Error Handling ✅

**Features**:
- Timeout increases for slow mirrors (10s → 15s)
- Multiple URL attempts for Debian (current + archive)
- Improved HTML parsing for Zorin with fallback patterns
- BeautifulSoup4 integration for reliable parsing

**Debian Improvements**:
```python
# Tries both current and archive URLs
urls_to_try = [
    f"{iso_dir}/SHA256SUMS",  # Current release
    f"https://cdimage.debian.org/cdimage/archive/{version}/amd64/iso-dvd/SHA256SUMS"  # Archive
]
```

**Zorin Improvements**:
```python
# Multiple parsing strategies
1. Regex pattern: "Zorin OS 17.3 Core 64-bit (r2): <checksum>"
2. Code block search with version matching
3. Fallback to manual verification link
```

## Workflow Integration

### Daily Maintenance

```bash
# Check all distributions
python3 scripts/fetch_checksums.py

# Update if needed
python3 scripts/fetch_checksums.py --update
```

### CI/CD Integration

```bash
# In GitHub Actions or similar
python3 scripts/fetch_checksums.py --no-cache --update
git diff luxusb/utils/distro_manager.py  # Review changes
```

### Pre-Release Verification

```bash
# Clear cache and fetch fresh
rm -rf ~/.cache/luxusb/checksums
python3 scripts/fetch_checksums.py --no-cache

# Review all checksums
python3 scripts/fetch_checksums.py | tee checksum_report.txt
```

## Distribution-Specific Notes

### Ubuntu
- ✅ Pattern matching handles version drift (24.04 → 24.04.3)
- ✅ Supports both desktop and server editions
- ⚠️ Requires network access to releases.ubuntu.com

### Fedora
- ✅ Direct .sha256 file access
- ✅ Reliable and fast
- ℹ️ CHECKSUM file format may change between releases

### Debian
- ✅ Fallback to archive for older versions
- ⚠️ Current symlink may point to different version
- ℹ️ Archive access slower than current

### Linux Mint
- ✅ Consistent sha256sum.txt format
- ✅ mirrors.kernel.org very reliable
- ✅ Fast and cacheable

### Pop!_OS
- ✅ Standard SHA256SUMS format
- ✅ Reliable System76 servers
- ℹ️ Limited mirror availability

### Manjaro
- ✅ Individual .sha256 files per ISO
- ✅ Most reliable method
- ✅ No parsing required

### Zorin OS
- ⚠️ HTML parsing required
- ⚠️ May break with website updates
- 💡 Manual verification recommended

### elementary OS
- ⚠️ Only latest version available
- ⚠️ Version mismatch expected for older releases
- 💡 Update distro_manager.py to latest version

## Testing

### Unit Tests

```bash
# Test specific distribution
python3 scripts/fetch_checksums.py --distro manjaro --no-cache

# Verify cache works
python3 scripts/fetch_checksums.py --distro manjaro  # Should use cache
```

### Integration Test

```bash
# Full workflow test
rm -rf ~/.cache/luxusb/checksums
python3 scripts/fetch_checksums.py --update
git diff luxusb/utils/distro_manager.py  # Review
git checkout luxusb/utils/distro_manager.py  # Revert test
```

## Troubleshooting

### Cache Issues

```bash
# Clear all cache
rm -rf ~/.cache/luxusb/checksums

# Clear specific distro
rm ~/.cache/luxusb/checksums/ubuntu.json
```

### Network Timeouts

```bash
# Use --no-cache to force fresh fetch with full timeout
python3 scripts/fetch_checksums.py --distro debian --no-cache
```

### Version Mismatches

Check if distribution has released a new version:
```bash
# For Ubuntu
curl -s https://releases.ubuntu.com/24.04/SHA256SUMS | grep desktop

# For Debian
curl -s https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/SHA256SUMS | head -5
```

## Future Enhancements (Optional)

### GPG Signature Verification

Add cryptographic verification:
```python
# Download .gpg file
# Verify signature using gnupg
# Report signature validity
```

### Parallel Fetching

Speed up multi-distribution checks:
```python
# Use asyncio or concurrent.futures
# Fetch all distributions in parallel
# Aggregate results
```

### Notification System

Alert on checksum changes:
```python
# Email notifications
# Slack/Discord webhooks
# GitHub issue creation
```

## Performance

### Benchmarks

**Without Cache**:
- Ubuntu: ~2s
- Fedora: ~1.5s
- Debian: ~3s (archive fallback)
- Linux Mint: ~1s
- Pop!_OS: ~1s
- Manjaro: ~0.5s (fastest)
- Zorin: ~4s (HTML parsing)
- elementary: ~3s (HTML parsing)

**With Cache**:
- All distributions: <0.1s

**Full Run** (8 distributions):
- First run (no cache): ~15-20s
- Subsequent runs (cached): ~1-2s

## Security Considerations

1. **Source Verification**: Only fetches from official distribution domains
2. **HTTPS Only**: All requests use TLS
3. **Backup Safety**: Creates backup before modifying source
4. **Pattern Validation**: Validates SHA256 format (64 hex characters)
5. **No Arbitrary Code**: Only replaces checksum strings, no Python execution

## Maintenance

### Weekly Check

```bash
python3 scripts/fetch_checksums.py
```

### Before Release

```bash
python3 scripts/fetch_checksums.py --no-cache --update
```

### After Distribution Release

```bash
# Clear cache for updated distribution
rm ~/.cache/luxusb/checksums/<distro>.json
python3 scripts/fetch_checksums.py --distro <distro> --update
```

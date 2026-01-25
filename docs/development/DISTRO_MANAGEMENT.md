# LUXusb Distribution Management

This document explains how to maintain and update Linux distribution metadata in LUXusb.

## Overview

LUXusb uses JSON files in `luxusb/data/distros/` to store distribution metadata including ISO URLs, checksums, and mirrors. To ensure downloads work reliably, we provide automated tools for updating and verifying these links.

## Tools

### 1. Distro Updater (`luxusb/utils/distro_updater.py`)

Automatically fetches the latest ISO releases from official distribution sources.

**Supported Distributions:**
- **Ubuntu**: Scrapes releases.ubuntu.com for latest LTS point release
- **Arch Linux**: Uses official API at archlinux.org/releng/releases/json/
- **Debian**: Scrapes cdimage.debian.org for latest stable release
- **Kali Linux**: Parses cdimage.kali.org for most recent version

**Usage:**
```bash
# From repository root with venv activated
python -m luxusb.utils.distro_updater

# Output shows which distros were successfully updated
=== Update Results ===
ubuntu: ✅ SUCCESS
arch: ✅ SUCCESS
debian: ✅ SUCCESS
kali: ✅ SUCCESS
```

**What It Does:**
1. Queries official distribution sources for latest releases
2. Extracts version, ISO URL, SHA256 checksum, and file size
3. Updates corresponding JSON files in `luxusb/data/distros/`
4. Sets `verified: true` in metadata

### 2. Link Verifier (`scripts/verify-distros.py`)

Tests all ISO URLs (primary and mirrors) to ensure they're accessible.

**Usage:**
```bash
# From repository root
python scripts/verify-distros.py

# Or make executable and run directly
chmod +x scripts/verify-distros.py
./scripts/verify-distros.py
```

**Output:**
```
=== Verifying 8 Distributions ===

Arch Linux 2026.01.01
  Primary: https://geo.mirror.pkgbuild.com/iso/2026.01.01/archlinux-2026.01.01-x86_64.iso
    ✅ OK (200)
  Mirrors:
    1. ✅ OK (200): https://mirrors.kernel.org/archlinux/iso/...
    2. ✅ OK (200): https://mirror.rackspace.com/archlinux/iso/...

============================================================
SUMMARY
============================================================
✅ Arch Linux 2026.01.01
✅ Debian 13.3.0
...
Total: 8
  ✅ Working: 8
  ❌ Failed: 0
```

**Exit Codes:**
- `0`: All links working
- `1`: One or more links failed

## Download System Robustness

### Automatic Mirror Failover

The downloader (`luxusb/utils/downloader.py`) implements intelligent mirror selection and failover:

1. **Primary URL First**: Attempts download from primary URL
2. **Automatic Fallback**: On failure, tries each mirror in sequence
3. **Resume Support**: Supports HTTP Range requests to resume interrupted downloads
4. **Retry Strategy**: Automatically retries on transient errors (429, 500, 502, 503, 504)

### Security Features

1. **SHA256 Verification**: All downloads verified against checksums in JSON files
2. **Partial File Validation**: Resume metadata tracks partial checksums
3. **Automatic Cleanup**: Deletes corrupted files on checksum mismatch
4. **HTTPS Only**: All URLs use secure HTTPS connections

### Example Usage

```python
from luxusb.utils.downloader import ISODownloader
from pathlib import Path

downloader = ISODownloader()

# Download with automatic mirror failover
success = downloader.download_with_mirrors(
    primary_url="https://releases.ubuntu.com/24.04/ubuntu-24.04.3-desktop-amd64.iso",
    mirrors=[
        "https://mirror.math.princeton.edu/pub/ubuntu-iso/24.04/ubuntu-24.04.3-desktop-amd64.iso",
        "https://mirror.pit.teraswitch.com/ubuntu-releases/24.04/ubuntu-24.04.3-desktop-amd64.iso"
    ],
    destination=Path("/tmp/ubuntu.iso"),
    expected_sha256="faabcf33ae53976d2b8207a001ff32f4e5daae013505ac7188c9ea63988f8328",
    auto_select_best=True,  # Test mirrors and use fastest
    allow_resume=True       # Resume interrupted downloads
)
```

## Maintenance Workflow

### Weekly Checks (Recommended)

```bash
# 1. Verify current links are working
python scripts/verify-distros.py

# 2. If any fail, update from official sources
python -m luxusb.utils.distro_updater

# 3. Re-verify after updates
python scripts/verify-distros.py
```

### Adding New Distributions

1. Create JSON file in `luxusb/data/distros/` (e.g., `elementary.json`)
2. Follow schema from existing files:
   ```json
   {
     "id": "elementary",
     "name": "elementary OS",
     "description": "...",
     "homepage": "https://elementary.io",
     "logo_url": "https://elementary.io/favicon.ico",
     "category": "Desktop",
     "popularity_rank": 9,
     "releases": [{
       "version": "7.1",
       "release_date": "2024-01-15",
       "iso_url": "https://...",
       "sha256": "...",
       "size_mb": 2800,
       "architecture": "x86_64",
       "mirrors": []
     }],
     "metadata": {
       "last_updated": "2024-01-15T00:00:00Z",
       "maintainer": "LUXusb Team",
       "verified": true
     }
   }
   ```
3. Download logo: `curl -o luxusb/data/icons/elementary.png https://elementary.io/favicon.ico`
4. Verify: `python scripts/verify-distros.py`

### Updating Auto-Updater

To add a distro to the auto-updater, edit `luxusb/utils/distro_updater.py`:

```python
def update_elementary(self) -> Optional[DistroRelease]:
    """Fetch latest elementary OS release"""
    try:
        # Implement API/scraping logic
        response = self.session.get("https://elementary.io/...", timeout=10)
        # Extract version, URL, SHA256, size
        return DistroRelease(...)
    except Exception as e:
        logger.error(f"Failed to update elementary: {e}")
        return None

# Add to update_all() method:
updaters = {
    'ubuntu': self.update_ubuntu,
    'arch': self.update_arch,
    'debian': self.update_debian,
    'kali': self.update_kali,
    'elementary': self.update_elementary,  # Add here
}
```

## Troubleshooting

### Issue: SHA256 mismatch during download

**Cause**: Distro released updated ISO with same version number

**Solution**:
```bash
# Re-run updater to fetch new checksum
python -m luxusb.utils.distro_updater
```

### Issue: All mirrors failing

**Cause**: Distro released new version, old version removed

**Solution**:
```bash
# Update to latest version
python -m luxusb.utils.distro_updater

# If auto-updater doesn't support this distro yet, manually update JSON:
# 1. Visit distro's official download page
# 2. Find latest ISO URL and SHA256
# 3. Update luxusb/data/distros/DISTRO.json
# 4. Verify: python scripts/verify-distros.py
```

### Issue: Timeout when verifying

**Cause**: Slow mirror or network issue

**Resolution**: Mirror failover will automatically use next mirror during download

### Issue: 404 on mirrors but primary works

**Status**: Working as designed

**Explanation**: The downloader tries primary first, only uses mirrors on failure. A few broken mirrors don't affect functionality as long as primary + at least one mirror works.

## Best Practices

1. **Test Before Committing**: Always run `verify-distros.py` before committing JSON changes
2. **Keep Multiple Mirrors**: Aim for 2-3 working mirrors per distro
3. **Use Official Sources**: Always prefer official CDN/mirrors over third-party hosts
4. **Document Updates**: Update `metadata.last_updated` when manually changing JSON files
5. **Verify Checksums**: Never use placeholder SHA256 values - always use real checksums from official sources

## Reference

- **Distro JSON Schema**: `luxusb/data/distro-schema.json`
- **Downloader Code**: `luxusb/utils/downloader.py`
- **Mirror Selector**: `luxusb/utils/mirror_selector.py`
- **Auto Updater**: `luxusb/utils/distro_updater.py`
- **Verifier Script**: `scripts/verify-distros.py`

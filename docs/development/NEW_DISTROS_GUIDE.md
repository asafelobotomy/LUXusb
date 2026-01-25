# New Distributions Guide

This document describes the newly added distributions and how to keep their checksums up-to-date using the automated updater tools.

## Added Distributions

### 1. **Bazzite Desktop** (`bazzite-desktop`)
- **Category**: Gaming
- **Family**: Fedora
- **Description**: Gaming-optimized Fedora Silverblue variant with Steam, HDR support, and enhanced gaming experience
- **Homepage**: https://bazzite.gg
- **Special Notes**: Uses OCI container images, not traditional ISOs. Checksums must be verified manually from https://docs.bazzite.gg/

### 2. **Bazzite Handheld** (`bazzite-handheld`)
- **Category**: Gaming
- **Family**: Fedora
- **Description**: Optimized for handheld gaming PCs (Steam Deck, ROG Ally, Legion Go) with Steam Gaming Mode
- **Homepage**: https://bazzite.gg
- **Special Notes**: Device-specific ISOs available via image picker at bazzite.gg

### 3. **CachyOS Desktop** (`cachyos-desktop`)
- **Category**: Desktop
- **Family**: Arch
- **Description**: Arch-based with optimized x86-64-v3/v4 packages and BORE scheduler
- **Homepage**: https://cachyos.org
- **Updater Support**: ✅ Automated checksum fetching from mirror.cachyos.org

### 4. **CachyOS Handheld** (`cachyos-handheld`)
- **Category**: Gaming
- **Family**: Arch
- **Description**: Performance-tuned for handheld gaming PCs
- **Homepage**: https://cachyos.org
- **Updater Support**: ✅ Automated checksum fetching from mirror.cachyos.org

### 5. **Parrot Security** (`parrotos`)
- **Category**: Security
- **Family**: Debian
- **Description**: Security-focused for penetration testing, forensics, and privacy
- **Homepage**: https://parrotsec.org
- **Updater Support**: ✅ Automated checksum fetching with GPG verification

### 6. **openSUSE Tumbleweed** (`opensuse-tumbleweed`)
- **Category**: Desktop
- **Family**: Independent
- **Description**: Rolling release with latest software, Btrfs snapshots, and YaST control panel
- **Homepage**: https://get.opensuse.org/tumbleweed
- **Updater Support**: ✅ Automated checksum fetching with GPG verification

## Using the Automated Updater

### Update All Distributions

Run the distro updater to automatically fetch latest versions and checksums:

```bash
python3 luxusb/utils/distro_updater.py
```

This will:
- Check official sources for each distribution
- Fetch the latest ISO URLs
- Verify checksums (and GPG signatures where available)
- Update the JSON files in `luxusb/data/distros/`

### Update Specific Distribution

```python
from luxusb.utils.distro_updater import DistroUpdater

updater = DistroUpdater()

# Update CachyOS Desktop
release = updater.update_cachyos_desktop()
if release:
    updater.update_distro_file('cachyos-desktop', release)
    print(f"Updated to version {release.version}")

# Update Parrot OS
release = updater.update_parrotos()
if release:
    updater.update_distro_file('parrotos', release)

# Update openSUSE Tumbleweed
release = updater.update_opensuse_tumbleweed()
if release:
    updater.update_distro_file('opensuse-tumbleweed', release)
```

### Fetch Checksum Only

Use the `fetch_checksums.py` script to verify checksums without updating files:

```bash
# Check specific distribution
python3 scripts/fetch_checksums.py --distro cachyos-desktop

# Check all distributions
python3 scripts/fetch_checksums.py

# Update files if checksums differ
python3 scripts/fetch_checksums.py --update
```

## Manual Verification Required

### Bazzite (Desktop & Handheld)

Bazzite uses OCI container-based images that are generated on-demand. To verify:

1. Visit https://docs.bazzite.gg/General/Installation_Guide/Installing_Bazzite_for_Desktop_or_Laptop_Hardware/
2. Download ISO using their image picker
3. Follow their documentation for calculating SHA256 checksums
4. Manually update the JSON file with correct checksum

**Important**: The placeholder checksum (`0000...`) in the JSON files **must** be replaced with the actual checksum before downloading.

## Checksum Sources

| Distribution | Checksum File Location | Format |
|--------------|------------------------|--------|
| CachyOS Desktop | `<iso_url>.sha256` | `checksum  filename` |
| CachyOS Handheld | `<iso_url>.sha256` | `checksum  filename` |
| Parrot OS | `https://download.parrotsec.org/parrot/iso/<version>/sha256.txt` | GPG-signed list |
| openSUSE Tumbleweed | `<iso_url>.sha256` | `checksum  filename` |
| Bazzite | Manual - see docs.bazzite.gg | Various |

## Adding More Distributions

To add support for additional distributions:

1. **Create JSON file** in `luxusb/data/distros/`:
   ```json
   {
     "id": "distro-id",
     "name": "Distribution Name",
     "family": "arch|debian|fedora|independent",
     "category": "Desktop|Gaming|Security|etc",
     "releases": [...]
   }
   ```

2. **Add updater method** in `luxusb/utils/distro_updater.py`:
   ```python
   def update_mydistro(self) -> Optional[DistroRelease]:
       # Fetch from official sources
       # Return DistroRelease with version, iso_url, sha256, etc.
   ```

3. **Add fetcher method** in `scripts/fetch_checksums.py`:
   ```python
   def fetch_mydistro_checksum(self, iso_url: str) -> Optional[str]:
       # Fetch checksum from official source
       # Return sha256 string
   ```

4. **Register in updater dictionaries**:
   - Add to `updaters` dict in `update_all()`
   - Add to `fetchers` dict in `fetch_checksum()`

## Troubleshooting

### Checksum Mismatch

If automated fetcher reports a different checksum:

1. Verify the fetcher is parsing the correct checksum file
2. Check if distribution released a new version
3. Manually verify checksum from official source
4. Run updater to update JSON file

### GPG Verification Fails

For distributions with GPG signatures (Parrot OS, openSUSE):

1. Import the distribution's GPG key first
2. Check `luxusb/data/gpg_keys.json` for key configuration
3. Verify signature manually using `gpg --verify`

### Network Errors

- Check mirror availability
- Try alternative mirrors listed in JSON
- Increase timeout in updater code if needed

## Security Considerations

- **Always verify checksums** before using ISOs
- **Check GPG signatures** when available
- **Use official mirrors** listed in distribution documentation
- **Update regularly** to get latest security patches
- **Placeholder checksums** (`0000...`) indicate manual verification needed

## See Also

- [DISTRO_MANAGEMENT.md](DISTRO_MANAGEMENT.md) - General distro management guide
- [GPG_VERIFICATION.md](GPG_VERIFICATION.md) - GPG signature verification details
- [distro-schema.json](../luxusb/data/distro-schema.json) - JSON schema for distributions

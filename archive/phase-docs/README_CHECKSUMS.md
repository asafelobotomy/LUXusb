# Checksum Fetcher

Automated tool to fetch official SHA256 checksums for Linux distributions.

## Features

✅ **Automated Fetching**: Retrieves checksums from official sources  
✅ **Verification**: Compares fetched checksums with current values  
✅ **Multiple Sources**: Supports 8 major distributions  
✅ **Safe Updates**: Shows differences before updating  

## Supported Distributions

| Distribution | Status | Source |
|-------------|--------|--------|
| Ubuntu | ✅ Working | releases.ubuntu.com |
| Fedora | ✅ Working | download.fedoraproject.org |
| Debian | ⚠️ Partial | cdimage.debian.org (version-dependent) |
| Linux Mint | ✅ Working | mirrors.kernel.org |
| Pop!_OS | ✅ Working | iso.pop-os.org |
| Manjaro | ✅ Working | download.manjaro.org |
| Zorin OS | ⚠️ Manual | help.zorin.com (HTML parsing) |
| elementary OS | ⚠️ Manual | elementary.io (latest version only) |

## Installation

```bash
# Install required dependency
pip install beautifulsoup4
```

## Usage

### Check All Distributions

```bash
python scripts/fetch_checksums.py
```

### Check Specific Distribution

```bash
python scripts/fetch_checksums.py --distro manjaro
```

### Available Distribution IDs

- `ubuntu` - Ubuntu Desktop
- `fedora` - Fedora Workstation
- `debian` - Debian
- `linuxmint` - Linux Mint
- `popos` - Pop!_OS
- `manjaro` - Manjaro
- `zorin` - Zorin OS
- `elementary` - elementary OS

## Example Output

```
======================================================================
  LUXusb Checksum Fetcher
======================================================================

Processing 8 distribution(s)...

======================================================================
Fetching checksum for: manjaro
======================================================================
📥 Fetching: https://download.manjaro.org/xfce/23.1.3/manjaro-xfce-23.1.3-240113-linux66.iso.sha256
✅ Found checksum: 2709aafc15ea39c4...

======================================================================
  SUMMARY
======================================================================

Manjaro 23.1.3 (Vulcan):
  Status:  ✅ MATCH
  Current: 2709aafc15ea39c4...
  Fetched: 2709aafc15ea39c4...
```

## How It Works

### 1. Ubuntu
Fetches from `https://releases.ubuntu.com/{version}/SHA256SUMS`

### 2. Fedora
Fetches from official CHECKSUM file in the release directory

### 3. Debian
Fetches from `SHA256SUMS` file in the ISO directory (note: "current" may not match specific versions)

### 4. Linux Mint
Fetches from `sha256sum.txt` in the version directory

### 5. Pop!_OS
Fetches from `SHA256SUMS` file in the build directory

### 6. Manjaro
Fetches from `.sha256` file alongside the ISO

### 7. Zorin OS
Parses checksums from official help documentation (requires HTML parsing)

### 8. elementary OS
Parses checksums from installation documentation (shows latest version)

## Known Limitations

1. **Version Matching**: Some distributions (Debian, elementary OS) may show checksums for different versions than configured
2. **Network Timeouts**: Large checksum files or slow mirrors may timeout
3. **HTML Parsing**: Zorin and elementary OS require parsing HTML which may break if pages change
4. **Manual Verification**: Always verify checksums from multiple sources for production use

## Adding New Distributions

To add support for a new distribution:

1. Add a new method `fetch_DISTRO_checksum()` in `ChecksumFetcher` class
2. Document the checksum file location and format
3. Add the method to the `fetchers` dictionary in `fetch_checksum()`
4. Test with `--distro DISTRO_ID`

Example:

```python
def fetch_newdistro_checksum(self, iso_url: str) -> Optional[str]:
    """
    Fetch NewDistro checksum from official source
    
    Example URL: https://example.com/isos/newdistro-1.0.iso
    Checksum file: https://example.com/isos/SHA256SUMS
    """
    try:
        iso_dir = iso_url.rsplit('/', 1)[0]
        iso_filename = iso_url.split('/')[-1]
        checksum_url = f"{iso_dir}/SHA256SUMS"
        
        response = self.session.get(checksum_url, timeout=10)
        response.raise_for_status()
        
        # Parse and return checksum
        for line in response.text.splitlines():
            if iso_filename in line:
                return line.split()[0]
        
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
```

## Future Enhancements

- [ ] Automatic update of distro_manager.py with `--update` flag
- [ ] Caching of fetched checksums
- [ ] Parallel fetching for better performance
- [ ] GPG signature verification
- [ ] Support for torrent file checksums
- [ ] JSON output format for automation

## Troubleshooting

### "Read timed out"
Increase timeout or check network connectivity:
```python
response = self.session.get(checksum_url, timeout=30)  # Increase from 10
```

### "Checksum not found"
Verify the ISO filename matches exactly what's in the checksum file. Check for:
- Version number differences
- Date stamps in filename
- Architecture suffixes (amd64, x86_64)

### "Different checksum"
This could mean:
1. Checksum file updated for newer release
2. ISO URL points to different version
3. Typo in configured checksum

Always verify manually before updating!

## Security Notes

- Always verify checksums from **official sources only**
- Cross-reference checksums with multiple mirrors when possible
- For production use, implement GPG signature verification
- Never blindly trust automated checksum updates
- Log all checksum changes for audit purposes

## License

Part of LUXusb project - see main LICENSE file

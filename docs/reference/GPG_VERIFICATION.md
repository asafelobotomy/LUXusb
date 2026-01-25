# GPG Signature Verification

LUXusb implements **two-layer security verification** for all downloaded ISO images:

1. **SHA256 Checksum** (Integrity) - Verifies the file wasn't corrupted during download
2. **GPG Signature** (Authenticity) - Verifies the file came from the official distributor

## Overview

When LUXusb updates distro metadata or downloads ISOs, it now verifies GPG signatures on checksum files to ensure they haven't been tampered with. This provides cryptographic proof that checksums come from official sources, protecting against:

- **Compromised mirrors** serving malicious ISOs
- **Man-in-the-middle attacks** modifying downloads
- **Tampered checksum files** on mirrors

## Implementation Status

### ✅ GPG-Verified Distributions

| Distribution | Checksum File | Signature File | Verification Type | Status |
|-------------|---------------|----------------|------------------|--------|
| **Ubuntu** | SHA256SUMS | SHA256SUMS.gpg | Detached | ✅ **VERIFIED** |
| **Debian** | SHA256SUMS | SHA256SUMS.sign | Detached | ✅ **VERIFIED** |
| **Kali Linux** | SHA256SUMS | SHA256SUMS.gpg | Detached | ✅ **VERIFIED** |
| **Linux Mint** | sha256sum.txt | sha256sum.txt.gpg | Detached | ✅ **VERIFIED** |
| **Pop!_OS** | SHA256SUMS | SHA256SUMS.gpg | Detached | ✅ **VERIFIED** |
| **openSUSE** | *.sha256 | *.sha256.asc | Detached | ✅ **VERIFIED** |
| **Fedora** | *-CHECKSUM | embedded | Embedded (cleartext) | ✅ **VERIFIED** |
| **ParrotOS** | signed-hashes.txt | embedded | Embedded (cleartext) | ✅ **VERIFIED** |
| **Manjaro** | *.iso.sha256 | *.iso.sig | Per-ISO | ✅ **VERIFIED** |
| **CachyOS Desktop** | *.iso.sha256 | *.iso.sig | Per-ISO | ✅ **VERIFIED** |
| **CachyOS Handheld** | *.iso.sha256 | *.iso.sig | Per-ISO | ✅ **VERIFIED** |
| **Arch Linux** | - | - | API-signed | ✅ **VERIFIED** |

### 🔐 Cosign-Verified Distributions

| Distribution | Verification Method | Status |
|-------------|-------------------|--------|
| **Bazzite Desktop** | Cosign (3-tier fallback) | ✅ **VERIFIED** |
| **Bazzite Handheld** | Cosign (3-tier fallback) | ✅ **VERIFIED** |

**GPG Verification Types:**

- **Detached** - Separate .gpg/.asc signature file verifies the checksum file
- **Embedded** - Cleartext-signed file with embedded PGP signature
- **Per-ISO** - Individual .sig file for each ISO release
- **API-signed** - Official API with cryptographic signing
- **Cosign** - Container signature verification with Sigstore/Fulcio

**Status: 14/14 distributions (100%) use cryptographic verification** ✅

## GPG Keys Database

Official GPG keys for all distributions are stored in [`luxusb/data/gpg_keys.json`](../luxusb/data/gpg_keys.json):

```json
{
  "ubuntu": {
    "key_id": "843938DF228D22F7B3742BC0D94AA3F0EFE21092",
    "fingerprint": "8439 38DF 228D 22F7 B374  2BC0 D94A A3F0 EFE2 1092",
    "signature_file": "SHA256SUMS.gpg"
  }
}
```

### Key Properties

- **key_id**: GPG key identifier for importing from keyservers
- **key_server**: Keyserver to fetch key from (e.g., `keyserver.ubuntu.com`)
- **key_url**: Official URL with key information/download
- **fingerprint**: Key fingerprint for manual verification
- **signature_file**: Expected signature file name pattern

## How It Works

### 1. Automatic Key Import

When verifying a distribution for the first time, LUXusb automatically imports the official GPG key from a keyserver:

```python
from luxusb.utils.gpg_verifier import GPGVerifier

verifier = GPGVerifier()
verifier.import_key('ubuntu')  # Imports from keyserver.ubuntu.com
```

Keys are stored in your system's GPG keyring (~/.gnupg/) and reused for future verifications.

### 2. Signature Verification During Updates

When the distro updater fetches new ISO metadata:

```python
# Download checksum file
sha_response = session.get("https://releases.ubuntu.com/24.04/SHA256SUMS")

# Download GPG signature
sig_response = session.get("https://releases.ubuntu.com/24.04/SHA256SUMS.gpg")

# Verify signature
success, message = verifier.verify_checksum_signature(
    sha_response.text,
    sig_response.content,
    "ubuntu"
)

# Only trust checksums if signature is valid
if success:
    # Extract SHA256 for ISO
    sha256 = extract_checksum(sha_response.text)
```

### 3. Graceful Degradation

If GPG is not available or verification fails:

- **Warning is logged** but update continues
- `gpg_verified` field set to `False` in metadata
- SHA256 checksum still verified during download
- Users warned in GUI about unverified checksums

## Verification Examples

### Test GPG Verifier

```bash
python -c "
from luxusb.utils.gpg_verifier import GPGVerifier

verifier = GPGVerifier()
print('GPG Available:', verifier.is_available())
print('Supported distros:', verifier.get_supported_distros())

# Test Ubuntu key
key_info = verifier.get_key_info('ubuntu')
print(f'Ubuntu key: {key_info.fingerprint}')
"
```

### Test Distro Update with GPG

```bash
python -c "
from luxusb.utils.distro_updater import DistroUpdater

updater = DistroUpdater()
release = updater.update_ubuntu()

print(f'Version: {release.version}')
print(f'SHA256: {release.sha256[:16]}...')
print(f'GPG Verified: {release.gpg_verified}')
"
```

### Manual GPG Verification (Ubuntu example)

```bash
# Download files
cd /tmp
wget https://releases.ubuntu.com/24.04/ubuntu-24.04.3-desktop-amd64.iso
wget https://releases.ubuntu.com/24.04/SHA256SUMS
wget https://releases.ubuntu.com/24.04/SHA256SUMS.gpg

# Import Ubuntu key
gpg --keyserver keyserver.ubuntu.com --recv-keys 843938DF228D22F7B3742BC0D94AA3F0EFE21092

# Verify signature
gpg --verify SHA256SUMS.gpg SHA256SUMS

# Should output: "Good signature from Ubuntu CD Image Automatic Signing Key"

# Verify ISO checksum
sha256sum -c SHA256SUMS 2>&1 | grep ubuntu-24.04.3-desktop-amd64.iso
```

## Architecture

### Components

**[`luxusb/utils/gpg_verifier.py`](../luxusb/utils/gpg_verifier.py)** - GPG verification module

- Manages GPG key import and verification
- Verifies detached signatures (.gpg, .sig files)
- Verifies embedded signatures (Fedora CHECKSUM files)
- Handles signature validation and error reporting

**[`luxusb/utils/distro_updater.py`](../luxusb/utils/distro_updater.py)** - Metadata updater

- Fetches latest ISO releases from official sources
- Downloads checksum files and GPG signatures
- Verifies signatures before trusting checksums
- Sets `gpg_verified` field in `DistroRelease` dataclass

**[`luxusb/data/gpg_keys.json`](../luxusb/data/gpg_keys.json)** - GPG key database

- Official GPG keys for all 8 distributions
- Key IDs, fingerprints, and keyserver info
- Signature file naming patterns

### Verification Workflow

```text
1. Distro Updater runs
   ↓
2. Fetches checksum file (SHA256SUMS)
   ↓
3. Fetches signature file (SHA256SUMS.gpg)
   ↓
4. GPG Verifier checks if key imported
   ↓ (if not)
5. Imports key from keyserver
   ↓
6. Verifies signature: gpg --verify SHA256SUMS.gpg SHA256SUMS
   ↓
7. If "Good signature" → trust checksums
   If "BAD signature" → reject and warn
   If GPG unavailable → warn but continue (degraded mode)
   ↓
8. Extract ISO checksum from verified file
   ↓
9. Save to distro JSON with gpg_verified=true
```

## Security Considerations

### Trust Model

LUXusb follows the **"Trust on First Use" (TOFU)** model:

1. **First run**: GPG keys automatically imported from keyservers
2. **Keyserver trust**: Assumes keyservers (keyserver.ubuntu.com, etc.) are trustworthy
3. **Key pinning**: Key IDs hardcoded in `gpg_keys.json` prevent key substitution
4. **Fingerprint verification**: Users can manually verify fingerprints match official sources

### Threat Protection

✅ **Protected Against:**

- Compromised mirrors serving tampered ISOs
- Man-in-the-middle attacks on downloads
- Malicious checksum file modifications
- Mirror drift/stale metadata

⚠️ **Not Protected Against:**

- Compromised keyservers (on first import)
- Compromised official distro signing keys
- Attacks before first GPG verification run

### Best Practices

**For Users:**

1. **Verify fingerprints** manually on first run (optional but recommended):

   ```bash
   gpg --fingerprint 843938DF228D22F7B3742BC0D94AA3F0EFE21092
   # Compare with https://ubuntu.com/tutorials/how-to-verify-ubuntu
   ```

2. **Keep GPG updated**: `sudo apt update && sudo apt install gnupg`

3. **Check logs**: Look for "✓ Valid GPG signature" in update logs

**For Developers:**

1. **Update keys annually**: Check official distro sites for key changes
2. **Test verification**: Run `python -m luxusb.utils.distro_updater` regularly
3. **Monitor failures**: Log and alert on GPG verification failures

## Troubleshooting

### GPG Not Available

**Symptom**: Warning "GPG not available - signature verification disabled"

**Solution**:
```bash
# Install GPG
sudo apt install gnupg  # Debian/Ubuntu
sudo pacman -S gnupg    # Arch
```

### Key Import Fails

**Symptom**: "Failed to import key from keyserver"

**Solutions**:

1. Check internet connection
2. Try alternate keyserver:

   ```bash
   gpg --keyserver keys.openpgp.org --recv-keys <KEY_ID>
   ```


3. Manually import from URL in `gpg_keys.json`

### Signature Verification Fails

**Symptom**: "✗ GPG signature verification failed"

**Investigation**:

1. Check if signature file downloaded correctly
2. Verify key is imported: `gpg --list-keys`
3. Check distro's official verification docs
4. Try manual verification (see examples above)

### "BAD signature" Error

**⚠️ CRITICAL**: This indicates potential tampering!

**Actions**:

1. **DO NOT USE THE ISO**
2. Try different mirror
3. Re-download checksum files
4. Report to distro security team
5. Check distro's status page for known issues

## Future Enhancements

### Planned (Medium Priority)

- [ ] GUI indicator showing "GPG Verified" badge per distro
- [ ] Config option for strict GPG mode (fail on unverified)
- [ ] Support Fedora embedded signatures (`gpg --verify-files`)
- [ ] Support Manjaro per-ISO signatures (`.iso.sig`)

### Considered (Low Priority)

- [ ] Local GPG keyring caching
- [ ] Key fingerprint verification UI
- [ ] Automatic key refresh/expiry checking
- [ ] Support for multiple signing keys per distro

## References

### Official Verification Documentation

- **Ubuntu**: https://ubuntu.com/tutorials/how-to-verify-ubuntu
- **Debian**: https://www.debian.org/CD/verify
- **Kali**: https://www.kali.org/docs/introduction/download-images-securely/
- **Linux Mint**: https://linuxmint-installation-guide.readthedocs.io/en/latest/verify.html
- **Arch Linux**: https://archlinux.org/download/ (ISO signatures section)
- **Fedora**: https://getfedora.org/security/
- **Manjaro**: https://forum.manjaro.org/t/root-tip-how-to-verify-iso-signature/146680

### GPG Resources

- **GPG Manual**: https://www.gnupg.org/documentation/manuals/gnupg/
- **Ubuntu Keyserver**: https://keyserver.ubuntu.com/
- **Linux Integrity Guide**: https://linuxsecurity.com/news/server-security/checksums-in-linux-integrity-guide

---

**Last Updated**: January 2026  
**Status**: ✅ **5/8 distros fully verified, 2/8 partial, 1/8 API-signed**

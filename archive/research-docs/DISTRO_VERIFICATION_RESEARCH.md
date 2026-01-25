# Distribution Verification Enhancement Research

**Date**: January 22, 2026  
**Purpose**: Research alternative verification methods for distributions rated below "Excellent"  
**Scope**: Linux Mint, Fedora, Kali, Pop!_OS, ParrotOS, openSUSE, Manjaro, CachyOS

## Executive Summary

Comprehensive research of 8 distributions revealed **significant opportunities** for verification improvements:

- **2 distributions** can leverage GPG-signed CHECKSUM files with embedded signatures
- **3 distributions** already provide comprehensive GPG verification instructions but need implementation
- **2 distributions** have manual checksum verification only (no cryptographic verification available)
- **1 distribution** (CachyOS) has potential for cosign verification research

**Key Finding**: Most distributions already provide GPG verification infrastructure; LUXusb simply needs to implement what's officially documented.

---

## Distribution-by-Distribution Analysis

### 1. Linux Mint (Good ⭐⭐⭐⭐)

**Current LUXusb Status**: GPG verification, hardcoded to version 22

**Official Verification Method Found**:
- ✅ **GPG Signature**: `sha256sum.txt.gpg` signs the `sha256sum.txt` file
- ✅ **Signing Key**: `27DEB15644C6B3CF3BD7D291300F846BA25BAE09` (Linux Mint ISO Signing Key)
- ✅ **Verification Workflow**:
  ```bash
  gpg --keyserver hkp://keys.openpgp.org:80 --recv-key 27DEB15644C6B3CF3BD7D291300F846BA25BAE09
  gpg --verify sha256sum.txt.gpg sha256sum.txt
  grep linuxmint-*.iso sha256sum.txt | sha256sum -c
  ```
- ✅ **Built-in Tool**: Linux Mint provides `mint-iso-verify` command for automated verification

**Recommendation**: 
- **Status**: Already implemented correctly
- **Enhancement**: Add version detection (currently hardcoded to 22)
- **Priority**: LOW (already "Good" rating)

**Sources**:
- https://linuxmint-installation-guide.readthedocs.io/en/latest/verify.html
- https://www.linuxmint.com/mirrors.php
- https://mirrors.kernel.org/linuxmint/stable/

---

### 2. Fedora (Adequate ⭐⭐⭐)

**Current LUXusb Status**: GPG marked as False, basic SHA256 verification

**Official Verification Method Found**:
- ✅ **GPG-Signed CHECKSUM Files**: Fedora's `*-CHECKSUM` files contain **embedded GPG signatures**
- ✅ **Signing Keys**: 
  - Fedora 43: `C6E7F081CF80E1314667 6E88829B60663164 5531`
  - Fedora 42: `B0F49504 58F69E1150C6 C5EDC8AC4916105EF944`
  - Fedora 41: `466CF2D8 B60BC3057AA9 453ED0622462E99D6AD1`
- ✅ **Download Key Bundle**: `https://fedoraproject.org/fedora.gpg`
- ✅ **Verification Workflow (Official)**:
  ```bash
  curl -O https://fedoraproject.org/fedora.gpg
  gpgv --keyring ./fedora.gpg Fedora-Workstation-43-*-CHECKSUM
  sha256sum -c --ignore-missing Fedora-Workstation-43-*.iso
  ```
- ✅ **Alternative**: Use `sq` (Sequoia-PGP) instead of gpgv

**Key Insight**: The CHECKSUM file **IS** the signature file (cleartext-signed format). No separate .sig or .gpg file needed.

**Recommendation**:
- **Action**: Implement GPG verification for Fedora CHECKSUM files
- **Method**: Download CHECKSUM file, verify embedded signature with gpgv/sq, then verify ISO checksum
- **Upgrade**: Adequate → **Good** (⭐⭐⭐⭐)
- **Priority**: HIGH (direct path to improvement)

**Implementation Notes**:
```python
# Workflow
1. Download: https://download.fedoraproject.org/.../Fedora-Workstation-43-*-CHECKSUM
2. Download Fedora GPG keyring: https://fedoraproject.org/fedora.gpg
3. Verify embedded signature: gpgv --keyring fedora.gpg <CHECKSUM_FILE>
4. Extract SHA256 from verified CHECKSUM file
5. Verify ISO: sha256sum -c <CHECKSUM_FILE>
```

**Sources**:
- https://fedoraproject.org/security/
- https://getfedora.org/security/
- Official documentation: "Verify with CHECKSUM files"

---

### 3. Kali Linux (Adequate ⭐⭐⭐)

**Current LUXusb Status**: GPG verification attempted but often fails

**Official Verification Method Found**:
- ✅ **SHA256SUMS + SHA256SUMS.gpg**: Separate signature file (detached signature)
- ✅ **Signing Key**: `827C8569F2518CC677FECA1AED65462EC8D5E4C5` (Kali Linux Archive Automatic Signing Key 2025)
- ✅ **Verification Workflow**:
  ```bash
  wget -q -O - https://archive.kali.org/archive-key.asc | gpg --import
  gpg --verify SHA256SUMS.gpg SHA256SUMS
  grep kali-linux-*.iso SHA256SUMS | shasum -a 256 -c
  ```
- ✅ **Three-Tier Verification** (Official Documentation):
  1. **Basic**: Manual checksum comparison (lowest assurance)
  2. **Better**: Torrent with .txt.sha256sum file (automatic verification)
  3. **Best**: GPG verification of SHA256SUMS file (highest assurance)

**Key Insight**: Kali provides the **most detailed verification documentation** of all distros researched.

**Recommendation**:
- **Status**: Currently implemented, but may need troubleshooting
- **Action**: Verify GPG key import and signature verification logic
- **Enhancement**: Implement all 3 tiers as fallback options
- **Priority**: MEDIUM (already attempted, needs debugging)

**Sources**:
- https://www.kali.org/docs/introduction/download-official-kali-linux-images/
- https://archive.kali.org/archive-key.asc
- https://cdimage.kali.org/current/ (SHA256SUMS + SHA256SUMS.gpg files)

---

### 4. Pop!_OS (Adequate ⭐⭐⭐)

**Current LUXusb Status**: Fixed - removed placeholder checksum, added 24.04/22.04 detection

**Official Verification Method Found**:
- ✅ **SHA256 Checksums**: Available on download page
- ❌ **No GPG Signatures**: Pop!_OS does **NOT** provide GPG signatures for ISO files
- ✅ **Verification Workflow (Manual)**:
  ```bash
  sha256sum Downloads/pop-os_*.iso
  # Compare with value on https://system76.com/pop/download/
  ```
- ❌ **No API**: No programmatic way to fetch checksums

**Key Insight**: System76 focuses on manual verification. No cryptographic signatures available.

**Recommendation**:
- **Status**: Best possible given limitations
- **Action**: None (already using official checksums from download page)
- **Rating**: Adequate ⭐⭐⭐ (cannot upgrade without GPG signatures)
- **Priority**: NONE (no better method available)

**Sources**:
- https://support.system76.com/articles/live-disk/
- https://system76.com/pop/download/
- https://github.com/pop-os/iso (build scripts only, no checksums)

---

### 5. ParrotOS (Adequate ⭐⭐⭐)

**Current LUXusb Status**: Fixed - removed placeholder checksum

**Official Verification Method Found**:
- ✅ **SHA256 Checksums**: Available on download mirrors
- ❌ **No GPG Signatures**: ParrotOS does **NOT** provide GPG signatures
- ✅ **Verification Workflow**:
  ```bash
  # Download from: https://deb.parrot.sh/parrot/iso/
  sha256sum parrot-*.iso
  # Compare with .sha256 file on server
  ```
- ❌ **No Signing**: GitHub repo contains build scripts but no verification infrastructure

**Key Insight**: Parrot provides checksums but no cryptographic verification.

**Recommendation**:
- **Status**: Best possible given limitations
- **Action**: None (already using official checksums from mirrors)
- **Rating**: Adequate ⭐⭐⭐ (cannot upgrade without signatures)
- **Priority**: NONE (no better method available)

**Sources**:
- https://parrotsec.org/download/
- https://deb.parrot.sh/parrot/iso/
- https://github.com/ParrotSec/parrot-iso-build (build configs only)

---

### 6. openSUSE Tumbleweed (Adequate ⭐⭐⭐)

**Current LUXusb Status**: Basic SHA256 verification from .sha256 file

**Official Verification Method Found**:
- ✅ **SHA256SUMS + .asc Signature**: Separate signature file
- ✅ **Signing Key**: `AD485664E901B867051AB15F35A2F86E29B700A4` (openSUSE Project Signing Key)
  - **Current Key** (rsa4096, expires 2026-06-19)
  - **Legacy Key**: `22C07BA534178CD02EFE22AAB88B2FD43DBDC284` (rsa2048, expired 2024-05-02)
- ✅ **Verification Workflow**:
  ```bash
  gpg --keyserver keyserver.ubuntu.com --recv-keys 0xAD485664E901B867051AB15F35A2F86E29B700A4
  gpg --fingerprint "openSUSE Project Signing Key <opensuse@opensuse.org>"
  gpg --verify openSUSE-Tumbleweed-*.iso.sha256.asc openSUSE-Tumbleweed-*.iso.sha256
  sha256sum -c openSUSE-Tumbleweed-*.iso.sha256
  ```
- ✅ **Alternative**: Download pre-packaged key from `/usr/lib/rpm/gnupg/keys/gpg-pubkey-*.asc`

**Key Insight**: openSUSE provides **comprehensive GPG verification** with detailed documentation.

**Recommendation**:
- **Action**: Implement GPG verification for openSUSE .sha256.asc files
- **Method**: Download .sha256 + .sha256.asc, verify signature, extract checksum
- **Upgrade**: Adequate → **Good** (⭐⭐⭐⭐)
- **Priority**: HIGH (direct path to improvement)

**Sources**:
- https://en.opensuse.org/SDB:Download_help
- https://download.opensuse.org/tumbleweed/iso/
- https://news.opensuse.org/2023/01/23/new-4096-bit-signing-key/

---

### 7. Manjaro (Needs Improvement ⭐⭐)

**Current LUXusb Status**: Complex fallback logic, GPG marked as attempted

**Official Verification Method Found**:
- ✅ **Individual ISO Signatures**: Manjaro provides `.iso.sig` files for **each ISO**
- ✅ **Signing Keys**: Available from official Manjaro keyservers
- ✅ **Verification Workflow**:
  ```bash
  # For each ISO, download corresponding .sig file
  gpg --recv-key <MANJARO_SIGNING_KEY>
  gpg --verify manjaro-*.iso.sig manjaro-*.iso
  ```
- ⚠️ **Multiple Editions**: Different ISOs (KDE, GNOME, XFCE) each have separate .sig files
- ❌ **No Unified CHECKSUM**: No single checksum file with all editions

**Key Insight**: Manjaro uses **per-ISO signature files** rather than checksum lists.

**Recommendation**:
- **Action**: Implement .iso.sig verification for Manjaro
- **Method**: For each ISO URL, append `.sig` and verify with GPG
- **Enhancement**: Simplify existing complex fallback logic
- **Upgrade**: Needs Improvement → **Good** (⭐⭐⭐⭐)
- **Priority**: HIGH (clear improvement path)

**Implementation Notes**:
```python
# Workflow
1. Detect ISO URL: https://download.manjaro.org/.../manjaro-xfce-*.iso
2. Construct .sig URL: https://download.manjaro.org/.../manjaro-xfce-*.iso.sig
3. Download both ISO and .sig
4. Verify: gpg --verify manjaro-*.iso.sig manjaro-*.iso
```

**Sources**:
- https://manjaro.org/download/
- https://wiki.manjaro.org/index.php/Burn_an_ISO_File
- https://download.manjaro.org/ (mirrors with .sig files)

---

### 8. CachyOS (Needs Improvement ⭐⭐)

**Current LUXusb Status**: Fixed - removed placeholder checksums

**Official Verification Method Found**:
- ✅ **SHA256 Checksums**: Available on download page
- ❌ **No GPG Signatures**: CachyOS does **NOT** provide GPG signatures for ISOs
- ❌ **No API**: No programmatic way to fetch checksums
- 🔬 **Cosign Research Opportunity**: CachyOS is Arch-based like Bazzite
  - Uses container technology (similar to Bazzite)
  - May sign container images with cosign
  - **Unconfirmed**: No evidence found in official sources

**Key Insight**: CachyOS provides basic checksums only, but **may** support cosign for containers.

**Recommendation**:
- **Immediate**: Use existing SHA256 checksums from download page (already implemented)
- **Research**: Investigate if CachyOS signs container images with cosign
  - Check https://github.com/CachyOS for signing infrastructure
  - Contact CachyOS team via Discord/Forum for verification methods
  - If cosign available: Add to `cosign_keys.json` and implement like Bazzite
- **Rating**: Adequate ⭐⭐⭐ (with current checksums)
- **Potential**: Good ⭐⭐⭐⭐ (if cosign implemented)
- **Priority**: LOW (research required first)

**Sources**:
- https://cachyos.org/
- https://github.com/CachyOS
- https://wiki.cachyos.org/

---

## Summary of Findings

### Immediate Implementation Opportunities (HIGH Priority)

1. **Fedora**: Implement GPG verification of embedded-signature CHECKSUM files
   - **Impact**: Adequate → Good (⭐⭐⭐⭐)
   - **Effort**: Medium (gpgv integration)
   - **Files**: `luxusb/utils/distro_updater.py` - update_fedora()

2. **openSUSE**: Implement GPG verification of .sha256.asc files
   - **Impact**: Adequate → Good (⭐⭐⭐⭐)
   - **Effort**: Medium (detached signature verification)
   - **Files**: `luxusb/utils/distro_updater.py` - update_opensuse_tumbleweed()

3. **Manjaro**: Implement per-ISO .sig file verification
   - **Impact**: Needs Improvement → Good (⭐⭐⭐⭐)
   - **Effort**: Medium (per-ISO signature logic)
   - **Files**: `luxusb/utils/distro_updater.py` - update_manjaro()

### Enhancement Opportunities (MEDIUM Priority)

4. **Kali Linux**: Debug existing GPG verification
   - **Impact**: Ensure reliability
   - **Effort**: Low (troubleshooting)
   - **Files**: `luxusb/utils/distro_updater.py` - update_kali()

5. **Linux Mint**: Add version detection
   - **Impact**: Usability improvement
   - **Effort**: Low (version detection logic)
   - **Files**: `luxusb/utils/distro_updater.py` - update_linuxmint()

### Research Opportunities (LOW Priority)

6. **CachyOS**: Investigate cosign support
   - **Impact**: Needs Improvement → Good (if cosign available)
   - **Effort**: High (research + implementation)
   - **Action**: Contact CachyOS team, check container signing

### No Further Action (Limitations)

7. **Pop!_OS**: No GPG signatures available
   - **Current**: Best possible with manual checksums
   - **Rating**: Adequate ⭐⭐⭐ (cannot improve)

8. **ParrotOS**: No GPG signatures available
   - **Current**: Best possible with SHA256 checksums
   - **Rating**: Adequate ⭐⭐⭐ (cannot improve)

---

## Verification Method Matrix

| Distribution | Current Method | Available Method | Implementation Needed |
|--------------|----------------|------------------|-----------------------|
| Linux Mint   | GPG + SHA256   | GPG + SHA256 ✅  | Version detection     |
| Fedora       | SHA256 only    | GPG-signed CHECKSUM ✅ | **GPG verification** |
| Kali         | GPG + SHA256   | GPG + SHA256 ✅  | Debug existing GPG    |
| Pop!_OS      | SHA256 only    | SHA256 only ❌   | None (no GPG)         |
| ParrotOS     | SHA256 only    | SHA256 only ❌   | None (no GPG)         |
| openSUSE     | SHA256 only    | GPG + SHA256 ✅  | **GPG verification**  |
| Manjaro      | Complex fallback | .iso.sig ✅    | **.sig verification** |
| CachyOS      | SHA256 only    | Cosign? 🔬       | Research needed       |

---

## Implementation Priority

### Phase 1: High-Impact GPG Implementations
1. **Fedora** - GPG-signed CHECKSUM files (embedded signatures)
2. **openSUSE** - .sha256.asc detached signatures
3. **Manjaro** - .iso.sig per-ISO signatures

**Expected Outcome**: 3 distributions upgraded from ⭐⭐⭐ or ⭐⭐ to ⭐⭐⭐⭐

### Phase 2: Reliability & Usability
4. **Kali** - Debug GPG verification reliability
5. **Linux Mint** - Version detection (22 → 22/21/other)

**Expected Outcome**: 2 distributions with enhanced reliability/usability

### Phase 3: Research & Exploration
6. **CachyOS** - Investigate cosign container signing
7. **Pop!_OS** - Monitor for future GPG support
8. **ParrotOS** - Monitor for future GPG support

**Expected Outcome**: Potential future improvements

---

## Technical Implementation Notes

### GPG Verification Patterns

#### Pattern 1: Embedded Signature (Fedora)
```python
# CHECKSUM file contains cleartext-signed data
result = subprocess.run([
    'gpgv', '--keyring', 'fedora.gpg', 'Fedora-*-CHECKSUM'
], capture_output=True, text=True)
if result.returncode == 0:
    # Signature valid, extract SHA256
    checksum = extract_sha256_from_checksum_file('Fedora-*-CHECKSUM')
```

#### Pattern 2: Detached Signature (openSUSE, Kali)
```python
# Separate .asc/.gpg file signs the checksum file
result = subprocess.run([
    'gpg', '--verify', 'SHA256SUMS.gpg', 'SHA256SUMS'
], capture_output=True, text=True)
if 'Good signature' in result.stderr:
    # Signature valid, use checksums
    checksum = extract_sha256_from_file('SHA256SUMS', iso_name)
```

#### Pattern 3: Per-ISO Signature (Manjaro)
```python
# Each ISO has its own .sig file
result = subprocess.run([
    'gpg', '--verify', 'manjaro-xfce-*.iso.sig', 'manjaro-xfce-*.iso'
], capture_output=True, text=True)
if 'Good signature' in result.stderr:
    # ISO signature valid, proceed with download
```

### Key Management

**Recommendation**: Extend `luxusb/data/gpg_keys.json` with:

```json
{
  "fedora": {
    "key_id": "C6E7F081CF80E1314667 6E88829B60663164 5531",
    "fingerprint": "C6E7 F081 CF80 E131 4667 6E88 829B 6066 3164 5531",
    "key_server": "keyserver.ubuntu.com",
    "key_url": "https://fedoraproject.org/fedora.gpg",
    "signature_file": "Fedora-*-CHECKSUM",
    "checksum_file": "Fedora-*-CHECKSUM",
    "signature_type": "embedded"
  },
  "opensuse": {
    "key_id": "AD485664E901B867051AB15F35A2F86E29B700A4",
    "fingerprint": "AD48 5664 E901 B867 051A B15F 35A2 F86E 29B7 00A4",
    "key_server": "keyserver.ubuntu.com",
    "signature_file": "*.iso.sha256.asc",
    "checksum_file": "*.iso.sha256",
    "signature_type": "detached"
  },
  "manjaro": {
    "key_id": "<MANJARO_KEY_ID>",
    "fingerprint": "<MANJARO_FINGERPRINT>",
    "key_server": "keyserver.ubuntu.com",
    "signature_file": "*.iso.sig",
    "checksum_file": null,
    "signature_type": "per-iso"
  }
}
```

---

## Conclusion

This research reveals that **most distributions below "Excellent" already provide GPG verification infrastructure** — LUXusb simply needs to implement what's officially documented. By implementing GPG verification for Fedora, openSUSE, and Manjaro, LUXusb can upgrade **3 distributions** from Adequate/Needs Improvement to **Good** rating.

**Key Takeaways**:
1. ✅ **Fedora, openSUSE, Manjaro** have official GPG verification - implement it
2. ✅ **Kali, Linux Mint** already have GPG - enhance reliability/usability
3. ❌ **Pop!_OS, ParrotOS** have no GPG infrastructure - cannot improve
4. 🔬 **CachyOS** may support cosign - requires research

**Next Steps**:
1. Implement Phase 1 (Fedora, openSUSE, Manjaro GPG verification)
2. Update `gpg_keys.json` with new distribution keys
3. Test GPG verification in full environment
4. Document new verification methods in DISTRO_MANAGEMENT.md

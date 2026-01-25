#!/usr/bin/env python3
"""
Automated checksum fetcher for Linux distributions

This script automatically fetches SHA256 checksums from official sources
and can update distro_manager.py or output them for manual verification.

Usage:
    python scripts/fetch_checksums.py [--update] [--distro DISTRO_ID] [--cache]
"""

import re
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from bs4 import BeautifulSoup


class ChecksumFetcher:
    """Fetch SHA256 checksums from official distribution sources"""
    
    def __init__(self, cache_dir: Optional[Path] = None, use_cache: bool = False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LUXusb-ChecksumFetcher/0.1.0'
        })
        self.use_cache = use_cache
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'luxusb' / 'checksums'
        if use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cached_checksum(self, distro_id: str, iso_url: str) -> Optional[str]:
        """Get cached checksum if available and not expired (24 hours)"""
        if not self.use_cache:
            return None
        
        cache_file = self.cache_dir / f"{distro_id}.json"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Check if URL matches and cache is not expired (24 hours)
            if data.get('iso_url') == iso_url:
                cached_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cached_time < timedelta(hours=24):
                    return data['checksum']
        except Exception:
            pass
        
        return None
    
    def _save_cached_checksum(self, distro_id: str, iso_url: str, checksum: str):
        """Save checksum to cache"""
        if not self.use_cache:
            return
        
        cache_file = self.cache_dir / f"{distro_id}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'distro_id': distro_id,
                    'iso_url': iso_url,
                    'checksum': checksum,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to cache checksum: {e}")
    
    def fetch_ubuntu_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Ubuntu checksum from SHA256SUMS file
        
        Example URL: https://releases.ubuntu.com/24.04.1/ubuntu-24.04.1-desktop-amd64.iso
        Checksum file: https://releases.ubuntu.com/24.04.1/SHA256SUMS
        """
        try:
            # Extract version from URL - handle both 24.04 and 24.04.1 formats
            match = re.search(r'/(\d+\.\d+(?:\.\d+)?)/ubuntu-.*\.iso', iso_url)
            if not match:
                print(f"❌ Could not parse Ubuntu version from URL: {iso_url}")
                return None
            
            version = match.group(1)
            iso_filename = iso_url.split('/')[-1]
            
            # Extract base pattern for matching (e.g., "ubuntu-24.04-desktop-amd64.iso" -> "ubuntu", "24.04", "desktop", "amd64")
            iso_parts = iso_filename.replace('.iso', '').split('-')
            
            # Try both versioned and base version (24.04.1 -> also try 24.04)
            versions_to_try = [version]
            if '.' in version and version.count('.') == 2:  # e.g., 24.04.1
                base_version = '.'.join(version.split('.')[:2])  # e.g., 24.04
                versions_to_try.append(base_version)
            
            for ver in versions_to_try:
                base_url = f"https://releases.ubuntu.com/{ver}"
                checksum_url = f"{base_url}/SHA256SUMS"
                
                print(f"📥 Fetching: {checksum_url}")
                try:
                    response = self.session.get(checksum_url, timeout=15)
                    response.raise_for_status()
                    
                    # Parse SHA256SUMS file
                    # Find the line matching the pattern (handle version mismatches like 24.04 -> 24.04.3)
                    best_match = None
                    best_match_checksum = None
                    
                    for line in response.text.splitlines():
                        # Match by edition (desktop/server) and architecture
                        if len(iso_parts) >= 3:
                            edition = iso_parts[2] if len(iso_parts) > 2 else 'desktop'
                            arch = iso_parts[3] if len(iso_parts) > 3 else 'amd64'
                            
                            if edition in line and arch in line and '.iso' in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    best_match = line
                                    best_match_checksum = parts[0].strip('*')
                                    # Prefer exact filename match
                                    if iso_filename in line:
                                        print(f"✅ Found checksum (exact match): {best_match_checksum[:16]}...")
                                        return best_match_checksum
                    
                    if best_match_checksum:
                        print(f"✅ Found checksum (pattern match): {best_match_checksum[:16]}...")
                        print(f"ℹ️  Matched line: {best_match.strip()}")
                        return best_match_checksum
                        
                except requests.exceptions.RequestException:
                    if ver == versions_to_try[-1]:  # Last attempt
                        raise
                    continue  # Try next version
            
            print(f"❌ Checksum not found for {iso_filename}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Ubuntu checksum: {e}")
            return None
    
    def fetch_fedora_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Fedora checksum from CHECKSUM file
        
        Example URL: https://download.fedoraproject.org/pub/fedora/linux/releases/39/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-39-1.5.iso
        Checksum file: https://download.fedoraproject.org/pub/fedora/linux/releases/39/Workstation/x86_64/iso/Fedora-Workstation-39-1.5-x86_64-CHECKSUM
        """
        try:
            # Extract directory and construct checksum URL
            iso_dir = iso_url.rsplit('/', 1)[0]
            iso_filename = iso_url.split('/')[-1]
            
            # Parse version from filename (e.g., 39-1.5)
            match = re.search(r'(\d+)-(\d+\.\d+)', iso_filename)
            if not match:
                print(f"❌ Could not parse Fedora version from filename")
                return None
            
            version_major = match.group(1)
            version_minor = match.group(2)
            
            # Construct checksum filename
            checksum_filename = f"Fedora-Workstation-{version_major}-{version_minor}-x86_64-CHECKSUM"
            checksum_url = f"{iso_dir}/{checksum_filename}"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=10)
            response.raise_for_status()
            
            # Parse checksum file (format: SHA256 (filename) = checksum)
            pattern = rf'SHA256\s*\({re.escape(iso_filename)}\)\s*=\s*([a-f0-9]{{64}})'
            match = re.search(pattern, response.text, re.IGNORECASE)
            
            if match:
                checksum = match.group(1)
                print(f"✅ Found checksum: {checksum[:16]}...")
                return checksum
            
            print(f"❌ Checksum not found for {iso_filename}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Fedora checksum: {e}")
            return None
    
    def fetch_debian_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Debian checksum from SHA256SUMS file
        
        Example URL: https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/debian-12.4.0-amd64-DVD-1.iso
        Checksum file: https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/SHA256SUMS
        """
        try:
            iso_dir = iso_url.rsplit('/', 1)[0]
            iso_filename = iso_url.split('/')[-1]
            
            # Try both current directory and archive
            urls_to_try = [f"{iso_dir}/SHA256SUMS"]
            
            # Extract version from filename to try archive
            version_match = re.search(r'debian-(\d+\.\d+(?:\.\d+)?)', iso_filename)
            if version_match:
                version = version_match.group(1)
                archive_url = f"https://cdimage.debian.org/cdimage/archive/{version}/amd64/iso-dvd/SHA256SUMS"
                urls_to_try.append(archive_url)
            
            for checksum_url in urls_to_try:
                print(f"📥 Fetching: {checksum_url}")
                try:
                    response = self.session.get(checksum_url, timeout=15)
                    response.raise_for_status()
                    
                    # Parse SHA256SUMS file (format: checksum  filename)
                    for line in response.text.splitlines():
                        if iso_filename in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                checksum = parts[0]
                                print(f"✅ Found checksum: {checksum[:16]}...")
                                return checksum
                except requests.exceptions.RequestException:
                    if checksum_url == urls_to_try[-1]:  # Last attempt
                        continue
            
            print(f"❌ Checksum not found for {iso_filename}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Debian checksum: {e}")
            return None
    
    def fetch_linuxmint_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Linux Mint checksum from sha256sum.txt file
        
        Example URL: https://mirrors.edge.kernel.org/linuxmint/stable/21.3/linuxmint-21.3-cinnamon-64bit.iso
        Checksum file: https://mirrors.edge.kernel.org/linuxmint/stable/21.3/sha256sum.txt
        """
        try:
            iso_dir = iso_url.rsplit('/', 1)[0]
            iso_filename = iso_url.split('/')[-1]
            checksum_url = f"{iso_dir}/sha256sum.txt"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=10)
            response.raise_for_status()
            
            # Parse sha256sum.txt file (format: checksum *filename)
            for line in response.text.splitlines():
                if iso_filename in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        checksum = parts[0]
                        print(f"✅ Found checksum: {checksum[:16]}...")
                        return checksum
            
            print(f"❌ Checksum not found for {iso_filename}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Linux Mint checksum: {e}")
            return None
    
    def fetch_popos_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Pop!_OS checksum from SHA256SUMS file
        
        Example URL: https://iso.pop-os.org/22.04/amd64/intel/35/pop-os_22.04_amd64_intel_35.iso
        Checksum file: https://iso.pop-os.org/22.04/amd64/intel/35/SHA256SUMS
        """
        try:
            iso_dir = iso_url.rsplit('/', 1)[0]
            iso_filename = iso_url.split('/')[-1]
            checksum_url = f"{iso_dir}/SHA256SUMS"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=10)
            response.raise_for_status()
            
            # Parse SHA256SUMS file (format: checksum *filename)
            for line in response.text.splitlines():
                if iso_filename in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        checksum = parts[0].strip('*')
                        print(f"✅ Found checksum: {checksum[:16]}...")
                        return checksum
            
            print(f"❌ Checksum not found for {iso_filename}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Pop!_OS checksum: {e}")
            return None
    
    def fetch_manjaro_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Manjaro checksum from .sha256 file
        
        Example URL: https://download.manjaro.org/xfce/23.1.3/manjaro-xfce-23.1.3-240113-linux66.iso
        Checksum file: https://download.manjaro.org/xfce/23.1.3/manjaro-xfce-23.1.3-240113-linux66.iso.sha256
        """
        try:
            checksum_url = f"{iso_url}.sha256"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=10)
            response.raise_for_status()
            
            # Parse .sha256 file (format: checksum  filename)
            parts = response.text.strip().split()
            if len(parts) >= 1:
                checksum = parts[0]
                print(f"✅ Found checksum: {checksum[:16]}...")
                return checksum
            
            print(f"❌ Could not parse checksum file")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Manjaro checksum: {e}")
            return None
    
    def fetch_zorin_checksum(self, version: str = "17.3") -> Optional[str]:
        """
        Fetch Zorin OS checksum from help documentation
        
        URL: https://help.zorin.com/docs/getting-started/check-the-integrity-of-your-copy-of-zorin-os/
        """
        try:
            checksum_url = "https://help.zorin.com/docs/getting-started/check-the-integrity-of-your-copy-of-zorin-os/"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple patterns to find checksum
            # Pattern 1: "Zorin OS 17.3 Core 64-bit (r2): <checksum>"
            pattern1 = rf'Zorin\s+OS\s+{re.escape(version)}\s+Core\s+64-bit[^:]*:\s*([a-f0-9]{{64}})'
            match = re.search(pattern1, response.text, re.IGNORECASE)
            
            if match:
                checksum = match.group(1)
                print(f"✅ Found checksum: {checksum[:16]}...")
                return checksum
            
            # Pattern 2: Search in code blocks for version-specific checksums
            for tag in soup.find_all(['code', 'pre', 'p']):
                text = tag.get_text()
                if version in text:
                    checksum_match = re.search(r'\b([a-f0-9]{64})\b', text)
                    if checksum_match:
                        checksum = checksum_match.group(1)
                        print(f"✅ Found checksum: {checksum[:16]}...")
                        return checksum
            
            print(f"❌ Checksum not found for version {version}")
            print(f"💡 Manual verification at: {checksum_url}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Zorin checksum: {e}")
            return None
    
    def fetch_elementary_checksum(self, version: str = "7.1") -> Optional[str]:
        """
        Fetch elementary OS checksum from installation documentation
        
        URL: https://elementary.io/docs/installation
        Note: The docs show the latest version, which may not match older releases
        """
        try:
            checksum_url = "https://elementary.io/docs/installation"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML and look for checksum pattern
            # The page shows checksums in code blocks
            pattern = r'([a-f0-9]{64})'
            matches = re.findall(pattern, response.text)
            
            if matches:
                # The first checksum found is usually the current stable release
                checksum = matches[0]
                print(f"⚠️  Found checksum (may be for newer version): {checksum[:16]}...")
                print(f"⚠️  Verify this matches elementary OS {version} before using!")
                return checksum
            
            print(f"❌ Checksum not found")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching elementary checksum: {e}")
            return None
    
    def fetch_bazzite_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Bazzite checksum
        
        Note: Bazzite uses OCI container images, not traditional ISOs with checksums.
        ISOs are generated on-demand and checksums must be verified manually from their docs.
        """
        print(f"⚠️  Bazzite uses container images - checksums not available via automated fetch")
        print(f"💡 Visit https://docs.bazzite.gg/ for manual verification instructions")
        return None
    
    def fetch_cachyos_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch CachyOS checksum from .sha256 file
        
        Example URL: https://mirror.cachyos.org/ISO/kde/cachyos-kde-linux-260115.iso
        Checksum file: https://mirror.cachyos.org/ISO/kde/cachyos-kde-linux-260115.iso.sha256
        """
        try:
            checksum_url = f"{iso_url}.sha256"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=15)
            response.raise_for_status()
            
            # Parse .sha256 file (format: checksum  filename)
            parts = response.text.strip().split()
            if len(parts) >= 1:
                checksum = parts[0]
                print(f"✅ Found checksum: {checksum[:16]}...")
                return checksum
            
            print(f"❌ Could not parse checksum file")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching CachyOS checksum: {e}")
            return None
    
    def fetch_parrotos_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch Parrot OS checksum from sha256.txt file
        
        Example URL: https://download.parrotsec.org/parrot/iso/7.0/Parrot-security-7.0_amd64.iso
        Checksum file: https://download.parrotsec.org/parrot/iso/7.0/sha256.txt
        """
        try:
            # Extract version directory from URL
            match = re.search(r'/parrot/iso/([^/]+)/', iso_url)
            if not match:
                print(f"❌ Could not parse Parrot OS version from URL")
                return None
            
            version = match.group(1)
            iso_filename = iso_url.split('/')[-1]
            
            checksum_url = f"https://download.parrotsec.org/parrot/iso/{version}/sha256.txt"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=15)
            response.raise_for_status()
            
            # Parse sha256.txt file - look for the specific filename or "security" edition
            for line in response.text.splitlines():
                if iso_filename in line or ('security' in line.lower() and 'amd64' in line):
                    parts = line.split()
                    if len(parts) >= 1 and len(parts[0]) == 64:
                        checksum = parts[0]
                        print(f"✅ Found checksum: {checksum[:16]}...")
                        return checksum
            
            print(f"❌ Checksum not found for {iso_filename}")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching Parrot OS checksum: {e}")
            return None
    
    def fetch_opensuse_tumbleweed_checksum(self, iso_url: str) -> Optional[str]:
        """
        Fetch openSUSE Tumbleweed checksum from .sha256 file
        
        Example URL: https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-DVD-x86_64-Current.iso
        Checksum file: https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-DVD-x86_64-Current.iso.sha256
        """
        try:
            checksum_url = f"{iso_url}.sha256"
            
            print(f"📥 Fetching: {checksum_url}")
            response = self.session.get(checksum_url, timeout=15)
            response.raise_for_status()
            
            # Parse .sha256 file (format: checksum  filename)
            parts = response.text.strip().split()
            if len(parts) >= 1:
                checksum = parts[0]
                print(f"✅ Found checksum: {checksum[:16]}...")
                return checksum
            
            print(f"❌ Could not parse checksum file")
            return None
            
        except Exception as e:
            print(f"❌ Error fetching openSUSE Tumbleweed checksum: {e}")
            return None
    
    def fetch_checksum(self, distro_id: str, iso_url: str, version: Optional[str] = None) -> Optional[str]:
        """
        Fetch checksum for any distribution
        
        Args:
            distro_id: Distribution identifier (ubuntu, fedora, etc.)
            iso_url: ISO download URL
            version: Optional version string for distros that need it
            
        Returns:
            SHA256 checksum or None if not found
        """
        print(f"\n{'='*70}")
        print(f"Fetching checksum for: {distro_id}")
        print(f"{'='*70}")
        
        # Check cache first
        if self.use_cache:
            cached = self._get_cached_checksum(distro_id, iso_url)
            if cached:
                print(f"✅ Using cached checksum: {cached[:16]}...")
                return cached
        
        fetchers = {
            'ubuntu': self.fetch_ubuntu_checksum,
            'fedora': self.fetch_fedora_checksum,
            'debian': self.fetch_debian_checksum,
            'linuxmint': self.fetch_linuxmint_checksum,
            'popos': self.fetch_popos_checksum,
            'manjaro': self.fetch_manjaro_checksum,
            'zorin': lambda url: self.fetch_zorin_checksum(version or "17.3"),
            'elementary': lambda url: self.fetch_elementary_checksum(version or "7.1"),
            'bazzite-desktop': self.fetch_bazzite_checksum,
            'bazzite-handheld': self.fetch_bazzite_checksum,
            'cachyos-desktop': self.fetch_cachyos_checksum,
            'cachyos-handheld': self.fetch_cachyos_checksum,
            'parrotos': self.fetch_parrotos_checksum,
            'opensuse-tumbleweed': self.fetch_opensuse_tumbleweed_checksum,
        }
        
        fetcher = fetchers.get(distro_id)
        if not fetcher:
            print(f"❌ No fetcher available for distribution: {distro_id}")
            return None
        
        checksum = fetcher(iso_url)
        
        # Save to cache if successful
        if checksum and self.use_cache:
            self._save_cached_checksum(distro_id, iso_url, checksum)
        
        return checksum


def update_distro_manager(results: dict) -> bool:
    """
    Update distro_manager.py with new checksums
    
    Args:
        results: Dictionary of {distro_id: {checksum data}}
    
    Returns:
        True if successful, False otherwise
    """
    distro_manager_path = Path(__file__).parent.parent / 'luxusb' / 'utils' / 'distro_manager.py'
    
    if not distro_manager_path.exists():
        print(f"❌ Could not find distro_manager.py at: {distro_manager_path}")
        return False
    
    try:
        # Read current file
        with open(distro_manager_path, 'r') as f:
            content = f.read()
        
        # Backup original
        backup_path = distro_manager_path.with_suffix('.py.bak')
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✅ Created backup: {backup_path.name}")
        
        # Update checksums
        updates_made = 0
        for distro_id, data in results.items():
            if data['matches']:
                continue  # Already up to date
            
            old_checksum = data['current']
            new_checksum = data['fetched']
            
            # Pattern: sha256="old_checksum"
            pattern = f'sha256="{old_checksum}"'
            replacement = f'sha256="{new_checksum}"'
            
            if pattern in content:
                content = content.replace(pattern, replacement)
                updates_made += 1
                print(f"✅ Updated {data['name']} checksum")
            else:
                print(f"⚠️  Could not find checksum pattern for {data['name']}")
        
        if updates_made > 0:
            # Write updated file
            with open(distro_manager_path, 'w') as f:
                f.write(content)
            print(f"\n✅ Successfully updated {updates_made} checksum(s) in distro_manager.py")
            return True
        else:
            print("\n⚠️  No updates were necessary")
            return False
            
    except Exception as e:
        print(f"❌ Error updating distro_manager.py: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Fetch official SHA256 checksums for Linux distributions'
    )
    parser.add_argument(
        '--distro',
        help='Specific distribution ID to fetch (e.g., ubuntu, fedora)',
        default=None
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update distro_manager.py with fetched checksums'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching and fetch fresh checksums'
    )
    
    args = parser.parse_args()
    
    # Import distro manager to get current configuration
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from luxusb.utils.distro_manager import DistroManager
    
    dm = DistroManager()
    fetcher = ChecksumFetcher(use_cache=not args.no_cache)
    
    results = {}
    
    # Get list of distros to process
    distros_to_process = [dm.get_distro_by_id(args.distro)] if args.distro else dm.get_all_distros()
    distros_to_process = [d for d in distros_to_process if d is not None]
    
    print("\n" + "="*70)
    print("  LUXusb Checksum Fetcher")
    print("="*70)
    print(f"\nProcessing {len(distros_to_process)} distribution(s)...")
    if not args.no_cache:
        print(f"Cache: Enabled (24-hour TTL)")
    else:
        print(f"Cache: Disabled (fetching fresh)")
    print()
    
    for distro in distros_to_process:
        release = distro.latest_release
        if not release:
            print(f"⚠️  Skipping {distro.name}: No releases configured")
            continue
        
        checksum = fetcher.fetch_checksum(
            distro.id,
            release.iso_url,
            release.version
        )
        
        if checksum:
            results[distro.id] = {
                'name': distro.name,
                'version': release.version,
                'current': release.sha256,
                'fetched': checksum,
                'matches': checksum == release.sha256
            }
    
    # Print summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    
    needs_update = []
    for distro_id, data in results.items():
        status = "✅ MATCH" if data['matches'] else "⚠️  DIFFERENT"
        print(f"\n{data['name']} {data['version']}:")
        print(f"  Status:  {status}")
        print(f"  Current: {data['current'][:16]}...")
        print(f"  Fetched: {data['fetched'][:16]}...")
        
        if not data['matches']:
            print(f"  🔄 Update recommended!")
            needs_update.append(distro_id)
    
    # Handle --update flag
    if args.update:
        if needs_update:
            print("\n" + "="*70)
            print("  UPDATING distro_manager.py")
            print("="*70)
            
            if update_distro_manager(results):
                print("\n✅ Update complete! Please review the changes.")
            else:
                print("\n❌ Update failed. Check the error messages above.")
        else:
            print("\n✅ All checksums are already up to date!")
    elif needs_update:
        print(f"\n💡 Run with --update flag to automatically update distro_manager.py")
    
    print("\n" + "="*70)
    print(f"Processed: {len(results)}/{len(distros_to_process)} distributions")
    print("="*70 + "\n")
    print("\n" + "="*70)
    print(f"Processed: {len(results)}/{len(distros_to_process)} distributions")
    print("="*70 + "\n")
    
    return 0 if results else 1


if __name__ == '__main__':
    sys.exit(main())

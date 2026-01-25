#!/usr/bin/env python3
"""
Script to fetch and update checksums for newly added distributions.
Handles special cases like Bazzite's dynamic ISO generation.
"""

import json
import logging
import requests
import re
from pathlib import Path
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_cachyos_desktop_checksum() -> Optional[Dict]:
    """Fetch latest CachyOS Desktop ISO and checksum"""
    try:
        response = requests.get("https://mirror.cachyos.org/ISO/kde/", timeout=30)
        response.raise_for_status()
        
        # Find latest ISO
        iso_pattern = r'cachyos-kde-linux-(\d{6})\.iso'
        matches = re.findall(iso_pattern, response.text)
        if not matches:
            logger.error("Could not find CachyOS Desktop ISO")
            return None
        
        version_date = sorted(matches, reverse=True)[0]
        iso_filename = f"cachyos-kde-linux-{version_date}.iso"
        iso_url = f"https://mirror.cachyos.org/ISO/kde/{iso_filename}"
        
        # Fetch checksum
        checksum_url = f"{iso_url}.sha256"
        checksum_response = requests.get(checksum_url, timeout=30)
        checksum_response.raise_for_status()
        
        # Parse checksum (format: "hash filename")
        sha256 = checksum_response.text.strip().split()[0]
        
        # Get size
        head_response = requests.head(iso_url, timeout=30)
        size_mb = int(head_response.headers.get('Content-Length', 0)) // (1024 * 1024)
        
        return {
            "version": f"20{version_date[:2]}.{version_date[2:4]}",
            "iso_url": iso_url,
            "sha256": sha256,
            "size_mb": size_mb if size_mb > 0 else 3500
        }
    except Exception as e:
        logger.error(f"Failed to fetch CachyOS Desktop: {e}")
        return None


def fetch_cachyos_handheld_checksum() -> Optional[Dict]:
    """Fetch latest CachyOS Handheld ISO and checksum"""
    try:
        response = requests.get("https://mirror.cachyos.org/ISO/handheld/", timeout=30)
        response.raise_for_status()
        
        # Find latest handheld ISO
        iso_pattern = r'cachyos-handheld-(\d{6})\.iso'
        matches = re.findall(iso_pattern, response.text)
        if not matches:
            logger.error("Could not find CachyOS Handheld ISO")
            return None
        
        version_date = sorted(matches, reverse=True)[0]
        iso_filename = f"cachyos-handheld-{version_date}.iso"
        iso_url = f"https://mirror.cachyos.org/ISO/handheld/{iso_filename}"
        
        # Fetch checksum
        checksum_url = f"{iso_url}.sha256"
        checksum_response = requests.get(checksum_url, timeout=30)
        checksum_response.raise_for_status()
        
        sha256 = checksum_response.text.strip().split()[0]
        
        # Get size
        head_response = requests.head(iso_url, timeout=30)
        size_mb = int(head_response.headers.get('Content-Length', 0)) // (1024 * 1024)
        
        return {
            "version": f"20{version_date[:2]}.{version_date[2:4]}",
            "iso_url": iso_url,
            "sha256": sha256,
            "size_mb": size_mb if size_mb > 0 else 3500
        }
    except Exception as e:
        logger.error(f"Failed to fetch CachyOS Handheld: {e}")
        return None


def fetch_parrotos_checksum() -> Optional[Dict]:
    """Fetch latest ParrotOS Security ISO and checksum"""
    try:
        base_url = "https://download.parrotsec.org/parrot/iso"
        
        # Get latest version directory
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        
        # Find version directories (format: 6.2, 6.1, etc.)
        version_pattern = r'href="(\d+\.\d+)/"'
        versions = re.findall(version_pattern, response.text)
        if not versions:
            logger.error("Could not find ParrotOS versions")
            return None
        
        latest_version = sorted(versions, key=lambda v: tuple(map(int, v.split('.'))), reverse=True)[0]
        version_url = f"{base_url}/{latest_version}"
        
        # Get ISO filename from version directory
        version_response = requests.get(version_url, timeout=30)
        version_response.raise_for_status()
        
        # Look for security edition ISO
        iso_pattern = r'(Parrot-security-[\d\.]+_amd64\.iso)'
        iso_matches = re.findall(iso_pattern, version_response.text)
        if not iso_matches:
            logger.error("Could not find ParrotOS Security ISO")
            return None
        
        iso_filename = iso_matches[0]
        iso_url = f"{version_url}/{iso_filename}"
        
        # Fetch SHA256SUMS file
        sha256sums_url = f"{version_url}/sha256.txt"
        checksum_response = requests.get(sha256sums_url, timeout=30)
        checksum_response.raise_for_status()
        
        # Find checksum for our ISO
        for line in checksum_response.text.splitlines():
            if iso_filename in line:
                sha256 = line.split()[0]
                break
        else:
            logger.error(f"Could not find checksum for {iso_filename}")
            return None
        
        # Get size
        head_response = requests.head(iso_url, timeout=30)
        size_mb = int(head_response.headers.get('Content-Length', 0)) // (1024 * 1024)
        
        return {
            "version": latest_version,
            "iso_url": iso_url,
            "sha256": sha256,
            "size_mb": size_mb if size_mb > 0 else 5000
        }
    except Exception as e:
        logger.error(f"Failed to fetch ParrotOS: {e}")
        return None


def fetch_opensuse_tumbleweed_checksum() -> Optional[Dict]:
    """Fetch latest openSUSE Tumbleweed ISO and checksum"""
    try:
        # openSUSE Tumbleweed is a rolling release
        base_url = "https://download.opensuse.org/tumbleweed/iso"
        iso_filename = "openSUSE-Tumbleweed-DVD-x86_64-Current.iso"
        iso_url = f"{base_url}/{iso_filename}"
        
        # Fetch checksum file
        checksum_url = f"{iso_url}.sha256"
        response = requests.get(checksum_url, timeout=30)
        response.raise_for_status()
        
        # Parse checksum (format: "hash *filename" or "hash filename")
        sha256 = response.text.strip().split()[0]
        
        # Get size
        head_response = requests.head(iso_url, timeout=30)
        size_mb = int(head_response.headers.get('Content-Length', 0)) // (1024 * 1024)
        
        # Version is based on snapshot date
        from datetime import datetime
        version = datetime.now().strftime("%Y%m%d")
        
        return {
            "version": version,
            "iso_url": iso_url,
            "sha256": sha256,
            "size_mb": size_mb if size_mb > 0 else 4700
        }
    except Exception as e:
        logger.error(f"Failed to fetch openSUSE Tumbleweed: {e}")
        return None


def fetch_bazzite_info() -> Dict:
    """
    Fetch information about Bazzite ISOs.
    Note: Bazzite uses dynamic ISO generation, so we provide documentation
    on how to verify manually.
    """
    return {
        "note": "Bazzite uses dynamic ISO generation via download.bazzite.gg",
        "verification": "SHA256 checksums are available at {iso_url}.sha256",
        "desktop_url": "https://download.bazzite.gg/bazzite-kde-stable.iso",
        "handheld_url": "https://download.bazzite.gg/bazzite-deck-stable.iso",
        "documentation": "Visit bazzite.gg for latest ISO links with checksums"
    }


def update_distro_json(distro_id: str, update_data: Dict) -> bool:
    """Update a distribution's JSON file with new release data"""
    try:
        json_path = Path(__file__).parent.parent / "luxusb" / "data" / "distros" / f"{distro_id}.json"
        
        if not json_path.exists():
            logger.error(f"Distribution JSON not found: {json_path}")
            return False
        
        # Load existing data
        with open(json_path, 'r') as f:
            distro_data = json.load(f)
        
        # Update first release entry
        if distro_data.get('releases') and len(distro_data['releases']) > 0:
            release = distro_data['releases'][0]
            release['version'] = update_data.get('version', release['version'])
            release['iso_url'] = update_data.get('iso_url', release['iso_url'])
            release['sha256'] = update_data.get('sha256', release['sha256'])
            release['size_mb'] = update_data.get('size_mb', release['size_mb'])
            release['release_date'] = update_data.get('release_date', release['release_date'])
            
            # Save updated data
            with open(json_path, 'w') as f:
                json.dump(distro_data, f, indent=2)
            
            logger.info(f"✓ Updated {distro_id}: {release['version']}")
            return True
        else:
            logger.error(f"No releases found in {distro_id}.json")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update {distro_id}: {e}")
        return False


def main():
    """Update all newly added distributions"""
    logger.info("Fetching checksums for newly added distributions...")
    logger.info("=" * 60)
    
    # CachyOS Desktop
    logger.info("\n[1/6] Fetching CachyOS Desktop...")
    cachyos_desktop = fetch_cachyos_desktop_checksum()
    if cachyos_desktop:
        update_distro_json('cachyos-desktop', cachyos_desktop)
    else:
        logger.warning("⚠ CachyOS Desktop update failed")
    
    # CachyOS Handheld
    logger.info("\n[2/6] Fetching CachyOS Handheld...")
    cachyos_handheld = fetch_cachyos_handheld_checksum()
    if cachyos_handheld:
        update_distro_json('cachyos-handheld', cachyos_handheld)
    else:
        logger.warning("⚠ CachyOS Handheld update failed")
    
    # ParrotOS
    logger.info("\n[3/6] Fetching ParrotOS...")
    parrotos = fetch_parrotos_checksum()
    if parrotos:
        update_distro_json('parrotos', parrotos)
    else:
        logger.warning("⚠ ParrotOS update failed")
    
    # openSUSE Tumbleweed
    logger.info("\n[4/6] Fetching openSUSE Tumbleweed...")
    opensuse = fetch_opensuse_tumbleweed_checksum()
    if opensuse:
        update_distro_json('opensuse-tumbleweed', opensuse)
    else:
        logger.warning("⚠ openSUSE Tumbleweed update failed")
    
    # Bazzite - informational only
    logger.info("\n[5/6] Bazzite Desktop (manual verification)...")
    bazzite_info = fetch_bazzite_info()
    logger.info(f"  Desktop: {bazzite_info['desktop_url']}")
    logger.info(f"  Checksum: {bazzite_info['desktop_url']}.sha256")
    logger.warning("  ⚠ Bazzite Desktop requires manual checksum fetch from bazzite.gg")
    
    logger.info("\n[6/6] Bazzite Handheld (manual verification)...")
    logger.info(f"  Handheld: {bazzite_info['handheld_url']}")
    logger.info(f"  Checksum: {bazzite_info['handheld_url']}.sha256")
    logger.warning("  ⚠ Bazzite Handheld requires manual checksum fetch from bazzite.gg")
    
    logger.info("\n" + "=" * 60)
    logger.info("Update complete! Remember to commit the updated JSON files.")
    
    # Print summary
    logger.info("\nNOTE: Bazzite distributions use dynamic ISO generation.")
    logger.info("Their checksums change with each build. To update:")
    logger.info("1. Visit https://bazzite.gg/")
    logger.info("2. Use the image picker to get your ISO URL")
    logger.info("3. Download the corresponding .sha256 file")
    logger.info("4. Update the JSON files manually with real checksums")


if __name__ == "__main__":
    main()

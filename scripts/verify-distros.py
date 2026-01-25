#!/usr/bin/env python3
"""Verify all distro ISO links are working"""

import sys
import json
import requests
from pathlib import Path
from typing import List, Dict

def test_url(url: str, timeout: int = 10) -> tuple[bool, str]:
    """Test if URL is accessible"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code in [200, 302]:
            return True, f"✅ OK ({response.status_code})"
        else:
            return False, f"❌ HTTP {response.status_code}"
    except requests.Timeout:
        return False, "❌ Timeout"
    except requests.RequestException as e:
        return False, f"❌ {type(e).__name__}"
    except Exception as e:
        return False, f"❌ {str(e)}"

def verify_distro_file(json_path: Path) -> Dict:
    """Verify a distro JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    distro_id = data['id']
    distro_name = data['name']
    
    results = {
        'distro': distro_name,
        'id': distro_id,
        'verified': data['metadata'].get('verified', False),
        'releases': []
    }
    
    for release in data.get('releases', []):
        version = release['version']
        iso_url = release['iso_url']
        mirrors = release.get('mirrors', [])
        
        print(f"\n{distro_name} {version}")
        print(f"  Primary: {iso_url}")
        
        # Test primary URL
        success, status = test_url(iso_url)
        print(f"    {status}")
        
        release_result = {
            'version': version,
            'primary_url': iso_url,
            'primary_status': success,
            'mirrors_status': []
        }
        
        # Test mirrors
        if mirrors:
            print(f"  Mirrors:")
            for i, mirror in enumerate(mirrors, 1):
                success, status = test_url(mirror)
                print(f"    {i}. {status}: {mirror}")
                release_result['mirrors_status'].append(success)
        
        results['releases'].append(release_result)
    
    return results

def main():
    # Find all distro JSON files
    repo_root = Path(__file__).parent.parent
    distros_dir = repo_root / "luxusb" / "data" / "distros"
    
    if not distros_dir.exists():
        print(f"❌ Distros directory not found: {distros_dir}")
        return 1
    
    json_files = sorted(distros_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {distros_dir}")
        return 1
    
    print(f"=== Verifying {len(json_files)} Distributions ===")
    
    all_results = []
    for json_file in json_files:
        try:
            result = verify_distro_file(json_file)
            all_results.append(result)
        except Exception as e:
            print(f"\n❌ Error processing {json_file.name}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total_ok = 0
    total_failed = 0
    
    for result in all_results:
        distro = result['distro']
        for release in result['releases']:
            if release['primary_status']:
                print(f"✅ {distro} {release['version']}")
                total_ok += 1
            else:
                print(f"❌ {distro} {release['version']}")
                total_failed += 1
    
    print(f"\nTotal: {total_ok + total_failed}")
    print(f"  ✅ Working: {total_ok}")
    print(f"  ❌ Failed: {total_failed}")
    
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

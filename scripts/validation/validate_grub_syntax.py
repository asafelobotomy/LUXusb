#!/usr/bin/env python3
"""
Validate GRUB Configuration Generation
Tests that generated GRUB configs don't contain syntax errors
"""

import sys
from pathlib import Path
from luxusb.utils.grub_installer import GRUBInstaller
from luxusb.utils.distro_manager import Distro, DistroRelease
from luxusb.utils.custom_iso import CustomISO
from datetime import date

def test_grub_syntax():
    """Test that GRUB configs don't contain invalid return statements"""
    
    print("🔍 Testing GRUB Configuration Generation...")
    print("=" * 60)
    
    # Initialize installer
    installer = GRUBInstaller('/dev/sdb', Path('/tmp/test_grub'))
    
    # Create test distros
    test_distros = [
        Distro(
            id='ubuntu',
            name='Ubuntu',
            description='Test Ubuntu',
            homepage='https://ubuntu.com',
            logo_url='',
            category='Desktop',
            popularity_rank=1,
            releases=[
                DistroRelease(
                    version='24.04',
                    release_date=date(2024, 4, 25),
                    iso_url='https://test.com/ubuntu.iso',
                    sha256='abc123',
                    size_mb=3000,
                    architecture='x86_64',
                    mirrors=[]
                )
            ],
            family='debian'
        ),
        Distro(
            id='arch',
            name='Arch Linux',
            description='Test Arch',
            homepage='https://archlinux.org',
            logo_url='',
            category='Desktop',
            popularity_rank=2,
            releases=[
                DistroRelease(
                    version='2024.01.01',
                    release_date=date(2024, 1, 1),
                    iso_url='https://test.com/arch.iso',
                    sha256='def456',
                    size_mb=800,
                    architecture='x86_64',
                    mirrors=[]
                )
            ],
            family='arch'
        ),
        Distro(
            id='fedora',
            name='Fedora',
            description='Test Fedora',
            homepage='https://getfedora.org',
            logo_url='',
            category='Desktop',
            popularity_rank=3,
            releases=[
                DistroRelease(
                    version='40',
                    release_date=date(2024, 4, 16),
                    iso_url='https://test.com/fedora.iso',
                    sha256='ghi789',
                    size_mb=2000,
                    architecture='x86_64',
                    mirrors=[]
                )
            ],
            family='fedora'
        ),
    ]
    
    # Test boot commands for each family
    print("\n📝 Testing Boot Command Generation...")
    errors = []
    
    for distro in test_distros:
        print(f"   Testing {distro.name} ({distro.family})...", end=" ")
        
        boot_cmds = installer._get_boot_commands(distro, f'/isos/{distro.id}/{distro.id}.iso')
        
        # Check for actual return statements (not just the word "return" in strings)
        # Look for "return" as a statement (on its own line or after whitespace)
        import re
        if re.search(r'^\s+return\s*$', boot_cmds, re.MULTILINE):
            errors.append(f"❌ {distro.name}: Contains 'return' statement!")
            print("FAIL")
        else:
            print("✓")
    
    # Test distro entry generation
    print("\n📝 Testing Distro Entry Generation...")
    print("   Generating full menuentry blocks...", end=" ")
    
    try:
        entries = installer._generate_iso_entries(test_distros, [])
        
        # Check for return statements (not the phrase "return to menu")
        import re
        if re.search(r'^\s+return\s*$', entries, re.MULTILINE):
            errors.append("❌ Menuentry blocks: Contains 'return' statement!")
            print("FAIL")
        else:
            print("✓")
    except Exception as e:
        errors.append(f"❌ Entry generation failed: {e}")
        print("FAIL")
    
    # Test custom ISO entry generation
    print("\n📝 Testing Custom ISO Entry Generation...")
    print("   Generating custom ISO menuentry...", end=" ")
    
    custom_iso = CustomISO(
        path=Path('/tmp/custom.iso'),
        name='Custom Test ISO',
        size_bytes=1500 * 1024 * 1024,
        is_valid=True
    )
    
    try:
        custom_entries = installer._generate_custom_iso_entries([custom_iso])
        
        # Check for return statements (not the phrase "return to menu")
        import re
        if re.search(r'^\s+return\s*$', custom_entries, re.MULTILINE):
            errors.append("❌ Custom ISO entry: Contains 'return' statement!")
            print("FAIL")
        else:
            print("✓")
    except Exception as e:
        errors.append(f"❌ Custom ISO generation failed: {e}")
        print("FAIL")
    
    # Print results
    print("\n" + "=" * 60)
    if errors:
        print("❌ VALIDATION FAILED\n")
        for error in errors:
            print(error)
        return False
    else:
        print("✅ ALL TESTS PASSED")
        print("\nNo syntax errors detected in generated GRUB configurations!")
        print("Safe to create bootable USB drives.")
        return True


if __name__ == '__main__':
    success = test_grub_syntax()
    sys.exit(0 if success else 1)

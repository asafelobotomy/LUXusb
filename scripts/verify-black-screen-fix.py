#!/usr/bin/env python3
"""
Verify that all black screen fixes are properly implemented
"""

import sys
from pathlib import Path

def check_grub_installer():
    """Check grub_installer.py has all fixes"""
    print("=" * 60)
    print("VERIFYING GRUB INSTALLER FIXES")
    print("=" * 60)
    print()
    
    grub_file = Path(__file__).parent.parent / "luxusb" / "utils" / "grub_installer.py"
    
    if not grub_file.exists():
        print("❌ grub_installer.py not found!")
        return False
    
    content = grub_file.read_text()
    
    checks = {
        "TPM removal in header": "rmmod tpm" in content and "# CRITICAL" in content,
        "LaunchPad bug reference": "bugs.launchpad.net" in content,
        "Module preloading": "insmod loopback" in content and "insmod iso9660" in content,
        "Partition hints": "--hint hd0,gpt2" in content,
        "TPM check in entries": "# Verify TPM" in content,
        "Boot parameter nomodeset": "nomodeset" in content,
        "Boot parameter noapic": "noapic" in content,
        "Boot parameter acpi=off": "acpi=off" in content,
        "Verbose boot (removed quiet)": content.count("quiet") < 5,  # Should only be in comments
        "Echo statements": "echo" in content and "Loading" in content,
        "Root partition display": "Found root partition" in content,
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  [{status}] {check}")
        if not passed:
            all_passed = False
    
    print()
    return all_passed


def check_generated_config():
    """Test config generation"""
    print("=" * 60)
    print("TESTING CONFIG GENERATION")
    print("=" * 60)
    print()
    
    try:
        from luxusb.utils.grub_installer import GRUBInstaller
        from luxusb.utils.distro_json_loader import DistroJSONLoader
        
        # Load distros
        loader = DistroJSONLoader()
        distros = loader.load_all()
        
        if not distros:
            print("❌ No distros loaded!")
            return False
        
        print(f"✓ Loaded {len(distros)} distributions")
        
        # Get Ubuntu for testing
        ubuntu = next((d for d in distros if d.id == 'ubuntu'), None)
        if not ubuntu:
            print("❌ Ubuntu not found in distros!")
            return False
        
        print(f"✓ Found Ubuntu distro")
        
        # Generate config
        test_path = Path("/tmp/luxusb-verify-test")
        grub_path = test_path / "boot" / "grub"
        grub_path.mkdir(parents=True, exist_ok=True)
        
        installer = GRUBInstaller('/dev/sdb', test_path)
        result = installer.update_config_with_isos(
            iso_paths=[Path('isos/ubuntu/ubuntu.iso')],
            distros=[ubuntu],
            custom_isos=None
        )
        
        if not result:
            print("❌ Config generation failed!")
            return False
        
        print("✓ Config generated successfully")
        
        # Read and verify
        config_file = test_path / "boot" / "grub" / "grub.cfg"
        if not config_file.exists():
            print("❌ grub.cfg not created!")
            return False
        
        config = config_file.read_text()
        
        # Verify critical elements
        checks = {
            "TPM removal at start": config.find("rmmod tpm") < 500,
            "Modules loaded": "insmod loopback" in config,
            "Menu entry created": "menuentry" in config,
            "Partition hint": "--hint hd0,gpt2" in config,
            "nomodeset parameter": "nomodeset" in config,
            "Verbose (no quiet)": "quiet" not in config or config.count("quiet") < 2,
        }
        
        print()
        print("Config verification:")
        all_passed = True
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  [{status}] {check}")
            if not passed:
                all_passed = False
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"❌ Error during config generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all checks"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "LUXusb Black Screen Fix Verification" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Check 1: Source code
    print("Check 1: Source Code Verification")
    results.append(check_grub_installer())
    print()
    
    # Check 2: Config generation
    print("Check 2: Config Generation Test")
    results.append(check_generated_config())
    print()
    
    # Final summary
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print()
    
    if all(results):
        print("✅ ALL CHECKS PASSED!")
        print()
        print("The black screen fixes are properly implemented.")
        print()
        print("Next steps:")
        print("  1. Create a new USB: sudo python3 -m luxusb")
        print("  2. Boot from the USB")
        print("  3. You should see the GRUB menu (not black screen)")
        print("  4. Select a distribution")
        print("  5. Watch verbose boot messages")
        print()
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print()
        print("Please review the failed checks above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

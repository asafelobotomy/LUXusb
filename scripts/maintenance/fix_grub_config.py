#!/usr/bin/env python3
"""
Script to fix GRUB configuration on USB drive
Regenerates grub.cfg with correct ISO paths
"""

import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from luxusb.utils.grub_installer import GRUBInstaller
from luxusb.utils.distro_manager import Distro, DistroRelease
from luxusb.utils.distro_json_loader import DistroJSONLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Fix GRUB configuration"""
    
    # Check if running as root
    import os
    if os.geteuid() != 0:
        print("❌ This script must be run as root")
        print("   Run: sudo .venv/bin/python fix_grub_config.py")
        return 1
    
    # Mount points
    efi_mount = Path("/tmp/luxusb-mount/efi")
    data_mount = Path("/tmp/luxusb-mount/data")
    
    # Check if partitions are mounted
    if not efi_mount.exists() or not data_mount.exists():
        print("❌ USB partitions not mounted")
        print("   Expected mount points:")
        print(f"   - {efi_mount}")
        print(f"   - {data_mount}")
        return 1
    
    # Find ISOs on data partition
    iso_dir = data_mount / "isos"
    if not iso_dir.exists():
        print(f"❌ ISO directory not found: {iso_dir}")
        return 1
    
    # Scan for ISOs and load distro metadata
    loader = DistroJSONLoader()
    all_distros = loader.load_all()
    
    iso_paths = []
    distros = []
    
    # Scan for distro ISOs
    for distro_subdir in iso_dir.iterdir():
        if not distro_subdir.is_dir() or distro_subdir.name == 'custom':
            continue
        
        # Find distro metadata
        distro_id = distro_subdir.name
        distro = next((d for d in all_distros if d.id == distro_id), None)
        
        if not distro:
            logger.warning(f"Unknown distro: {distro_id}")
            continue
        
        # Find ISO file
        iso_files = list(distro_subdir.glob("*.iso"))
        if not iso_files:
            logger.warning(f"No ISO found in {distro_subdir}")
            continue
        
        iso_path = iso_files[0]
        iso_paths.append(iso_path)
        distros.append(distro)
        logger.info(f"Found: {distro.name} - {iso_path.name}")
    
    if not iso_paths:
        print("❌ No ISOs found on USB drive")
        return 1
    
    print(f"\n✅ Found {len(iso_paths)} ISO(s)")
    for iso, distro in zip(iso_paths, distros):
        print(f"   • {distro.name}: {iso.name}")
    
    # Create GRUB installer
    device = "/dev/sdb"  # Update if different
    installer = GRUBInstaller(device, efi_mount)
    
    # Regenerate GRUB config
    print(f"\n🔧 Regenerating GRUB configuration...")
    if installer.update_config_with_isos(iso_paths, distros, timeout=10):
        print("✅ GRUB configuration updated successfully!")
        print(f"\n📄 Config location: {efi_mount}/boot/grub/grub.cfg")
        
        # Show sample of config
        grub_cfg = efi_mount / "boot" / "grub" / "grub.cfg"
        if grub_cfg.exists():
            print("\n📋 First menuentry:")
            with open(grub_cfg, 'r') as f:
                in_menuentry = False
                line_count = 0
                for line in f:
                    if 'menuentry' in line and '{' in line:
                        in_menuentry = True
                    if in_menuentry:
                        print(f"   {line.rstrip()}")
                        line_count += 1
                        if line.strip() == '}' and line_count > 1:
                            break
        
        print("\n🎉 USB drive is ready to boot!")
        print("   Test on both UEFI and BIOS systems")
        return 0
    else:
        print("❌ Failed to update GRUB configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())

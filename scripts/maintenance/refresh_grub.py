#!/usr/bin/env python3
"""
LUXusb GRUB Configuration Refresh Tool
Automatically scans ISOs and regenerates GRUB config

Usage:
    sudo python refresh_grub.py [--device /dev/sdX] [--timeout 10]
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from luxusb.utils.grub_refresher import GRUBConfigRefresher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Refresh GRUB configuration on LUXusb USB drive'
    )
    parser.add_argument(
        '--device',
        default='/dev/sdb',
        help='USB device (default: /dev/sdb)'
    )
    parser.add_argument(
        '--efi-mount',
        default='/tmp/luxusb-mount/efi',
        help='EFI partition mount point'
    )
    parser.add_argument(
        '--data-mount',
        default='/tmp/luxusb-mount/data',
        help='Data partition mount point'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='GRUB menu timeout in seconds (default: 10)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check if config is fresh, do not update'
    )
    parser.add_argument(
        '--auto-mount',
        action='store_true',
        help='Automatically mount partitions if not mounted'
    )
    
    args = parser.parse_args()
    
    # Check if running as root
    import os
    if os.geteuid() != 0:
        print("❌ This tool requires root privileges")
        print("   Run with: sudo python refresh_grub.py")
        return 1
    
    efi_mount = Path(args.efi_mount)
    data_mount = Path(args.data_mount)
    
    # Auto-mount if requested
    mounted_here = False
    if args.auto_mount and (not efi_mount.exists() or not data_mount.exists()):
        print(f"📍 Auto-mounting {args.device}...")
        import subprocess
        
        try:
            # Create mount points
            efi_mount.mkdir(parents=True, exist_ok=True)
            data_mount.mkdir(parents=True, exist_ok=True)
            
            # Mount partitions
            subprocess.run(['mount', f'{args.device}2', str(efi_mount)], check=True)
            subprocess.run(['mount', f'{args.device}3', str(data_mount)], check=True)
            mounted_here = True
            print("✅ Partitions mounted")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to mount partitions: {e}")
            return 1
    
    # Check if partitions are mounted
    if not efi_mount.exists() or not data_mount.exists():
        print("❌ USB partitions not mounted")
        print(f"   Expected mount points:")
        print(f"   - {efi_mount}")
        print(f"   - {data_mount}")
        print(f"\n   Mount manually:")
        print(f"   sudo mount {args.device}2 {efi_mount}")
        print(f"   sudo mount {args.device}3 {data_mount}")
        print(f"\n   Or use --auto-mount flag")
        return 1
    
    # Create refresher
    refresher = GRUBConfigRefresher(efi_mount, data_mount)
    
    # Check config freshness
    print("\n🔍 Checking GRUB configuration...")
    is_fresh, message = refresher.verify_config_freshness()
    print(f"   {message}")
    
    if args.check_only:
        if is_fresh:
            print("\n✅ Configuration is up to date")
            return 0
        else:
            print("\n⚠️  Configuration needs refresh")
            print("   Run without --check-only to update")
            return 1
    
    # Refresh config if needed
    if not is_fresh or '--force' in sys.argv:
        print("\n🔧 Refreshing GRUB configuration...")
        if refresher.refresh_config(args.device, timeout=args.timeout):
            print("✅ GRUB configuration refreshed successfully!")
            print(f"\n📄 Config: {efi_mount}/boot/grub/grub.cfg")
            print("\n🎉 USB drive is ready to boot!")
        else:
            print("❌ Failed to refresh configuration")
            return 1
    else:
        print("\n✅ No refresh needed - configuration is already up to date")
    
    # Unmount if we mounted here
    if mounted_here:
        print("\n🔓 Unmounting partitions...")
        import subprocess
        try:
            subprocess.run(['umount', str(efi_mount)], check=True)
            subprocess.run(['umount', str(data_mount)], check=True)
            print("✅ Partitions unmounted safely")
        except subprocess.CalledProcessError:
            print("⚠️  Warning: Failed to unmount partitions")
            print("   Unmount manually before removing USB")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

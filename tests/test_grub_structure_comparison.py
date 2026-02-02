#!/usr/bin/env python3
"""
GRUB Structure Comparison Test

Generates and compares two approaches to GRUB menuentry generation:
1. Current LUXusb approach (nested structure, 12-space indentation)
2. GLIM-inspired approach (flat structure, 2-space indentation)

This test helps decide which approach to use for bootloader configuration.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from luxusb.utils.grub_installer import GRUBInstaller
from luxusb.utils.distro_manager import Distro, DistroRelease


@dataclass
class SimplifiedGRUBGenerator:
    """Generates GRUB configs using GLIM's simplified approach."""
    
    @staticmethod
    def create_helper_functions() -> str:
        """Create helper functions like GLIM uses."""
        return """# Helper functions (GLIM-inspired)
function loop {
  if [ -e (loop) ]; then
    loopback -d loop
  fi
  loopback loop "$1"
}

function use {
  echo "Using $1 ..."
}

# Global setup (done once)
probe --set rootuuid --fs-uuid $root
set isopath=/isos
export rootuuid
export isopath

"""
    
    @staticmethod
    def generate_ubuntu_menuentry(distro: Distro, release: DistroRelease, hotkey: Optional[str] = None) -> str:
        """Generate simplified Ubuntu menuentry (GLIM style)."""
        display_name = f"{distro.name} {release.version}"
        iso_rel = f"/isos/{distro.id}/{distro.id}-{release.version}-{release.architecture}.iso"
        
        hotkey_attr = f"--hotkey={hotkey} " if hotkey else ""
        
        # GLIM-style: flat structure, 2-space indentation
        entry = f"""menuentry {hotkey_attr}'{display_name}' --class {distro.id} {{
  use "{display_name}"
  set isofile="{iso_rel}"
  loop "$isofile"
  
  if [ -f (loop)/boot/grub/loopback.cfg ]; then
    set iso_path="$isofile"
    export iso_path
    configfile (loop)/boot/grub/loopback.cfg
  elif [ -f (loop)/casper/vmlinuz ]; then
    linux (loop)/casper/vmlinuz boot=casper iso-scan/filename=${{isofile}} quiet splash
    initrd (loop)/casper/initrd
  elif [ -f (loop)/live/vmlinuz ]; then
    linux (loop)/live/vmlinuz boot=live findiso=${{isofile}} quiet splash
    initrd (loop)/live/initrd.img
  else
    echo "Error: Could not find kernel in ISO"
    read
  fi
}}
"""
        return entry
    
    @staticmethod
    def generate_fedora_menuentry(distro: Distro, release: DistroRelease, hotkey: Optional[str] = None) -> str:
        """Generate simplified Fedora menuentry (GLIM style)."""
        display_name = f"{distro.name} {release.version}"
        iso_rel = f"/isos/{distro.id}/{distro.id}-{release.version}-{release.architecture}.iso"
        
        hotkey_attr = f"--hotkey={hotkey} " if hotkey else ""
        
        # GLIM-style with variable-based path detection
        entry = f"""menuentry {hotkey_attr}'{display_name}' --class {distro.id} {{
  use "{display_name}"
  set isofile="{iso_rel}"
  loop "$isofile"
  probe --set isolabel --label (loop)
  
  # Detect ISO type and set paths
  set linux_path=""
  if [ -d "(loop)/LiveOS" ]; then
    # Live ISO
    set linux_path="(loop)/isolinux/vmlinuz"
    set initrd_path="(loop)/isolinux/initrd.img"
    set bootargs="root=live:CDLABEL=${{isolabel}} rd.live.image iso-scan/filename=${{isofile}}"
  else
    # NetInst ISO
    set linux_path="(loop)/images/pxeboot/vmlinuz"
    set initrd_path="(loop)/images/pxeboot/initrd.img"
    set bootargs="inst.stage2=hd:LABEL=${{isolabel}} iso-scan/filename=${{isofile}}"
  fi
  
  if [ -z "${{linux_path}}" ]; then
    echo "Error: Could not detect Fedora ISO type"
    read
  else
    linux ${{linux_path}} ${{bootargs}} quiet
    initrd ${{initrd_path}}
  fi
}}
"""
        return entry
    
    @staticmethod
    def generate_arch_menuentry(distro: Distro, release: DistroRelease, hotkey: Optional[str] = None) -> str:
        """Generate simplified Arch menuentry (GLIM style)."""
        display_name = f"{distro.name} {release.version}"
        iso_rel = f"/isos/{distro.id}/{distro.id}-{release.version}-{release.architecture}.iso"
        
        hotkey_attr = f"--hotkey={hotkey} " if hotkey else ""
        
        entry = f"""menuentry {hotkey_attr}'{display_name}' --class {distro.id} {{
  use "{display_name}"
  set isofile="{iso_rel}"
  loop "$isofile"
  
  linux (loop)/arch/boot/x86_64/vmlinuz-linux img_dev=/dev/disk/by-uuid/${{rootuuid}} img_loop=${{isofile}} earlymodules=loop
  initrd (loop)/arch/boot/x86_64/initramfs-linux.img
}}
"""
        return entry


def create_test_distros():
    """Create test distro data for comparison."""
    ubuntu_release = DistroRelease(
        version="24.04.3",
        release_date="2024-08-29",
        iso_url="https://releases.ubuntu.com/24.04.3/ubuntu-24.04.3-desktop-amd64.iso",
        sha256="a435f6f393dda581172490eda9f683c32e495158a780b5a1de422ee77d98e909",
        size_mb=6000,
        architecture="x86_64",
        mirrors=[]
    )
    
    ubuntu = Distro(
        id="ubuntu",
        name="Ubuntu Desktop",
        description="Popular Linux distribution",
        homepage="https://ubuntu.com",
        logo_url="",
        category="Desktop",
        popularity_rank=1,
        releases=[ubuntu_release]
    )
    
    fedora_release = DistroRelease(
        version="41",
        release_date="2024-10-29",
        iso_url="https://download.fedoraproject.org/pub/fedora/linux/releases/41/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-41-1.4.iso",
        sha256="3e220c709ee1c90454e84dcc011f4e9fcedff6e59c7ec0e790fb8fdc39c60e52",
        size_mb=2100,
        architecture="x86_64",
        mirrors=[]
    )
    
    fedora = Distro(
        id="fedora",
        name="Fedora Workstation",
        description="Cutting-edge Linux distribution",
        homepage="https://fedoraproject.org",
        logo_url="",
        category="Desktop",
        popularity_rank=3,
        releases=[fedora_release]
    )
    
    arch_release = DistroRelease(
        version="2025.01.01",
        release_date="2025-01-01",
        iso_url="https://mirror.rackspace.com/archlinux/iso/2025.01.01/archlinux-2025.01.01-x86_64.iso",
        sha256="placeholder",
        size_mb=950,
        architecture="x86_64",
        mirrors=[]
    )
    
    arch = Distro(
        id="archlinux",
        name="Arch Linux",
        description="Lightweight rolling release",
        homepage="https://archlinux.org",
        logo_url="",
        category="Advanced",
        popularity_rank=5,
        releases=[arch_release]
    )
    
    return [
        (ubuntu, ubuntu_release, 'a'),
        (fedora, fedora_release, 'b'),
        (arch, arch_release, 'c'),
    ]


def generate_current_approach():
    """Generate GRUB config using current LUXusb approach."""
    print("=" * 80)
    print("CURRENT LUXusb APPROACH (v0.4.1)")
    print("=" * 80)
    print("Characteristics:")
    print("  - 4-space base indentation")
    print("  - Nested if/else structure (5 levels deep)")
    print("  - 12-space indentation for boot commands")
    print("  - Search logic inside each menuentry")
    print("  - No helper functions")
    print("=" * 80)
    print()
    
    # Create a minimal GRUBInstaller instance for testing
    # We'll use temporary paths since we're just generating config text
    from tempfile import TemporaryDirectory
    import shutil
    
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        efi_mount = tmp_path / "efi"
        data_mount = tmp_path / "data"
        efi_mount.mkdir()
        data_mount.mkdir()
        
        # Create ISO directories and mock ISO files
        test_distros = create_test_distros()
        iso_paths = []
        distros_list = []
        
        for distro, release, hotkey in test_distros:
            # Create mock ISO file
            iso_dir = data_mount / "isos" / distro.id
            iso_dir.mkdir(parents=True, exist_ok=True)
            iso_file = iso_dir / f"{distro.id}-{release.version}-{release.architecture}.iso"
            iso_file.write_text("mock iso data")
            
            iso_paths.append(iso_file)
            distros_list.append(distro)
        
        # Create GRUBInstaller with correct parameter names
        installer = GRUBInstaller(
            device="/dev/sdX",
            efi_mount=efi_mount,
            data_mount=data_mount
        )
        
        # Generate entries using the actual method
        entries = installer._generate_iso_entries(iso_paths, distros_list)
        
        config = f"""# LUXusb GRUB Configuration
set timeout=30
set default=0

{entries}
"""
        
        print(config)
        print()
        
        return config


def generate_simplified_approach():
    """Generate GRUB config using GLIM-inspired simplified approach."""
    print("=" * 80)
    print("SIMPLIFIED APPROACH (GLIM-Inspired)")
    print("=" * 80)
    print("Characteristics:")
    print("  - 2-space indentation only")
    print("  - Flat structure (1-2 nesting levels max)")
    print("  - Helper functions for common tasks")
    print("  - Global partition setup (done once)")
    print("  - Variables for path detection")
    print("=" * 80)
    print()
    
    generator = SimplifiedGRUBGenerator()
    
    config_lines = [
        "# LUXusb GRUB Configuration (GLIM-Inspired)",
        "set timeout=30",
        "set default=0",
        "",
        generator.create_helper_functions(),
    ]
    
    test_distros = create_test_distros()
    
    # Ubuntu
    distro, release, hotkey = test_distros[0]
    config_lines.append(generator.generate_ubuntu_menuentry(distro, release, hotkey))
    
    # Fedora
    distro, release, hotkey = test_distros[1]
    config_lines.append(generator.generate_fedora_menuentry(distro, release, hotkey))
    
    # Arch
    distro, release, hotkey = test_distros[2]
    config_lines.append(generator.generate_arch_menuentry(distro, release, hotkey))
    
    config = "\n".join(config_lines)
    print(config)
    print()
    
    return config


def analyze_complexity(config: str, approach_name: str):
    """Analyze the complexity of a GRUB config."""
    lines = config.split('\n')
    
    max_indent = 0
    indent_counts = {}
    nesting_levels = []
    
    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        # Count leading spaces
        indent = len(line) - len(line.lstrip())
        max_indent = max(max_indent, indent)
        
        indent_counts[indent] = indent_counts.get(indent, 0) + 1
        
        # Track nesting by counting braces
        if '{' in line:
            nesting_levels.append(indent)
    
    print(f"\n{approach_name} - Complexity Analysis:")
    print(f"  Max indentation: {max_indent} spaces")
    print(f"  Max nesting depth: {len(nesting_levels)} levels")
    print(f"  Indentation distribution:")
    for indent in sorted(indent_counts.keys()):
        print(f"    {indent} spaces: {indent_counts[indent]} lines")
    
    # Count total lines
    non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
    print(f"  Total non-empty lines: {len(non_empty_lines)}")
    
    return {
        'max_indent': max_indent,
        'nesting_depth': len(nesting_levels),
        'total_lines': len(non_empty_lines),
    }


def compare_approaches():
    """Generate and compare both approaches."""
    print("\n" + "=" * 80)
    print("GRUB STRUCTURE COMPARISON TEST")
    print("=" * 80)
    print()
    
    # Generate both configs
    current_config = generate_current_approach()
    simplified_config = generate_simplified_approach()
    
    # Analyze complexity
    current_stats = analyze_complexity(current_config, "CURRENT APPROACH")
    simplified_stats = analyze_complexity(simplified_config, "SIMPLIFIED APPROACH")
    
    # Comparison summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    print("\nComplexity Metrics:")
    print(f"  Max Indentation:  {current_stats['max_indent']:3d} spaces (current) vs {simplified_stats['max_indent']:2d} spaces (simplified)")
    print(f"  Nesting Depth:    {current_stats['nesting_depth']:3d} levels  (current) vs {simplified_stats['nesting_depth']:2d} levels  (simplified)")
    print(f"  Config Size:      {current_stats['total_lines']:3d} lines   (current) vs {simplified_stats['total_lines']:3d} lines   (simplified)")
    
    # Calculate reductions (avoid division by zero)
    if current_stats['max_indent'] > 0:
        indent_reduction = ((current_stats['max_indent'] - simplified_stats['max_indent']) / current_stats['max_indent']) * 100
    else:
        indent_reduction = 0
    
    if current_stats['nesting_depth'] > 0:
        nesting_reduction = ((current_stats['nesting_depth'] - simplified_stats['nesting_depth']) / current_stats['nesting_depth']) * 100
    else:
        nesting_reduction = 0
    
    print(f"\nReductions with Simplified Approach:")
    if indent_reduction != 0:
        print(f"  Indentation: -{indent_reduction:.1f}%")
    if nesting_reduction != 0:
        print(f"  Nesting:     -{nesting_reduction:.1f}%")
    
    # Pros and cons
    print("\n" + "-" * 80)
    print("CURRENT APPROACH - Pros & Cons")
    print("-" * 80)
    print("Pros:")
    print("  ✓ Comprehensive error checking")
    print("  ✓ Validates partition and ISO path before boot")
    print("  ✓ Clear error messages at each failure point")
    print("\nCons:")
    print("  ✗ Very deep nesting (5 levels)")
    print("  ✗ Complex structure harder to debug")
    print("  ✗ 12-space indentation fragile and unusual")
    print("  ✗ Repeated search logic in each menuentry")
    print("  ✗ No code reuse (no helper functions)")
    
    print("\n" + "-" * 80)
    print("SIMPLIFIED APPROACH - Pros & Cons")
    print("-" * 80)
    print("Pros:")
    print("  ✓ Simple, flat structure (1-2 levels max)")
    print("  ✓ Standard 2-space indentation")
    print("  ✓ Helper functions for code reuse")
    print("  ✓ Matches proven working implementations (GLIM)")
    print("  ✓ Easier to maintain and debug")
    print("\nCons:")
    print("  ✗ Less detailed error checking")
    print("  ✗ Assumes partition is already found (global setup)")
    print("  ✗ May need to add error handling to helper functions")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("Option 1: KEEP CURRENT APPROACH")
    print("  When: If third boot test with v0.4.1 fixes WORKS")
    print("  Why:  Comprehensive error checking, validated paths")
    print("  Risk: Complex structure may still cause issues")
    print()
    print("Option 2: SWITCH TO SIMPLIFIED APPROACH")
    print("  When: If third boot test STILL FAILS")
    print("  Why:  Matches proven working implementations (GLIM)")
    print("  Risk: Need to ensure error handling is adequate")
    print()
    print("Option 3: HYBRID APPROACH")
    print("  When: Want best of both worlds")
    print("  Why:  Use simplified structure + keep error checking")
    print("  How:  Move validation to helper functions, flatten menuentry")
    print()
    print("NEXT STEP: Boot test current v0.4.1 code on real hardware")
    print("=" * 80)


if __name__ == "__main__":
    compare_approaches()

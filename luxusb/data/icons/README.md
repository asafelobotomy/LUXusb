# Distribution Icons

This directory contains logo icons for all supported Linux distributions displayed in the LUXusb GUI.

## Icon Specifications

- **Format**: PNG (Portable Network Graphics)
- **Resolution**: 512x512 pixels (high-resolution)
- **Display Size**: 48x48 pixels (scaled by GTK)
- **Naming Convention**: `{distro-id}.png` 
  - Lowercase only
  - Hyphens for multi-word names
  - Must exactly match distribution ID in JSON files
  - Examples: `arch.png`, `bazzite-desktop.png`, `opensuse-tumbleweed.png`
- **Quality**: All logos upgraded to high-resolution (512x512) as of 2026-01-23

## Current Icons

### High-Resolution Icons (14/14) ⭐
All distribution logos are now 512x512 high-resolution PNGs:

| Distribution | File | Size | Source | Resolution |
|--------------|------|------|--------|------------|
| Arch Linux | `arch.png` | 28 KB | Wikimedia Commons SVG | 512x512 |
| Bazzite Desktop | `bazzite-desktop.png` | 54 KB | Official GitHub PNG | 512x512 |
| Bazzite Handheld | `bazzite-handheld.png` | 54 KB | Official GitHub PNG | 512x512 |
| CachyOS Desktop | `cachyos-desktop.png` | 3.9 KB | Arch logo (Arch-based) | 512x512 |
| CachyOS Handheld | `cachyos-handheld.png` | 3.9 KB | Arch logo (Arch-based) | 512x512 |
| Debian | `debian.png` | 31 KB | Wikimedia Commons SVG | 512x512 |
| Fedora | `fedora.png` | 20 KB | Wikimedia Commons SVG | 512x512 |
| Kali Linux | `kali.png` | 40 KB | Wikimedia Commons SVG | 512x512 |
| Linux Mint | `linuxmint.png` | 25 KB | Wikimedia Commons SVG | 512x512 |
| Manjaro | `manjaro.png` | 2.4 KB | Wikimedia Commons SVG | 512x512 |
| openSUSE Tumbleweed | `opensuse-tumbleweed.png` | 34 KB | Wikimedia Commons SVG | 512x512 |
| Parrot Security | `parrotos.png` | 17 KB | Simple Icons SVG | 512x512 |
| Pop!_OS | `popos.png` | 17 KB | Simple Icons SVG | 512x512 |
| Ubuntu | `ubuntu.png` | 27 KB | Wikimedia Commons SVG | 512x512 |

**Quality Improvement**: All logos upgraded from varying sizes (641B-11KB) to consistent high-resolution 512x512 PNGs (2.4KB-54KB) on 2026-01-23.

## Adding New Distribution Icons

### Option 1: Official Logo (Recommended)
```bash
cd luxusb/data/icons

# Download official logo at 256x256 or higher
wget -O newdistro.png "https://example.com/logo.png"

# Verify icon displays correctly
file newdistro.png
```

### Option 2: Symbolic Link to Similar Distro
```bash
cd luxusb/data/icons

# Link to parent distribution (Arch-based → arch.png, Debian-based → debian.png, etc.)
ln -s arch.png newdistro.png
```

### Option 3: System Fallback
If no icon file exists, the GUI automatically uses the generic CD-ROM icon:
- Icon name: `application-x-cd-image`
- Provided by system icon theme

## Icon Sources

### Official Distribution Websites & Repositories
- **Bazzite**: https://github.com/ublue-os/bazzite (logo.png from repo_content/)
- **CachyOS**: https://github.com/CachyOS/cachyos-repo (using Arch logo for Arch-based distro)
- **openSUSE**: https://www.opensuse.org/ (official logos)
- **ParrotOS**: https://parrotlinux.org/ (Simple Icons project SVG)
- **Pop!_OS**: https://system76.com/pop (Simple Icons project SVG)

### Simple Icons Project
High-quality SVG logos from [Simple Icons](https://github.com/simple-icons/simple-icons):
- Pop!_OS: `popos.svg` → converted to 512x512 PNG
- Parrot Security: `parrotsecurity.svg` → converted to 512x512 PNG

### License Compliance
All distribution logos are trademarks of their respective owners:
- Used for identification purposes only
- No endorsement implied
- Fair use for software distribution purposes

If you represent a distribution and want your logo updated or removed, please open an issue at:
https://github.com/solon/luxusb/issues

## Testing Icons

```python
# Test icon loading for all distributions
python3 << 'EOF'
from pathlib import Path

icons_dir = Path("luxusb/data/icons")
distros = ["arch", "debian", "fedora", "ubuntu", "cachyos-desktop", "bazzite-desktop"]

for distro_id in distros:
    icon_path = icons_dir / f"{distro_id}.png"
    if icon_path.exists():
        print(f"✓ {distro_id}: {icon_path.stat().st_size} bytes")
    else:
        print(f"✗ {distro_id}: Missing (will use fallback)")
EOF
```

## TODO: Official Icon Replacement

The following distributions currently use symbolic links and should be replaced with official logos when available:

- [ ] **bazzite-desktop.png** - Need official Bazzite logo (currently → fedora.png)
- [ ] **bazzite-handheld.png** - Need official Bazzite logo (currently → fedora.png)
- [ ] **cachyos-desktop.png** - Need official CachyOS logo (currently → arch.png)
- [ ] **cachyos-handheld.png** - Need official CachyOS logo (currently → arch.png)
- [ ] **parrotos.png** - Need official ParrotOS logo (currently → debian.png)

### How to Obtain Official Logos

1. **Check distribution's website** for press kit or assets page
2. **Contact distribution maintainers** for official logo files
3. **Use public domain logos** from wikimedia/commons if available
4. **Screenshot from official website** as last resort (ensure proper licensing)

Recommended size: 512x512 PNG with transparent background

---

**Note**: All icons in this directory are the property of their respective owners and are used solely for the purpose of identifying their distributions within this application.

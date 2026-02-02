# LUXusb

A user-friendly AppImage application for creating bootable USB drives with multiple Linux distributions.

## Features

- 🔍 Automatic USB device detection
- 💾 Smart partitioning (EFI + Data)
- 🌐 Download popular Linux distributions (14+ distros)
- 📁 **Custom ISO support** - Add your own bootable ISOs
- ✅ ISO integrity verification (SHA256 + GPG)
- 🔐 **Cosign verification** - Cryptographic verification for container-based distros
- 🚀 GRUB2-based multi-boot support
  - **32-bit UEFI support** - Boots on 2010-2012 Atom tablets (i386-efi + x86_64-efi)
  - **MEMDISK fallback** - Loads small ISOs (<512MB) directly into RAM for compatibility
- 🔒 **Secure Boot signing** - Sign bootloader with MOK keys
- 🔄 Pause/resume downloads with mirror failover
- 🤖 **Automatic distro updates** - Tools to keep ISO links current
- 🛡️ **Enhanced security** - Multi-tier verification, automatic retries
- 📊 Real-time download progress with mirror health tracking
- 🎯 Secure privilege handling via pkexec
- 📋 JSON-based distribution metadata

## Architecture

```
Host Application (AppImage)
├── USB Detection & Selection
├── ISO Download Manager
├── Partition Manager
└── GRUB Installer

Boot Environment (USB)
├── Minimal Linux (Alpine-based)
├── GRUB2 Bootloader
└── ISO Boot Menu
```

## Requirements

### Host System (Required)
- Linux (kernel 4.0+)
- Python 3.10+
- GTK4
- polkit (for privilege escalation)
- 2GB+ free space for ISOs

### Host System (Optional)
- **cosign** - For container signature verification (Bazzite, etc.)
  - Debian/Ubuntu: `sudo apt install cosign`
  - Fedora: `sudo dnf install cosign`
  - Arch: `sudo pacman -S cosign`
- **docker** or **podman** - For container digest retrieval

> **Note**: App fully functional without optional dependencies.
> Install cosign for 100% automated Bazzite verification!

### Target USB
- **Capacity**: 8GB+ recommended (4GB minimum for single ISO)
- **Speed**: USB 2.0+ supported (USB 3.0+ recommended for faster transfers)
- **Compatibility**: 
  - Modern systems (2015+): Full compatibility with exFAT
  - Legacy systems (2010-2015): 95%+ compatible, may need `rootdelay=30` kernel parameter
  - Older USB 2.0 controllers (~5%): Known firmware bugs with exFAT, use FAT32 if boot fails

#### Filesystem Trade-offs
LUXusb uses **exFAT** by default for the data partition:
- ✅ **Advantages**: Supports ISOs >4GB (Windows 11, some Fedora spins)
- ⚠️ **Known issue**: ~5% of USB 2.0 controllers have firmware bugs causing slow enumeration
- 🔧 **Workaround**: If boot hangs, add `rootdelay=30` to GRUB kernel parameters, or reformat USB with FAT32 (4GB file limit)

**When to use FAT32 instead**:
- All your ISOs are <4GB
- Using older USB 2.0 hardware (pre-2010)
- Maximum compatibility is critical

## Quick Start

```bash
# Download the AppImage
wget https://github.com/solon/luxusb/releases/latest/download/luxusb.AppImage

# Make executable
chmod +x luxusb.AppImage

# Run
./luxusb.AppImage
```

## Development Setup

```bash
# Clone repository
git clone https://github.com/solon/luxusb.git
cd luxusb

# Create virtual environment (REQUIRED on Arch/modern systems)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode (use venv Python!)
.venv/bin/python -m luxusb

# Or with activated venv:
python -m luxusb
```

> **Important**: Always use the virtual environment (`.venv/bin/python`) to avoid dependency issues!
> Modern Linux distributions use PEP 668 externally-managed environments.

## Building

```bash
# Build AppImage
./scripts/build-appimage.sh

# Build boot environment
./scripts/build-boot-env.sh
```

## Project Structure

```
luxusb/
├── luxusb/          # Main Python package
│   ├── gui/               # GTK4 interface
│   ├── core/              # Core functionality
│   ├── utils/             # Utility modules
│   └── data/              # Static data (distros, configs)
├── boot-environment/      # Minimal Linux for USB
├── scripts/               # Build and helper scripts
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
└── assets/                # Icons, images, etc.
```

## Usage Guide

1. **Launch Application**: Run the AppImage
2. **Select USB Device**: Choose your target USB drive (⚠️ all data will be erased)
3. **Choose Distribution**: Select from the list of popular Linux distros or add custom ISO
4. **Download & Install**: Application downloads ISO and sets up bootable USB
5. **Boot**: Restart computer, boot from USB, select your distro

### Maintenance Tools

Keep distribution links up-to-date:

```bash
# Verify all distro links are working
## Supported Distributions (14+)

**Traditional Distros** (GPG verified):
- Ubuntu (Desktop, Server)
- Fedora Workstation
- Debian
- Linux Mint
- Arch Linux
- Pop!_OS
- Manjaro
- Kali Linux

**Gaming-Optimized** (Cosign verified):
- Bazzite Desktop - Fedora Silverblue gaming variant
- Bazzite Handheld - Steam Deck optimized
- CachyOS Desktop - Performance-tuned Arch
- CachyOS Handheld - Portable gaming

**Other**:
- ParrotOS - Security testing
- openSUSE Tumbleweed - Rolling release

See [DISTRO_MANAGEMENT.md](docs/DISTRO_MANAGEMENT.md) for full details and [COSIGN_VERIFICATION.md](docs/COSIGN_VERIFICATION.md) for cosign integration.

## Safety Features

- USB device confirmation dialog
- Free space validation
- ISO checksum verification
- Atomic operations (rollback on failure)
- Clear error messages

## Troubleshooting

### USB Not Booting

**Symptom**: System doesn't detect the USB drive at boot

**Solutions**:
1. **BIOS settings**: Enable "USB Boot" in BIOS/UEFI settings
2. **Boot order**: Set USB as first boot device
3. **Legacy vs UEFI**: Try toggling between Legacy/UEFI boot modes
4. **USB port**: Try different USB ports (USB 2.0 ports may be more reliable on older systems)

### Boot Hangs with "Waiting for USB"

**Symptom**: Boot process hangs with message about waiting for USB device

**Solutions**:
1. **Slow enumeration**: Add `rootdelay=30` to GRUB kernel parameters:
   - Press `e` at GRUB menu
   - Add `rootdelay=30` to the `linux` line
   - Press `Ctrl+X` to boot
2. **USB 2.0 compatibility**: ~5% of USB 2.0 controllers have firmware bugs with exFAT
   - If issue persists, reformat USB with FAT32 (4GB file size limit)

### 32-bit UEFI Systems (2010-2012 Tablets)

**Symptom**: "No bootable device" on Atom-based tablets/netbooks

**Solution**: LUXusb automatically installs both i386-efi and x86_64-efi GRUB targets. If boot still fails:
1. Verify host system has `grub-efi-ia32-bin` package installed:
   - Debian/Ubuntu: `sudo apt install grub-efi-ia32-bin`
   - Fedora: `sudo dnf install grub2-efi-ia32-modules`
   - Arch: `sudo pacman -S grub`
2. Recreate USB with updated host system

### Secure Boot Errors

**Symptom**: "Secure Boot violation" or "shim-signed not found"

**Solution**: Install shim bootloader:
- Ubuntu/Debian: `sudo apt install shim-signed`
- Fedora: `sudo dnf install shim-x64`
- Arch: `sudo pacman -S shim-signed`

Then disable Secure Boot in BIOS or recreate USB after installing shim.

### Small ISOs Not Booting

**Symptom**: Utility ISOs (<512MB) like GParted/Clonezilla fail to boot

**Solution**: LUXusb automatically generates MEMDISK fallback entries for small ISOs. Look for "(RAM Boot)" entries in the GRUB menu.

Requirements:
- Host system needs `syslinux-common` or `syslinux` package installed
- Debian/Ubuntu: `sudo apt install syslinux-common`
- Fedora: `sudo dnf install syslinux`
- Arch: `sudo pacman -S syslinux`

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

GPLv3 - See [LICENSE](LICENSE) for details.

## Disclaimer

⚠️ **Warning**: This tool will erase all data on the selected USB device. Always backup important data before proceeding.

## Credits

Inspired by Ventoy (https://www.ventoy.net/)

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
- 8GB+ capacity recommended
- USB 2.0+ (USB 3.0+ recommended)

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

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

GPLv3 - See [LICENSE](LICENSE) for details.

## Disclaimer

⚠️ **Warning**: This tool will erase all data on the selected USB device. Always backup important data before proceeding.

## Credits

Inspired by Ventoy (https://www.ventoy.net/)

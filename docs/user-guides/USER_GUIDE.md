# User Guide

## Installation

### Download

Download the latest AppImage from the [releases page](https://github.com/yourusername/luxusb/releases).

### Make Executable

```bash
chmod +x LUXusb-*.AppImage
```

### Run

```bash
./LUXusb-*.AppImage
```

The application will request administrator privileges when needed.

## Usage

### Step 1: Select USB Device

1. Launch LUXusb
2. Insert your USB drive
3. Click "Scan for USB Devices"
4. Select your USB device from the list
5. Click "Continue"

⚠️ **Warning**: All data on the selected USB will be erased!

### Step 2: Choose Distribution Family

1. Select a distribution family (Arch-based, Debian-based, Fedora-based, or Independent)
2. Browse distributions within that family
3. Use the search box to filter distributions
4. Select one or more distributions (checkbox)
5. Review the details (version, size, GPG verification status)

**Optional: Add Custom ISOs**

1. From the family page, click "📁 Add Custom ISO Files"
2. Select your own ISO files
3. Optionally upload verification files (checksum, GPG signature, GPG key)
4. LUXusb will validate the ISO format
5. Add multiple custom ISOs for a multi-boot USB

**Optional: Enable Secure Boot**

1. Toggle "Secure Boot" switch in the header bar (if available)
2. Bootloader will be signed with MOK keys
3. On first boot, you'll need to enroll the MOK keys

5. Click "Download & Install"

### Step 3: Wait for Installation

The application will:
1. Partition your USB device
2. Download the ISO file
3. Verify the download integrity
4. Install the bootloader
5. Configure the boot menu

This may take 10-60 minutes depending on your internet speed.

### Step 4: Boot from USB

1. Remove the USB drive safely
2. Insert it into your target computer
3. Boot from USB (usually F12, F2, or DEL at startup)
4. Select the Linux distribution from the menu
5. Follow the distribution's installation instructions

## Requirements

### System Requirements

- Linux operating system
- 2GB free disk space (for downloading ISOs)
- Internet connection
- Administrator privileges

### USB Requirements

- 8GB or larger capacity (16GB+ recommended)
- USB 2.0 or higher (USB 3.0+ recommended)
- Will be completely erased

### Supported Systems

- Ubuntu 20.04+
- Fedora 35+
- Debian 11+
- Arch Linux (latest)
- Most modern Linux distributions

## Features

### Safety Features

- ✅ System disk protection (prevents formatting system drives)
- ✅ Device confirmation dialog
- ✅ ISO checksum verification (SHA256)
- ✅ Custom ISO format validation
- ✅ Bootable ISO detection
- ✅ Free space validation
- ✅ Detailed error messages
- ✅ Pause/resume downloads
- ✅ Mirror failover support

### Supported Distributions

LUXusb includes 14+ curated distributions organized by family, with GPG verification and checksums:

**Arch-based:**
- Arch Linux, Manjaro, CachyOS (Desktop & Handheld)

**Debian-based:**
- Debian, Ubuntu, Linux Mint, Pop!_OS, Kali Linux

**Fedora-based:**
- Fedora Workstation, Bazzite (Desktop & Handheld)

**Independent:**
- openSUSE Tumbleweed

**Plus:** Add any bootable ISO file with custom ISO support!

Distributions loaded from JSON files - easily updated without code changes.

## Troubleshooting

### "No USB devices found"

**Solutions:**
- Ensure USB is properly inserted
- Try a different USB port
- Check if USB is recognized by system: `lsblk`
- Try clicking "Scan for USB Devices" again

### "Permission denied"

**Solutions:**
- The application requires administrator privileges
- Run with: `sudo ./LUXusb-*.AppImage`
- Or use pkexec: `pkexec ./LUXusb-*.AppImage`

### "Download failed"

**Solutions:**
- Check internet connection
- Try again (downloads can resume)
- Check if firewall is blocking
- Try different network

### "Checksum verification failed"

**Solutions:**
- Delete partial download and retry
- Check available disk space
- Report issue if persists

### "GRUB installation failed"

**Solutions:**
- Ensure GRUB is installed: `sudo apt install grub-efi-amd64`
- Try different USB device
- Check USB is not write-protected

### "Custom ISO validation failed"

**Solutions:**
- Ensure file is a valid ISO 9660 format
- Check file size (10 MB - 10 GB)
- Verify ISO is bootable using `isoinfo -d -i file.iso`
- Try re-downloading the ISO

### "Secure Boot signing failed"

**Solutions:**
- Install sbsign: `sudo apt install sbsigntool`
- Install mokutil: `sudo apt install mokutil`
- Check if EFI variables are accessible: `ls /sys/firmware/efi/efivars/`
- Run as root if needed

### USB won't boot

**Possible causes:**

1. **Secure Boot enabled**
   - Enable "Secure Boot" toggle in LUXusb before creating USB
   - Or disable Secure Boot in BIOS/UEFI
   - Enroll MOK keys if using Secure Boot

2. **Wrong boot mode**
   - Ensure UEFI mode is enabled (not Legacy/CSM)
   - Check BIOS boot order

3. **USB not selected**
   - Press F12, F2, or DEL at startup
   - Select USB device from boot menu

4. **Hardware compatibility**
   - Some older systems don't support UEFI boot
   - Try different USB port (USB 2.0 vs 3.0)

## FAQ

### Q: Can I add multiple ISOs?

A: Yes! You can select multiple distributions from the family pages and add custom ISO files for a multi-boot USB.

### Q: Can I use my own ISO files?

A: Absolutely! Click "📁 Add Custom ISO Files" from the family page. You can also upload verification files (checksum, GPG signature, GPG key) for security.

### Q: What about Secure Boot?

A: LUXusb supports Secure Boot signing. Toggle the "Secure Boot" switch in the header. You'll need to enroll the MOK keys on first boot.

### Q: Does this work on Mac/Windows?

A: No, LUXusb only runs on Linux. However, you can use the created USB on any system that supports UEFI boot.

### Q: What verification methods are supported?

A: LUXusb supports SHA256 checksums, GPG signatures, and Cosign signatures. All official distributions are verified automatically.

### Q: Is my USB encrypted?

A: No, the USB is not encrypted. Do not store sensitive data.

### Q: Can I use this USB for normal storage too?

A: The data partition can store files, but space is limited after ISO download.

### Q: How do I remove LUXusb from USB?

A: Format the USB using your system's disk utility or:
```bash
sudo wipefs -a /dev/sdX  # Replace X with your device
```

### Q: What if I want to change the ISO?

A: Run LUXusb again and select a different distribution. You can also add more ISOs to an existing LUXusb USB in "append mode".

### Q: Can I add ISOs to an existing LUXusb USB?

A: Yes! When you select a USB that already has LUXusb configured, you'll be asked if you want to "Add More ISOs" or "Erase and Start Fresh".

## Advanced Usage

### Viewing Logs

Logs are saved to:
```
~/.local/share/luxusb/logs/luxusb.log
```

View with:
```bash
tail -f ~/.local/share/luxusb/logs/luxusb.log
```

### Configuration

Config file location:
```
~/.config/luxusb/config.yaml
```

You can edit this to change default settings.

### Manual ISO Verification

Verify ISO checksum manually:
```bash
sha256sum /path/to/downloaded.iso
```

Compare with official checksum from distribution website.

## Getting Help

- [GitHub Issues](https://github.com/yourusername/luxusb/issues)
- [Documentation](https://github.com/yourusername/luxusb/docs)
- [Community Forum](https://forum.luxusb.org)

## Safety and Warnings

⚠️ **Important Warnings:**

1. **Data Loss**: All data on selected USB will be permanently erased
2. **System Disk**: Never select your system disk (protected by default)
3. **Power Loss**: Don't disconnect USB or shutdown during installation
4. **Internet**: Large downloads can consume significant bandwidth
5. **Verification**: Always verify downloaded ISOs for security

## License

LUXusb is licensed under GPLv3. See LICENSE file for details.

## Credits

- Uses [GRUB](https://www.gnu.org/software/grub/) bootloader
- Built with [GTK4](https://www.gtk.org/) and [Libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/)
- Security verification with [GnuPG](https://gnupg.org/) and [Sigstore Cosign](https://docs.sigstore.dev/cosign/overview/)

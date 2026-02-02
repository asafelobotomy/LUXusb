# LUXusb Boot Menu - User Guide

**Version**: 0.6.3  
**What You'll See**: Complete guide to the new comprehensive boot menu

## Main Menu

When you boot from your LUXusb drive, you'll see:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         LUXusb Multiboot Menu                             ║
║                            Version 0.6.3                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

  ℹ️  View Help & Keyboard Shortcuts
  
  [A] Ubuntu 24.04
  [B] Arch Linux 2026.01.01
  [C] Linux Mint 22
  [D] Fedora 40
  [E] Debian 12.4
  
  🔄 Reboot System
  ⏻  Power Off

Use the ↑ and ↓ keys to select an entry. Press Enter to boot it.
Press 'A'-'E' to quickly jump to an ISO. Press 'H' for help.
Booting automatically in 30 seconds...
```

### Quick Actions

- **↑/↓ Arrows**: Move selection up/down
- **Enter**: Boot selected item
- **A-E (or any hotkey)**: Jump directly to that ISO
- **ESC**: Go back (when in submenu)
- **Any key**: Stop the countdown timer

## Help Screen

Press Enter on "ℹ️  View Help & Keyboard Shortcuts" to see:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         LUXusb Multiboot Menu                             ║
║                            Version 0.6.3                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  5 ISOs available                                                         ║
║                                                                           ║
║  Navigation:                                                              ║
║    ↑/↓     - Select menu item                                             ║
║    Enter   - Boot selected item                                           ║
║    [A-Z]   - Quick jump to ISO (hotkeys shown in [brackets])              ║
║    Esc     - Return to previous menu / Exit submenu                       ║
║                                                                           ║
║  Boot Options (in ISO submenus):                                          ║
║    Normal        - Standard boot with default kernel parameters           ║
║    Safe Graphics - Disable GPU acceleration (nomodeset + vendor flags)    ║
║    MEMDISK       - Load entire ISO into RAM (small ISOs only)             ║
║                                                                           ║
║  Advanced:                                                                ║
║    Press 'c' for GRUB command line                                        ║
║    Press 'e' to edit boot parameters                                      ║
║                                                                           ║
║  Timeout: Menu auto-boots first item in 30 seconds                        ║
║           Press any key to stop countdown                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

Press ESC to return to menu...
```

**To exit**: Press ESC or wait (menu returns after 9999 seconds, but any key works)

## ISO Submenu

When you select an ISO (e.g., press 'A' or arrow down and hit Enter), you'll see:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         [A] Ubuntu 24.04                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  Description: User-friendly Linux distribution with GNOME desktop         ║
║  ISO Size: 3500 MB                                                        ║
║  Architecture: x86_64                                                     ║
╚═══════════════════════════════════════════════════════════════════════════╝

  ▶ Boot Normally (Recommended)
  🛡️  Safe Graphics Mode (GPU Issues)
  💾 MEMDISK Mode (Load to RAM)
  
  ←  Return to Main Menu

Use the ↑ and ↓ keys to select an option. Press Enter to boot it.
Press ESC to return to the main menu.
```

### Boot Options Explained

#### ▶ Boot Normally (Recommended)

**What it does**: Boots the Linux distribution with standard kernel parameters

**Use when**:
- First time trying this distribution
- Your hardware is modern and well-supported
- You want the fastest boot and best performance
- Previous boots worked fine

**Technical**: No special parameters, just loads kernel and initrd from ISO

---

#### 🛡️  Safe Graphics Mode (GPU Issues)

**What it does**: Disables GPU acceleration and uses basic display drivers

**Use when**:
- Screen goes black after selecting normal boot
- You see corrupted graphics or garbled display
- System hangs with a blank screen
- You have NVIDIA, AMD, or Intel GPU problems
- Running in a virtual machine with display issues

**Technical details**:
- Adds `nomodeset` - Disables kernel mode setting (keeps basic VESA/framebuffer)
- Adds `i915.modeset=0` - Disables Intel GPU modesetting
- Adds `nouveau.modeset=0` - Disables NVIDIA open-source driver modesetting
- Adds `radeon.modeset=0` - Disables AMD Radeon modesetting
- Adds `nvidia.modeset=0` - Disables NVIDIA proprietary driver modesetting

**Trade-offs**:
- ✅ Works on almost any hardware
- ✅ Fixes black screen issues
- ✅ Good for initial installation
- ❌ Lower screen resolution
- ❌ No GPU acceleration (slower graphics)
- ❌ May not support multiple monitors

---

#### 💾 MEMDISK Mode (Load to RAM)

**What it does**: Loads the entire ISO file into system RAM, then boots from RAM

**Use when**:
- You have plenty of RAM (check ISO size requirement!)
- You want faster ISO access after initial load
- You need to remove the USB drive after booting
- You're troubleshooting USB read errors
- The ISO is a rescue/recovery tool you'll use extensively

**Requirements**:
- **Ubuntu 24.04 example**: Requires 3500 MB (3.5 GB) of free RAM
- **Arch Linux example**: Requires 800 MB of free RAM
- **Windows PE example**: Requires 512 MB of free RAM

**Benefits**:
- ⚡ Much faster ISO access after initial load
- 🔌 Can remove USB drive after loading
- 🛡️ No USB read errors during operation
- 💪 Better for rescue operations

**Drawbacks**:
- 🐌 Slower initial boot (copying ISO to RAM)
- 💾 Uses RAM (can't use that RAM for applications)
- ⚠️ Not available if not enough RAM
- ❌ Not shown if ISO is too large (>2GB by default)

**When you'll see this**:
- Small ISOs (< 2GB): MEMDISK option shown
- Large ISOs (> 2GB): MEMDISK option hidden
- Windows PE ISOs: Always shown (different loading method)
- System with low RAM: May fail if not enough memory

---

#### ←  Return to Main Menu

**What it does**: Takes you back to the main menu without booting

**Use when**:
- You selected the wrong ISO
- You want to check other options
- You're just browsing
- You changed your mind

**Shortcut**: Press ESC anywhere in a submenu to go back

## Example Scenarios

### Scenario 1: Normal Boot (Everything Works)

1. Boot USB → Main menu appears
2. Press **'A'** (or arrow to Ubuntu, press Enter)
3. Submenu appears with three options
4. **▶ Boot Normally** is already highlighted
5. Press **Enter**
6. Ubuntu boots successfully ✅

**Time**: ~30 seconds from USB boot to desktop

---

### Scenario 2: Black Screen - Use Safe Graphics

1. Boot USB → Main menu appears
2. Press **'A'** to jump to Ubuntu
3. Try **▶ Boot Normally** first
4. ❌ Screen goes black after GRUB
5. Reboot and return to USB menu
6. Press **'A'** again
7. Arrow down to **🛡️  Safe Graphics Mode**
8. Press **Enter**
9. ✅ Screen works! System boots with basic graphics

**Why it worked**: `nomodeset` disabled GPU driver, fell back to VESA framebuffer

**Next steps**: 
- After installation, install proper GPU drivers
- Or keep using safe graphics if it works for your use case

---

### Scenario 3: USB is Slow - Try MEMDISK

1. Boot USB → Main menu appears
2. Notice: "Arch Linux" is only 800 MB (shown in submenu)
3. Your system has 8 GB RAM (plenty of space!)
4. Press **'B'** to jump to Arch Linux
5. Arrow down to **💾 MEMDISK Mode**
6. See: "Requires: 800 MB of available RAM"
7. Press **Enter**
8. Wait ~20 seconds while ISO loads to RAM
9. ✅ Boots from RAM - MUCH faster than USB!

**Benefits**: 
- ISO operations are instant (RAM speed)
- Can remove USB drive if needed
- No USB read errors

**Trade-off**: 
- 800 MB of your 8 GB RAM is used
- Initial load was slower (20 sec vs 5 sec)

---

### Scenario 4: Need Help

1. Boot USB → Main menu appears
2. Press **↑** to highlight **ℹ️  View Help & Keyboard Shortcuts**
3. Press **Enter**
4. Screen clears, shows full help text with box drawing
5. Read through all instructions:
   - Navigation keys
   - Boot mode descriptions
   - Hotkey usage
   - Advanced options (e/c keys)
6. Press **ESC** when done
7. ✅ Back to main menu, now you know what to do!

---

### Scenario 5: Wrong ISO Selected

1. Boot USB → Main menu appears
2. Press **'A'** (thinking it's Arch Linux)
3. Submenu shows: **Ubuntu 24.04** - Oops, wrong one!
4. Press **ESC**
5. ✅ Back to main menu
6. Now press **'B'** for Arch Linux
7. Submenu shows: **Arch Linux 2026.01.01** ✅
8. Press **Enter** on Boot Normally

---

### Scenario 6: Advanced User - Edit Parameters

1. Boot USB → Main menu appears
2. Press **'A'** for first ISO
3. Arrow to **▶ Boot Normally**
4. **Instead of Enter, press 'e'** (Edit)
5. GRUB editor opens showing boot commands:
   ```
   set isofile="/isos/ubuntu-24.04-desktop-amd64.iso"
   loopback loop "$isofile"
   linux (loop)/casper/vmlinuz boot=casper iso-scan/filename=$isofile quiet splash
   initrd (loop)/casper/initrd
   ```
6. Arrow down to `linux` line
7. Add custom parameters (e.g., `debug loglevel=7`)
8. Press **Ctrl+X** or **F10** to boot with edited parameters
9. ✅ Boots with your custom settings

**Use cases**:
- Enable debug logging
- Change resolution
- Add custom kernel parameters
- Override default settings

---

### Scenario 7: GRUB Command Line

1. Boot USB → Main menu appears
2. Press **'c'** (GRUB command line)
3. Terminal appears:
   ```
   grub>
   ```
4. Try commands like:
   - `ls` - List devices
   - `ls (hd0,gpt1)/` - List files on partition
   - `set` - Show all variables
   - `cat (hd0,gpt1)/boot/grub/grub.cfg` - View config
5. Type `exit` to return to menu

**Use cases**:
- Manual boot commands
- Troubleshooting
- Checking partitions
- Advanced debugging

## Troubleshooting

### "I can't see the menu, just a black screen"

**If you see nothing at all**:
1. Wait 30 seconds - it might be loading
2. Press Enter blindly - might boot first option
3. Try Safe Graphics mode on next boot
4. Check if USB was created with LUXusb v0.6.2+ (font fix)

**If this is pre-v0.6.2 USB**:
- Recreate USB with LUXusb v0.6.3
- Font loading bug was fixed in v0.6.2

### "Help screen shows weird characters"

**Cause**: Terminal doesn't support Unicode box-drawing

**What you'll see**: `╔` becomes `?` or strange symbols

**Solution**: 
- Text is still readable, just ignore the weird borders
- Or: Recreate USB, ensure `unicode.pf2` font is present
- Or: Try different display mode (console vs gfxterm)

### "Emoji don't show, just see boxes"

**Cause**: GRUB font may not include emoji glyphs

**Impact**: Minimal - text labels are still clear:
- "Information" instead of ℹ️
- "Play" instead of ▶
- "Shield" instead of 🛡️
- "Disk" instead of 💾

**Solution**: Not critical, menu is functional

### "Hotkeys don't work"

**Check**:
1. Are you in main menu? (Hotkeys only work there)
2. Did you press just the letter? (No Shift/Ctrl needed)
3. Is the letter shown in [brackets] next to ISO name?

**Example**: 
- ✅ `[A] Ubuntu` - Press 'A' works
- ❌ `Ubuntu` - No hotkey assigned (too many ISOs)

### "Menu auto-boots before I can select"

**Solution**: Press **any key** immediately when menu appears

**Changes**:
- Stops 30-second countdown
- Menu stays until you select something
- No timeout anymore in this session

**To restart countdown**: Reboot and don't press any keys

### "I booted wrong option, how do I go back?"

**Options**:
1. **Best**: Reboot system, return to USB menu
2. **In submenu**: Press ESC to go back without booting
3. **After booting**: Let it fail/error, reboot

**Can't cancel after pressing Enter**: Once boot starts, it's committed

## Tips & Tricks

### Fast Selection

- **Know which ISO you want?** Just press its hotkey (A-Z)
- **Always use same ISO?** Edit timeout in config, set it as default
- **Multiple USBs?** Label them clearly (USB1: Ubuntu/Arch, USB2: Rescue Tools)

### Safe Mode First

- **New hardware?** Try Safe Graphics first, confirm it works
- **Then** try Normal mode to test GPU acceleration
- **Better**: Boot safe, install OS, install drivers, then use full GPU

### MEMDISK Strategy

- **Small rescue ISOs**: Always use MEMDISK (faster, can remove USB)
- **Large installation ISOs**: Skip MEMDISK (wastes RAM, not much benefit)
- **Check size**: Shown in submenu (e.g., "ISO Size: 800 MB")

### Learning GRUB

- **Press 'c'** to explore GRUB command line
- **Press 'e'** to see exact boot commands
- **Read comments** in generated config (educational!)
- **Check `/boot/grub/grub.cfg`** after creating USB

### Customization

- **Want different timeout?** Edit `set timeout=30` in grub.cfg
- **Want different colors?** Edit `set menu_color_normal=` lines
- **Want different order?** Edit menuentry order in config
- **Want custom entries?** Add custom menuentry blocks at end

## Advanced: Reading the Generated Config

If you mount your LUXusb data partition and open `/boot/grub/grub.cfg`, you'll see:

```grub
# ══════════════════════════════════════════════════════════════
# GRUB Configuration for LUXusb v0.6.3
# Generated: Thu Jan 30 12:00:00 UTC 2026
# Total ISOs: 5
# ══════════════════════════════════════════════════════════════

# ═══ MODULE LOADING ═══
# Load all required GRUB modules first
insmod part_gpt
insmod fat
...

# ═══ GRAPHICS SETUP ═══
# Initialize video subsystem and load font
# CRITICAL: Font path must be explicit ($prefix/fonts/unicode.pf2)
# Without proper font, menu will be invisible (black screen)
load_video
if loadfont $prefix/fonts/unicode.pf2 ; then
    terminal_output gfxterm
else
    terminal_output console
    echo "Warning: Font file not found, using text mode"
fi
```

**Key sections**:
1. **MODULE LOADING**: All `insmod` commands
2. **GRAPHICS SETUP**: Font and terminal setup
3. **MENU APPEARANCE**: Colors and pager
4. **MENU BEHAVIOR**: Timeout and default
5. **STORAGE SETUP**: Search for LUXusb partition
6. **HELP & INFORMATION**: Help menu entry
7. **BOOTABLE ISOS**: Your distribution entries
8. **SYSTEM CONTROLS**: Reboot/Power off

**Each section has**:
- Clear comments explaining what it does
- Technical details for learning
- Critical warnings where needed

## Summary

LUXusb v0.6.3 provides a **comprehensive, self-documenting boot menu**:

✅ **Beginner-friendly**: Help screen, clear descriptions, visual cues  
✅ **Power-user capable**: Hotkeys, command line, parameter editing  
✅ **Informative**: ISO details, RAM requirements, parameter explanations  
✅ **Safe**: Explicit safe graphics mode with use cases  
✅ **Professional**: Beautiful formatting, icons, organized structure  

**No external documentation needed** - everything you need is in the menu!

---

**Questions?** Check:
- [GRUB_COMPREHENSIVE_INFO.md](GRUB_COMPREHENSIVE_INFO.md) - Technical implementation details
- [GRUB_INVISIBLE_MENU_FIX.md](../fixes/GRUB_INVISIBLE_MENU_FIX.md) - Font loading background
- [GRUB_SUBMENU_RESEARCH.md](../../docs/development/GRUB_SUBMENU_RESEARCH.md) - Research and design decisions

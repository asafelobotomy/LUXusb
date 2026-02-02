# Testing Checklist for LUXusb v0.6.3

**Version**: 0.6.3  
**Focus**: Comprehensive GRUB menu information system  
**Tester**: _______________  
**Date**: _______________

## Pre-Test Setup

### 1. Create Fresh USB
```bash
# Run LUXusb
sudo python3 -m luxusb

# Select options:
# - Choose USB device
# - Add at least 2-3 Linux distributions
# - Let it complete creation
```

### 2. Verify Creation
```bash
# Mount the USB data partition
# Check files exist:
ls -lh /path/to/usb/boot/grub/grub.cfg
ls -lh /path/to/usb/boot/grub/fonts/unicode.pf2
ls -lh /path/to/usb/isos/

# Quick config check:
head -50 /path/to/usb/boot/grub/grub.cfg
```

**Expected in config**:
- [ ] Header says "GRUB Configuration for LUXusb v0.6.3"
- [ ] Organized sections with `# ═══` markers
- [ ] `loadfont $prefix/fonts/unicode.pf2` (NOT just "unicode")
- [ ] Help menuentry with formatted text
- [ ] ISO submenus with descriptions

## Main Menu Tests

### Test 1: Initial Boot
**Action**: Boot from USB

**Expected**:
- [ ] Menu appears (NOT black screen!)
- [ ] Version "0.6.3" visible somewhere
- [ ] Help option at top: "ℹ️  View Help & Keyboard Shortcuts"
- [ ] ISOs listed with hotkeys: `[A] Ubuntu`, `[B] Arch`, etc.
- [ ] Bottom options: "🔄 Reboot System", "⏻ Power Off"
- [ ] Countdown timer visible: "Booting automatically in 30 seconds..."

**Visual Quality**:
- [ ] Text is readable (white on black or similar)
- [ ] Icons render (or show reasonable fallback text)
- [ ] Box-drawing characters look good (or acceptable)
- [ ] No garbled text or weird symbols

**Notes**: _____________________________________

---

### Test 2: Help Screen
**Action**: Arrow to "View Help & Keyboard Shortcuts", press Enter

**Expected**:
- [ ] Screen clears
- [ ] Box-drawn header appears: `╔═══...═══╗`
- [ ] Shows "LUXusb Multiboot Menu"
- [ ] Shows "Version 0.6.3"
- [ ] Shows ISO count: "5 ISOs available" (or your actual count)
- [ ] Navigation section lists: ↑/↓, Enter, [A-Z], Esc
- [ ] Boot Options section explains: Normal, Safe Graphics, MEMDISK
- [ ] Advanced section mentions: 'c' and 'e' keys
- [ ] Timeout information shown
- [ ] Instructions: "Press ESC to return to menu..."

**Visual Quality**:
- [ ] Box-drawing creates clear borders (or readable without)
- [ ] All sections visible and formatted
- [ ] Text not cut off or wrapped badly

**Action**: Press ESC

**Expected**:
- [ ] Returns to main menu
- [ ] Selection preserved (or resets to top)

**Notes**: _____________________________________

---

### Test 3: Hotkey Navigation
**Action**: At main menu, press 'A' (first ISO's hotkey)

**Expected**:
- [ ] Immediately jumps to first ISO's submenu
- [ ] No need to arrow down and press Enter

**Action**: Press ESC, then press 'B' (second ISO)

**Expected**:
- [ ] Jumps to second ISO's submenu

**Hotkey Availability**:
- [ ] First 26 ISOs have hotkeys [A-Z]
- [ ] Hotkeys shown in brackets: `[A]`, `[B]`, etc.
- [ ] If >26 ISOs, later ones have no hotkey (still accessible via arrows)

**Notes**: _____________________________________

---

### Test 4: Timeout and Interrupt
**Action**: Boot USB and wait (don't press anything)

**Expected**:
- [ ] Countdown starts: "29 seconds...", "28 seconds...", etc.
- [ ] After 30 seconds, automatically boots first menu item

**Action**: Boot USB again, immediately press any key

**Expected**:
- [ ] Countdown stops
- [ ] Menu stays indefinitely (no auto-boot)
- [ ] Can now select any option

**Notes**: _____________________________________

## ISO Submenu Tests

### Test 5: ISO Metadata Display
**Action**: Select any ISO (press hotkey or arrow + Enter)

**Expected Submenu Header**:
- [ ] Shows ISO name: `[A] Ubuntu 24.04` or similar
- [ ] Separator line: `─── Ubuntu 24.04 ───`
- [ ] "Description:" line with actual description
- [ ] "ISO Size:" line showing MB (e.g., "3500 MB")
- [ ] "Architecture:" line (e.g., "x86_64")

**Notes**: _____________________________________

---

### Test 6: Boot Option Descriptions
**Action**: In ISO submenu, read each option

**Expected Options** (at minimum):
1. [ ] "▶ Boot Normally (Recommended)"
   - Has comment: "Standard boot with default kernel parameters"
2. [ ] "🛡️  Safe Graphics Mode (GPU Issues)"
   - Has comment: "Disables GPU acceleration for compatibility"
   - Has comment: "Use if: Black screen, corrupted display, GPU hangs"
   - Has comment: "Adds: nomodeset i915.modeset=0 ..."
3. [ ] "💾 MEMDISK Mode" (only if ISO is small, e.g., <2GB)
   - Has comment: "Loads entire ISO into system RAM"
   - Has comment: "Requires: XXX MB of available RAM"
   - Has comment: "Benefit: Faster boot, USB can be removed..."
   - Has comment: "Warning: Slower initial load, uses RAM"
4. [ ] "←  Return to Main Menu"
   - Has comment: "Press ESC or select this to go back"
   - Has comment: "Tip: ESC key works from anywhere..."

**Visual Quality**:
- [ ] Icons visible (or text labels clear)
- [ ] Comments readable (indented or clearly formatted)
- [ ] RAM requirement shows actual ISO size

**Notes**: _____________________________________

---

### Test 7: MEMDISK Availability
**Setup**: Check ISO sizes on USB

**Expected Logic**:
- [ ] Small ISOs (<2GB): MEMDISK option appears
- [ ] Large ISOs (>2GB): MEMDISK option hidden
- [ ] Windows PE ISOs: Special MEMDISK option (if applicable)

**Test**: Select a small ISO (e.g., Arch Linux ~800MB)

**Expected**:
- [ ] MEMDISK option present
- [ ] Shows RAM requirement matching ISO size

**Test**: Select a large ISO (e.g., Ubuntu 24.04 ~3.5GB)

**Expected** (if >2GB):
- [ ] MEMDISK option NOT shown (too large)

**Notes**: _____________________________________

---

### Test 8: Return to Main Menu
**Action**: In ISO submenu, arrow to "←  Return to Main Menu"

**Expected**:
- [ ] Selecting it returns to main menu
- [ ] No boot happens

**Action**: In ISO submenu, press ESC (don't select return option)

**Expected**:
- [ ] Also returns to main menu
- [ ] Same result as selecting "Return to Main Menu"

**Notes**: _____________________________________

## Boot Functionality Tests

### Test 9: Normal Boot
**Action**: Select ISO → "▶ Boot Normally"

**Expected**:
- [ ] ISO boots correctly
- [ ] Reaches distribution's boot menu or desktop
- [ ] No black screen
- [ ] No errors

**Distributions to test**:
- [ ] Ubuntu: _________________________
- [ ] Arch Linux: _____________________
- [ ] Other: __________________________

**Notes**: _____________________________________

---

### Test 10: Safe Graphics Mode
**Setup**: Ideally test on hardware with GPU issues OR force it

**Action**: Select ISO → "🛡️  Safe Graphics Mode"

**Expected**:
- [ ] Boots with nomodeset parameters
- [ ] Screen remains visible (no black screen)
- [ ] May have lower resolution
- [ ] Reaches boot menu/desktop

**To verify safe mode is active**:
- [ ] Once booted, check: `cat /proc/cmdline` should show "nomodeset"

**Notes**: _____________________________________

---

### Test 11: MEMDISK Mode (if available)
**Action**: Select small ISO → "💾 MEMDISK Mode"

**Expected**:
- [ ] Shows "Loading ISO into RAM..." or similar
- [ ] Takes longer initially (10-30 seconds depending on size)
- [ ] Then boots normally
- [ ] After boot, can remove USB drive (test if needed)

**Notes**: _____________________________________

---

### Test 12: Edit Parameters (Advanced)
**Action**: In ISO submenu, highlight boot option, press 'e'

**Expected**:
- [ ] GRUB editor opens
- [ ] Shows boot commands:
  ```
  set isofile="/isos/..."
  loopback loop "$isofile"
  linux (loop)/... boot=... iso-scan/...
  initrd (loop)/...
  ```
- [ ] Comments visible if present
- [ ] Can arrow through lines

**Action**: Don't edit, press ESC or Ctrl+C

**Expected**:
- [ ] Returns to submenu without booting

**Action**: Try again, press 'e', make edit (e.g., add "debug"), press Ctrl+X or F10

**Expected**:
- [ ] Boots with edited parameters

**Notes**: _____________________________________

---

### Test 13: GRUB Command Line
**Action**: At main menu, press 'c'

**Expected**:
- [ ] GRUB command line appears: `grub>`
- [ ] Can type commands

**Commands to try**:
- `ls` - [ ] Lists devices/partitions
- `set` - [ ] Shows variables (check for `prefix`, `root`, etc.)
- `cat ($root)/boot/grub/grub.cfg` - [ ] Shows config file

**Action**: Type `exit`

**Expected**:
- [ ] Returns to main menu

**Notes**: _____________________________________

## System Controls Tests

### Test 14: Reboot
**Action**: Select "🔄 Reboot System"

**Expected**:
- [ ] Shows message: "Rebooting..."
- [ ] System reboots

**Notes**: _____________________________________

---

### Test 15: Power Off
**Action**: Select "⏻  Power Off"

**Expected**:
- [ ] Shows message: "Shutting down..."
- [ ] System powers off (or halts if power-off not supported)

**Notes**: _____________________________________

## Configuration File Tests

### Test 16: Inspect Generated Config
**Action**: Mount USB, open `/boot/grub/grub.cfg`

**Expected Structure**:
- [ ] Header with version: "GRUB Configuration for LUXusb v0.6.3"
- [ ] Date stamp
- [ ] ISO count in comment
- [ ] Section markers: `# ═══ MODULE LOADING ═══`, etc.
- [ ] Clear sections:
  - [ ] Module Loading
  - [ ] Graphics Setup
  - [ ] Menu Appearance
  - [ ] Menu Behavior
  - [ ] Storage Setup
  - [ ] Help & Information
  - [ ] Bootable ISOs
  - [ ] System Controls

**Code Quality**:
- [ ] Comments explain each section
- [ ] Critical warnings present (e.g., font path importance)
- [ ] Organized and readable
- [ ] No obvious syntax errors

**Font Loading Section**:
- [ ] Has `load_video`
- [ ] Has `loadfont $prefix/fonts/unicode.pf2` (with path!)
- [ ] Has fallback: `else terminal_output console`
- [ ] Has warning echo if font fails

**Notes**: _____________________________________

---

### Test 17: Version Consistency
**Action**: Check version in multiple places

**Expected**: ALL should show "0.6.3"
- [ ] Python: `python3 -c "from luxusb._version import __version__; print(__version__)"`
- [ ] Config file header: `# GRUB Configuration for LUXusb v0.6.3`
- [ ] Help screen: `║  Version 0.6.3  ║`
- [ ] CHANGELOG.md: `## [0.6.3]`

**Notes**: _____________________________________

## Edge Cases & Stress Tests

### Test 18: Many ISOs
**Setup**: Create USB with 10+ ISOs (or max available)

**Expected**:
- [ ] Main menu scrolls properly
- [ ] First 26 ISOs get hotkeys [A-Z]
- [ ] Remaining ISOs accessible via arrows (no hotkey)
- [ ] ISO count correct in help screen
- [ ] All submenus work

**Notes**: _____________________________________

---

### Test 19: Long ISO Names
**Setup**: Rename ISO with very long name (if possible)

**Expected**:
- [ ] Name displays (may truncate gracefully)
- [ ] Menu remains readable
- [ ] No text overflow or garbling

**Notes**: _____________________________________

---

### Test 20: Missing Metadata
**Setup**: Edit distro JSON, remove description field

**Expected**:
- [ ] Falls back to "Linux Distribution" or similar
- [ ] No crash or blank line
- [ ] Other metadata still displays

**Notes**: _____________________________________

---

### Test 21: No ISOs
**Setup**: Create USB but add no ISOs (if possible, or delete all ISOs after creation)

**Expected**:
- [ ] Menu shows "No ISOs Found" or similar
- [ ] Help and system controls still available
- [ ] No crash or hang

**Notes**: _____________________________________

## Visual Regression Tests

### Test 22: Different Display Modes
**Test on**: BIOS boot, UEFI boot, different resolutions

**Expected**:
- [ ] Menu visible in all modes
- [ ] Box-drawing acceptable in all modes
- [ ] Colors reasonable
- [ ] Text readable

**Notes**: _____________________________________

---

### Test 23: Non-Unicode Terminal
**Setup**: Boot in console mode or force text terminal

**Expected**:
- [ ] Box-drawing may show as ASCII (`+---+` instead of `╔═══╗`)
- [ ] Emoji may show as `?` or boxes
- [ ] Text labels still readable
- [ ] Menu still functional

**Notes**: _____________________________________

## Bug Hunting

### Test 24: Known Issues from v0.6.2
**Previous issue**: Invisible menu (black screen)

**Expected in v0.6.3**:
- [ ] Menu VISIBLE
- [ ] Font loads successfully
- [ ] No black screen
- [ ] If font fails, falls back to console mode cleanly

**Notes**: _____________________________________

---

### Test 25: Look for New Issues
**Watch for**:
- [ ] Any crashes or hangs
- [ ] Garbled text
- [ ] Missing options
- [ ] Non-functional hotkeys
- [ ] Incorrect ISO counts
- [ ] Wrong version displayed
- [ ] Config syntax errors

**Notes**: _____________________________________

## Final Assessment

### Overall Quality
- **Visual Appeal**: ☐ Excellent  ☐ Good  ☐ Acceptable  ☐ Poor
- **Usability**: ☐ Excellent  ☐ Good  ☐ Acceptable  ☐ Poor
- **Information Clarity**: ☐ Excellent  ☐ Good  ☐ Acceptable  ☐ Poor
- **Functionality**: ☐ All works  ☐ Minor issues  ☐ Major issues
- **Boot Success Rate**: ___ / ___ ISOs booted successfully

### Feedback

**What works well**:
_____________________________________
_____________________________________
_____________________________________

**What needs improvement**:
_____________________________________
_____________________________________
_____________________________________

**Bugs found**:
_____________________________________
_____________________________________
_____________________________________

**Suggestions**:
_____________________________________
_____________________________________
_____________________________________

### Test Result
☐ **PASS** - Ready for release  
☐ **CONDITIONAL PASS** - Minor issues, release with notes  
☐ **FAIL** - Critical issues, needs fixes  

**Tester Signature**: _______________
**Date**: _______________

---

## Quick Test (Minimal)

If time is limited, run this abbreviated test:

1. [ ] **Boot** - Menu visible, no black screen
2. [ ] **Help** - View help screen, press ESC returns
3. [ ] **Hotkey** - Press 'A' jumps to first ISO
4. [ ] **Submenu** - See descriptions and options
5. [ ] **Normal Boot** - One ISO boots successfully
6. [ ] **Safe Mode** - One ISO boots in safe graphics
7. [ ] **Return** - ESC returns from submenu
8. [ ] **Version** - Check help screen shows "0.6.3"

**Result**: ☐ Pass  ☐ Fail  

**Notes**: _____________________________________

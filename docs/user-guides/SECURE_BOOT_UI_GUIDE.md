# Secure Boot Feature - Quick Visual Guide

## UI Flow

```
┌────────────────────────────────────────────────────────────┐
│  LUXusb                                    [🌙] [SB Toggle] │  ← Toolbar
├────────────────────────────────────────────────────────────┤
│                                                              │
│  SELECT USB → SELECT DISTRO → PROGRESS → DONE              │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

## Secure Boot Toggle States

### OFF (Default)
```
Toolbar: [Secure Boot: ○]  ← Toggle is OFF

Distro List:
  ☑ Ubuntu 24.04           ← Selectable
  ☑ Arch Linux 2026.01.01  ← Selectable  
  ☑ Fedora 41              ← Selectable
  ☑ CachyOS Desktop        ← Selectable
  
All distros available for selection
```

### ON (Secure Boot Enabled)
```
Toolbar: [Secure Boot: ●]  ← Toggle is ON

Distro List:
  ☑ Ubuntu 24.04                                    ← Selectable (compatible)
  ☐ Arch Linux [❌ Incompatible with Secure Boot]  ← GREYED OUT (incompatible)
  ☑ Fedora 41                                       ← Selectable (compatible)
  ☐ CachyOS Desktop [❌ Incompatible]               ← GREYED OUT (incompatible)
  
Only compatible distros can be selected
```

## Device Information Display

### Device Selection Page
```
┌──────────────────────────────────────────────────────┐
│  Select USB Device                                   │
│                                                       │
│  ┌────────────────────────────────────────────────┐  │
│  │ [✓ LUXusb Icon]  Kingston DataTraveler         │  │
│  │                  32.0 GB • Mounted              │  │
│  │                  4 ISO(s) installed             │  │
│  │                  🔒 Secure Boot Enabled  ← NEW  │  │
│  │                                          [✓ Configured] │
│  └────────────────────────────────────────────────┘  │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### Distro Selection Page - USB Info Panel
```
┌──────────────────────────────────────────┐
│  💾 USB Storage                          │
│  Total: 32.0 GB                          │
│  Available: 26.5 GB                      │
│  Required: 12.3 GB                       │
│  [████████░░░░░░] 46% of available      │
├──────────────────────────────────────────┤
│  📀 ISOs Already on USB                  │
│  4 ISOs installed:                       │
│  • ubuntu-24.04.3.iso                    │
│  • fedora-41.iso                         │
│  • linuxmint-22.iso                      │
│  • popos-22.04.iso                       │
│                                           │
│  🔒 Secure Boot: Enabled  ← NEW          │
└──────────────────────────────────────────┘
```

## Incompatible Distro Row (Greyed Out)

### Normal State (Secure Boot OFF)
```
┌────────────────────────────────────────────────────────┐
│ ☑ [Arch Icon]  Arch Linux                             │
│                A lightweight and flexible Linux...     │
│                Latest: 2026.01.01 • 1.4 GB            │
└────────────────────────────────────────────────────────┘
```

### Incompatible State (Secure Boot ON)
```
┌────────────────────────────────────────────────────────┐
│ ☐ [Arch Icon]  Arch Linux [❌ Incompatible with SB]   │  ← Red error icon
│                A lightweight and flexible Linux...     │  ← 40% opacity (grey)
│                Latest: 2026.01.01 • 1.4 GB            │
│                [Checkbox and row are disabled]         │
└────────────────────────────────────────────────────────┘
```

## Compatibility Matrix (At a Glance)

| Distribution       | Secure Boot | Family  | Reason                    |
|-------------------|-------------|---------|---------------------------|
| Ubuntu            | ✅ YES      | Debian  | Official signed shim      |
| Fedora            | ✅ YES      | Fedora  | Red Hat signed shim       |
| Pop!_OS           | ✅ YES      | Debian  | Ubuntu-based (signed)     |
| Linux Mint        | ✅ YES      | Debian  | Ubuntu-based (signed)     |
| Debian            | ✅ YES      | Debian  | Official signed shim      |
| Kali Linux        | ✅ YES      | Debian  | Debian-based (signed)     |
| Parrot Security   | ✅ YES      | Debian  | Debian-based (signed)     |
| openSUSE          | ✅ YES      | Indep.  | SUSE signed shim          |
| Arch Linux        | ❌ NO       | Arch    | Unsigned kernel           |
| Manjaro           | ❌ NO       | Arch    | Arch-based (unsigned)     |
| CachyOS Desktop   | ❌ NO       | Arch    | Arch-based (unsigned)     |
| CachyOS Handheld  | ❌ NO       | Arch    | Arch-based (unsigned)     |

## User Interaction Flow

### Scenario: User Wants Arch + Ubuntu

1. **Initial State**: Secure Boot toggle OFF
   - User sees: All distros selectable
   - User selects: ☑ Arch Linux, ☑ Ubuntu

2. **User Enables Secure Boot**
   - User toggles: Secure Boot ON
   - **Immediate effect**: Distro list refreshes
   - Arch Linux becomes greyed out
   - Red error badge appears: "❌ Incompatible with Secure Boot"
   - Arch automatically deselected (checkbox unchecked)
   - Ubuntu remains selected (compatible)

3. **User Proceeds**
   - User clicks "Continue with 1 Distro"
   - Only Ubuntu is included in USB creation
   - USB metadata saves: `secure_boot_enabled: true`

4. **Later: User Views USB**
   - Device page shows: "🔒 Secure Boot Enabled"
   - Distro page USB info shows: "🔒 Secure Boot: Enabled"
   - User knows this USB works with Secure Boot

### Scenario: User Wants All Distros (Including Arch)

1. **Decision Point**: User needs Arch (incompatible)
2. **Solution**: Toggle Secure Boot OFF
3. **Result**: 
   - All distros become selectable (including Arch)
   - USB created with `secure_boot_enabled: false`
   - User must disable Secure Boot in BIOS to boot this USB

## Key Benefits

✅ **No Surprises**: Users see incompatibility before creation  
✅ **Informed Choice**: Clear visual feedback on what works  
✅ **Educational**: Users learn which distros support Secure Boot  
✅ **Flexible**: Toggle allows choosing compatibility vs. choice  
✅ **Trackable**: USB metadata shows how it was created  
✅ **Persistent**: Information available for future append operations  

## Technical Notes

- **Real-time Updates**: Toggle changes refresh the distro list immediately
- **Opacity**: Incompatible distros shown at 40% opacity (grey)
- **Disabled Interaction**: Checkbox and row activation disabled for incompatible distros
- **Metadata Storage**: `.luxusb-config` file on USB tracks `secure_boot_enabled` flag
- **Future-proof**: MOK enrollment can enable Arch distros in v0.3.0 (see SECURE_BOOT_IMPLEMENTATION_PLAN.md)

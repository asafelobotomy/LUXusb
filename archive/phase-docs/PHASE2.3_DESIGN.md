# Phase 2.3: Multiple ISO Support - Design Document

## Overview

Phase 2.3 adds support for installing multiple Linux distributions on a single USB drive, creating a multi-boot environment with a GRUB menu.

## User Experience

### Current (Single ISO)
1. User selects one USB device
2. User selects one distribution
3. System creates bootable USB with that distribution

### New (Multiple ISOs)
1. User selects one USB device
2. User selects **multiple distributions** (checkboxes)
3. System downloads all ISOs
4. System creates bootable USB with GRUB multi-boot menu
5. User boots USB and selects which distro to boot

## Technical Design

### Data Structures

**New: DistroSelection**
```python
@dataclass
class DistroSelection:
    """Represents a user-selected distribution for installation"""
    distro: Distro
    release: DistroRelease
    priority: int = 0  # Boot menu order (0 = default)
```

**Updated: LUXusbWorkflow**
```python
class LUXusbWorkflow:
    def __init__(
        self,
        device: USBDevice,
        selections: List[DistroSelection],  # Changed from single distro
        progress_callback: Optional[Callable] = None
    ):
        ...
```

### UI Changes

**distro_page.py**
- Change from `Gtk.CheckButton` (radio) to `Gtk.CheckButton` (checkbox)
- Add "Select Multiple" mode toggle
- Show selected count: "3 distributions selected"
- Add "Set as Default" button for boot order

**device_page.py**
- Add size validation: Check if USB has enough space for all ISOs
- Show required vs available space

**progress_page.py**
- Show per-ISO progress: "Downloading Ubuntu (1/3)..."
- Aggregate progress across all ISOs

### Workflow Changes

**Stage Breakdown for Multiple ISOs**

Current single-ISO stages:
1. Partition (0-20%)
2. Mount (20-25%)
3. Install GRUB (25-35%)
4. Download ISO (35-85%)
5. Configure GRUB (85-95%)
6. Cleanup (95-100%)

New multi-ISO stages:
1. Partition (0-15%)
2. Mount (15-20%)
3. Install GRUB (20-25%)
4. **Download ISOs** (25-85%) - divided equally among ISOs
   - For 3 ISOs: ISO1 (25-45%), ISO2 (45-65%), ISO3 (65-85%)
5. Configure GRUB multi-boot (85-95%)
6. Cleanup (95-100%)

**Download Strategy**
- Sequential downloads (simple, reliable)
- Show which ISO is downloading: "Downloading Fedora (2/3)"
- Use resume/mirror features for each ISO
- Validate checksums for each ISO

### Storage Layout

**Partition Structure** (unchanged)
- EFI Partition (FAT32, 1GB): `/boot/efi/`
- Data Partition (ext4, remaining): `/data/`

**File Structure** (enhanced)
```
/boot/efi/
  └── EFI/
      └── BOOT/
          ├── BOOTX64.EFI
          └── grub.cfg

/data/
  └── isos/
      ├── ubuntu/
      │   └── ubuntu-24.04.iso
      ├── fedora/
      │   └── fedora-41.iso
      └── debian/
          └── debian-12.iso
```

### GRUB Configuration

**Multi-Boot Menu Example**
```grub
# /boot/efi/EFI/BOOT/grub.cfg

set timeout=10
set default=0

menuentry "Ubuntu 24.04 LTS" {
    set isofile="/isos/ubuntu/ubuntu-24.04.iso"
    loopback loop $isofile
    linux (loop)/casper/vmlinuz boot=casper iso-scan/filename=$isofile quiet splash
    initrd (loop)/casper/initrd
}

menuentry "Fedora Workstation 41" {
    set isofile="/isos/fedora/fedora-41.iso"
    loopback loop $isofile
    linux (loop)/isolinux/vmlinuz root=live:CDLABEL=Fedora-WS-Live-41 iso-scan/filename=$isofile
    initrd (loop)/isolinux/initrd.img
}

menuentry "Debian 12" {
    set isofile="/isos/debian/debian-12.iso"
    loopback loop $isofile
    linux (loop)/live/vmlinuz boot=live components quiet splash findiso=$isofile
    initrd (loop)/live/initrd.img
}
```

### Size Validation

**Calculate Required Space**
```python
def calculate_required_space(selections: List[DistroSelection]) -> int:
    """Calculate total space needed for all ISOs"""
    efi_size = 1024 * 1024 * 1024  # 1GB
    iso_total = sum(s.release.size_mb * 1024 * 1024 for s in selections)
    overhead = 512 * 1024 * 1024  # 512MB overhead for filesystem
    return efi_size + iso_total + overhead
```

**Validation Flow**
1. User selects distributions
2. System calculates total size needed
3. If USB too small, show error: "Need 12.5 GB, only 8.0 GB available"
4. User can deselect some distros or choose smaller USB

### Error Handling

**Partial Failure Scenarios**
- ISO 1 downloads ✅, ISO 2 fails ❌, ISO 3 not started
- Options:
  1. **Retry Failed**: Retry only ISO 2
  2. **Continue Anyway**: Install only successful ISOs
  3. **Abort All**: Remove all ISOs and cleanup

**Implementation**
```python
class MultiISOResult:
    successful: List[DistroSelection]
    failed: List[Tuple[DistroSelection, Exception]]
    
    @property
    def all_succeeded(self) -> bool:
        return len(self.failed) == 0
```

## Implementation Plan

### Phase 2.3.1: Data Structures
- Create `DistroSelection` dataclass
- Update `LUXusbWorkflow.__init__()` signature
- Add size calculation utilities

### Phase 2.3.2: UI Multi-Selection
- Update `distro_page.py` for checkbox mode
- Add selected counter and default boot option
- Update `device_page.py` for size validation

### Phase 2.3.3: Workflow Multi-ISO
- Update `_download_iso()` to handle multiple ISOs
- Add per-ISO progress tracking
- Update stage percentage ranges

### Phase 2.3.4: GRUB Multi-Boot
- Update `grub_installer.py` to generate multi-boot menu
- Add per-distro boot parameters
- Set default boot entry

### Phase 2.3.5: Testing
- Unit tests for size calculation
- Integration tests for multi-ISO workflow
- Mock downloads for testing

## Configuration

New settings:
```yaml
multi_iso:
  max_isos: 10  # Maximum number of ISOs per USB
  default_boot_timeout: 10  # GRUB menu timeout (seconds)
  sequential_downloads: true  # Download one at a time
  abort_on_failure: false  # Continue with successful ISOs
```

## Backward Compatibility

**Single ISO Mode** (default)
- If user selects one distro: works exactly as before
- No UI changes for single-selection users
- Workflow detects `len(selections) == 1`

**Multi ISO Mode**
- Enabled when user selects 2+ distros
- Shows multi-selection UI
- Uses enhanced workflow

## Future Enhancements

- **Parallel Downloads**: Download multiple ISOs simultaneously
- **Persistence**: Create persistent storage for live USBs
- **Custom Boot Order**: Drag-and-drop reordering in UI
- **ISO Updates**: Update individual ISOs without reformatting
- **Space Optimization**: Compress ISOs or share common files

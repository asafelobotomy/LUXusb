# LUXusb Architecture

## Overview

LUXusb follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    GUI Layer (GTK4)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Device   │  │ Distro   │  │ Progress │  │ Dialogs │ │
│  │ Page     │  │ Page     │  │ Page     │  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Core Layer                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Workflow Orchestrator                    │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Utils Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   USB    │  │  Distro  │  │Download  │  │  GRUB   │ │
│  │ Detector │  │ Manager  │  │  Manager │  │Installer│ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │Partition │  │  Config  │  │ Custom   │  │ Secure  │ │
│  │ Manager  │  │  Manager │  │   ISO    │  │  Boot   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              System Layer (Linux)                        │
│    lsblk, parted, mkfs, mount, grub-install, wget       │
└─────────────────────────────────────────────────────────┘
```

## Components

### GUI Layer (`luxusb/gui/`)

**Purpose**: User interface and interaction

**Components**:
- `main_window.py`: Application window and navigation
- `device_page.py`: USB device selection
- `distro_page.py`: Distribution selection
- `progress_page.py`: Installation progress display

**Technologies**: GTK4, Libadwaita

### Core Layer (`luxusb/core/`)

**Purpose**: Business logic and workflow orchestration

**Components**:
- `workflow.py`: Main workflow orchestrator
- Coordinates all operations in correct sequence
- Handles error recovery
- Provides progress callbacks

### Utils Layer (`luxusb/utils/`)

**Purpose**: Specialized utilities for specific tasks

**Components**:

1. **USB Detector** (`usb_detector.py`)
   - Scans for USB devices
   - Validates devices
   - Protects system disks

2. **Distro Manager** (`distro_manager.py`)
   - Maintains distribution metadata
   - Provides release information
   - Handles search and filtering

3. **Partitioner** (`partitioner.py`)
   - Creates GPT partition table
   - Formats partitions (FAT32, ext4)
   - Mounts/unmounts filesystems

4. **Downloader** (`downloader.py`)
   - Downloads ISOs with resume support
   - Verifies checksums
   - Reports progress

5. **GRUB Installer** (`grub_installer.py`)
   - Installs GRUB bootloader
   - Generates boot configuration
   - Creates ISO boot entries
   - Supports custom ISO boot entries

6. **Config Manager** (`config.py`)
   - Manages user preferences
   - Stores application settings
   - Provides default configuration

7. **Custom ISO** (`custom_iso.py`)
   - Validates custom ISO files
   - Checks ISO 9660 format
   - Detects bootable status
   - Enforces size constraints

8. **Secure Boot** (`secure_boot.py`)
   - Detects Secure Boot status
   - Signs bootloader with MOK keys
   - Generates signing keys
   - Installs shim bootloader

## Data Flow

### Device Selection Flow

```
User → Device Page → USB Detector → lsblk
                                     ↓
        Display ← USB Devices ← Parse Output
```

### Installation Flow

```
User Selection
    ↓
Workflow Orchestrator
    ↓
┌───────────────────────────┐
│ 1. Partition USB          │ → parted, mkfs
│ 2. Mount Partitions       │ → mount
│ 3. Install GRUB           │ → grub-install
│ 4. Download ISO           │ → wget/requests
│ 5. Verify Checksum        │ → sha256sum
│ 6. Configure GRUB         │ → grub.cfg
│ 7. Unmount                │ → umount
└───────────────────────────┘
    ↓
Bootable USB
```

## Error Handling

### Strategy

1. **Validation First**: Check requirements before operations
2. **Graceful Degradation**: Fallback methods for failures
3. **Atomic Operations**: Rollback on failure
4. **Clear Error Messages**: User-friendly error reporting

### Error Recovery

```python
try:
    # Attempt operation
    operation()
except SpecificError:
    # Try fallback method
    fallback_operation()
except Exception:
    # Cleanup and report
    cleanup()
    report_error()
```

## Security Considerations

### Privilege Escalation

- Uses `pkexec` for GUI privilege requests
- Minimal privilege scope
- Clear justification for root access

### ISO Verification

- SHA256 checksum verification
- Download from official sources only
- Warning on checksum mismatch

### System Protection

- Prevents formatting system disks
- Checks for critical mount points
- Confirmation dialogs for destructive operations

## Performance

### Optimization Strategies

1. **Parallel Operations**: Where safe and beneficial
2. **Streaming Downloads**: No memory buffering of large files
3. **Progress Reporting**: Real-time updates without blocking
4. **Background Processing**: Threading for long operations

### Resource Usage

- Memory: ~50-100 MB
- Disk: 2-5 GB (ISO downloads)
- Network: Bandwidth-limited downloads

## Testing Strategy

### Unit Tests

- Individual module testing
- Mocked external dependencies
- Fast, isolated tests

### Integration Tests

- Multi-component interaction
- Real system operations (careful!)
- USB device mocking

### Manual Testing

- Real hardware testing
- Different Linux distributions
- Edge case scenarios

## Future Architecture

### Planned Improvements

1. **Plugin System**: For custom distributions
2. **Mirror Management**: Smart mirror selection
3. **Caching Layer**: Local ISO cache
4. **Update System**: Auto-update distribution metadata
5. **Multi-ISO Support**: Multiple bootable ISOs

### Scalability

- Modular design supports feature additions
- Clear interfaces between components
- Plugin-friendly architecture
- Extensible metadata system

## Dependencies

### Required

- Python 3.10+
- GTK4, Libadwaita
- System tools: lsblk, parted, mkfs, grub-install

### Optional

- Torrent client (future)
- Additional bootloaders (future)

## Build System

### AppImage Build

1. Create AppDir structure
2. Install dependencies
3. Package Python application
4. Generate launcher scripts
5. Build AppImage with appimagetool

### Distribution

- Single AppImage file
- Self-contained
- No installation required
- Works across distributions

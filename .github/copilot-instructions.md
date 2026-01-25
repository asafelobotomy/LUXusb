# LUXusb - AI Coding Instructions

## Project Overview

LUXusb is a GTK4-based Linux application for creating bootable USB drives with multiple Linux distributions. It uses a three-layer architecture: **GUI Layer** (GTK4/Libadwaita) → **Core Layer** (workflow orchestration) → **Utils Layer** (specialized operations).

## Architecture & Key Patterns

### Three-Layer Architecture
- **GUI Layer** (`luxusb/gui/`): GTK4 widgets, navigation, user interaction
- **Core Layer** (`luxusb/core/`): `LUXusbWorkflow` orchestrates multi-stage operations (partition → mount → install GRUB → download ISO → configure → cleanup)
- **Utils Layer** (`luxusb/utils/`): Isolated utility modules for USB detection, partitioning, downloading, GRUB installation

**Critical Pattern**: Utils are self-contained. Each utility module (e.g., `USBDetector`, `USBPartitioner`) handles one responsibility and uses subprocess calls to Linux system tools (`lsblk`, `parted`, `mkfs`, `grub-install`).

### Workflow Orchestration
The `LUXusbWorkflow` class (`core/workflow.py`) is the brain of operations:
- Sequential stages with progress tracking (0-100%)
- Each stage has discrete progress range (e.g., partition: 0-20%, download: 35-85%)
- Progress callbacks update GUI in real-time via `WorkflowProgress` dataclass
- Cleanup guaranteed via try/except/finally pattern

**Example**: When adding new installation steps, update stage progress ranges and insert into `execute()` method.

### Dataclass-Based Models
All data structures use `@dataclass` with typed properties:
- `USBDevice`: Device metadata (path, size, vendor, mount status)
- `Distro` & `DistroRelease`: Distribution metadata and download URLs
- `WorkflowProgress`: Stage tracking for UI updates

**Convention**: Use `@property` methods for computed fields (e.g., `USBDevice.size_gb`, `USBDevice.display_name`).

## Development Workflows

### Running & Testing
```bash
# Development run (limited privileges)
python3 -m luxusb
# Or: ./scripts/run-dev.sh

# With root for USB operations
sudo python3 -m luxusb

# Unit tests (safe)
pytest

# USB detection test (safe)
python3 -c "from luxusb.utils.usb_detector import get_usb_devices; print(get_usb_devices())"

# GTK debugging
GTK_DEBUG=interactive python3 -m luxusb
```

### Building AppImage
```bash
./scripts/build-appimage.sh  # Creates LUXusb-0.1.0-x86_64.AppImage
```

⚠️ **USB Testing**: Use test devices or loop devices (`losetup`) only. USB operations are destructive!

## Project-Specific Conventions

### System Command Execution
All system operations use `subprocess.run()` with proper error handling:
```python
result = subprocess.run(
    ['lsblk', '-J', '-o', 'NAME,SIZE,...'],
    capture_output=True,
    text=True,
    check=True
)
```
**Pattern**: Parse JSON output when available (`lsblk -J`), fall back to regex parsing for plain text.

### GTK4 Patterns
- Use `Adw.Application` and `Adw.ApplicationWindow` for GNOME HIG compliance
- Navigation via `Adw.NavigationView` with page pushing/popping
- Dialogs use `Adw.MessageDialog` with destructive action appearance for confirmations
- Always require GObject imports: `gi.require_version('Gtk', '4.0')` before imports

### Configuration Management
- Config stored in XDG directories (`~/.config/luxusb`, `~/.cache/luxusb`)
- YAML-based configuration via `config.py` with dot-notation access: `config.get('download.verify_checksums')`
- Default config in `_default_config()` method

### Safety & Validation
- **System disk protection**: `USBDetector` filters out non-USB devices
- **Confirmation dialogs**: Required before destructive operations
- **Checksum verification**: SHA256 validation for downloaded ISOs
- **Mount point management**: Cleanup in try/finally blocks

## Key Files to Reference

- [`luxusb/core/workflow.py`](luxusb/core/workflow.py): Main orchestration logic and stage sequencing
- [`luxusb/utils/usb_detector.py`](luxusb/utils/usb_detector.py): USB detection and lsblk parsing patterns
- [`luxusb/gui/main_window.py`](luxusb/gui/main_window.py): GTK4 application structure and navigation
- [`pyproject.toml`](pyproject.toml): Dependencies and project metadata
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Detailed component interactions

## Adding Features

### New Linux Distribution
1. Create JSON file in `luxusb/data/distros/` (e.g., `mydistro.json`)
2. Follow schema in `luxusb/data/distro-schema.json`
3. Include: id, name, description, homepage, logo_url, category, popularity_rank, releases
4. Each release needs: version, release_date, iso_url, sha256, size_mb, architecture, mirrors
5. No code changes needed - `DistroJSONLoader` auto-discovers `*.json` files
6. Test: `python3 -c "from luxusb.utils.distro_json_loader import DistroJSONLoader; loader = DistroJSONLoader(); print(loader.load_all())"`

### New Utility Module
1. Create in `utils/` with single responsibility
2. Use dataclasses for input/output
3. Subprocess calls for system operations
4. Add pytest tests to `tests/`

### New GUI Page
1. Subclass `Gtk.Box` or use `Adw` widgets
2. Integrate into `main_window.py` navigation
3. Connect to workflow via callbacks
4. Update progress via `WorkflowProgress` dataclass

## Dependencies & Requirements

- **Python**: 3.10+ (uses modern type hints and match/case)
- **GTK4 + Libadwaita**: UI framework
- **System tools**: `lsblk`, `parted`, `mkfs.fat`, `mkfs.ext4`, `grub-install`
- **Python packages**: See [`requirements.txt`](requirements.txt) - PyGObject, requests, psutil, pyudev

## Distribution Management

### Adding New Distributions

**JSON-Based Loading**: From Phase 2.3, distributions are now loaded from JSON files in [`luxusb/data/distros/`](luxusb/data/distros/):

```json
{
  "id": "distro-slug",
  "name": "Distribution Name",
  "description": "Brief description",
  "homepage": "https://example.com",
  "logo_url": "https://example.com/logo.png",
  "category": "Desktop",
  "popularity_rank": 10,
  "releases": [
    {
      "version": "1.0",
      "release_date": "2024-01-01",
      "iso_url": "https://mirror.example.com/distro.iso",
      "sha256": "actual_checksum_here",
      "size_mb": 3000,
      "architecture": "x86_64",
      "mirrors": ["https://mirror1.com/iso.iso", "https://mirror2.com/iso.iso"]
    }
  ]
}
```

**Workflow**:
1. Create new JSON file in `luxusb/data/distros/` (e.g., `mydistro.json`)
2. Validate against schema: `luxusb/data/distro-schema.json` (JSON Schema v7)
3. `DistroJSONLoader` auto-loads all `*.json` files on startup
4. No code changes required - purely data-driven

**Key Points**:
- SHA256 checksums are **mandatory** for integrity verification
- `mirrors` array enables automatic mirror selection and failover
- `popularity_rank` determines display order (lower = higher priority)
- Schema validation ensures data consistency across distros

### Mirror Selection & Resume Support ✅
**Implemented** in Phase 2.2 and 2.1. From [`utils/mirror_selector.py`](luxusb/utils/mirror_selector.py) and [`utils/downloader.py`](luxusb/utils/downloader.py):

```python
# MirrorSelector tests mirrors in parallel and ranks by speed
selector = MirrorSelector()
best_mirror = selector.select_best_mirror(mirror_list)

# ISODownloader supports automatic mirror selection and resume
downloader.download_with_mirrors(
    primary_url="https://ubuntu.com/iso.iso",
    mirrors=["https://mirror1.com/iso.iso", "..."],
    destination=Path("ubuntu.iso"),
    auto_select_best=True,  # Auto-select fastest mirror
    allow_resume=True       # Resume interrupted downloads
)
```

**Key Features**:
- Parallel mirror speed testing with ThreadPoolExecutor
- HTTP Range requests for resume support (.part files)
- Resume metadata tracking (.resume JSON files)
- SHA256 verification across resumed chunks
- Automatic mirror failover on connection errors

**Pattern**: `DistroRelease` includes `mirrors: List[str]` field populated from JSON files.

## Privilege Escalation Patterns

USB operations require root privileges. The application uses **pkexec** (PolicyKit) for secure privilege escalation:

### AppImage Launcher Pattern
From [`scripts/build-appimage.sh`](scripts/build-appimage.sh):
```bash
if [ "$EUID" -ne 0 ]; then
    if command -v pkexec &> /dev/null; then
        exec pkexec "$APPDIR/usr/venv/bin/python3" -m luxusb "$@"
    else
        echo "This application requires root privileges."
        echo "Please run with sudo or install polkit."
        exit 1
    fi
fi
```

### Design Philosophy
- **Lazy elevation**: Only request root when USB operation starts, not at launch
- **Transparent**: pkexec shows system authentication dialog (no custom password prompts)
- **Graceful fallback**: Detect missing pkexec, provide clear error message
- **Minimal scope**: Only subprocess commands run with elevated privileges

### Adding Privileged Operations
When adding new system operations:
1. Check if operation requires root (test without sudo first)
2. Document in docstring: `Requires root privileges`
3. Ensure cleanup runs even on permission errors
4. Test with both `sudo` and `pkexec` execution

## Error Handling & Recovery

### Three-Tier Error Strategy

**1. Validation First** (Prevent errors before operations):
```python
# In USBDetector: Filter system disks before showing to user
if device.get('tran') == 'usb' and device.get('type') == 'disk':
    # Only add USB devices
```

**2. Graceful Degradation** (Try-catch with cleanup):
```python
try:
    if not self._partition_usb():
        return False
    if not self._mount_partitions():
        return False
    # ... more stages
except Exception as e:
    logger.exception(f"Workflow failed: {e}")
    self._cleanup()  # Always cleanup
    return False
```

**3. User-Friendly Errors** (Clear messages via dialogs):
```python
def show_error_dialog(self, title: str, message: str):
    dialog = Adw.MessageDialog.new(self, title, message)
    dialog.add_response("ok", "OK")
    dialog.present()
```

### Stage-Based Recovery
From [`core/workflow.py`](luxusb/core/workflow.py):
- Each stage returns bool for success/failure
- Failed stage stops execution immediately
- Cleanup **always** runs in finally block:
  ```python
  finally:
      self._cleanup()  # Unmount partitions
  ```

### Subprocess Error Pattern
All system commands use consistent error handling:
```python
try:
    result = subprocess.run(
        ['command', 'args'],
        capture_output=True,
        text=True,
        check=True  # Raises CalledProcessError on non-zero exit
    )
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {e.stderr}")
    return False
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    return False
```

### Download Error Recovery
From [`utils/downloader.py`](luxusb/utils/downloader.py):
- Checksum mismatch → delete partial file automatically
- Network error → automatic mirror failover (if mirrors provided)
- Timeout → configurable via `config.get('download.timeout')`
- Resume support → `.part` and `.resume` files track partial downloads
- Pause/resume → Thread-safe pause_event (Event) for user control

## Testing Strategy

### Safe Testing Without USB Devices

**1. Mock-Based Unit Tests** ([`tests/test_usb_detector.py`](tests/test_usb_detector.py)):
```python
@patch('subprocess.run')
def test_scan_devices_success(self, mock_run):
    mock_run.return_value = Mock(
        stdout='{"blockdevices": [...]}'
    )
    detector = USBDetector()
    devices = detector.scan_devices()
    assert len(devices) == 1
```

**2. Loop Device Testing** (safe, non-destructive):
```bash
# Create virtual USB for testing
dd if=/dev/zero of=/tmp/test-usb.img bs=1M count=8192
sudo losetup -f /tmp/test-usb.img  # Returns /dev/loop0

# Now test with /dev/loop0 as device
python3 -c "
from luxusb.utils.partitioner import USBPartitioner
from luxusb.utils.usb_detector import USBDevice

device = USBDevice(
    device='/dev/loop0',
    size_bytes=8589934592,
    model='Test Loop Device',
    vendor='Loop',
    serial='TEST',
    partitions=[],
    is_mounted=False,
    mount_points=[]
)
partitioner = USBPartitioner(device)
# Test partitioning
"

# Cleanup
sudo losetup -d /dev/loop0
rm /tmp/test-usb.img
```

**3. Detection-Only Testing** (completely safe):
```bash
# Test USB detection without any writes
python3 -c "
from luxusb.utils.usb_detector import USBDetector
detector = USBDetector()
devices = detector.scan_devices()
for dev in devices:
    print(f'{dev.display_name}')
"
```

### Test Coverage Guidelines
- **Utils layer**: High coverage with mocks (80%+ target)
- **Core workflow**: Integration tests with loop devices
- **GUI layer**: Manual testing (GTK4 widget testing complex)
- **System commands**: Mock `subprocess.run()` to avoid real execution

### GTK4 Debugging
```bash
# Interactive inspector
GTK_DEBUG=interactive python3 -m luxusb

# Show all warnings
G_ENABLE_DIAGNOSTIC=1 python3 -m luxusb

# Trace signal connections
GTK_DEBUG=actions python3 -m luxusb
```

## Common Pitfalls

- Don't run USB operations without root privileges (use `sudo` or `pkexec`)
- Always cleanup mount points in finally blocks to prevent orphaned mounts
- GTK4 must run in main thread; use `GLib.idle_add()` for background thread updates
- Test JSON parsing with mock data before testing with real devices
- `lsblk` output format can vary by kernel version; include fallback parsing
- Never hardcode checksums as "placeholder" - always use real SHA256 values
- Delete partial downloads on error to prevent corrupted ISO usage
- Test with loop devices before testing with real USB drives

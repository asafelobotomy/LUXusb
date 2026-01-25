# Constants Library Quick Reference

## Import Patterns

```python
# Configuration keys
from luxusb.constants import ConfigKeys

# File paths
from luxusb.constants import PathPattern

# Distro families
from luxusb.constants import DistroFamily

# Time intervals
from luxusb.constants import Interval, Timeout

# Sizes
from luxusb.constants import Size

# UI elements
from luxusb.constants import StatusIcon, Theme

# All at once
from luxusb.constants import (
    ConfigKeys, PathPattern, DistroFamily, 
    Interval, Timeout, Size, StatusIcon
)
```

## Common Use Cases

### 1. Config Key Access
```python
# ❌ Old way
theme = config.get('ui.theme')
timeout = config.get('download.timeout')

# ✅ New way
theme = config.get(ConfigKeys.UI.THEME)
timeout = config.get(ConfigKeys.Download.TIMEOUT)
```

### 2. Path Construction
```python
# ❌ Old way
config_dir = Path.home() / ".config" / "luxusb"
cache_file = cache_dir / "mirror_stats.json"

# ✅ New way
config_dir = Path.home() / PathPattern.CONFIG_DIR
cache_file = cache_dir / PathPattern.MIRROR_STATS_FILE
```

### 3. Family Names
```python
# ❌ Old way
if family == "arch":
    name = "Arch-based Distributions"

# ✅ New way
if family == DistroFamily.ARCH.value:
    name = DistroFamily.ARCH.display_name
```

### 4. Time Intervals
```python
# ❌ Old way
GLib.timeout_add_seconds(6 * 3600, callback)
request = requests.get(url, timeout=30)

# ✅ New way
GLib.timeout_add_seconds(Interval.PERIODIC_UPDATE_CHECK, callback)
request = requests.get(url, timeout=Timeout.HTTP_REQUEST)
```

### 5. Size Constants
```python
# ❌ Old way
efi_size = 1024  # MB
min_usb = 8 * 1024 * 1024 * 1024  # bytes

# ✅ New way
efi_size = Size.EFI_PARTITION_MB
min_usb = Size.MIN_USB_SIZE_GB * Size.GB
```

## Available Constants

### ConfigKeys
```python
ConfigKeys.Download.TIMEOUT           # "download.timeout"
ConfigKeys.Download.VERIFY_CHECKSUMS  # "download.verify_checksums"
ConfigKeys.UI.THEME                   # "ui.theme"
ConfigKeys.Metadata.AUTO_UPDATE       # "metadata.auto_update_on_startup"
ConfigKeys.Metadata.UPDATE_FREQUENCY  # "metadata.update_frequency_days"
```

### PathPattern
```python
PathPattern.CONFIG_DIR          # ".config/luxusb"
PathPattern.CACHE_DIR           # ".cache/luxusb"
PathPattern.CONFIG_FILE         # "config.yaml"
PathPattern.UPDATE_MARKER_FILE  # "last_metadata_update.json"
```

### DistroFamily (Enum)
```python
DistroFamily.ARCH.value          # "arch"
DistroFamily.ARCH.display_name   # "Arch-based Distributions"
DistroFamily.DEBIAN.value        # "debian"
DistroFamily.FEDORA.value        # "fedora"
DistroFamily.INDEPENDENT.value   # "independent"
```

### Interval
```python
Interval.PERIODIC_UPDATE_CHECK  # 21600 (6 hours)
Interval.PROGRESS_UPDATE_MS     # 100 (milliseconds)
Interval.TOAST_TIMEOUT          # 5 (seconds)
```

### Timeout
```python
Timeout.HTTP_REQUEST      # 30 seconds
Timeout.MIRROR_TEST       # 10 seconds
Timeout.DOWNLOAD_DEFAULT  # 3600 seconds (1 hour)
Timeout.UPDATE_CHECK      # 30 seconds
```

### Size
```python
Size.KB                  # 1024 bytes
Size.MB                  # 1048576 bytes
Size.GB                  # 1073741824 bytes
Size.EFI_PARTITION_MB    # 1024 MB
Size.MIN_USB_SIZE_GB     # 8 GB
```

### StatusIcon
```python
StatusIcon.SUCCESS    # "✅"
StatusIcon.ERROR      # "❌"
StatusIcon.WARNING    # "⚠️"
StatusIcon.INFO       # "ℹ️"
StatusIcon.PENDING    # "🔄"
```

### Theme (Enum)
```python
Theme.DARK.value      # "dark"
Theme.LIGHT.value     # "light"
Theme.DEFAULT.value   # "default"
```

## IDE Autocomplete

When you type `ConfigKeys.`, your IDE will show:
- `Download` → `TIMEOUT`, `VERIFY_CHECKSUMS`, `MAX_RETRIES`, etc.
- `UI` → `THEME`, `SHOW_SPLASH`, etc.
- `Metadata` → `AUTO_UPDATE_ON_STARTUP`, `UPDATE_FREQUENCY_DAYS`, etc.

This prevents typos and makes discovery easy!

## Type Safety

```python
# Enum validation catches errors
try:
    family = DistroFamily("invalid")  # ❌ Raises ValueError
except ValueError:
    family = DistroFamily.INDEPENDENT  # ✅ Fallback

# Valid usage
family = DistroFamily.ARCH  # ✅ Type-safe
print(family.value)         # "arch"
print(family.display_name)  # "Arch-based Distributions"
```

## Refactoring Safety

When renaming constants, IDE refactoring tools work:

1. Right-click `ConfigKeys.UI.THEME`
2. Select "Rename Symbol"
3. All usages update automatically

This is **impossible** with string literals like `"ui.theme"`.

## Migration Checklist

When migrating a file:

- [ ] Add constant imports at top
- [ ] Replace hardcoded strings with constants
- [ ] Replace magic numbers with constants
- [ ] Test imports: `python3 -c "from luxusb.module import *"`
- [ ] Test functionality: Run application
- [ ] Verify no regressions: Check logs

## See Also

- **[luxusb/constants.py](../luxusb/constants.py)** - Full constant definitions
- **[docs/CONSTANTS_MIGRATION.md](CONSTANTS_MIGRATION.md)** - Migration report and examples
- **[.github/copilot-instructions.md](../.github/copilot-instructions.md)** - Development guidelines

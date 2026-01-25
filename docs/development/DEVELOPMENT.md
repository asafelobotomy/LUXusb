# Development Guide

## Setup Development Environment

### 1. Clone Repository

```bash
git clone https://github.com/solon/luxusb.git
cd luxusb
```

### 2. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y \
    python3-dev python3-venv python3-pip \
    libgirepository1.0-dev libcairo2-dev \
    gir1.2-gtk-4.0 gir1.2-adwaita-1 \
    parted grub-efi-amd64 grub-common \
    dosfstools e2fsprogs
```

**Fedora:**
```bash
sudo dnf install -y \
    python3-devel python3-pip \
    gtk4-devel gobject-introspection-devel cairo-devel \
    python3-gobject gtk4 libadwaita \
    parted grub2-efi-x64-modules grub2-tools-extra \
    dosfstools e2fsprogs
```

**Arch Linux:**
```bash
sudo pacman -S --needed \
    python python-pip \
    gtk4 libadwaita python-gobject \
    parted grub dosfstools e2fsprogs
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 4. Run Development Version

```bash
# Simple run (limited privileges)
python3 -m ventoy_maker

# Or use helper script
chmod +x scripts/run-dev.sh
./scripts/run-dev.sh

# With root privileges (for USB operations)
sudo python3 -m ventoy_maker
```

## Project Structure

```
luxusb/
├── luxusb/              # Main package
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point
│   ├── config.py             # Configuration management
│   ├── gui/                  # GTK4 GUI
│   │   ├── __init__.py
│   │   ├── main_window.py    # Main application window
│   │   ├── device_page.py    # USB device selection
│   │   ├── distro_page.py    # Distribution selection
│   │   └── progress_page.py  # Installation progress
│   └── utils/                # Utility modules
│       ├── __init__.py
│       ├── usb_detector.py   # USB device detection
│       ├── distro_manager.py # Distribution metadata
│       ├── partitioner.py    # USB partitioning
│       ├── downloader.py     # ISO downloads
│       └── grub_installer.py # GRUB bootloader
├── scripts/                   # Build and utility scripts
├── tests/                     # Test suite
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
└── README.md                 # Main documentation
```

## Testing

### USB Operations Testing

⚠️ **Warning**: USB operations are destructive. Use test USBs only!

```bash
# Test USB detection (safe)
python3 -c "
from luxusb.utils.usb_detector import get_usb_devices
devices = get_usb_devices()
for dev in devices:
    print(f'{dev.display_name}')
"

# Test with virtual USB (safe)
# Create a test image file
dd if=/dev/zero of=/tmp/test-usb.img bs=1M count=8192
sudo losetup /dev/loop0 /tmp/test-usb.img
# Now test with /dev/loop0
```

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=luxusb --cov-report=html

# Run specific test file
pytest tests/test_usb_detector.py
```

### GUI Development

```bash
# Run with GTK debugging
GTK_DEBUG=interactive python3 -m luxusb

# Check GTK warnings
G_ENABLE_DIAGNOSTIC=1 python3 -m luxusb
```

## Building

### Build AppImage

```bash
chmod +x scripts/build-appimage.sh
./scripts/build-appimage.sh
```

This creates `LUXusb-0.1.0-x86_64.AppImage`

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for all public functions

```bash
# Format code
black luxusb/

# Check style
flake8 luxusb/

# Type checking
mypy luxusb/
```

### Commit Messages

Format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Build/tooling

Example:
```
feat: add USB device detection

- Implement USBDetector class
- Add device validation
- Include system disk protection

Closes #123
```

## Common Tasks

### Adding a New Distribution

Edit `luxusb/utils/distro_manager.py`:

```python
Distro(
    id="newdistro",
    name="New Distro",
    description="Description",
    homepage="https://...",
    logo_url="https://...",
    category="Desktop",
    popularity_rank=N,
    releases=[
        DistroRelease(
            version="X.Y",
            release_date="YYYY-MM-DD",
            iso_url="https://...",
            sha256="checksum",
            size_mb=SIZE,
        ),
    ]
)
```

### Adding a New GUI Page

1. Create `luxusb/gui/my_page.py`:

```python
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class MyPage(Adw.NavigationPage):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.set_title("My Page")
        # ... page content
```

2. Add to `main_window.py`:

```python
from luxusb.gui.my_page import MyPage

# In MainWindow.__init__:
self.my_page = MyPage(self)
```

### Debugging

```bash
# Enable debug logging
export VENTOY_MAKER_DEBUG=1
python3 -m ventoy_maker

# View logs
tail -f ~/.local/share/ventoy-maker/logs/ventoy-maker.log
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure tests pass (`pytest`)
6. Format code (`black luxusb/`)
7. Commit your changes
8. Push to the branch
9. Open a Pull Request

## Troubleshooting

### GTK4 Not Found

```bash
# Ensure GTK4 is installed
pkg-config --modversion gtk4

# Install PyGObject
pip install PyGObject
```

### Permission Denied for USB Operations

USB operations require root. Use one of:

```bash
# Option 1: sudo
sudo python3 -m ventoy_maker

# Option 2: pkexec (GUI)
pkexec python3 -m ventoy_maker

# Option 3: Add user to disk group (not recommended)
sudo usermod -a -G disk $USER
# Logout and login
```

### GRUB Installation Fails

Ensure GRUB tools are installed:

```bash
# Ubuntu/Debian
sudo apt install grub-efi-amd64 grub-common

# Fedora
sudo dnf install grub2-efi-x64-modules grub2-tools-extra

# Arch
sudo pacman -S grub
```

## Resources

- [GTK4 Documentation](https://docs.gtk.org/gtk4/)
- [Libadwaita Documentation](https://gnome.pages.gitlab.gnome.org/libadwaita/)
- [PyGObject Documentation](https://pygobject.readthedocs.io/)
- [GRUB Manual](https://www.gnu.org/software/grub/manual/)
- [Ventoy Project](https://www.ventoy.net/)

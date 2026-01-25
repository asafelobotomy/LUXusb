#!/bin/bash
# Build AppImage for LUXusb

set -e  # Exit on error

echo "Building LUXusb AppImage..."

# Configuration
APP_NAME="LUXusb"
APP_DIR="$APP_NAME.AppDir"

# Get version from Python module
VERSION=$(python3 -c "import sys; sys.path.insert(0, 'luxusb'); from _version import __version__; print(__version__)")

# Clean previous build
echo "Cleaning previous build..."
rm -rf "$APP_DIR"
rm -f "$APP_NAME-$VERSION-x86_64.AppImage"

# Create AppDir structure
echo "Creating AppDir structure..."
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/lib"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"

# Install Python application
echo "Installing application..."
python3 -m venv "$APP_DIR/usr/venv"
source "$APP_DIR/usr/venv/bin/activate"
pip install --upgrade pip
pip install -e .
deactivate

# Create launcher script
echo "Creating launcher..."
cat > "$APP_DIR/usr/bin/luxusb-launcher" << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export PATH="$APPDIR/usr/bin:$PATH"
export PYTHONPATH="$APPDIR/usr/lib/python3/site-packages:$PYTHONPATH"

# Activate virtual environment
source "$APPDIR/usr/venv/bin/activate"

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    # Try to run with pkexec
    if command -v pkexec &> /dev/null; then
        exec pkexec "$APPDIR/usr/venv/bin/python3" -m luxusb "$@"
    else
        echo "This application requires root privileges."
        echo "Please run with sudo or install polkit."
        exit 1
    fi
fi

# Run application
exec "$APPDIR/usr/venv/bin/python3" -m luxusb "$@"
EOF

chmod +x "$APP_DIR/usr/bin/luxusb-launcher"

# Create desktop file
echo "Creating desktop file..."
cat > "$APP_DIR/usr/share/applications/luxusb.desktop" << EOF
[Desktop Entry]
Type=Application
Name=LUXusb
Comment=Create bootable USB drives with multiple Linux distributions
Exec=luxusb-launcher
Icon=luxusb
Categories=System;Utility;
Terminal=false
EOF

# Create AppRun
echo "Creating AppRun..."
cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
exec "$APPDIR/usr/bin/luxusb-launcher" "$@"
EOF

chmod +x "$APP_DIR/AppRun"

# Copy application icon
echo "Copying application icon..."
if [ -f "luxusb/data/icons/com.luxusb.LUXusb.png" ]; then
    cp "luxusb/data/icons/com.luxusb.LUXusb.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/"
    cp "luxusb/data/icons/com.luxusb.LUXusb.png" "$APP_DIR/luxusb.png"
    cp "luxusb/data/icons/com.luxusb.LUXusb.png" "$APP_DIR/.DirIcon"
    echo "✓ Application icon installed"
else
    echo "⚠ Icon not found at luxusb/data/icons/com.luxusb.LUXusb.png"
fi

# Copy desktop file to root
cp "$APP_DIR/usr/share/applications/luxusb.desktop" "$APP_DIR/"

# Download appimagetool if not present
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Build AppImage
echo "Building AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage "$APP_DIR" "$APP_NAME-$VERSION-x86_64.AppImage"

echo "✓ Build complete: $APP_NAME-$VERSION-x86_64.AppImage"
echo ""
echo "To run: ./$APP_NAME-$VERSION-x86_64.AppImage"

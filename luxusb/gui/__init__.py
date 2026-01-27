"""
GUI package initialization with consolidated GTK imports
"""

import sys
import gi

# Require specific versions before importing
try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, GLib, Gio, GdkPixbuf, Gdk
except (ImportError, ValueError) as exc:
    print(f'Error: GTK4/Libadwaita dependencies not met: {exc}', file=sys.stderr)
    sys.exit(1)

# Export for use in other modules
__all__ = ['Gtk', 'Adw', 'GLib', 'Gio', 'GdkPixbuf', 'Gdk']

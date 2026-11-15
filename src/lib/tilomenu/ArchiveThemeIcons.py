"""Connect archived theme renderer's icon lookup to GTK3 and bundled assets."""
import os
import gi
gi.require_version('Gtk','3.0')
gi.require_version('GdkPixbuf','2.0')
from gi.repository import Gtk, GdkPixbuf, GLib


def load_named_icon(name, size=16):
    theme = Gtk.IconTheme.get_default()
    for candidate in (name, os.path.splitext(name)[0], 'image-missing'):
        try:
            pixbuf = theme.load_icon(candidate, max(1, int(size)), Gtk.IconLookupFlags.FORCE_SIZE)
            return Gtk.Image.new_from_pixbuf(pixbuf)
        except (GLib.Error, TypeError, ValueError, AttributeError):
            pass
    return None

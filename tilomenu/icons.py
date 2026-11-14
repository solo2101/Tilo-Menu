"""Load icons through GTK's icon theme, skipping broken or absent assets."""

from pathlib import Path

from gi.repository import Gtk


def load_icon(icon, size=20):
    """Return a pixbuf-backed Gtk.Image, or None if an icon cannot be loaded."""
    if icon is None:
        return None
    theme = Gtk.IconTheme.get_default()
    if theme is None:
        return None
    try:
        info = theme.lookup_by_gicon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE)
        if info is None:
            return None
        filename = info.get_filename()
        if filename and not Path(filename).is_file():
            return None
        pixbuf = info.load_icon()
        return Gtk.Image.new_from_pixbuf(pixbuf) if pixbuf else None
    except (Exception):
        # A missing icon should never prevent an application from appearing.
        return None


def load_named_icon(name, size=16):
    if not name:
        return None
    theme = Gtk.IconTheme.get_default()
    if theme is None:
        return None
    try:
        info = theme.lookup_icon(name, size, Gtk.IconLookupFlags.FORCE_SIZE)
        if info is None:
            return None
        pixbuf = info.load_icon()
        return Gtk.Image.new_from_pixbuf(pixbuf) if pixbuf else None
    except Exception:
        return None

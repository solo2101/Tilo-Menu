#!/usr/bin/env python3

import os
import gc
import urllib.parse

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, GdkPixbuf, Gio, GObject

import xdg.BaseDirectory as bd

import Globals
import utils

Icontype = ["png", "xpm", "svg"]

try:
    INSTALL_PREFIX = open("/etc/tilo/prefix", "r", encoding="utf-8").read().strip()
except Exception:
    INSTALL_PREFIX = "/usr"

import gettext
gettext.textdomain('tilo')
gettext.bindtextdomain('tilo', INSTALL_PREFIX + '/share/locale')
gettext.install('tilo', INSTALL_PREFIX + '/share/locale')

_ = gettext.gettext


def _file_uri_to_path(uri: str) -> str:
    if uri.startswith("file://"):
        return urllib.parse.unquote(uri[7:])
    return uri


def GetSystemIcon(icon):
    """Return absolute filename for a themed icon if resolvable, else None."""
    if not icon:
        return None
    # strip extension if present
    base = str(icon)
    for n in Icontype:
        base = base.replace('.' + n, '')
    theme = Gtk.IconTheme.get_default()
    info = theme.lookup_icon(base, 48, Gtk.IconLookupFlags.FORCE_SVG)
    return info.get_filename() if info else None


class IconFactory(GObject.GObject):
    __gsignals__ = {
        "icons-changed": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()

        self.gtkicontheme = Gtk.IconTheme.get_default()
        self.icontheme = getattr(Globals, "DefaultIconTheme", None)
        self.old_icontheme = self.icontheme

        # Optional thumbnailer via MATE (utils.thumbnailengine), if available
        self.thumbnailer = None
        if Globals.Settings.get('Show_Thumb'):
            try:
                self.thumbnailer = utils.thumbnailengine(Globals.PG_iconsize)
                if self.thumbnailer:
                    self.thumbnailer.connect("worklist-finished",
                                             lambda *_: self.emit('icons-changed'))
            except Exception:
                self.thumbnailer = None

    # -----------------------------
    # Theme change
    # -----------------------------
    def Icon_change(self):
        """Refresh Gtk icon theme (called when theme changes)."""
        self.icontheme = Gtk.Settings.get_default().get_property("gtk-icon-theme-name")
        self.gtkicontheme = Gtk.IconTheme.get_default()
        self.emit('icons-changed')

    # -----------------------------
    # Gio / GIcon helpers
    # -----------------------------
    def getgicon(self, gicon):
        """Return the first name of a GIcon that exists in current theme, else fallback."""
        try:
            # gicon can be ThemedIcon or others
            if isinstance(gicon, Gio.ThemedIcon):
                names = gicon.get_names()
                for name in names:
                    if self.gtkicontheme.has_icon(name):
                        return name
        except Exception:
            pass
        return 'gtk-execute'

    # -----------------------------
    # Recent item thumbnails
    # -----------------------------
    def getthumb(self, recent_info):
        """
        Return a GdkPixbuf for a Gtk.RecentInfo item, using thumbnail cache when possible.
        Falls back to recent_info.get_icon(size).
        """
        size = Globals.PG_iconsize
        try:
            path = _file_uri_to_path(recent_info.get_uri())
            if not os.path.exists(path):
                return recent_info.get_icon(size)

            # Prefer Gio thumbnail path if available
            try:
                gfile = Gio.File.new_for_path(path)
                info = gfile.query_info(Gio.FILE_ATTRIBUTE_THUMBNAIL_PATH,
                                        Gio.FileQueryInfoFlags.NONE, None)
                thumbfile = info.get_attribute_as_string(Gio.FILE_ATTRIBUTE_THUMBNAIL_PATH)
                if thumbfile and os.path.isfile(thumbfile):
                    return GdkPixbuf.Pixbuf.new_from_file_at_size(thumbfile, size, size)
            except Exception:
                pass

            # Optional MATE thumbnailer path
            if self.thumbnailer:
                icon, isthumbnail = self.thumbnailer.CheckWorkList(path)
                if not icon:
                    self.thumbnailer.AddToWorkList(path, recent_info.get_mime_type())
                    return recent_info.get_icon(size)
                return icon if isthumbnail else recent_info.get_icon(size)

            # Fallback to the recent item’s own icon
            return recent_info.get_icon(size)

        except Exception:
            return recent_info.get_icon(size)

    # -----------------------------
    # General icon loader
    # -----------------------------
    def geticonfile(self, icon):
        """
        Resolve an icon name or file path to a GdkPixbuf.Pixbuf at Globals.PG_iconsize.
        Search order:
        1) current Gtk theme (by icon name)
        2) XDG data dirs (icons/ or pixmaps/ with exact filename)
        3) direct file path
        4) theme missing-image fallback
        """
        size = Globals.PG_iconsize
        # 1) theme icon by name
        try:
            if icon and self.gtkicontheme.has_icon(icon):
                return self.gtkicontheme.load_icon(icon, size, Gtk.IconLookupFlags.FORCE_SIZE)
        except Exception:
            pass

        # 2) search common XDG dirs for a file match
        try:
            for dir_ in bd.xdg_data_dirs:
                for subdir in ('pixmaps', 'icons'):
                    path = os.path.join(dir_, subdir, str(icon))
                    if os.path.isfile(path):
                        return GdkPixbuf.Pixbuf.new_from_file_at_size(path, size, size)
        except Exception:
            pass

        # 3) direct file path
        try:
            if icon and os.path.isfile(str(icon)):
                return GdkPixbuf.Pixbuf.new_from_file_at_size(str(icon), size, size)
        except Exception:
            pass

        # 4) fallback
        try:
            return self.gtkicontheme.load_icon('gtk-missing-image', size, Gtk.IconLookupFlags.FORCE_SIZE)
        except Exception:
            # absolute last resort: empty pixbuf
            return GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, size, size)


# Keep module-level API compatible
def _(s):
    return gettext.gettext(s)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License v3 (or later)
# http://www.gnu.org/licenses/gpl.txt
# utils — Part of Tilo (modernized for Python 3 / Gtk 3 / MATE)

import os
import subprocess
from typing import Tuple, Optional

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject, GLib, GdkPixbuf

# ---- Optional: libnotify (preferred) ----
try:
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify  # type: ignore
    Notify.init("Tilo")
    _HAVE_NOTIFY = True
except Exception:
    _HAVE_NOTIFY = False

# ---- Optional: DBus (fallback for notifications & compiz) ----
try:
    import dbus  # type: ignore
    BUS = dbus.SessionBus()
    _HAVE_DBUS = True
except Exception:
    BUS = None
    _HAVE_DBUS = False

# ---- Optional: MATE/GNOME desktop thumbnail factory ----
# Prefer MateDesktop (MATE), then GnomeDesktop (GNOME),
# otherwise we fall back to a simple placeholder approach.
_THUMB_BACKEND = None
_THUMB_ENUM_LARGE = None
try:
    gi.require_version("MateDesktop", "2.0")
    from gi.repository import MateDesktop  # type: ignore

    _THUMB_BACKEND = MateDesktop
    _THUMB_ENUM_LARGE = getattr(MateDesktop, "ThumbnailSize", None)
except Exception:
    try:
        gi.require_version("GnomeDesktop", "3.0")
        from gi.repository import GnomeDesktop  # type: ignore

        _THUMB_BACKEND = GnomeDesktop
        _THUMB_ENUM_LARGE = getattr(GnomeDesktop, "ThumbnailSize", None)
    except Exception:
        _THUMB_BACKEND = None
        _THUMB_ENUM_LARGE = None

# ---- Optional: xdg BaseDirectory (used by xdg_dir) ----
try:
    import xdg.BaseDirectory as bd  # type: ignore
    _HAVE_XDG = True
except Exception:
    _HAVE_XDG = False


# ---------------------------
# Simple dialog helpers
# ---------------------------

def show_message(message: str, title: str = "Tilo") -> None:
    md = Gtk.MessageDialog(
        parent=None,
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    md.format_secondary_text(str(message))
    md.run()
    md.destroy()


def show_warning(message: str, title: str = "Tilo") -> None:
    md = Gtk.MessageDialog(
        parent=None,
        flags=0,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    md.format_secondary_text(str(message))
    md.run()
    md.destroy()


def show_question(message: str, title: str = "Tilo") -> bool:
    md = Gtk.MessageDialog(
        parent=None,
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text=title,
    )
    md.format_secondary_text(str(message))
    response = md.run()
    md.destroy()
    return response == Gtk.ResponseType.YES


# ---------------------------
# Notifications
# ---------------------------

def emit_notification(title: str, message: str) -> None:
    """Send a desktop notification. Prefer libnotify; fallback to DBus."""
    if _HAVE_NOTIFY:
        try:
            n = Notify.Notification.new(title, message, "dialog-information")
            n.show()
            return
        except Exception:
            pass
    if _HAVE_DBUS:
        try:
            notifications = dbus.Interface(
                BUS.get_object("org.freedesktop.Notifications",
                               "/org/freedesktop/Notifications"),
                "org.freedesktop.Notifications",
            )
            notifications.Notify("Tilo", 0, "dialog-information",
                                 title, message, [], {}, 3000)
        except Exception:
            pass


# ---------------------------
# Environment helpers
# ---------------------------

def sys_get_window_manager() -> str:
    """
    Best-effort window manager name.
    Tries `wmctrl -m`, then xprop dance, else returns ''.
    """
    # 1) wmctrl (simple)
    try:
        out = subprocess.check_output(["wmctrl", "-m"], stderr=subprocess.DEVNULL)
        for line in out.decode("utf-8", "replace").splitlines():
            if line.startswith("Name:"):
                return line.partition(":")[2].strip()
    except Exception:
        pass

    # 2) xprop fallback
    try:
        # Get the supporting WM window id
        out = subprocess.check_output(
            ["xprop", "-root", "_NET_SUPPORTING_WM_CHECK"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8", "replace")
        parts = out.strip().split()
        if parts and parts[-1].startswith("0x"):
            wm_win = parts[-1]
            out2 = subprocess.check_output(
                ["xprop", "-id", wm_win, "_NET_WM_NAME"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", "replace")
            # _NET_WM_NAME(UTF8_STRING) = "Compiz"
            if "=" in out2:
                name = out2.split("=", 1)[1].strip().strip('"')
                return name
    except Exception:
        pass

    return ""


def get_image_size(path: str) -> Tuple[int, int]:
    """Return (width, height) for an image at `path`."""
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
    return int(pixbuf.get_width()), int(pixbuf.get_height())


def xdg_dir(key: str) -> Optional[str]:
    """
    Resolve a user dir from ~/.config/user-dirs.dirs.
    Example key: 'XDG_DOWNLOAD_DIR'
    """
    user_dirs = (
        f"{bd.xdg_config_home}/user-dirs.dirs" if _HAVE_XDG
        else os.path.expanduser("~/.config/user-dirs.dirs")
    )
    if os.path.exists(user_dirs):
        with open(user_dirs, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith(key):
                    # Format: XDG_DOWNLOAD_DIR="$HOME/Downloads"
                    val = line[len(key) + 1:].strip()
                    if val.startswith("="):
                        val = val[1:].strip().strip('"')
                    return os.path.expandvars(val)
    return None


def readMountFile(filename: str):
    """Parse /etc/fstab style file and return a sorted list of mount points."""
    fstab = []
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            ls = line.strip()
            if not ls or ls.startswith("#") or ls.lower().startswith("none"):
                continue
            cols = ls.split()
            if len(cols) > 1 and cols[1] not in ("none", "/proc"):
                fstab.append(cols[1])
    fstab.sort()
    return fstab


def compiz_call(obj_path: str, func_name: str, *args):
    """Call Compiz over DBus (best-effort)."""
    if not _HAVE_DBUS:
        return ""
    try:
        path = "/org/freedesktop/compiz"
        if obj_path:
            path += f"/{obj_path}"
        obj = BUS.get_object("org.freedesktop.compiz", path)
        iface = dbus.Interface(obj, "org.freedesktop.compiz")
        func = getattr(iface, func_name, None)
        if func:
            return func(*args)
    except Exception:
        pass
    return ""


# ---------------------------
# Notifier convenience wrapper
# ---------------------------

class Notifier:
    """A convenience wrapper around libnotify/DBus notifications."""
    def __init__(self):
        self._have_notify = _HAVE_NOTIFY
        self._have_dbus = _HAVE_DBUS

    def notify(self, message: str, title: str = "", icon: str = "", timeout: int = -1) -> bool:
        try:
            if self._have_notify:
                n = Notify.Notification.new(title or "Tilo", message, icon or "dialog-information")
                if timeout >= 0:
                    try:
                        n.set_timeout(timeout)
                    except Exception:
                        pass
                n.show()
                return True
            if self._have_dbus:
                notifications = dbus.Interface(
                    BUS.get_object("org.freedesktop.Notifications",
                                   "/org/freedesktop/Notifications"),
                    "org.freedesktop.Notifications",
                )
                notifications.Notify("Tilo", 0, icon or "dialog-information",
                                     title or "Tilo", message, [], {}, timeout if timeout >= 0 else 3000)
                return True
        except Exception:
            pass
        print("Notify: libnotify/DBus unavailable.")
        return False


# ---------------------------
# Thumbnail engine (MATE/GNOME if available; graceful fallback)
# ---------------------------

class thumbnailengine(GObject.GObject):
    """
    Queues URIs for thumbnailing. Emits:
      - "thumbnail-finished" (uri: str)
      - "worklist-finished"  ()
    """

    __gsignals__ = {
        "thumbnail-finished": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "worklist-finished": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, icon_size: int):
        super().__init__()
        self.icon_size = icon_size
        self.WorkList = []
        self.DoneList = []
        self.Timer = None

        # Default icon path (fallback)
        self.stockimage = "/usr/share/icons/application-default-icon.png"
        if not os.path.exists(self.stockimage):
            # Try a very generic fallback icon from Adwaita or hicolor
            # We still return a path; not guaranteed to exist everywhere.
            self.stockimage = "/usr/share/icons/hicolor/48x48/apps/utilities-terminal.png"

        # Try to create a desktop thumbnail factory (MATE or GNOME)
        self._factory = None
        if _THUMB_BACKEND is not None:
            try:
                size_enum = None
                if _THUMB_ENUM_LARGE is not None:
                    # Enum may differ slightly by namespace
                    # Prefer LARGE; else fall back to NORMAL
                    size_enum = getattr(_THUMB_BACKEND.ThumbnailSize, "LARGE", None) \
                                or getattr(_THUMB_BACKEND.ThumbnailSize, "NORMAL", None)
                self._factory = _THUMB_BACKEND.ThumbnailFactory(size_enum) if size_enum else _THUMB_BACKEND.ThumbnailFactory()
            except Exception:
                self._factory = None

    # Mate/GNOME helpers (best-effort)

    def lookup(self, uri: str) -> str:
        """Return an existing thumbnail path or stock icon."""
        if self._factory:
            try:
                thumb = self._factory.lookup(uri, 0)
                if thumb:
                    return thumb
            except Exception:
                pass
        return self.stockimage

    def _process_with_factory(self, uri: str, mime_type: str) -> str:
        """
        Use Mate/GNOME factory if we can; otherwise return stock icon
        or the original file uri if that’s acceptable.
        """
        if not self._factory:
            return self.stockimage
        try:
            if self._factory.can_thumbnail(uri, mime_type, 0):
                thumb = self._factory.lookup(uri, 0)
                if not thumb:
                    thumb = self._factory.generate_thumbnail(uri, mime_type)
                    if thumb is not None:
                        self._factory.save_thumbnail(thumb, uri, 0)
                # If generation failed, fallback to stock
                return self.lookup(uri)
        except Exception:
            pass
        return self.stockimage

    # Public API mirrored from the old code

    def Process(self, uri: str, mime_type: str) -> str:
        """
        Return a path to an icon/thumbnail for the given (uri, mime_type).
        Uses MATE/GNOME factories when available.
        """
        return self._process_with_factory(uri, mime_type)

    def ProcessWorkList(self):
        """Internal worker for GLib timeout processing."""
        processitem = self.WorkList.pop(0)
        uri, mime_type = processitem[0], processitem[1]

        image = self.Process(uri, mime_type)
        isthumbnail = bool(image and image != self.stockimage)

        self.DoneList.append([uri, image, isthumbnail])
        self.emit("thumbnail-finished", uri)

        if not self.WorkList:
            self.emit("worklist-finished")
            self.Timer = None
            return False
        return True

    def CheckWorkList(self, uri: str):
        """Return (image_path, is_thumbnail) if already processed, else (None, False)."""
        for item in self.DoneList:
            if item[0] == uri:
                return item[1], item[2]
        return None, False

    def AddToWorkList(self, uri: str, mime_type: str) -> None:
        if [uri, mime_type] in self.WorkList:
            return
        self.WorkList.append([uri, mime_type])
        if not self.Timer:
            self.Timer = GLib.timeout_add(50, self.ProcessWorkList)

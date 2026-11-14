"""Show the same account portrait that MATE About Me uses.

MATE's control center saves the user picture in ~/.face. The XML IconSettings
define the frame and inset. We never require a manually named picture file or
replace GnoMenu's original artwork.
"""

import configparser
import getpass
import shutil
import subprocess
from pathlib import Path

from gi.repository import GdkPixbuf, Gio, Gtk


def face_candidates(home=None, username=None):
    """MATE's ~/.face first, AccountsService as an optional compatible fallback."""
    home = Path.home() if home is None else Path(home)
    username = getpass.getuser() if username is None else username
    yield home / ".face"
    if not username or "/" in username or username in (".", ".."):
        return
    record = Path("/var/lib/AccountsService/users") / username
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(record, encoding="utf-8")
        icon = config.get("User", "Icon", fallback="")
        if icon and Path(icon).is_absolute():
            yield Path(icon)
    except (OSError, configparser.Error, UnicodeError):
        pass
    yield Path("/var/lib/AccountsService/icons") / username


def face_file(home=None, username=None):
    """Return a real readable image, never assume a missing ~/.face exists."""
    for path in face_candidates(home=home, username=username):
        try:
            if path.is_file():
                GdkPixbuf.Pixbuf.new_from_file(str(path))
                return path
        except Exception:
            continue
    return None


def _scaled_portrait(pixbuf, width, height):
    """Center-crop the avatar to the original GnoMenu inset without distortion."""
    source_w, source_h = pixbuf.get_width(), pixbuf.get_height()
    if source_w < 1 or source_h < 1:
        return None
    ratio = max(width / source_w, height / source_h)
    target_w = max(width, round(source_w * ratio))
    target_h = max(height, round(source_h * ratio))
    resized = pixbuf.scale_simple(target_w, target_h, GdkPixbuf.InterpType.BILINEAR)
    if resized is None:
        return None
    return resized.new_subpixbuf((target_w - width) // 2, (target_h - height) // 2,
                                width, height)


def _fallback_portrait(width, height):
    theme = Gtk.IconTheme.get_default()
    if theme is None:
        return None
    for name in ("avatar-default", "user-identity", "stock_person", "user-info"):
        try:
            info = theme.lookup_icon(name, max(width, height), Gtk.IconLookupFlags.FORCE_SIZE)
            if info is not None:
                pixbuf = info.load_icon()
                if pixbuf:
                    return _scaled_portrait(pixbuf, width, height)
        except Exception:
            pass
    return None


def portrait_pixbuf(width, height, home=None):
    candidate = face_file(home=home)
    if candidate is not None:
        try:
            return _scaled_portrait(GdkPixbuf.Pixbuf.new_from_file(str(candidate)),
                                    width, height)
        except Exception:
            pass
    return _fallback_portrait(width, height)


def render_user_face(layout, theme, on_open=None):
    """Use IconSettings X/Y and InsetX/Y/Width/Height from each original XML."""
    settings = theme.icon
    if settings is None:
        return None
    frame_w, frame_h = settings.integer("Width"), settings.integer("Height")
    inset_w, inset_h = settings.integer("InsetWidth"), settings.integer("InsetHeight")
    if min(frame_w, frame_h, inset_w, inset_h) <= 0:
        return None

    x, y = settings.integer("X"), settings.integer("Y")
    inset_x, inset_y = settings.integer("InsetX"), settings.integer("InsetY")
    if (inset_x < 0 or inset_y < 0
            or inset_x + inset_w > frame_w or inset_y + inset_h > frame_h):
        return None

    surface = Gtk.Fixed()
    surface.set_size_request(frame_w, frame_h)
    surface.set_app_paintable(True)
    portrait = Gtk.Image()
    surface.put(portrait, inset_x, inset_y)

    frame_path = theme.directory / "user-image-frame.png"
    if frame_path.is_file():
        try:
            border = GdkPixbuf.Pixbuf.new_from_file(str(frame_path))
            surface.put(Gtk.Image.new_from_pixbuf(border), 0, 0)
        except Exception:
            pass

    def refresh():
        picture = portrait_pixbuf(inset_w, inset_h)
        portrait.set_from_pixbuf(picture)
        return False

    refresh()
    box = Gtk.EventBox()
    box.set_visible_window(False)
    box.set_above_child(True)
    box.set_size_request(frame_w, frame_h)
    box.set_tooltip_text("About Me")
    box.add(surface)
    box.connect("button-release-event",
                lambda _widget, event: bool(on_open()) if event.button == 1 and on_open else False)

    # MATE About Me can change ~/.face while the menu is open. Watch the
    # containing directory so creation of a previously missing file is caught.
    try:
        monitor = Gio.File.new_for_path(str(Path.home())).monitor_directory(
            Gio.FileMonitorFlags.NONE, None
        )
        def changed(_monitor, file, _other, _event):
            if file is not None and file.get_basename() == ".face":
                refresh()
        monitor.connect("changed", changed)
        box._face_monitor = monitor
        box.connect("destroy", lambda _widget: monitor.cancel())
    except Exception:
        pass

    layout.put(box, x, y)
    return box


def open_mate_about_me():
    executable = shutil.which("mate-about-me")
    if executable is None:
        return False
    try:
        subprocess.Popen([executable], start_new_session=True)
        return True
    except OSError as error:
        print(f"Tilo Menu: unable to open MATE About Me: {error}")
        return False

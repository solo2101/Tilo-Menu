"""Render original GnoMenu XML chrome independently of the desktop GTK theme.

Each button's Image is its hover state, not a permanently visible fill.
ImageBack is the optional resting background. Original Pango markup is honored.
"""
import getpass
import html
import platform
import shutil
import subprocess
import socket
import xml.etree.ElementTree as ET
from pathlib import Path

from gi.repository import GdkPixbuf, Gtk, Pango
from ..icons import load_named_icon
from .contrast import legible_markup


def _pixbuf(directory, filename, size=None):
    if not filename:
        return None
    root = directory.resolve()
    path = (root / filename).resolve()
    if path.is_relative_to(root) and path.is_file():
        try:
            if size:
                return GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), size, size, True)
            return GdkPixbuf.Pixbuf.new_from_file(str(path))
        except Exception:
            return None
    return None


def _icon(directory, filename, size=0):
    pix = _pixbuf(directory, filename, size if size > 0 else None)
    if pix is not None:
        return pix
    if filename:
        image = load_named_icon(Path(filename).stem, size if size > 0 else 16)
        if image:
            return image.get_pixbuf()
    return None


def _set_safe_markup(label, markup, fallback=""):
    """Ignore malformed legacy markup rather than issuing GTK warnings."""
    if not markup:
        label.set_text(fallback)
        return
    try:
        ET.fromstring("<root>" + markup + "</root>")
    except ET.ParseError:
        label.set_text(fallback)
        return
    label.set_markup(markup)


def _valid_markup(markup, fallback=""):
    """Keep legacy typography if valid, otherwise show a readable label."""
    if markup:
        try:
            ET.fromstring("<root>" + markup + "</root>")
            return markup
        except ET.ParseError:
            pass
    return html.escape(fallback)


def _color_label(label, theme, markup, fallback, x, y, width,
                 *, selected=False, invert_unselected=False, overlay="",
                 overlay_x=0, overlay_y=0):
    valid = _valid_markup(markup, fallback)
    corrected = legible_markup(
        theme, valid, x, y, width,
        selected=selected, invert_unselected=invert_unselected,
        overlay=overlay, overlay_x=overlay_x, overlay_y=overlay_y,
    )
    _set_safe_markup(label, corrected, fallback)


def _markup(container, attrs, width, *, theme, x=0, y=0, fallback="",
            selected=False, invert_unselected=False, overlay=""):
    markup = attrs.get("Markup", "")
    if not markup and not fallback:
        return None
    label = Gtk.Label()
    xoff = int(attrs.get("TextX", "0"))
    yoff = int(attrs.get("TextY", "0"))
    available = max(1, width - xoff - 4)
    _color_label(
        label, theme, markup, fallback, x + xoff, y + yoff, available,
        selected=selected, invert_unselected=invert_unselected,
        overlay=overlay, overlay_x=x, overlay_y=y,
    )
    label.set_xalign(
        (0.0, 0.5, 1.0)[max(0, min(2, int(attrs.get("TextAlignment", "0"))))]
    )
    label.set_ellipsize(Pango.EllipsizeMode.END)
    label.set_size_request(available, -1)
    container.put(label, xoff, yoff)
    return label


def _event_box(child, width, height, name, callback):
    eventbox = Gtk.EventBox()
    eventbox.set_visible_window(False)
    eventbox.set_above_child(True)
    eventbox.set_size_request(width, height)
    eventbox.add(child)
    if name and name != ":SEPARATOR:":
        eventbox.set_tooltip_text(name)
        if callback is not None:
            eventbox.connect(
                "button-release-event",
                lambda _widget, event: bool(callback(name)) if event.button == 1 else False
            )
    return eventbox


def render_theme_buttons(layout: Gtk.Fixed, theme, on_activate=None) -> None:
    """Draw original normal and hover button frames at their XML coordinates."""
    for element in theme.buttons:
        attrs = element.attributes
        hover = _pixbuf(theme.directory, attrs.get("Image", ""))
        back = _pixbuf(theme.directory, attrs.get("ImageBack", ""))
        if hover is None and back is None:
            continue
        reference = hover or back
        width, height = reference.get_width(), reference.get_height()
        container = Gtk.Fixed()
        container.set_app_paintable(True)
        container.set_size_request(width, height)
        if back is not None:
            container.put(Gtk.Image.new_from_pixbuf(back), 0, 0)
        foreground = Gtk.Image()
        container.put(foreground, 0, 0)
        if attrs.get("Name") == ":SEPARATOR:":
            foreground.set_from_pixbuf(hover)
        default_icon_name = attrs.get("ButtonIcon") or attrs.get("Icon", "")
        icon_size = int(attrs.get("ButtonIconSize", "0") or "0")
        default_icon = _icon(theme.directory, default_icon_name, icon_size)
        selected_icon = _icon(theme.directory, attrs.get("ButtonIconSel", ""), icon_size)
        icon = Gtk.Image()
        if default_icon is not None:
            icon.set_from_pixbuf(default_icon)
        if default_icon is not None or selected_icon is not None:
            container.put(
                icon,
                int(attrs.get("ButtonIconX", "0")),
                int(attrs.get("ButtonIconY", "0")),
            )
        x, y = element.integer("ButtonX"), element.integer("ButtonY")
        label = _markup(
            container, attrs, width, theme=theme, x=x, y=y,
            overlay=attrs.get("ImageBack", ""),
            fallback=attrs.get("Name", "") if attrs.get("Markup") else "",
        )
        name = attrs.get("Name", "")
        eventbox = _event_box(container, width, height, name, on_activate)
        if name != ":SEPARATOR:":
            def change_state(hovered, foreground=foreground, icon=icon,
                             picture=hover, default=default_icon,
                             selected=selected_icon, text=label,
                             attr=attrs, bx=x, by=y, w=width):
                foreground.set_from_pixbuf(picture if hovered else None)
                icon.set_from_pixbuf((selected or default) if hovered else default)
                if text is not None:
                    _color_label(
                        text, theme, attr.get("Markup", ""), attr.get("Name", ""),
                        bx + int(attr.get("TextX", "0")),
                        by + int(attr.get("TextY", "0")),
                        max(1, w - int(attr.get("TextX", "0")) - 4),
                        selected=hovered,
                        overlay=attr.get("Image", "") if hovered
                                else attr.get("ImageBack", ""),
                        overlay_x=bx, overlay_y=by,
                    )

            eventbox.connect(
                "enter-notify-event",
                lambda _widget, _event, state=change_state: state(True) or False,
            )
            eventbox.connect(
                "leave-notify-event",
                lambda _widget, _event, state=change_state: state(False) or False,
            )
        layout.put(eventbox, element.integer("ButtonX"), element.integer("ButtonY"))


def render_theme_details(layout: Gtk.Fixed, theme, on_tab=None) -> dict:
    """Draw XML static images, labels and tabs without desktop-theme styling."""
    for element in theme.images:
        picture = _pixbuf(theme.directory, element.attributes.get("Image", ""))
        if picture is not None:
            layout.put(
                Gtk.Image.new_from_pixbuf(picture),
                element.integer("ImageX"), element.integer("ImageY"),
            )

    for element in theme.labels:
        attrs = element.attributes
        markup = attrs.get("Markup", "")
        command = attrs.get("Command", "").strip().casefold()
        replacement = ""
        if command == "whoami":
            replacement = getpass.getuser()
        elif "lsb_release" in command:
            try:
                replacement = platform.freedesktop_os_release().get(
                    "PRETTY_NAME", platform.system()
                )
            except (OSError, AttributeError):
                replacement = platform.system()
        elif command.startswith("df "):
            try:
                disk = shutil.disk_usage("/")
                replacement = f"{round(100 * disk.used / disk.total)}%"
            except OSError:
                replacement = "N/A"
        elif command.startswith("/sbin/ip route") or command.startswith("ip route"):
            try:
                result = subprocess.run(
                    ["ip", "-4", "-o", "addr", "show", "scope", "global"],
                    capture_output=True, text=True, timeout=1, check=False,
                )
                replacement = next(
                    (word.split("/")[0] for word in result.stdout.split()
                     if word.count(".") == 3 and "/" in word),
                    "N/A"
                )
            except (OSError, subprocess.TimeoutExpired):
                replacement = "N/A"
        elif attrs.get("Name") == "Username":
            replacement = getpass.getuser()

        text = markup.replace("[TEXT]", html.escape(replacement))
        label = Gtk.Label()
        x, y = element.integer("LabelX"), element.integer("LabelY")
        width = max(1, theme.width - x - 4)
        _color_label(
            label, theme, text, attrs.get("Name", ""), x, y,
            min(width, max(70, theme.width // 2)),
        )
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_size_request(width, -1)
        label.set_xalign(
            (0.0, 0.5, 1.0)[max(0, min(2, int(attrs.get("TextAlignment", "0"))))]
        )
        layout.put(label, x, y)

    tabs = {}
    tab_names = [e.attributes.get("Name", "") for e in theme.tabs]
    active = "Applications" if "Applications" in tab_names else (
        tab_names[0] if tab_names else ""
    )
    for element in theme.tabs:
        attrs = element.attributes
        normal = _pixbuf(theme.directory, attrs.get("Image", ""))
        selected = _pixbuf(theme.directory, attrs.get("ImageSel", ""))
        reference = selected or normal
        if reference is None:
            continue
        width, height = reference.get_width(), reference.get_height()
        container = Gtk.Fixed()
        container.set_size_request(width, height)
        picture = Gtk.Image()
        container.put(picture, 0, 0)
        icon_size = int(attrs.get("TabIconSize", "0") or "0")
        icon_name = attrs.get("TabIcon", "") or attrs.get("Icon", "")
        icon_pix = _icon(theme.directory, icon_name, icon_size)
        if icon_pix is not None:
            container.put(
                Gtk.Image.new_from_pixbuf(icon_pix),
                int(attrs.get("TabIconX", "0")), int(attrs.get("TabIconY", "0")),
            )
        name = attrs.get("Name", "")
        tx, ty = element.integer("TabX"), element.integer("TabY")
        inverted = attrs.get("InvertTextColorOnSel", "0") == "1"
        label = _markup(
            container, attrs, width, theme=theme, x=tx, y=ty,
            fallback=name,
            selected=name == active, invert_unselected=inverted,
            overlay=attrs.get("ImageSel", "") if name == active
                    else attrs.get("Image", ""),
        )

        def set_selected(value, picture=picture, normal=normal, selected=selected,
                         text=label, attr=attrs, bx=tx, by=ty, w=width,
                         tab_name=name, invert=inverted):
            picture.set_from_pixbuf((selected or normal) if value else normal)
            if text is not None:
                _color_label(
                    text, theme, attr.get("Markup", ""), tab_name,
                    bx + int(attr.get("TextX", "0")),
                    by + int(attr.get("TextY", "0")),
                    max(1, w - int(attr.get("TextX", "0")) - 4),
                    selected=value, invert_unselected=invert,
                    overlay=attr.get("ImageSel", "") if value
                            else attr.get("Image", ""),
                    overlay_x=bx, overlay_y=by,
                )
        tabs[name] = set_selected
        set_selected(name == active)
        box = _event_box(container, width, height, name, on_tab)
        layout.put(box, element.integer("TabX"), element.integer("TabY"))
    return tabs

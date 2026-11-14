"""Render original GnoMenu XML chrome independently of the desktop GTK theme.

Each button's Image is its hover state, not a permanently visible fill.
ImageBack is the optional resting background. Original Pango markup is honored.
"""
import getpass
import platform
from pathlib import Path

from gi.repository import GdkPixbuf, Gtk, Pango
from ..icons import load_named_icon


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


def _icon(directory, filename, size=16):
    pix = _pixbuf(directory, filename, size if size > 0 else None)
    if pix is not None:
        return pix
    if filename:
        image = load_named_icon(Path(filename).stem, size if size > 0 else 16)
        if image:
            return image.get_pixbuf()
    return None


def _markup(container, attrs, width, *, fallback=""):
    markup = attrs.get("Markup", "")
    if not markup and not fallback:
        return
    label = Gtk.Label()
    try:
        if markup:
            label.set_markup(markup)
        else:
            label.set_text(fallback)
    except Exception:
        label.set_text(fallback)
    label.set_xalign((0.0, 0.5, 1.0)[max(0, min(2, int(attrs.get("TextAlignment", "0"))))])
    label.set_ellipsize(Pango.EllipsizeMode.END)
    x = int(attrs.get("TextX", "0"))
    label.set_size_request(max(1, width - x - 4), -1)
    container.put(label, x, int(attrs.get("TextY", "0")))


def _event_box(child, width, height, name, callback):
    eventbox = Gtk.EventBox()
    eventbox.set_visible_window(False)
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
        _markup(container, attrs, width)
        name = attrs.get("Name", "")
        eventbox = _event_box(container, width, height, name, on_activate)
        if name != ":SEPARATOR:":
            def change_state(hovered, foreground=foreground, icon=icon,
                             picture=hover, default=default_icon, selected=selected_icon):
                foreground.set_from_pixbuf(picture if hovered else None)
                icon.set_from_pixbuf((selected or default) if hovered else default)

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
        name = attrs.get("Name", "")
        replacement = (
            getpass.getuser() if name == "Username"
            else platform.system() if name == "System"
            else name
        )
        text = markup.replace("[TEXT]", replacement)
        label = Gtk.Label()
        try:
            label.set_markup(text)
        except Exception:
            label.set_text(replacement)
        label.set_xalign((0.0, 0.5, 1.0)[max(0, min(2, int(attrs.get("TextAlignment", "0"))))])
        layout.put(label, element.integer("LabelX"), element.integer("LabelY"))

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
        _markup(container, attrs, width)
        name = attrs.get("Name", "")
        def set_selected(value, picture=picture, normal=normal, selected=selected):
            picture.set_from_pixbuf((selected or normal) if value else normal)
        tabs[name] = set_selected
        set_selected(name == active)
        box = _event_box(container, width, height, name, on_tab)
        layout.put(box, element.integer("TabX"), element.integer("TabY"))
    return tabs

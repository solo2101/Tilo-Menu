"""Render original GnoMenu 2.9.1 XML button geometry with GTK 3.

Theme images and markup are kept intact. No per-theme hardcoded positions.
"""

from pathlib import Path

from gi.repository import GdkPixbuf, Gtk, Pango

from ..icons import load_named_icon


def _image(directory, filename):
    if not filename:
        return None
    root = directory.resolve()
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    try:
        return Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(str(path)))
    except Exception:
        return None


def _dimensions(image):
    pixbuf = image.get_pixbuf()
    return (pixbuf.get_width(), pixbuf.get_height()) if pixbuf else (0, 0)


def render_theme_buttons(layout: Gtk.Fixed, theme, on_activate=None) -> None:
    """Position original backgrounds, overlays, icons and labels."""
    for element in theme.buttons:
        attrs = element.attributes
        base = _image(theme.directory, attrs.get("Image", ""))
        if base is None:
            continue

        width, height = _dimensions(base)
        container = Gtk.Fixed()
        container.set_size_request(width, height)
        container.put(base, 0, 0)

        overlay = _image(theme.directory, attrs.get("ButtonIcon", ""))
        if overlay is not None:
            container.put(
                overlay, element.integer("ButtonIconX"), element.integer("ButtonIconY")
            )

        # Icon is a named theme icon. ButtonIcon is a separate overlay image.
        icon_name = attrs.get("Icon", "")
        icon = None
        if icon_name:
            icon = _image(theme.directory, icon_name)
            if icon is None:
                icon = load_named_icon(Path(icon_name).stem, 16)
            if icon is not None:
                icon_x = element.integer("IconX", 4)
                icon_y = element.integer("IconY", max(0, (height - 16) // 2))
                container.put(icon, icon_x, icon_y)

        markup = attrs.get("Markup", "")
        if markup:
            label = Gtk.Label()
            label.set_markup(markup)
            label.set_xalign(0)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            text_x = element.integer("TextX")
            # Reserve room for the icon when the XML text inset overlaps it.
            if icon is not None:
                icon_width = _dimensions(icon)[0] or 16
                text_x = max(text_x, icon_x + icon_width + 4)
            label.set_size_request(max(1, width - text_x - 4), -1)
            container.put(label, text_x, element.integer("TextY"))

        layout.put(container, element.integer("ButtonX"), element.integer("ButtonY"))
        if attrs.get("Name") != ":SEPARATOR:":
            name = attrs.get("Name", "")
            container.set_tooltip_text(name)
            if on_activate is not None:
                hitbox = Gtk.EventBox()
                hitbox.set_visible_window(False)
                hitbox.set_size_request(width, height)
                hitbox.connect("button-release-event",
                    lambda _widget, event, action=name: on_activate(action) if event.button == 1 else False)
                layout.put(hitbox, element.integer("ButtonX"), element.integer("ButtonY"))

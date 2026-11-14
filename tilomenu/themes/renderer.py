"""GTK 3 renderer for GnoMenu XML-defined button artwork.

All positions, images, icons and label markup come from the selected theme.
No Vista-specific coordinates or command execution.
"""

from pathlib import Path

from gi.repository import Gtk


def _image(directory: Path, filename: str):
    if not filename:
        return None
    path = (directory / filename).resolve()
    if not path.is_relative_to(directory.resolve()) or not path.is_file():
        return None
    return Gtk.Image.new_from_file(str(path))


def render_theme_buttons(layout: Gtk.Fixed, theme) -> None:
    """Render buttons, separators and theme-provided icons and text."""
    for element in theme.buttons:
        attrs = element.attributes
        base = _image(theme.directory, attrs.get("Image", ""))
        if base is None:
            continue

        container = Gtk.Fixed()
        container.put(base, 0, 0)

        # Original themes use a separate foreground image for icon-only controls.
        overlay = _image(theme.directory, attrs.get("ButtonIcon", ""))
        if overlay is not None:
            container.put(overlay, 0, 0)

        icon_name = attrs.get("Icon", "")
        if icon_name:
            icon_path = _image(theme.directory, icon_name)
            if icon_path is not None:
                icon = icon_path
            else:
                icon = Gtk.Image.new_from_icon_name(
                    Path(icon_name).stem, Gtk.IconSize.MENU
                )
            container.put(
                icon, element.integer("IconX", 5), element.integer("IconY", 6)
            )

        markup = attrs.get("Markup", "")
        if markup:
            label = Gtk.Label()
            label.set_use_markup(True)
            label.set_markup(markup)
            label.set_halign(Gtk.Align.START)
            container.put(
                label, element.integer("TextX"), element.integer("TextY")
            )

        layout.put(
            container, element.integer("ButtonX"), element.integer("ButtonY")
        )
        if attrs.get("Name") != ":SEPARATOR:":
            container.set_tooltip_text(attrs.get("Name", ""))

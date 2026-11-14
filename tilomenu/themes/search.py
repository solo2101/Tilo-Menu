"""Theme-controlled search field that does not inherit GTK widget artwork.

GnoMenu's custom PNG and Cairo search settings provide the visuals; a frameless
Gtk.Entry supplies keyboard input, Unicode, selection and accessibility.
"""
from pathlib import Path

from gi.repository import Gdk, GdkPixbuf, Gtk


def _hex_rgb(value):
    value = (value or "").strip()
    if not (len(value) == 7 and value[0] == "#"):
        return None
    try:
        return tuple(int(value[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    except ValueError:
        return None


def _sample_theme(theme, x, y):
    """Return foreground and field colors based on the actual menu artwork."""
    try:
        pix = GdkPixbuf.Pixbuf.new_from_file(str(theme.directory / theme.background))
        x, y = max(0, min(pix.get_width() - 1, x)), max(0, min(pix.get_height() - 1, y))
        pixels = pix.get_pixels()
        i = y * pix.get_rowstride() + x * pix.get_n_channels()
        r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return ("#202020", (1.0, 1.0, 1.0, 0.85)) if luminance >= 145 else (
            "#ffffff", (0.04, 0.04, 0.04, 0.65)
        )
    except (OSError, ValueError, IndexError):
        return "#ffffff", (0.04, 0.04, 0.04, 0.65)


class ThemeSearch(Gtk.Overlay):
    def __init__(self, theme, on_change):
        super().__init__()
        self.theme = theme
        self.settings = theme.search.attributes
        self.width = max(1, theme.search.integer("Width"))
        self.height = max(1, theme.search.integer("Height"))
        self.set_size_request(self.width, self.height)
        self.get_style_context().add_class("tilo-search-control")
        self.set_app_paintable(True)

        image_name = self.settings.get("Background", "")
        self.background = None
        if image_name:
            root = theme.directory.resolve()
            file = (root / image_name).resolve()
            if file.is_relative_to(root) and file.is_file():
                try:
                    self.background = GdkPixbuf.Pixbuf.new_from_file(str(file))
                except Exception:
                    pass

        foreground, self.field_color = _sample_theme(
            theme,
            theme.search.integer("X") + self.width // 2,
            theme.search.integer("Y") + self.height // 2,
        )
        self.foreground = self.settings.get("TextColor")
        if _hex_rgb(self.foreground) is None:
            self.foreground = foreground

        self.surface = Gtk.DrawingArea()
        self.surface.set_size_request(self.width, self.height)
        self.surface.set_app_paintable(True)
        self.surface.connect("draw", self._draw_field)
        self.add(self.surface)

        self.entry = Gtk.Entry()
        self.entry.set_has_frame(False)
        self.entry.set_placeholder_text(self.settings.get("InitialText", "Search"))
        self.entry.set_halign(Gtk.Align.FILL)
        self.entry.set_valign(Gtk.Align.CENTER)
        self.entry.set_margin_start(max(2, self._inset_x()))
        self.entry.set_margin_end(5)
        self.entry.set_size_request(-1, self.height)
        self.entry.get_style_context().add_class("tilo-search-input")
        css = Gtk.CssProvider()
        css.load_from_data(("""
            entry.tilo-search-input, entry.tilo-search-input:focus {
                background-color: transparent;
                background-image: none;
                box-shadow: none;
                border: none;
                border-radius: 0;
                outline: none;
                min-width: 0;
                min-height: 0;
                padding: 0;
                margin: 0;
                color: FOREGROUND;
                font-size: 12px;
            }
            entry.tilo-search-input selection {
                background-color: rgba(60, 120, 210, 0.65);
                color: #ffffff;
            }
        """.replace("FOREGROUND", self.foreground)).encode("utf-8"))
        self.entry.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_USER + 10
        )
        self.entry.connect("changed", on_change)
        self.add_overlay(self.entry)

    def _inset_x(self):
        try:
            value = int(self.settings.get("InsetX", "5"))
        except (TypeError, ValueError):
            value = 5
        # Some GnoMenu PNGs include their own search icon.
        return min(max(2, value), max(2, self.width // 3))

    def _draw_field(self, _widget, cr):
        cr.rectangle(0, 0, self.width, self.height)
        cr.clip()
        if self.background is not None:
            Gdk.cairo_set_source_pixbuf(cr, self.background, 0, 0)
            cr.paint()
            return False
        fill = _hex_rgb(self.settings.get("BackColor", ""))
        if fill is None:
            fill = self.field_color[:3]
            alpha = self.field_color[3]
        else:
            alpha = 1.0
        cr.set_source_rgba(*fill, alpha)
        cr.rectangle(0.5, 0.5, self.width - 1, self.height - 1)
        cr.fill_preserve()
        border = _hex_rgb(self.settings.get("BorderColor", ""))
        if border is None:
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.45)
        else:
            cr.set_source_rgb(*border)
        cr.set_line_width(1)
        cr.stroke()
        return False

    def get_text(self):
        return self.entry.get_text()

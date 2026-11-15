"""GTK3 chrome and contrast helpers ported from archived renderer.

Keep the original theme XML and PNG pixels as source of truth. In GTK3,
container widgets must not add their own opaque desktop-theme rectangles.
"""
import re
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk


def transparent_chrome(*widgets):
    css = Gtk.CssProvider()
    css.load_from_data(b"""
        .tilomenu-original-chrome {
            background: transparent;
            background-image: none;
            border: 0;
            border-radius: 0;
            box-shadow: none;
            outline: none;
            padding: 0;
            margin: 0;
        }
    """)
    for widget in widgets:
        widget.get_style_context().add_class('tilomenu-original-chrome')
        widget.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        widget.set_app_paintable(True)
    # Store provider on widgets for GTK3 lifetime.
    widgets[0]._tilomenu_chrome_css = css


_COLOR = re.compile(r'(foreground\\s*=\\s*[\\\'\\"])(#[0-9a-fA-F]{6})([\\\'\\"])')


def legible_markup(markup, background, x, y, width):
    """Adapt archive's image sampling to the original loaded GdkPixbuf.

    Preserve the XML's font, size, style and markup. Change its foreground
    only if the original color has poor contrast against original artwork.
    """
    match = _COLOR.search(markup or '')
    if not match or background is None:
        return markup
    channels = background.get_n_channels()
    rowstride = background.get_rowstride()
    pixels = background.get_pixels()
    samples = []
    for dx in (2, min(18, width // 2), min(38, max(2, width - 2))):
        px, py = int(x + dx), int(y + 10)
        if not (0 <= px < background.get_width() and 0 <= py < background.get_height()):
            continue
        offset = py * rowstride + px * channels
        if channels == 4 and pixels[offset + 3] < 165:
            continue
        samples.append(tuple(pixels[offset:offset + 3]))
    if not samples:
        return markup
    background_rgb = sorted(samples, key=lambda rgb: sum(rgb))[len(samples) // 2]

    def luminance(rgb):
        values = [z / 255.0 for z in rgb]
        values = [z / 12.92 if z <= .04045 else ((z + .055) / 1.055) ** 2.4
                  for z in values]
        return .2126 * values[0] + .7152 * values[1] + .0722 * values[2]

    def contrast(a, b):
        a, b = luminance(a), luminance(b)
        return (max(a, b) + .05) / (min(a, b) + .05)

    original = tuple(int(match.group(2)[i:i + 2], 16) for i in (1, 3, 5))
    if contrast(original, background_rgb) >= 4.5:
        return markup
    light = (250, 250, 250)
    dark = (24, 24, 24)
    chosen = max((light, dark), key=lambda color: contrast(color, background_rgb))
    return markup[:match.start(2)] + '#%02x%02x%02x' % chosen + markup[match.end(2):]

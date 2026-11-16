"""Original XML text colors and fallback contrast for unstyled captions.

Preserve authored foreground colors, even when a modern contrast heuristic
would choose something else. Sample theme pixels only when XML has no color.
"""
from functools import lru_cache
from pathlib import Path
import re

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf


FOREGROUND = re.compile(r"foreground\s*=\s*['\"](#[0-9a-fA-F]{6})['\"]")


def _rgb(value):
    if not value or len(value) != 7 or value[0] != "#":
        return None
    try:
        return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))
    except ValueError:
        return None


def _hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _invert(rgb):
    return tuple(255 - value for value in rgb)


def _luminance(rgb):
    channels = []
    for value in rgb:
        channel = value / 255.0
        channels.append(channel / 12.92 if channel <= 0.04045 else
                        ((channel + 0.055) / 1.055) ** 2.4)
    return (0.2126 * channels[0] + 0.7152 * channels[1]
            + 0.0722 * channels[2])


def contrast_ratio(a, b):
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@lru_cache(maxsize=100)
def _asset(filename):
    try:
        return GdkPixbuf.Pixbuf.new_from_file(filename)
    except (OSError, ValueError):
        return None


def _pixel(pixbuf, x, y):
    if pixbuf is None:
        return None
    x, y = int(x), int(y)
    if not (0 <= x < pixbuf.get_width() and 0 <= y < pixbuf.get_height()):
        return None
    n = pixbuf.get_n_channels()
    pixels = pixbuf.get_pixels()
    index = y * pixbuf.get_rowstride() + x * n
    rgb = tuple(pixels[index:index + 3])
    alpha = pixels[index + 3] / 255 if n == 4 else 1.0
    return rgb, alpha


@lru_cache(maxsize=256)
def _trusted_image(root, filename):
    if not filename:
        return None
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    return _asset(str(path))


def _image(theme, filename):
    return _trusted_image(theme.directory.resolve(), filename)


def sample_background(theme, x, y, overlay="", overlay_x=0, overlay_y=0):
    """Return RGBA-composited artwork color or None if mostly transparent."""
    # Original GnoMenu flips the background PNG for top-panel menus while
    # keeping text and icon assets upright at recalculated XML coordinates.
    # Sample the actual background pixel behind the label.
    base_y = theme.height - 1 - int(y) if theme.flipped else y
    base = _pixel(_image(theme, theme.background), x, base_y)
    if base is None:
        rgb, alpha = (127, 127, 127), 0.0
    else:
        rgb, alpha = base
    if overlay:
        top = _pixel(_image(theme, overlay), x - overlay_x, y - overlay_y)
        if top is not None:
            color, top_alpha = top
            combined = top_alpha + alpha * (1.0 - top_alpha)
            if combined > 0:
                rgb = tuple(round((color[i] * top_alpha
                            + rgb[i] * alpha * (1 - top_alpha)) / combined)
                            for i in range(3))
            alpha = combined
    return rgb if alpha >= 0.65 else None


def suggested_color(theme, text_x, text_y, width, preferred=None,
                    overlay="", overlay_x=0, overlay_y=0):
    """Choose foreground against the median brightness of the text region."""
    colors = []
    distance = max(0, min(max(0, width - 5), 38))
    for dx in (2, distance // 2, distance):
        for dy in (5, 10):
            color = sample_background(
                theme, text_x + dx, text_y + dy, overlay, overlay_x, overlay_y
            )
            if color is not None:
                colors.append(color)
    if not colors:
        return preferred or (255, 255, 255)

    colors.sort(key=_luminance)
    background = colors[len(colors) // 2]
    if preferred is not None and contrast_ratio(preferred, background) >= 4.5:
        return preferred
    black, white = (24, 24, 24), (250, 250, 250)
    return max((black, white), key=lambda color: contrast_ratio(color, background))


def legible_markup(theme, markup, text_x, text_y, width, *,
                   selected=False, invert_unselected=False,
                   overlay="", overlay_x=0, overlay_y=0):
    """Respect original XML foreground colors, including tab inversion.

    GnoMenu's XML defines each caption's foreground. Contrast correction of
    an explicit foreground is not compatible with the source themes: notably
    XP's authored white footer text was being rendered black. Only choose a
    background-aware color if a theme omits the foreground entirely.
    """
    match = FOREGROUND.search(markup)
    if match:
        # The original MenuTab.SetSelectedTab inverts an unselected tab
        # only when the XML explicitly requests InvertTextColorOnSel.
        if not invert_unselected or selected:
            return markup
        source = _rgb(match.group(1))
        if source is None:
            return markup
        inverse = _hex(_invert(source))
        return markup[:match.start(1)] + inverse + markup[match.end(1):]

    # Themes without foreground metadata still need a readable default
    # independent of the GTK desktop theme.
    chosen = suggested_color(
        theme, text_x, text_y, width, None, overlay, overlay_x, overlay_y
    )
    return "<span foreground='{}'>{}</span>".format(_hex(chosen), markup)

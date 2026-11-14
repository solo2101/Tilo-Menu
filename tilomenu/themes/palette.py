"""Theme-derived text contrast for application surfaces.

Sample the actual original PNG beneath the program list rather than inheriting
GTK desktop colors. Works for light and dark artwork without per-theme names.
"""
from gi.repository import GdkPixbuf


def program_colors(theme):
    path = theme.directory / theme.background
    try:
        pix = GdkPixbuf.Pixbuf.new_from_file(str(path))
        width, height = pix.get_width(), pix.get_height()
        channels, stride = pix.get_n_channels(), pix.get_rowstride()
        pixels = pix.get_pixels()
        region = theme.program_list
        x, y = region.integer("X"), region.integer("Y")
        w, h = region.integer("Width"), region.integer("Height")
        samples = []
        for fy in (0.15, 0.3, 0.5, 0.7, 0.85):
            for fx in (0.15, 0.3, 0.5, 0.7, 0.85):
                px, py = x + int(w * fx), y + int(h * fy)
                if not (0 <= px < width and 0 <= py < height):
                    continue
                offset = py * stride + px * channels
                r, g, b = pixels[offset:offset + 3]
                alpha = pixels[offset + 3] / 255 if channels == 4 else 1
                if alpha < 0.25:
                    continue
                samples.append((0.2126 * r + 0.7152 * g + 0.0722 * b, alpha))
        if samples:
            samples.sort()
            median = samples[len(samples) // 2][0]
            if median >= 135:
                return "#202020", "rgba(30, 70, 130, 0.15)"
    except (OSError, ValueError, TypeError):
        pass
    return "#f4f4f4", "rgba(90, 145, 210, 0.35)"

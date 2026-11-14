"""Draw GnoMenu application controls over the original artwork with Cairo.

GTK handles input, not the list's pixels. Appearance never inherits the MATE
GTK theme, keeping text legible after switching between light and dark styles.
"""
from gi.repository import Gdk, GdkPixbuf, Gtk, Pango, PangoCairo
from ..icons import load_icon


class ThemeAppList(Gtk.DrawingArea):
    ROW_HEIGHT = 32
    HEADER_HEIGHT = 30

    def __init__(self, theme, on_launch, on_category, on_favorite):
        super().__init__()
        self.theme = theme
        self.on_launch = on_launch
        self.on_category = on_category
        self.on_favorite = on_favorite
        self.rows = []
        self.favorites = set()
        self.category = "All Applications"
        self.show_categories = False
        self.offset = 0
        self.hover = -1
        self.icon_cache = {}
        self.set_size_request(theme.program_list.integer("Width"), theme.program_list.integer("Height"))
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.SCROLL_MASK
        )
        self.connect("draw", self._draw)
        self.connect("button-press-event", self._button_press)
        self.connect("motion-notify-event", self._motion)
        self.connect("leave-notify-event", self._leave)
        self.connect("scroll-event", self._scroll)
        self.background = None
        try:
            self.background = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(theme.directory / theme.background),
                theme.width, theme.height, False,
            )
        except Exception:
            pass

    def set_content(self, rows, category, show_categories, favorites):
        self.rows = list(rows)
        self.favorites = set(favorites)
        self.category = category
        self.show_categories = show_categories
        self.offset = 0
        self.hover = -1
        self.queue_draw()

    def _visible_count(self):
        height = self.get_allocated_height() or self.theme.program_list.integer("Height")
        return max(1, (height - self.HEADER_HEIGHT) // self.ROW_HEIGHT)

    def _max_offset(self):
        return max(0, len(self.rows) - self._visible_count())

    def _label(self, cr, value, x, y, max_width, light_text):
        layout = PangoCairo.create_layout(cr)
        layout.set_text(value, -1)
        layout.set_font_description(Pango.FontDescription("Sans 9"))
        layout.set_width(max(1, max_width) * Pango.SCALE)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        if light_text:
            cr.set_source_rgb(0.97, 0.97, 0.97)
        else:
            cr.set_source_rgb(0.09, 0.09, 0.09)
        cr.move_to(x, y)
        PangoCairo.show_layout(cr, layout)

    def _light_text_at(self, x, y):
        """Match each text row against its real background pixel."""
        if self.background is None:
            return True
        px = self.theme.program_list.integer("X") + x
        py = self.theme.program_list.integer("Y") + y
        pix = self.background
        if not (0 <= px < pix.get_width() and 0 <= py < pix.get_height()):
            return True
        channels = pix.get_n_channels()
        offset = py * pix.get_rowstride() + px * channels
        pixels = pix.get_pixels()
        r, g, b = pixels[offset:offset + 3]
        if channels == 4 and pixels[offset + 3] < 128:
            return True
        return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 140

    def _icon(self, app):
        key = app.get_id() or app.get_name()
        if key not in self.icon_cache:
            image = load_icon(app.get_icon(), 20)
            self.icon_cache[key] = image.get_pixbuf() if image else None
        return self.icon_cache[key]

    def _draw(self, _widget, cr):
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        cr.rectangle(0, 0, width, height)
        cr.clip()
        if self.background is not None:
            Gdk.cairo_set_source_pixbuf(
                cr, self.background,
                -self.theme.program_list.integer("X"),
                -self.theme.program_list.integer("Y"),
            )
            cr.paint()
        else:
            cr.set_source_rgb(0.15, 0.15, 0.15)
            cr.paint()

        self._label(cr, self.category + "  ▾", 8, 7, width - 16,
                    self._light_text_at(min(50, width // 2), 15))
        cr.save()
        cr.rectangle(0, self.HEADER_HEIGHT, width, max(0, height - self.HEADER_HEIGHT))
        cr.clip()
        count = self._visible_count()
        for index in range(self.offset, min(len(self.rows), self.offset + count + 1)):
            y = self.HEADER_HEIGHT + (index - self.offset) * self.ROW_HEIGHT
            if index == self.hover:
                cr.set_source_rgba(0.25, 0.47, 0.72, 0.24)
                cr.rectangle(0, y, width - 8, self.ROW_HEIGHT)
                cr.fill()
            light = self._light_text_at(min(55, width // 2), y + 15)
            item = self.rows[index]
            if self.show_categories:
                self._label(cr, item, 10, y + 7, width - 20, light)
                continue
            pixbuf = self._icon(item)
            if pixbuf is not None:
                Gdk.cairo_set_source_pixbuf(
                    cr, pixbuf, 7, y + (self.ROW_HEIGHT - pixbuf.get_height()) / 2
                )
                cr.paint()
            name = item.get_display_name() or item.get_name()
            self._label(cr, name, 34 if pixbuf is not None else 10, y + 7,
                        width - (47 if pixbuf is not None else 22), light)
        cr.restore()
        if len(self.rows) > count:
            track = max(1, height - self.HEADER_HEIGHT - 8)
            bar_h = max(16, track * count / len(self.rows))
            bar_y = self.HEADER_HEIGHT + 4 + (track - bar_h) * self.offset / max(1, self._max_offset())
            cr.set_source_rgba(0.4, 0.4, 0.4, 0.55)
            cr.rectangle(width - 6, bar_y, 4, bar_h)
            cr.fill()
        return False

    def _index_at(self, y):
        if y < self.HEADER_HEIGHT:
            return None
        index = self.offset + int((y - self.HEADER_HEIGHT) // self.ROW_HEIGHT)
        return index if 0 <= index < len(self.rows) else None

    def _button_press(self, _widget, event):
        if event.y < self.HEADER_HEIGHT:
            if event.button == 1:
                self.on_category(None, not self.show_categories)
                return True
            return False
        index = self._index_at(event.y)
        if index is None:
            return False
        item = self.rows[index]
        if event.button == 1:
            if self.show_categories:
                self.on_category(item, False)
            else:
                self.on_launch(item)
            return True
        if event.button == 3 and not self.show_categories and item.get_id():
            menu = Gtk.Menu()
            favorite = item.get_id() in self.favorites
            entry = Gtk.MenuItem(label="Remove from Favorites" if favorite else "Add to Favorites")
            entry.connect("activate", lambda _item: self.on_favorite(item))
            menu.append(entry)
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False

    def _motion(self, _widget, event):
        index = self._index_at(event.y)
        next_hover = index if index is not None else -1
        if next_hover != self.hover:
            self.hover = next_hover
            self.queue_draw()
        return False

    def _leave(self, _widget, _event):
        self.hover = -1
        self.queue_draw()
        return False

    def _scroll(self, _widget, event):
        step = 0
        if event.direction == Gdk.ScrollDirection.DOWN:
            step = 3
        elif event.direction == Gdk.ScrollDirection.UP:
            step = -3
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            valid, _dx, dy = event.get_scroll_deltas()
            if valid:
                step = 3 if dy > 0 else -3 if dy < 0 else 0
        self.offset = max(0, min(self._max_offset(), self.offset + step))
        self.queue_draw()
        return bool(step)

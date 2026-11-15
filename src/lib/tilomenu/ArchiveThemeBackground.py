"""Cairo background for archived GTK3 theme geometry.

Gtk.Image inside Gtk.Overlay can leave the old background in a composited
popup after a redraw. Paint directly from the loaded original PNG instead.
"""
import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk


class ArchiveThemeBackground(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self._pixbuf = None
        self.set_app_paintable(True)
        self.connect("draw", self._draw_background)

    def set_from_pixbuf(self, pixbuf):
        self._pixbuf = pixbuf
        if pixbuf is not None:
            self.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        self.queue_draw()

    def get_pixbuf(self):
        return self._pixbuf

    def _draw_background(self, widget, cr):
        if self._pixbuf is None:
            return False
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        Gdk.cairo_set_source_pixbuf(cr, self._pixbuf, 0, 0)
        cr.paint()
        cr.restore()
        return True

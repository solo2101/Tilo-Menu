#!/usr/bin/env python3
# Panel top translucent helper (GTK 3)

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

import os


class PanelTopWindow:
    def __init__(self):
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("")
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.set_keep_above(True)
        self.window.stick()
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)

        # events
        self.window.connect("draw", self._on_draw)
        self.window.connect("screen-changed", self._on_screen_changed)
        self.window.connect("destroy", self._on_destroy)

        # state
        self.scale = 1.0
        self.opacity = 0.0
        self.pixbuf = None
        self.w = 1
        self.h = 1

        self._on_screen_changed(self.window, None)

        self.window.resize(1, 1)
        self.window.show_all()
        self.window.hide()

    # visuals for transparency
    def _on_screen_changed(self, widget, _old_screen):
        screen = widget.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None:
            widget.set_visual(visual)
        self.window.set_keep_above(True)

    # paint
    def _on_draw(self, _widget, cr):
        # clear with transparent background
        cr.set_source_rgba(1, 1, 1, 0)
        cr.set_operator(gi.repository.cairo.OPERATOR_SOURCE)
        cr.paint()

        if self.pixbuf is not None:
            # scale if needed
            sw = max(1, int(self.w * self.scale))
            sh = max(1, int(self.h * self.scale))
            if self.pixbuf.get_width() != sw or self.pixbuf.get_height() != sh:
                pb = self._scaled_pixbuf(self.pixbuf_original, sw, sh)
                self.pixbuf = pb
            Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
            cr.set_operator(gi.repository.cairo.OPERATOR_OVER)
            cr.paint_with_alpha(1.0)
        return False

    def _scaled_pixbuf(self, pb, w, h):
        try:
            return pb.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
        except Exception:
            return pb

    # API parity
    def move(self, x, y):
        self.window.move(int(x), int(y))

    def destroy(self):
        self.window.destroy()

    def set_scale(self, scale):
        try:
            self.scale = float(scale)
        except Exception:
            self.scale = 1.0
        self.window.resize(max(1, int(self.w * self.scale)), max(1, int(self.h * self.scale)))
        self.window.queue_draw()

    def update(self):
        self._on_screen_changed(self.window, None)
        self.window.queue_draw()

    def updateimage(self, image_path):
        if not image_path or not os.path.isfile(image_path):
            return
        try:
            self.pixbuf_original = GdkPixbuf.Pixbuf.new_from_file(image_path)
            self.w = self.pixbuf_original.get_width()
            self.h = self.pixbuf_original.get_height()
            self.pixbuf = self._scaled_pixbuf(self.pixbuf_original, int(self.w * self.scale), int(self.h * self.scale))
            self.window.resize(max(1, int(self.w * self.scale)), max(1, int(self.h * self.scale)))
            self.window.queue_draw()
        except Exception:
            pass

    def get_height(self):
        if self.pixbuf is None:
            return 0
        return int(self.h * self.scale)

    # show / hide with simple fade
    def show_window(self):
        if not self.window.get_visible():
            self.window.show_all()
        self.window.set_opacity(0.0)
        self.opacity = 0.0
        GLib.timeout_add(30, self._fade_in_step)

    def _fade_in_step(self):
        self.opacity = min(1.0, self.opacity + 0.1)
        self.window.set_opacity(self.opacity)
        return self.opacity < 1.0

    def hide_window(self):
        self.window.hide()

    # legacy names kept
    def fade(self):
        return self._fade_in_step()

    def undestroy(self, *args, **kwargs):
        pass

    # destroy handler
    def _on_destroy(self, *_):
        pass

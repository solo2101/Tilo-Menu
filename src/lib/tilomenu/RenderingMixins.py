"""GTK3 rendering compatibility shared by the original GnoMenu widgets.

The theme PNG/XML and the original event handlers remain authoritative.
Adapted from the archived Tilo-Menu GTK3 renderer's transparent-window path.
"""
import cairo
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk


class ThemeWindowRenderingMixin:
    def configure_theme_window(self, window):
        # GTK3's default window CSS otherwise paints a rectangular desktop
        # theme background underneath transparent GnoMenu PNG artwork.
        screen = window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            window.set_visual(visual)
        window.set_app_paintable(True)
        window.set_resizable(False)
        window.get_style_context().add_class('tilomenu-original-window')
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            window.tilomenu-original-window,
            window.tilomenu-original-window:backdrop {
                background-color: transparent;
                background-image: none;
                box-shadow: none;
                border: 0;
            }
        """)
        window.get_style_context().add_provider(
            provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._original_window_css = provider

    def style_original_search(self, entry):
        # GTK3 focus borders and opaque entry backgrounds obscure the original
        # PNG search frame. Reuse the archived renderer's frameless GTK3 style.
        if not isinstance(entry, Gtk.Entry):
            return
        entry.set_has_frame(False)
        entry.get_style_context().add_class('tilomenu-original-search')
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            entry.tilomenu-original-search,
            entry.tilomenu-original-search:focus {
                background-color: transparent;
                background-image: none;
                box-shadow: none;
                border: 0;
                border-radius: 0;
                outline: none;
                padding: 0;
                margin: 0;
                min-width: 0;
                min-height: 0;
            }
        """)
        entry.get_style_context().add_provider(
            provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._original_search_css = provider

    def draw_original_theme(self, cr, background):
        # The original background pixbuf is already loaded by shape().
        # Paint only the window's allocation and keep its alpha channel.
        cr.save()
        cr.rectangle(0, 0, self.w, self.h)
        cr.clip()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        Gdk.cairo_set_source_pixbuf(cr, background, 0, 0)
        cr.paint()
        cr.restore()
        return False

"""Verify actual iTheme pixels remain aligned when the menu flips panels."""
from pathlib import Path
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import backend
import Globals
from Menu_Main import Main_Menu

# x=140,y=100 is an opaque artwork gutter, not a tab, image, field,
# application list or portrait overlay in either iTheme orientation.
x, y = 140, 100
try:
    backend.save_setting("Menu_Name", "iTheme")
    for direction in ("bottom", "top"):
        Globals.ReloadSettings(orientation_override=direction)
        menu = Main_Menu(lambda: None)
        try:
            menu.show_window()
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            for _ in range(3):
                menu.window.get_window().process_updates(True)
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)
            raw = menu.bgpb
            stride, n = raw.get_rowstride(), raw.get_n_channels()
            at = y * stride + x * n
            original = bytes(raw.get_pixels()[at:at+3])
            if n == 4:
                assert raw.get_pixels()[at+3] == 255, (
                    direction, "expected opaque source sample"
                )
            screenshot = Gdk.pixbuf_get_from_window(
                menu.window.get_window(), x, y, 1, 1)
            assert screenshot is not None, (direction, "missing rendered pixel")
            actual = bytes(screenshot.get_pixels()[:3])
            assert all(abs(int(a)-int(b)) <= 6 for a, b in zip(actual, original)), (
                direction, "GTK3 artwork overpaint or wrong flip", actual, original)
        finally:
            menu.window.destroy()
finally:
    backend.save_setting("Menu_Name", "Menu")
    Globals.ReloadSettings(orientation_override="bottom")
print("PASS: actual iTheme GTK3 pixels match source PNG at both panel edges")

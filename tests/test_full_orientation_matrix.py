"""Construct original GTK3 popup in both directions for every Menu theme.

Catches rendering integration failures the isolated drawing tests miss:
background flip, XDG list placement, search positioning, portrait crop,
and errors caused by switching theme and orientation repeatedly.
"""
from pathlib import Path
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import backend
import Globals
from Menu_Main import Main_Menu

root = Path(__file__).resolve().parents[1] / "src/share/tilomenu/Themes/Menu"
names = sorted(p.name for p in root.iterdir() if (p / "themedata.xml").is_file())
count = 0


def pixel(pixbuf, x, y):
    n = pixbuf.get_n_channels()
    i = y * pixbuf.get_rowstride() + x * n
    return bytes(pixbuf.get_pixels()[i:i+n])


try:
    for theme_name in names:
        backend.save_setting("Menu_Name", theme_name)
        for direction in ("bottom", "top"):
            Globals.ReloadSettings(orientation_override=direction)
            menu = Main_Menu(lambda: None)
            try:
                original = GdkPixbuf.Pixbuf.new_from_file(
                    Globals.ImageDirectory + Globals.StartMenuTemplate)
                expected = original.flip(False) if direction == "top" else original
                assert (menu.w, menu.h) == (
                    original.get_width(), original.get_height()), (
                    theme_name, direction, "popup size")
                for x, y in ((3, 3), (original.get_width() // 2,
                                       original.get_height() // 2),
                             (original.get_width() - 4, original.get_height() - 4)):
                    assert pixel(menu.bgpb, x, y) == pixel(expected, x, y), (
                        theme_name, direction, "background", x, y)

                assert menu.background.get_pixbuf() is menu.bgpb, (
                    theme_name, direction, "source artwork not shown")
                assert menu.menuframe.get_size_request() == (menu.w, menu.h)
                assert menu.PGL is not None
                if Globals.MenuHasIcon:
                    image = menu.usericon.backimagearea
                    x, y = Globals.UserIconFrameOffsetX, Globals.UserIconFrameOffsetY
                    # Portrait backdrop must match the currently selected
                    # orientation's background, without a second flip.
                    assert pixel(image, 0, 0) == pixel(expected, x, y), (
                        theme_name, direction, "portrait backdrop")
                if menu.has_search:
                    x = menu.menuframe.child_get_property(menu.SearchBar, "x")
                    y = menu.menuframe.child_get_property(menu.SearchBar, "y")
                    assert (x, y) == (Globals.SearchX, Globals.SearchY), (
                        theme_name, direction, "search position")
                count += 1
            finally:
                menu.window.destroy()
finally:
    backend.save_setting("Menu_Name", "Menu")
    Globals.ReloadSettings(orientation_override="bottom")
assert count == len(names) * 2, count
print(f"PASS: {count} real GTK3 popups across {len(names)} themes and both panel edges")

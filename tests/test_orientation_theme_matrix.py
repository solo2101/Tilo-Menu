"""Match original top/bottom panel rendering across every bundled Menu theme.

GnoMenu flips menu background and tab PNGs vertically on a top panel,
but retains upright text, icons and action-button artwork. Regression
tests must exercise switching top -> bottom -> top in one process:
cached images must never be modified by the earlier orientation.
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
from ArchiveThemeBridge import oriented_theme
from ArchiveThemeParser import load_menu_theme
from ArchiveThemeRenderer import render_theme_buttons, render_theme_details

root = Path(__file__).resolve().parents[1] / "src/share/tilomenu/Themes/Menu"
names = sorted(folder.name for folder in root.iterdir()
               if (folder / "themedata.xml").is_file())
checked = 0


def same_pixels(actual, expected, where):
    assert actual is not None, (where, "image missing")
    assert (actual.get_width(), actual.get_height()) == (
        expected.get_width(), expected.get_height()), (where, "image size changed")
    assert bytes(actual.get_pixels()) == bytes(expected.get_pixels()), (
        where, "original image orientation or artwork changed"
    )


try:
    for name in names:
        backend.save_setting("Menu_Name", name)
        for direction in ("bottom", "top", "bottom"):
            Globals.ReloadSettings(orientation_override=direction)
            theme = oriented_theme(load_menu_theme(Globals.ImageDirectory))
            assert theme.flipped == (direction == "top"), (name, direction)
            frame = Gtk.Fixed()
            frame.set_size_request(theme.width, theme.height)
            buttons = render_theme_buttons(frame, theme)
            states, tabs = render_theme_details(frame, theme)

            assert len(buttons) == Globals.MenuButtonCount, (name, direction)
            assert len(tabs) == Globals.MenuTabCount, (name, direction)
            for i, button in enumerate(buttons):
                if button is not None:
                    assert frame.child_get_property(button, "y") == Globals.MenuButtonY[i], (
                        name, direction, "button", i
                    )
            for i, tab in enumerate(tabs):
                if tab is None:
                    continue
                attrs = theme.tabs[i].attributes
                assert frame.child_get_property(tab, "y") == Globals.MenuTabY[i], (
                    name, direction, "tab", i
                )
                # Switch both tab states. Original MenuTab.Setimage()
                # reverses only the PNG pixels when the panel is on top.
                picture = next(child for child in tab.get_child().get_children()
                               if isinstance(child, Gtk.Image))
                name_of_tab = attrs.get("Name", "")
                for active in (True, False, True):
                    states[name_of_tab](active)
                    image_name = (attrs.get("ImageSel") or attrs.get("Image")
                                  if active else attrs.get("Image"))
                    observed = picture.get_pixbuf()
                    if not image_name:
                        assert observed is None, (
                            name, direction, name_of_tab, active, "expected no image"
                        )
                        continue
                    source = GdkPixbuf.Pixbuf.new_from_file(
                        str(theme.directory / image_name))
                    expected = source.flip(False) if direction == "top" else source
                    same_pixels(observed, expected,
                                (name, direction, name_of_tab, active))
                checked += 1

    assert len(names) >= 15, names
    assert checked >= 30, checked
finally:
    backend.save_setting("Menu_Name", "Menu")
    Globals.ReloadSettings(orientation_override="bottom")
print(f"PASS: {checked} tab artwork checks and positions across "
      f"{len(names)} themes, including top/bottom/top switching")

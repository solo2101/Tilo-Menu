"""Verify original top/bottom flip behavior with archived renderer."""
from pathlib import Path
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import Globals
from Menu_Main import Main_Menu
from ArchiveThemeBridge import oriented_theme
from ArchiveThemeParser import load_menu_theme

def pixels(pix, x, y):
    idx = y * pix.get_rowstride() + x * pix.get_n_channels()
    data = pix.get_pixels()
    return bytes(data[idx:idx + pix.get_n_channels()])

try:
    for direction in ('bottom', 'top'):
        Globals.ReloadSettings(orientation_override=direction)
        menu = Main_Menu(lambda: None)
        theme = oriented_theme(load_menu_theme(Globals.ImageDirectory))
        expected = Globals.orientation
        assert expected == direction
        assert tuple(int(v) for v in Globals.PG_buttonframe) == (
            theme.program_list.integer('X'),
            theme.height - theme.program_list.integer('Y')
            - theme.program_list.integer('Height')
            if direction == 'top' else theme.program_list.integer('Y'),
        )
        for i, button in enumerate(menu.MenuButtons):
            if button is None:
                continue
            x, y = (menu.menuframe.child_get_property(button.Button, 'x'), menu.menuframe.child_get_property(button.Button, 'y'))
            assert (x, y) == (Globals.MenuButtonX[i], Globals.MenuButtonY[i]), (
                direction, 'button', i, x, y)
        for i, tab in enumerate(menu.MenuTabs):
            if tab is None:
                continue
            x, y = (menu.menuframe.child_get_property(tab.Tab, 'x'), menu.menuframe.child_get_property(tab.Tab, 'y'))
            assert (x, y) == (Globals.MenuTabX[i], Globals.MenuTabY[i]), (
                direction, 'tab', i, x, y)
        if menu.has_search:
            x, y = (menu.menuframe.child_get_property(menu.SearchBar, 'x'), menu.menuframe.child_get_property(menu.SearchBar, 'y'))
            assert (x, y) == (Globals.SearchX, Globals.SearchY), direction
        original = GdkPixbuf.Pixbuf.new_from_file(
            Globals.ImageDirectory + Globals.StartMenuTemplate)
        x = min(10, original.get_width() - 1)
        y = min(20, original.get_height() - 1)
        expected_y = original.get_height() - y - 1 if direction == 'top' else y
        assert pixels(menu.bgpb, x, y) == pixels(original, x, expected_y), (
            direction, 'original PNG vertical flip')
        menu.window.destroy()
    print('PASS: original GnoMenu vertical flip and XML widget positions for both panel edges')
finally:
    Globals.ReloadSettings(orientation_override='bottom')

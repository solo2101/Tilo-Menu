"""Regression checks for archived GTK3 chrome over original theme assets."""
import sys
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
from ArchivedThemeChrome import transparent_chrome, legible_markup
from Menu_Main import Main_Menu
import Globals


button = Gtk.EventBox()
frame = Gtk.Fixed()
transparent_chrome(button, frame)
assert not button.get_style_context().has_class('theme-button')
assert button.get_style_context().has_class('tilomenu-original-chrome')
assert frame.get_style_context().has_class('tilomenu-original-chrome')

pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 60, 35)
pixbuf.fill(0xffffffff)
white = "<span foreground='#FFFFFF' font_desc='sans 8'>Test</span>"
fixed = legible_markup(white, pixbuf, 4, 4, 40)
assert '#FFFFFF' not in fixed, fixed
assert 'font_desc=' in fixed, fixed
pixbuf.fill(0x101010ff)
assert legible_markup(white, pixbuf, 4, 4, 40) == white

menu = Main_Menu(lambda: None)
assert menu.menuframe.get_style_context().has_class('tilomenu-original-chrome')
assert all(tab.Tab.get_style_context().has_class('tilomenu-original-chrome')
           for tab in menu.MenuTabs)
for item in menu.MenuButtons:
    if hasattr(item, 'Button'):
        assert not item.Button.get_visible_window()
        assert item.Button.get_style_context().has_class('tilomenu-original-chrome')
assert menu.window.get_opacity() == 1.0
# The screenshot uses a light, graphic-heavy theme. Check its authored
# widget geometry as well as the default dark Menu theme.
import backend
backend.save_setting('Menu_Name', 'Vista')
Globals.ReloadSettings()
vista = Main_Menu(lambda: None)
assert vista.MenuButtons
assert vista.menuframe.get_size_request() == (
    Globals.MenuWidth, Globals.MenuHeight)
assert all(button.Button.get_style_context().has_class('tilomenu-original-chrome')
           for button in vista.MenuButtons if hasattr(button, 'Button'))
print('PASS: default and Vista theme rendering geometry under GTK3')

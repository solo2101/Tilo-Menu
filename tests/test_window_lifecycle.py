"""Exercise the original Main_Menu window without replacing its renderer.

A real Xvfb/GTK3 test, beyond merely importing the legacy class modules.
"""
import sys
from pathlib import Path
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import Globals
from Menu_Main import Main_Menu

closed = []
def hide():
    closed.append(True)
    menu.hide_window()

menu = Main_Menu(hide)
assert menu.window is not None
assert menu.window.get_style_context().has_class('tilomenu-original-window')
if menu.has_search:
    from ArchiveThemeSearch import ThemeSearch
    assert isinstance(menu.SearchBar, ThemeSearch)
    assert menu.SearchBar.entry.get_style_context().has_class('tilo-search-input')
assert menu.PGL is not None
assert menu.MenuTabs, 'Original theme tab widgets were not constructed'
assert all(not tab.Tab.get_visible_window() for tab in menu.MenuTabs), (
    'GTK3 EventBox must not paint opaque rectangles over original tab art')
assert menu.menuframe.get_size_request() == (Globals.MenuWidth, Globals.MenuHeight)
assert menu.window.get_size_request() == (Globals.MenuWidth, Globals.MenuHeight)
menu.show_window()
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
assert menu.window.get_visible()
allocation = menu.menuframe.get_allocation()
assert allocation.width >= Globals.MenuWidth, (allocation.width, Globals.MenuWidth)
assert allocation.height >= Globals.MenuHeight, (allocation.height, Globals.MenuHeight)
menu.hide_window()
assert not menu.window.get_visible()
# Allow the process to exit without gtk_main_quit on a non-running main loop.
print("PASS: original Main_Menu constructor/show/hide under GTK3")

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
if Globals.MenuHasSearch and Globals.SearchWidget.upper() == 'GTK':
    assert menu.SearchBar.get_style_context().has_class('tilomenu-original-search')
assert menu.PGL is not None
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

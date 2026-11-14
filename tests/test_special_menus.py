"""Exercise the original GnoMenu special page and Back opcode behavior.

No new navigation engine. Calls original XDGMenu.CallSpecialMenu through
the original IconProgramList widget, exactly as Menu_Main.Tab_click does.
"""
import sys
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import Globals
from Menu_Main import Main_Menu

Globals.Settings['Prog_List'] = 3
menu = Main_Menu(lambda: None)
menu.show_window()
widget = menu.PGL
xdg = widget.XDG
for code, label in (
    (1, "Applications"), (2, "Recent Applications"),
    (3, "Auxiliary"), (4, "Recent Items"), (7, "Favorites"),
    (8, "Places"), (9, "Shutdown"), (10, "Web Bookmarks"),
):
    widget.CallSpecialMenu(code)
    assert isinstance(xdg.L_Names, list), label
    print('PASS: original special page', label, len(xdg.L_Names))
    widget.CallSpecialMenu(0)
    assert isinstance(xdg.L_Names, list)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
widget.CallSpecialMenu(5, "tilo")
widget.CallSpecialMenu(5, "")
print('PASS: original search and Back navigation')

# Test the original four-field "::" favorites format through the original
# XDGMenu.addfav/removefav methods, without an external notification daemon.
import backend
xdg.notifier.notify = lambda *args, **kwargs: None
xdg.addfav(None, None, "Test Favorite", "/usr/bin/true",
           "application-x-executable", 1)
fav = "Test Favorite::/usr/bin/true::application-x-executable::1"
assert fav in backend.load_setting('favorites')
xdg.Restart('favorites')
assert "Test Favorite" in xdg.L_Names
xdg.removefav(None, None, "Test Favorite", "/usr/bin/true",
              "application-x-executable", 1)
assert fav not in backend.load_setting('favorites')
print('PASS: original add/remove Favorites and GSettings persistence')

menu.hide_window()
# Allow the process to exit without gtk_main_quit on a non-running main loop.

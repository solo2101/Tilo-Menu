"""Exercise the original Main_Menu window without replacing its renderer.

A real Xvfb/GTK3 test, beyond merely importing the legacy class modules.
"""
import sys
from pathlib import Path
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
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
# The original theme artwork must be a visible GTK child below the archived
# chrome. Window-only painting is not sufficient with GTK3 Fixed children.
assert menu.background.get_pixbuf() is not None, 'Missing background PNG'
assert menu.background.get_pixbuf().get_width() == Globals.MenuWidth
assert menu.background.get_pixbuf().get_height() == Globals.MenuHeight
children = menu.menuframe.get_children()
assert children[0] is menu.background, 'Theme PNG must paint under button chrome'
if Globals.MenuHasIcon:
    # The portrait's original backdrop must come from its XML coordinates,
    # even when the panel asks the popup to open upward.
    x, y = Globals.UserIconFrameOffsetX, Globals.UserIconFrameOffsetY
    original = menu.bgpb
    excerpt = menu.usericon.backimagearea
    stride = original.get_rowstride()
    channels = original.get_n_channels()
    index = y * stride + x * channels
    assert bytes(excerpt.get_pixels()[:channels]) == bytes(
        original.get_pixels()[index:index + channels])


# Flip direction chooses above/below the actual panel while preserving
# original XML art (no upside-down labels).
from unittest.mock import patch
from gi.repository import Gdk
rect = Gdk.Rectangle()
rect.x, rect.y, rect.width, rect.height = 0, 0, 1600, 900
with patch.object(menu.window, 'move') as moved, \
     patch.object(menu.window.get_screen(), 'get_monitor_geometry', return_value=rect):
    with patch.dict('os.environ', {'TILOMENU_MENU_DIRECTION': 'down'}):
        menu.Adjust_Window_Dimensions(16, 0, 30)
        assert moved.call_args.args == (16, 30)
    with patch.dict('os.environ', {'TILOMENU_MENU_DIRECTION': 'up'}):
        menu.Adjust_Window_Dimensions(16, 890, 30)
        assert moved.call_args.args == (16, 890 - Globals.MenuHeight)

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

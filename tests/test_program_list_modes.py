"""Render original GnoMenu 2.9.1 selectable program-list modes.

Modes 0..4 are original classes from Menu_Widgets, not the archived recreation.
"""
import sys
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import Globals
from Menu_Main import Main_Menu

mode = int(sys.argv[1])
Globals.Settings['Prog_List'] = mode
menu = Main_Menu(lambda: None)
menu.show_window()
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
assert menu.window.get_visible()
assert menu.PGL is not None
if mode == 3:
    from ArchivedCairoProgramList import ArchivedCairoProgramList
    assert isinstance(menu.PGL, ArchivedCairoProgramList)
    assert menu.PGL.view.get_size_request() == Globals.PG_buttonframedimensions
    assert not hasattr(menu.PGL, 'ScrollFrame'), 'Horizontal scrollbar still installed'
    assert menu.PGL._max_offset() >= 0
    assert menu.PGL._visible_count() > 0
    assert menu.PGL.XDG.L_Names, 'Applications list is empty'
    menu.PGL._scroll(None, type('Wheel', (), {'direction': 1})())
    assert menu.PGL.offset >= 0
if mode == 0:
    # The initial Favorites list is often empty. Applications exposes
    # the width regression because it has icons and longer names.
    menu.PGL.CallSpecialMenu(1)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    assert menu.PGL.EBox.get_size_request() == Globals.PG_buttonframedimensions
    scroll_width, scroll_height = menu.PGL.ScrollFrame.get_size_request()
    theme_width, theme_height = Globals.PG_buttonframedimensions
    assert scroll_width == theme_width
    assert 0 < scroll_height <= theme_height
    viewport = menu.PGL.EBox.get_allocation()
    assert viewport.width <= theme_width + 2, (
        f'list overflow: actual={viewport.width} expected={theme_width}')
    scroll_allocation = menu.PGL.ScrollFrame.get_allocation()
    assert scroll_allocation.width <= theme_width + 2, (
        f'scroll overflow: actual={scroll_allocation.width} expected={theme_width}')
if mode == 3:
    import cairo
    canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, *Globals.PG_buttonframedimensions)
    assert menu.PGL._draw(menu.PGL.view, cairo.Context(canvas)) is False
    menu.PGL._leave(None, None)
    assert menu.PGL.hover == -1
menu.hide_window()
# Allow the process to exit without gtk_main_quit on a non-running main loop.
print(f'PASS: original Prog_List={mode} using {type(menu.PGL).__name__}')

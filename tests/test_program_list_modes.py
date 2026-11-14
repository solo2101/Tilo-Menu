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
menu.hide_window()
menu.window.destroy()
print(f'PASS: original Prog_List={mode} using {type(menu.PGL).__name__}')

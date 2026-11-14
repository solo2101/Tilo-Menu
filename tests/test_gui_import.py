"""Import original GnoMenu GTK3-port modules under a temporary X server.

This checks loading the unchanged XML and original application/widget classes.
It does not claim the popup works until the original GTK2 drawing is ported.
"""
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src/lib/tilomenu"))
import Globals
assert Globals.MenuWidth > 0, Globals.MenuWidth
assert Globals.MenuHeight > 0, Globals.MenuHeight
assert len(Globals.StartButton) == 3
print("PASS: original theme loader, window geometry, button images")
import Menu_Widgets
assert hasattr(Menu_Widgets, "MenuButton")
assert hasattr(Menu_Widgets, "CairoProgramList")
import Menu_Main
assert hasattr(Menu_Main, "Main_Menu")
import MenuParser
assert hasattr(MenuParser, "MenuParser")
print("PASS: original GTK3 menu classes import and GTK GObject registrations")

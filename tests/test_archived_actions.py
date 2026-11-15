"""Check archived GTK3 artwork still forwards original menu commands."""
import sys
from pathlib import Path
from unittest.mock import patch

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import backend
import Globals
from Menu_Main import Main_Menu
from ArchiveThemeBridge import ButtonAdapter, TabAdapter


# Vista contains ordinary buttons, separators and no tabs. Its actions must
# keep their original indexes after changing the rendering engine.
backend.save_setting('Menu_Name', 'Vista')
Globals.ReloadSettings()
menu = Main_Menu(lambda: None)
assert len(menu.MenuButtons) == Globals.MenuButtonCount
index = next(i for i, item in enumerate(menu.MenuButtons)
             if isinstance(item, ButtonAdapter)
             and Globals.MenuButtonNames[i] == 'Documents')
assert menu.MenuButtons[index].Button is not None
# The original Main_Menu invokes Setimage/SetBackground on pointer enter/leave.
# Confirm they now redraw the actual archived GTK3 button, not a no-op.
images = [child for child in menu.MenuButtons[index].Button.get_child().get_children()
          if isinstance(child, Gtk.Image)]
foreground = next(image for image in images if image.get_pixbuf() is None)
menu.MenuButtons[index].Setimage(Globals.MenuButtonImage[index])
assert foreground.get_pixbuf() is not None, 'Original hover image not painted'
menu.MenuButtons[index].SetBackground()
assert foreground.get_pixbuf() is None, 'Normal button state not restored'
assert Globals.MenuButtonSub[index] == 0
with patch.object(menu.Launcher, 'Launch') as launch, \
     patch.object(menu, 'PlaySound'):
    menu.Button_click(None, None, index)
    launch.assert_called_once_with(Globals.MenuButtonCommands[index])
with patch.object(menu.Launcher, 'Launch') as launch, \
     patch.object(menu, 'PlaySound'):
    event = Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE)
    event.button = 1
    menu.MenuButtons[index].Button.emit('button-release-event', event)
    launch.assert_called_once_with(Globals.MenuButtonCommands[index])

# The default theme has tabs; keep its original page/navigation indexes.
backend.save_setting('Menu_Name', 'Menu')
Globals.ReloadSettings()
menu2 = Main_Menu(lambda: None)
assert len(menu2.MenuTabs) == Globals.MenuTabCount
assert all(isinstance(tab, TabAdapter) for tab in menu2.MenuTabs if tab is not None)
if menu2.MenuTabs:
    menu2.MenuTabs[0].SetSelectedTab(True)
    assert menu2.MenuTabs[0].GetSelectedTab()
print('PASS: archived chrome forwards original menu commands and tab state')

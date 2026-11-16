"""Verify GTK3 event-box wiring for real original theme buttons and tabs.

These tests emit button-release GDK events on the rendered widgets rather
than calling Main_Menu.Button_click/Tab_click directly.
"""
from pathlib import Path
from unittest.mock import patch
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import backend
import Globals
from Menu_Main import Main_Menu

root = Path(__file__).resolve().parents[1] / 'src/share/tilomenu/Themes/Menu'
names = sorted(p.name for p in root.iterdir() if (p / 'themedata.xml').is_file())
total = 0

try:
    for name in names:
        backend.save_setting('Menu_Name', name)
        Globals.ReloadSettings(orientation_override='bottom')
        menu = Main_Menu(lambda: None)
        try:
            button_event = Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE)
            button_event.button = 1
            right_event = Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE)
            right_event.button = 3
            with patch.object(menu.Launcher, 'Launch') as launch, \
                 patch.object(menu.PGL, 'CallSpecialMenu') as special, \
                 patch.object(menu, 'PlaySound'):
                buttons = [
                    (i, widget) for i, widget in enumerate(menu.MenuButtons)
                    if widget is not None and
                    Globals.MenuButtonNames[i] != ':SEPARATOR:' and
                    Globals.MenuButtonCommands[i] != ':ALLAPPS:'
                ]
                if buttons:
                    i, widget = buttons[0]
                    widget.Button.emit('button-release-event', button_event)
                    if Globals.MenuButtonSub[i]:
                        special.assert_called_with(int(Globals.MenuButtonCommands[i]))
                    else:
                        launch.assert_called_with(Globals.MenuButtonCommands[i])
                    total += 1
                    launch.reset_mock()
                    special.reset_mock()
                    widget.Button.emit('button-release-event', right_event)
                    launch.assert_not_called()
                    special.assert_not_called()

                if menu.MenuTabs:
                    i = next(i for i, widget in enumerate(menu.MenuTabs)
                             if widget is not None)
                    tab = menu.MenuTabs[i]
                    tab.Tab.emit('button-release-event', button_event)
                    if Globals.MenuTabSub[i]:
                        special.assert_called_with(int(Globals.MenuTabCommands[i]))
                    else:
                        launch.assert_called_with(Globals.MenuTabCommands[i])
                    total += 1
        finally:
            menu.window.destroy()
finally:
    backend.save_setting('Menu_Name', 'Menu')
    Globals.ReloadSettings(orientation_override='bottom')

assert len(names) == 15 and total >= 15, (len(names), total)
print(f'PASS: {total} original theme button/tab GDK signal connections across 15 themes')

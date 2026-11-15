"""Exercise original menu actions for all 15 bundled themes, without executing commands."""
from pathlib import Path
import sys
from unittest.mock import patch

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import backend
import Globals
from Menu_Main import Main_Menu

folders = Path(__file__).resolve().parents[1] / 'src/share/tilomenu/Themes/Menu'
themes = sorted(folder.name for folder in folders.iterdir()
                if (folder / 'themedata.xml').is_file())
count = 0
for theme in themes:
    backend.save_setting('Menu_Name', theme)
    Globals.ReloadSettings(orientation_override='bottom')
    menu = Main_Menu(lambda: None)
    with patch.object(menu.Launcher, 'Launch') as launch, \
         patch.object(menu.PGL, 'CallSpecialMenu') as special, \
         patch.object(menu, 'PlaySound'):
        for i, button in enumerate(menu.MenuButtons):
            if button is None or Globals.MenuButtonNames[i] == ':SEPARATOR:':
                continue
            menu.Button_click(None, None, i)
            if Globals.MenuButtonSub[i] == 0:
                launch.assert_any_call(Globals.MenuButtonCommands[i])
            else:
                special.assert_any_call(int(Globals.MenuButtonCommands[i]))
            count += 1
        for i, tab in enumerate(menu.MenuTabs):
            if tab is None:
                continue
            menu.Tab_click(None, None, i)
            assert tab.GetSelectedTab(), (theme, i)
            if Globals.MenuTabSub[i] == 0:
                launch.assert_any_call(Globals.MenuTabCommands[i])
            else:
                special.assert_any_call(int(Globals.MenuTabCommands[i]))
            count += 1
    menu.window.destroy()
assert len(themes) == 15, themes
assert count >= 70, count
print(f'PASS: {count} original theme buttons and tabs route commands across {len(themes)} themes')

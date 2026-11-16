"""Exercise actual original XDG navigation for every theme submenu button/tab.

Unlike the action-dispatch mock tests, this asserts that page opcodes
produce the intended original XDGMenu page. External programs are not run.
"""
from pathlib import Path
import sys
from unittest.mock import patch

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import backend
import Globals
from Menu_Main import Main_Menu

root = Path(__file__).resolve().parents[1] / "src/share/tilomenu/Themes/Menu"
names = sorted(path.name for path in root.iterdir()
               if (path / "themedata.xml").is_file())
pages = {
    2: "<RecentApps>", 3: "<AuxiliaryFunctions>",
    4: "<RecentItems>", 7: "<Favorites>", 8: "<Bookmarks>",
    9: "<Shutdown>", 10: "<WebBookmarks>",
}
total = 0
try:
    for name in names:
        backend.save_setting("Menu_Name", name)
        Globals.ReloadSettings(orientation_override="bottom")
        menu = Main_Menu(lambda: None)
        try:
            with patch.object(menu, "PlaySound"):
                for kind, widgets, names_list, commands, subs in (
                    ("Button", menu.MenuButtons, Globals.MenuButtonNames,
                     Globals.MenuButtonCommands, Globals.MenuButtonSub),
                    ("Tab", menu.MenuTabs, Globals.MenuTabNames,
                     Globals.MenuTabCommands, Globals.MenuTabSub),
                ):
                    for i, widget in enumerate(widgets):
                        if widget is None or names_list[i] == ":SEPARATOR:" or subs[i] != 1:
                            continue
                        opcode = int(commands[i])
                        # Return to the base page before each independent action.
                        menu.PGL.CallSpecialMenu(1)
                        if kind == "Button":
                            menu.Button_click(None, None, i)
                        else:
                            menu.Tab_click(None, None, i)
                        xdg = menu.PGL.XDG
                        if opcode == 1:
                            assert xdg.Menu == xdg.menuparser.CacheApplications, (
                                name, kind, names_list[i], opcode
                            )
                        elif opcode in pages:
                            assert xdg.Menu == pages[opcode], (
                                name, kind, names_list[i], opcode, xdg.Menu
                            )
                        assert isinstance(xdg.L_Names, list), (name, kind, opcode)
                        total += 1
        finally:
            menu.window.destroy()
finally:
    backend.save_setting("Menu_Name", "Menu")
    Globals.ReloadSettings(orientation_override="bottom")

assert len(names) == 15 and total >= 45, (len(names), total)
print(f"PASS: {total} real XDG navigation actions across {len(names)} themes")

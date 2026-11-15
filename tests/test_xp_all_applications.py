"""XP All Applications must switch the original XDG list without closing the menu."""
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

for theme in ('XP', 'SilverXP'):
    backend.save_setting('Menu_Name', theme)
    Globals.ReloadSettings(orientation_override='bottom')
    closed = []
    menu = Main_Menu(lambda: closed.append(True))
    index = Globals.MenuButtonCommands.index(':ALLAPPS:')
    assert Globals.MenuButtonClose[index] == 1, theme
    assert Globals.OnlyShowFavs == 1, theme
    assert menu.PGL.XDG.Menu == '<Favorites>', theme

    # Run the original XML action through Launcher and its special-command
    # signal, rather than mocking away the broken Gnome_Me code path.
    with patch.object(menu, 'PlaySound'):
        menu.Button_click(None, None, index)
        assert not closed, f'{theme}: popup closed when opening all applications'
        assert menu.PGL.XDG.Menu == menu.PGL.XDG.menuparser.CacheApplications, theme
        assert menu.PGL.XDG.Menu != '<Favorites>', theme
        assert Globals.OnlyShowFavs == 1, f'{theme}: changed global theme behavior'
        assert menu.PGL.XDG.L_Names, f'{theme}: no applications populated'
    menu.window.destroy()
print('PASS: XP and SilverXP All Applications routes original XDG list without dismissing popup')

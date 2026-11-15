"""Search typing and GLib debounce through the original menu controller."""
import sys
from pathlib import Path
from unittest.mock import patch

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import backend
import Globals
from Menu_Main import Main_Menu

backend.save_setting('Menu_Name', 'Menu')
Globals.ReloadSettings()
menu = Main_Menu(lambda: None)
assert menu.has_search
with patch.object(menu.PGL, 'CallSpecialMenu') as navigate:
    menu.SearchBar.set_text('term')
    assert menu.searchitem == 'term'
    assert menu.callback_search is not None
    menu.SearchBar.set_text('terminal')
    assert menu.searchitem == 'terminal'
    assert menu.callback_search is not None
    menu.timeout_callback_search()
    navigate.assert_called_once_with(5, 'terminal')
    assert menu.callback_search is None
    menu.SearchBar.set_text('')
    menu.timeout_callback_search()
    assert navigate.call_args.args == (5, '')
print('PASS: live original application search, clearing and GLib debounce')

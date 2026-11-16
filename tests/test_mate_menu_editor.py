"""Exercise the original panel Edit Menus action with MATE's Mozo editor."""
from pathlib import Path
import sys
from unittest.mock import patch

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('MatePanelApplet', '4.0')

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import TiloMenu
import Globals

panel = TiloMenu.TiloMenu.__new__(TiloMenu.TiloMenu)
with patch('TiloMenu.shutil.which', side_effect=lambda program:
           '/usr/bin/' + program if program == 'mozo' else None), \
     patch.dict(Globals.Settings, {'MenuEditor': 'alacarte'}), \
     patch('TiloMenu.subprocess.Popen') as launch:
    assert panel._menu_editor_command() == ['mozo']
    panel.edit_menus(None)
    launch.assert_called_once_with(['mozo'], start_new_session=True)

with patch('TiloMenu.shutil.which', return_value=None), \
     patch('TiloMenu.subprocess.Popen') as launch:
    assert panel._menu_editor_command() is None
    panel.edit_menus(None)
    launch.assert_not_called()

with patch('TiloMenu.shutil.which', return_value='/usr/bin/custom-editor'), \
     patch.dict(Globals.Settings, {'MenuEditor': 'custom-editor --original'}):
    assert panel._menu_editor_command() == ['custom-editor', '--original']

print('PASS: original Edit Menus action launches Mozo, preserves custom editors, skips missing programs')

"""Exercise the original GnoMenu panel button connected to Main_Menu.

The source applet is hosted in a plain Gtk.EventBox, as with the original
'run-in-window' test mode, avoiding changes to the original popup widgets.
"""
import sys
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('MatePanelApplet', '4.0')
from gi.repository import Gtk, MatePanelApplet

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
from TiloMenu import TiloMenu
import Globals

# Production panel activation must use the same BLAS-limited entry point as
# the working standalone launcher, not import TiloMenu.py directly.
root = Path(__file__).resolve().parents[1]
metadata = (root / 'src/lib/mate-panel/applets/org.mate.panel.TiloMenu.mate-panel-applet').read_text()
service = (root / 'src/share/dbus-1/services/org.mate.panel.applet.TiloMenuFactory.service').read_text()
launcher = (root / 'src/bin/TiloMenu.py').read_text()
assert 'Location=/usr/bin/tilomenu' in metadata
assert 'Exec=/usr/bin/tilomenu' in service
assert "OPENBLAS_NUM_THREADS" in launcher

class Sandpit(Gtk.EventBox):
    def get_orient(self):
        return 1

    def get_size(self):
        return 32

    def setup_menu(self, xml, action_group):
        self.actions = action_group
        self.menu_xml = xml

host = Gtk.Window(title="TiloMenu original panel test")
host.set_default_size(200, 80)
applet = Sandpit()
menu = TiloMenu(applet, '')
host.add(applet)
host.show_all()
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
assert menu.hwg is not None, "Original Main_Menu was not attached on map"
assert menu.hwg.window is not None
assert applet.actions.get_action('Props').get_sensitive()
assert applet.actions.get_action('About').get_sensitive()
# The original MATE context-menu Preferences/About actions launch
# the original Settings script. Verify the arguments, do not spawn it.
from unittest.mock import patch
with patch('TiloMenu.subprocess.Popen') as launch:
    applet.actions.get_action('Props').activate()
    assert launch.called
    assert launch.call_args.args[0][1].endswith('TiloMenu-Settings.py')
with patch('TiloMenu.subprocess.Popen') as launch:
    applet.actions.get_action('About').activate()
    assert launch.called
    assert launch.call_args.args[0][-1] == '--about'
# Simulate a new Button theme saved by the separate Preferences process.
# The MATE panel must update its own image without recreating the applet.
from unittest.mock import patch as mock_patch
with mock_patch('TiloMenu.backend.load_setting', return_value='TestButton'), \
     mock_patch('TiloMenu.start_button_images',
                return_value=('first.png', 'hover.png', 'pressed.png')), \
     mock_patch('TiloMenu.GdkPixbuf.Pixbuf.get_file_info',
                return_value=('png', 16, 16)), \
     mock_patch.object(menu, 'Redraw_graphics') as redraw:
    assert menu._refresh_button_theme() is False
    assert menu._button_theme == 'TestButton'
    assert menu.StartButton == ('first.png', 'hover.png', 'pressed.png')
    redraw.assert_called_once()
    # Repeated GSettings writes should not need another redraw.
    assert menu._refresh_button_theme() is False
    redraw.assert_called_once()
# Restore original button assets for popup tests below.
menu.StartButton = Globals.StartButton
menu._button_theme = str(Globals.Settings['Button_Name'])
print('PASS: original panel right-click Preferences/About actions')

from types import SimpleNamespace
# Exercise the original button_press flow, not only the popup helpers.
menu.button_press(applet, SimpleNamespace(button=1))
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
assert menu.hwg.window.get_visible(), "Original left-click did not open the popup"
assert menu.Button_state == 2
menu.button_press(applet, SimpleNamespace(button=1))
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
assert not menu.hwg.window.get_visible(), "Original second left-click did not close the popup"
assert menu.Button_state == 1
menu.HideMenu()
assert menu.Button_state == 0

# The original Preferences process writes Menu_Name to GSettings. Applying a
# different menu theme must rebuild the popup without destroying this applet.
old_popup = menu.hwg
original_load = __import__('backend').load_setting
target = 'Vista' if Globals.Settings['Menu_Name'] != 'Vista' else 'Menu'
def changed_setting(key):
    if key == 'Menu_Name':
        return target
    return original_load(key)

with patch('TiloMenu.backend.load_setting', side_effect=changed_setting):
    assert menu._refresh_menu_theme() is False
assert menu.hwg is not old_popup, 'Applying a new theme kept the old popup'
assert menu.hwg.window is not None
assert menu._menu_signature[0] == target
assert menu.applet.get_parent() is host
print('PASS: original menu theme rebuild preserves the MATE panel applet')
host.destroy()
print('PASS: original panel button opens/closes original Main_Menu and exposes Settings')

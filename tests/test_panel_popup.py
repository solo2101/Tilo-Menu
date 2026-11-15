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
host.destroy()
print('PASS: original panel button opens/closes original Main_Menu and exposes Settings')

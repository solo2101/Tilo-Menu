"""Exercise the original launcher with GTK3-era .desktop Exec conventions."""
import sys
from pathlib import Path
from unittest.mock import patch

import gi
gi.require_version('Gtk', '3.0')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
from Launcher import Launcher

launcher = Launcher()
with patch('Launcher.subprocess.Popen') as spawn:
    launcher.Launch('"/opt/Sample Program/bin/app" --title "two words" %f %U', 1)
    spawn.assert_called_once_with(
        ['/opt/Sample Program/bin/app', '--title', 'two words'],
        start_new_session=True)
with patch('Launcher.subprocess.Popen') as spawn:
    launcher.Launch('/usr/bin/true --name "A B"', 1)
    spawn.assert_called_once_with(
        ['/usr/bin/true', '--name', 'A B'], start_new_session=True)
with patch('Launcher.subprocess.Popen') as spawn:
    launcher.Launch('/home/test user/Documents', 3)
    spawn.assert_called_once_with(
        ['xdg-open', '/home/test user/Documents'], start_new_session=True)
with patch('Launcher.subprocess.Popen') as spawn:
    launcher.Launch('printf test', 5)
    spawn.assert_called_once_with(
        ['/bin/sh', '-c', 'printf test'], start_new_session=True)
with patch('Launcher.utils.xdg_dir', return_value=False):
    assert launcher.LookUpCommand('home').startswith('xdg-open ')
print('PASS: original launcher honors quoted arguments, desktop fields and URI paths')

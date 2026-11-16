"""Theme changes must refresh resource paths, not reuse a previous skin."""
from pathlib import Path
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import backend
import Globals

previous = None
for name in ('Menu', 'XP', 'Kde', 'SilverXP', 'Menu'):
    backend.save_setting('Menu_Name', name)
    Globals.ReloadSettings(orientation_override='bottom')
    expected = Path(Globals.ImageDirectory) / 'user-image-frame.png'
    current = Path(Globals.UserImageFrame)
    assert current == expected, (name, current, expected)
    if expected.exists():
        image = GdkPixbuf.Pixbuf.new_from_file(str(current))
        assert image.get_width() > 0 and image.get_height() > 0
    if previous is not None and name != previous:
        assert current.parent.name != previous, (name, previous, current)
    previous = name

print('PASS: selected theme updates user-picture frame path after each theme switch')

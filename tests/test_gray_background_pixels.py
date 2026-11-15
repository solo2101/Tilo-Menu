"""Verify GTK3 paints opaque source pixels for the original Gray theme."""
from pathlib import Path
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import backend
import Globals
from Menu_Main import Main_Menu

backend.save_setting('Menu_Name', 'Gray')
Globals.ReloadSettings(orientation_override='bottom')
menu = Main_Menu(lambda: None)
menu.show_window()
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
menu.window.get_window().process_updates(True)

# Gray's XML places icons at x=323 with gaps between successive buttons.
# This point is in a gap, away from the application list and button art.
x, y = 350, 300
background = menu.bgpb
channels = background.get_n_channels()
start = y * background.get_rowstride() + x * channels
expected = tuple(background.get_pixels()[start:start + 3])
assert expected == (0, 0, 0), (expected, 'Unexpected original Gray art')
sample = Gdk.pixbuf_get_from_window(menu.window.get_window(), x, y, 1, 1)
assert sample is not None
rgb = tuple(sample.get_pixels()[:3])
assert all(abs(rgb[i]-expected[i]) <= 5 for i in range(3)), (
    'GTK3 rendered desktop through original opaque Gray background', rgb, expected)
menu.hide_window()
print('PASS: original Gray theme opaque background rendered through GTK3')

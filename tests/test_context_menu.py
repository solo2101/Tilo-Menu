"""Exercise original GnoMenu 2.9.1 program-list context actions.

No new context menu implementation. Invokes XDGMenu.ButtonClick with a GTK3
right-click event and checks the original GTK menu construction.
"""
import sys
from pathlib import Path
from types import SimpleNamespace
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gtk
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
import backend
from Menu_Items import XDGMenu

model = XDGMenu()
model.notifier.notify = lambda *args, **kwargs: None
model.addfav(None, None, "Test Program", "/usr/bin/true",
             "application-x-executable", 1)
model.Restart('favorites')
assert 'Test Program' in model.L_Names
index = model.L_Names.index('Test Program')
event = SimpleNamespace(
    type=Gdk.EventType.BUTTON_PRESS, button=3, time=Gtk.get_current_event_time())
model.ButtonClick(index, event)
assert isinstance(model.m, Gtk.Menu)
assert len(model.m.get_children()) > 1, 'Original context menu did not populate'
print('PASS: original right-click application context menu built under GTK3')
model.m.destroy()

"""Verify application icons preserve Gio identity and survive theme fallback."""
import os
import sys
from pathlib import Path
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gio, GdkPixbuf, Gtk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/lib/tilomenu'))
from IconFactory import IconFactory, GetSystemIcon
import Globals

factory = IconFactory()
themed = Gio.ThemedIcon.new('application-x-executable')
assert factory.getgicon(themed) == 'application-x-executable'
icon = factory.geticonfile('application-x-executable')
assert isinstance(icon, GdkPixbuf.Pixbuf)
missing = factory.geticonfile('nonexistent-tilomenu-icon-99999')
assert isinstance(missing, GdkPixbuf.Pixbuf)
fileicon = Gio.FileIcon.new(Gio.File.new_for_path(Globals.BrokenImage))
assert os.path.normpath(factory.getgicon(fileicon)) == os.path.normpath(Globals.BrokenImage)
assert isinstance(factory.geticonfile(fileicon), GdkPixbuf.Pixbuf)
print('PASS: Gio icon identity, system icon, file icon and missing-icon fallback')

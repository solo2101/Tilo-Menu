"""Original XDG separators are horizontal rules, not selectable text rows."""
from pathlib import Path
import sys
from unittest.mock import patch

import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import backend
import Globals
from ArchivedCairoProgramList import ArchivedCairoProgramList

backend.save_setting("Menu_Name", "Menu")
Globals.ReloadSettings()
widget = ArchivedCairoProgramList()
widget.XDG.L_Names = ["First", "<separator>", "Second"]
widget.XDG.L_Types = [1, 8, 1]
widget.XDG.L_Icons = [None, None, None]
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, widget.width, widget.height)
widget._draw(widget.view, cairo.Context(surface))
separator_y = widget.row_height + widget.row_height // 2
assert widget._index_at(separator_y) is None
with patch.object(widget.XDG, "ButtonClick") as click:
    class Mouse:
        button = 1
        type = Gdk.EventType.BUTTON_PRESS
    widget._activate(1, Mouse())
    click.assert_not_called()
assert widget._index_at(widget.row_height // 2) == 0
print("PASS: separators are horizontal rules and cannot execute")

"""Smoke test the original GnoMenu-Settings.py class, ported in place."""
import runpy
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

source = Path(__file__).resolve().parents[1] / "src/lib/tilomenu"
sys.path.insert(0, str(source))
sys.argv = ["TiloMenu-Settings.py"]
settings_globals = runpy.run_path(str(source / "TiloMenu-Settings.py"))
window = settings_globals["TiloMenuSettings"]()
assert window.notebook.get_n_pages() == 4
assert [window.notebook.get_tab_label_text(window.notebook.get_nth_page(i))
        for i in range(4)] == [
    "Themes", "Preferences", "Commands", "About"
]
assert window.combo_menu.get_active_text()
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
window.window.destroy()
print("PASS: original four-page settings window constructed under GTK3")

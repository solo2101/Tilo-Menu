"""Regression checks for direct source port. No UI redesign or new renderer."""
import ast
import os
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
library = root / "src" / "lib" / "tilomenu"
source_files = sorted(library.glob("*.py"))
assert len(source_files) >= 13, len(source_files)

expected_classes = {
    "Menu_Main.py": "Main_Menu",
    "Menu_Widgets.py": "MenuButton",
    "Menu_Items.py": "XDGMenu",
    "MenuParser.py": "MenuParser",
    "TiloMenu-Settings.py": "TiloMenuSettings",
    "TiloMenu.py": "TiloMenu",
}
for name in expected_classes:
    file = library / name
    tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assert expected_classes[name] in classes, (name, classes)
for file in source_files:
    ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
print("PASS: original classes and Python 3 syntax", len(source_files))


# Backend API keeps its original signatures. dconf is used by Gio.Settings
# on actual MATE installations. Memory backend isolates CI from desktops.
sys.path.insert(0, str(library))
import backend

assert backend.BACKEND == "gsettings", backend.BACKEND
for key, value in (
    ("Menu_Name", "Menu"),
    ("IconSize", 28),
    ("favorites", ["app.desktop", "another.desktop"]),
    ("TabHover", 1),
):
    backend.save_setting(key, value)
    actual = backend.load_setting(key)
    assert actual == value, (key, actual, value)
assert backend.load_setting("missing-key") is None
assert backend.load_setting("favorites") == ["app.desktop", "another.desktop"]
print("PASS: original GnoMenu settings API backed by Gio.Settings")

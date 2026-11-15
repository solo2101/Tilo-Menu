"""Validate the generic button XML contract, including future installed themes."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys
import xml.dom.minidom

import gi
gi.require_version("Gtk", "3.0")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import TiloMenu

directory = TiloMenu.ThemeDirectory / "Button"
has_top = 0
without_top = 0
for folder in sorted(directory.iterdir()):
    if not (folder / "themedata.xml").is_file():
        continue
    document = xml.dom.minidom.parse(str(folder / "themedata.xml"))
    xml_theme = document.getElementsByTagName("theme")[0]
    images = TiloMenu.start_button_images(folder.name)
    assert len(images) == 3 and all(Path(image).is_file() for image in images)
    tops = TiloMenu.start_button_top_images(folder.name)
    if xml_theme.getAttribute("Top") == "1":
        assert tops is not None and len(tops) == 3, folder.name
        assert all(Path(top).is_file() for top in tops)
        has_top += 1
    else:
        assert tops is None, folder.name
        without_top += 1

# Prove the engine supports a future user-installed theme, not only bundled
# theme names. Borrow known PNG assets but put them under a fresh name.
with TemporaryDirectory() as tmp:
    root = Path(tmp) / "Button"
    custom = root / "FutureCustomTheme"
    custom.mkdir(parents=True)
    existing = TiloMenu.start_button_images("GnoBlue")
    (custom / "themedata.xml").write_text(
        '<content type="Button"><theme Top="0">'
        '<Background Image="normal.png" ImageHover="hover.png" '
        'ImagePressed="pressed.png"/></theme></content>',
        encoding="utf-8")
    for src, dst in zip(existing, ("normal.png", "hover.png", "pressed.png")):
        (custom / dst).symlink_to(Path(src))
    with patch.object(TiloMenu, "ThemeDirectory", root):
        assert all(Path(p).is_file() for p in
                   TiloMenu.start_button_images("FutureCustomTheme"))
        assert TiloMenu.start_button_top_images("FutureCustomTheme") is None
        assert TiloMenu.start_button_top_images("MissingOptionalTheme") is None
assert has_top > 0 and without_top > 0
print(f"PASS: generic XML button engine, {has_top} Top themes, "
      f"{without_top} ordinary themes, and an external theme")

"""Original button XML Top artwork is independent of Background image states."""
from pathlib import Path
import sys

import gi
gi.require_version("Gtk", "3.0")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
from TiloMenu import start_button_images, start_button_top_images

main = start_button_images("Arch")
top = start_button_top_images("Arch")
assert len(main) == 3
assert top is not None and len(top) == 3
assert all(Path(path).is_file() for path in top)
assert all(Path(path).is_file() for path in main)
assert start_button_top_images("GnoBlue") is None
print("PASS: original overhanging Arch button artwork loads all three states")

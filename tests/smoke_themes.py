"""Exercise Tilo-Menu rendering with every original GnoMenu menu theme.

Runs in Xvfb with GTK3; draws each theme briefly to catch parser,
Pango markup, widget geometry, and Cairo painting exceptions.
"""
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from tilomenu.menu import MenuWindow
from tilomenu.themes import load_menu_theme


def main(root):
    directories = sorted(
        path for path in Path(root).iterdir()
        if path.is_dir() and (path / "themedata.xml").is_file()
    )
    if len(directories) < 15:
        raise RuntimeError(f"Expected 15 original themes, found {len(directories)}")
    failures = []
    for directory in directories:
        try:
            theme = load_menu_theme(directory)
            window = MenuWindow(theme)
            window.show_all()
            if hasattr(window, "search_control"):
                window.search_control.entry.set_text("control")
                window.search_control.entry.set_text("")
            window._select_from_list("Favorites", False)
            window._select_from_list("All Applications", False)
            GLib.timeout_add(120, lambda: window.destroy() or False)
            Gtk.main()
            print(f"OK: {directory.name} ({window.menu_width}x{window.menu_height})")
        except Exception as error:
            failures.append((directory.name, repr(error)))
            print(f"FAIL: {directory.name}: {error}", file=sys.stderr)
    if failures:
        raise SystemExit(f"{len(failures)} theme(s) failed: {failures}")


if __name__ == "__main__":
    main(sys.argv[1])

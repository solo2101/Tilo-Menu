"""Exercise Tilo-Menu rendering with every original GnoMenu menu theme.

Runs in Xvfb with GTK3; draws each theme briefly to catch parser,
Pango markup, widget geometry, and Cairo painting exceptions.
"""
import sys
import tempfile
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from tilomenu.menu import MenuWindow
from tilomenu.themes.avatar import face_file, face_candidates, _scaled_portrait, avatar_visible
from tilomenu.themes import load_menu_theme
from tilomenu.themes.contrast import (
    FOREGROUND, contrast_ratio, legible_markup, sample_background,
)


def check_tab_contrast(theme):
    """Guard against gray/white labels disappearing into theme artwork."""
    for tab in theme.tabs:
        attrs = tab.attributes
        markup = attrs.get("Markup", "")
        if not FOREGROUND.search(markup):
            continue
        name = attrs.get("Name", "")
        x, y = tab.integer("TabX"), tab.integer("TabY")
        text_x, text_y = x + tab.integer("TextX"), y + tab.integer("TextY")
        image_path = attrs.get("ImageSel", "")
        overlay = theme.directory / image_path
        for selected in (False, True):
            image_name = image_path if selected else attrs.get("Image", "")
            corrected = legible_markup(
                theme, markup, text_x, text_y, 72,
                selected=selected,
                invert_unselected=attrs.get("InvertTextColorOnSel", "0") == "1",
                overlay=image_name, overlay_x=x, overlay_y=y,
            )
            changed = FOREGROUND.search(corrected)
            assert changed is not None, (theme.directory.name, name)
            foreground = tuple(int(changed.group(1)[i:i+2], 16)
                               for i in (1, 3, 5))
            # The same representative pixel used for selected text appearance.
            background = sample_background(
                theme, text_x + 12, text_y + 10,
                image_name, x, y,
            )
            if background is None:
                continue
            # Gradients and icon decorations can vary under individual
            # glyphs; verify the higher-level palette never returns a
            # near-identical foreground on a uniform background.
            ratio = contrast_ratio(foreground, background)
            if name in ("Favorites", "Applications") and theme.directory.name in (
                "Slab", "iTheme", "Menu", "Kde"
            ):
                assert ratio > 2.0, (theme.directory.name, name, selected, ratio)


def test_face_source():
    """MATE's face takes priority and portrait crop preserves XML dimensions."""
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        assert next(face_candidates(home=home, username="test-user")) == home / ".face"
        assert face_file(home=home, username="test-user") is None
        png_path = home / ".face"
        from gi.repository import GdkPixbuf
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 20, 40)
        pixbuf.fill(0xff3366ff)
        pixbuf.savev(str(png_path), "png", [], [])
        assert face_file(home=home, username="test-user") == png_path
        cropped = _scaled_portrait(pixbuf, 46, 46)
        assert cropped.get_width() == cropped.get_height() == 46


def main(root):
    test_face_source()
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
            check_tab_contrast(theme)
            window = MenuWindow(theme)
            window.show_all()
            # The original XML Capabilities.HasIcon is authoritative.
            # Opaque artwork must never hide an enabled portrait.
            enabled = theme.capabilities.attributes.get("HasIcon") == "1"
            visible = avatar_visible(theme)
            assert visible == enabled, (directory.name, "HasIcon", enabled)
            assert (window.avatar is not None) == enabled, directory.name
            if enabled:
                assert window.avatar.get_tooltip_text() == "About Me"
            if directory.name in ("Dock", "Slab", "Avio", "Short", "Lancelot"):
                assert not enabled, directory.name
            if directory.name in ("Vista", "XP", "iTheme", "Menu", "Kde"):
                assert enabled, directory.name

            # A regression once constrained every legacy label to 1 pixel,
            # displaying only "..." despite correct original XML markup.
            canvas = window.get_child()
            visible_labels = [
                child for child in canvas.get_children()
                if isinstance(child, Gtk.Label)
            ]
            assert len(visible_labels) >= len(theme.labels), (
                directory.name, "missing original XML labels"
            )
            for label in visible_labels:
                if len(label.get_text().strip()) >= 4:
                    requested_width, _height = label.get_size_request()
                    assert requested_width >= 12, (
                        directory.name, label.get_text(), requested_width
                    )
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

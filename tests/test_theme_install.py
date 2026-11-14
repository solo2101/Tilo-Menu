"""Exercise legacy theme installation and the GTK3 settings notebook.

Uses the official GnoMenu 2.9.1 archive and temporary directories.
Never installs anything in the user's real theme library.
"""
import io
import os
import sys
import tarfile
import tempfile
import warnings
import zipfile
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from tilomenu.preferences import (
    PreferencesWindow, installed_themes, load_settings, save_settings,
)
from tilomenu.themes import load_menu_theme
from tilomenu.themes.importer import ThemeImportError, import_theme_archive


def rejects(callback):
    try:
        callback()
    except ThemeImportError:
        return
    raise AssertionError("Expected ThemeImportError")


def tar_bytes(path, entries):
    with tarfile.open(path, "w") as archive:
        for name, data, typeflag in entries:
            info = tarfile.TarInfo(name=name)
            info.type = typeflag
            info.size = len(data)
            if typeflag == tarfile.SYMTYPE:
                info.linkname = "../outside"
                info.size = 0
            archive.addfile(info, io.BytesIO(data) if info.isfile() else None)


def main(gnomenu_archive, original_menu):
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        os.environ["XDG_CONFIG_HOME"] = str(root / "config")
        target = root / "installed"
        names = import_theme_archive(gnomenu_archive, target)
        assert len(names) == 15, names
        assert len(installed_themes(target)) == 15
        assert "Vista" in names and "XP" in names
        for name in names:
            theme = load_menu_theme(target / name)
            assert theme.width > 0
            original = Path(original_menu) / name / "themedata.xml"
            assert original.read_bytes() == (target / name / "themedata.xml").read_bytes()
        print("PASS: original 15 Menu theme XML files imported byte-identically")

        # Nested single-theme archives are supported, like common old
        # third-party GnoMenu packages, without changing the XML.
        sample = root / "single.tar"
        with tarfile.open(sample, "w") as archive:
            archive.add(Path(original_menu) / "Vista", arcname="Outer/ExtraTheme")
        result = import_theme_archive(sample, target)
        assert result == ["ExtraTheme"], result
        again = import_theme_archive(sample, target)
        assert again == ["ExtraTheme-2"], again
        assert (target / "ExtraTheme" / "themedata.xml").read_bytes() == (
            Path(original_menu) / "Vista" / "themedata.xml"
        ).read_bytes()
        print("PASS: nested and duplicate-name Menu archives")

        zipped = root / "single.zip"
        with zipfile.ZipFile(zipped, "w") as archive:
            for path in (Path(original_menu) / "Vista").rglob("*"):
                if path.is_file():
                    archive.write(path, "Sample/" + str(path.relative_to(
                        Path(original_menu) / "Vista"
                    )))
        assert import_theme_archive(zipped, target) == ["Sample"]
        print("PASS: ZIP theme import")

        bad = root / "traversal.tar"
        tar_bytes(bad, [("../evil.txt", b"no", tarfile.REGTYPE)])
        rejects(lambda: import_theme_archive(bad, target))
        assert not (root / "evil.txt").exists()

        bad = root / "symlink.tar"
        tar_bytes(bad, [("Face/symlink", b"", tarfile.SYMTYPE)])
        rejects(lambda: import_theme_archive(bad, target))

        bad = root / "other-type.zip"
        with zipfile.ZipFile(bad, "w") as archive:
            archive.writestr(
                "SomeIcon/themedata.xml", '<content type="Icon"/>'
            )
        rejects(lambda: import_theme_archive(bad, target))
        print("PASS: unsafe archives and non-Menu theme types rejected")

        save_settings({"theme": "XP", "tab_hover": True, "icon_size": 28})
        window = PreferencesWindow(target)
        window.show_all()
        assert window.notebook.get_n_pages() == 4
        assert [window.notebook.get_tab_label_text(window.notebook.get_nth_page(i))
                for i in range(4)] == [
            "Themes", "Preferences", "Commands", "About"
        ]
        assert window.choice.get_active_text() == "XP"
        assert window.icon_size.get_value_as_int() == 28
        assert window.tab_hover.get_active()
        window.icon_size.set_value(32)
        window.tooltips.set_active(False)
        window._apply(None)
        data = load_settings()
        assert data["theme"] == "XP"
        assert data["icon_size"] == 32
        assert data["show_tooltips"] is False
        window.destroy()
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        print("PASS: original four-tab settings applet, preview and live settings")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

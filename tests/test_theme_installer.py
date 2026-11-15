"""Regression tests for importing original TiloMenu theme archives."""
import importlib.util
from pathlib import Path
import io
import os
import tarfile
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "src/lib/tilomenu/ThemeInstaller.py"
spec = importlib.util.spec_from_file_location("ThemeInstaller", MODULE)
themes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(themes)


class ThemeInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, {"XDG_DATA_HOME": self.temp.name})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.root = Path(self.temp.name)
        self.system = self.root / "system"
        self.system.mkdir()

    def archive(self, entries):
        path = self.root / "test.tar.gz"
        with tarfile.open(path, "w:gz") as out:
            for name, data in entries.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                out.addfile(info, io.BytesIO(data))
        return path

    def test_install_original_root_content_xml(self):
        archive = self.archive({
            "Sample/themedata.xml": b'<content type="Menu"><ContentData Name="Sample"/></content>',
            "Sample/image.png": b"png",
        })
        self.assertEqual(themes.install_archive(archive), ("Menu", "Sample"))
        folder = Path(themes.theme_path("Menu", "Sample", self.system))
        self.assertEqual((folder / "image.png").read_bytes(), b"png")
        self.assertIn("Sample", themes.installed_themes("Menu", self.system))
        themes.uninstall_user_theme("Menu", "Sample")
        self.assertNotIn("Sample", themes.installed_themes("Menu", self.system))

    def test_reject_parent_traversal(self):
        archive = self.archive({
            "Sample/themedata.xml": b'<content type="Button"/>',
            "Sample/../../escape": b"x",
        })
        with self.assertRaises(ValueError):
            themes.install_archive(archive)
        self.assertFalse((self.root / "escape").exists())

    def test_reject_unexpected_type(self):
        archive = self.archive({"Sample/themedata.xml": b'<content type="Unexpected"/>'})
        with self.assertRaises(ValueError):
            themes.install_archive(archive)

    def test_user_theme_overrides_system_theme(self):
        system = self.system / "Button" / "Sample"
        system.mkdir(parents=True)
        (system / "themedata.xml").write_text('<content type="Button"/>')
        user = themes.theme_root() / "Button" / "Sample"
        user.mkdir(parents=True)
        (user / "themedata.xml").write_text('<content type="Button"/>')
        self.assertEqual(Path(themes.theme_path("Button", "Sample", self.system)), user)
        self.assertEqual(themes.installed_themes("Button", self.system), ["Sample"])


if __name__ == "__main__":
    unittest.main()

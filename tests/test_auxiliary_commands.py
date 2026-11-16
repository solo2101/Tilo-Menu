"""Port the actual original Auxiliary menu commands without launching programs."""
from pathlib import Path
import shlex
import sys
from unittest.mock import patch

import gi
gi.require_version("Gtk", "3.0")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import backend
import Globals
from Launcher import Launcher
from Menu_Items import XDGMenu

installed = {
    "mate-about-me", "mate-appearance-properties", "mozo",
    "mate-screensaver-preferences", "mate-system-monitor",
}
expected = {
    "About Me": "mate-about-me",
    "Appearance": "mate-appearance-properties",
    "Menu editor": "mozo",
    "Screensaver": "mate-screensaver-preferences",
    "System Monitor": "mate-system-monitor",
}
with patch("Launcher.shutil.which", side_effect=lambda name:
           "/usr/bin/" + name if name in installed else None):
    xdg = XDGMenu()
    xdg.Restart("auxiliary")
    entries = dict(zip(xdg.L_Names, zip(xdg.L_Execs, xdg.L_Types)))
    for label, cmd in expected.items():
        assert label in entries, (label, list(entries))
        original, typ = entries[label]
        assert typ in (5, 6), (label, typ)
        with patch("Launcher.subprocess.Popen") as spawn:
            xdg.Launcher.Launch(original, typ)
            spawn.assert_called_once_with(
                ["/bin/sh", "-c", cmd], start_new_session=True)

    settings = next((value for name, value in entries.items()
                     if name.startswith("TiloMenu settings")), None)
    assert settings is not None
    command, typ = settings
    assert typ == 7
    assert shlex.split(command) == [
        sys.executable, Globals.ProgramDirectory + "TiloMenu-Settings.py"
    ], command
    with patch("Launcher.subprocess.Popen") as spawn:
        xdg.Launcher.Launch(command, typ)
        spawn.assert_called_once_with(
            ["/bin/sh", "-c", command], start_new_session=True)
print("PASS: all six original Auxiliary menu actions resolve to modern MATE commands")

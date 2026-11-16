"""Audit every original theme command against GTK3/MATE action routing.

The previous matrix only mocked Launcher.Launch, which failed to expose
retired GNOME commands and the missing original session-manager helpers.
Do not spawn external applications or end the desktop session in this test.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import shlex
import sys
import xml.etree.ElementTree as ET

import gi
gi.require_version("Gtk", "3.0")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import backend
import Globals
from Launcher import Launcher, resolve_legacy_action, resolve_legacy_exec
from Menu_Widgets import ImageFrame

root = Path(__file__).resolve().parents[1] / "src/share/tilomenu/Themes/Menu"
themes = sorted(p for p in root.iterdir() if (p / "themedata.xml").is_file())
installed = {
    "mate-search-tool", "mate-control-center", "dnfdragora",
    "mate-session-save", "mate-screensaver-command", "mate-panel",
    "mate-terminal", "systemctl", "mozo", "xdg-open",
}
expected = {
    "Search": "mate-search-tool",
    "Control Panel": "mate-control-center",
    "Package Manager": "dnfdragora",
    "Power": "mate-session-save --shutdown-dialog",
    "Shutdown": "mate-session-save --shutdown-dialog",
    "Lock": "mate-screensaver-command --lock",
    "Suspend": "systemctl suspend",
    "Hibernate": "systemctl hibernate",
    "Run": "mate-panel --run-dialog",
    "Logout": "mate-session-save --logout-dialog",
    "LogoutNow": "mate-session-save --logout",
    "Restart": "mate-session-save --shutdown-dialog",
    "User": "mate-control-center",
    "MenuEditor": "mozo",
}

with patch("Launcher.shutil.which", side_effect=lambda name:
           "/usr/bin/" + name if name in installed else None):
    for key, wanted in expected.items():
        setting_name = {
            "Control Panel": "Control_Panel",
            "Package Manager": "Package_Manager",
        }.get(key, key)
        original = Globals.DefaultSettings[setting_name]
        assert resolve_legacy_action(key, original) == wanted, (key, original)
        assert resolve_legacy_exec(original) == wanted, (key, original)
        custom = "custom-script --flag"
        assert resolve_legacy_action(key, custom) == custom, key

    for key, original in Globals.DefaultSettings.items():
        backend.save_setting(key, original)
    Globals.ReloadSettings(orientation_override="bottom")
    launcher = Launcher()

    with patch("Launcher.utils.xdg_dir", return_value=False):
        for action in expected:
            if action not in Globals.MenuActions:
                continue
            command = launcher.LookUpCommand(action)
            assert command == expected[action] + " &", (action, command)
        assert launcher.LookUpCommand("gnome-terminal") == "mate-terminal &"
        assert launcher.LookUpCommand("gnome-app-install") == "dnfdragora &"

        # Run dialog, shutdown and lock are also launched from the XDG
        # Shutdown page with tag=1, bypassing normal LookUpCommand.
        with patch("Launcher.subprocess.Popen") as spawn:
            launcher.Launch(Globals.DefaultSettings["Shutdown"], 1)
            spawn.assert_called_once_with(
                ["mate-session-save", "--shutdown-dialog"],
                start_new_session=True,
            )

        # The theme portrait is an additional clickable source command.
        with patch("Menu_Widgets.os.system") as system:
            ImageFrame.but_click(object(), None, SimpleNamespace(button=1))
            system.assert_called_once_with("mate-control-center &")

        with patch("Launcher.utils.xdg_dir", return_value="/tmp/My Documents"):
            value = launcher.LookUpCommand("Documents")
            assert value == "xdg-open '/tmp/My Documents' &", value

        # Validate all original XML Button and Tab routes, not only the
        # themes currently selected in Preferences.
        total, separators = 0, 0
        named = set(Globals.MenuActions)
        xdg = {"Home", "Documents", "Pictures", "Music", "Videos",
               "Computer", "Network", "Trash"}
        raw = {"gnome-terminal", "gnome-app-install"}
        for theme in themes:
            xml = ET.parse(theme / "themedata.xml").getroot()
            for element in xml.findall(".//Button") + xml.findall(".//Tab"):
                attrs = element.attrib
                if attrs.get("Name") == ":SEPARATOR:":
                    separators += 1
                    continue
                command = attrs["Command"]
                if attrs.get("SubMenu") == "1":
                    assert command.isdigit() and int(command) in {
                        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
                    }, (theme.name, attrs)
                elif command == ":ALLAPPS:":
                    assert element.tag == "Button", theme.name
                else:
                    assert command in named | xdg | raw, (
                        theme.name, attrs.get("Name"), command
                    )
                    value = launcher.LookUpCommand(command)
                    assert value.endswith(" &"), (theme.name, command, value)
                    if command in expected:
                        assert value == expected[command] + " &", (
                            theme.name, command, value
                        )
                total += 1

assert len(themes) == 15, len(themes)
assert total >= 160 and separators >= 10, (total, separators)
print(f"PASS: {total} actionable Button/Tab entries across "
      f"{len(themes)} original themes, including legacy defaults and XDG paths")

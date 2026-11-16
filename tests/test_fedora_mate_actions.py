"""Check original About Me portrait and Fedora MATE action fallbacks.

GTK3 event signals must reach ImageFrame's original button handler.
The old source used gnome-about-me, which maps to mate-about-me on Fedora.
"""
from pathlib import Path
from unittest.mock import patch
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))

import backend
import Globals
from Launcher import Launcher, resolve_legacy_action
from Menu_Main import Main_Menu

installed = {
    "mate-about-me", "mate-control-center", "mate-panel", "nm-connection-editor",
    "gnome-software", "gpk-application", "dnfdragora",
}

def available(command):
    return "/usr/bin/" + command if command in installed else None

try:
    with patch("Launcher.shutil.which", side_effect=available):
        # The same named XML commands work without per-theme changes.
        launcher = Launcher()
        assert resolve_legacy_action("User", "gnome-about-me") == "mate-about-me"
        assert launcher.LookUpCommand("Control Panel") == "mate-control-center &"
        assert launcher.LookUpCommand("Package Manager") == "gnome-software &"
        assert launcher.LookUpCommand("Network Config") == "nm-connection-editor &"
        assert launcher.LookUpCommand("gnome-app-install") == "gnome-software &"

        # Distinguish missing package-manager frontends from missing dnf.
        with patch("Launcher.shutil.which", side_effect=lambda command:
                   "/usr/bin/" + command if command in {"gpk-application", "mate-control-center"}
                   else None):
            assert launcher.LookUpCommand("Package Manager") == "gpk-application &"
            assert launcher.LookUpCommand("gnome-app-install") == "gpk-application &"
            assert launcher.LookUpCommand("Network Config") == "mate-control-center &"

        # Custom user-configured commands win over the compatibility mapping.
        with patch.dict(Globals.Settings, {
            "User": "custom-about-me --current-user",
            "Package_Manager": "my-package-manager",
        }):
            assert resolve_legacy_action("User", Globals.Settings["User"]) == (
                "custom-about-me --current-user")
            assert resolve_legacy_action("Package Manager",
                                         Globals.Settings["Package_Manager"]) == (
                "my-package-manager")

        # Verify actual EventBox button-press handler in multiple XML themes.
        left = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
        left.button = 1
        right = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
        right.button = 3
        for name in ("XP", "Kde", "iTheme"):
            backend.save_setting("Menu_Name", name)
            Globals.ReloadSettings(orientation_override="bottom")
            menu = Main_Menu(lambda: None)
            try:
                assert Globals.MenuHasIcon == 1, name
                assert menu.usericon.frame_window.get_tooltip_text() == "About Me"
                with patch("Menu_Widgets.os.system") as system:
                    menu.usericon.frame_window.emit("button-press-event", left)
                    system.assert_called_once_with("mate-about-me &")
                    system.reset_mock()
                    menu.usericon.frame_window.emit("button-press-event", right)
                    system.assert_not_called()
            finally:
                menu.window.destroy()
finally:
    backend.save_setting("Menu_Name", "Menu")
    Globals.ReloadSettings(orientation_override="bottom")

print("PASS: portrait click opens About Me and Fedora package/control/network fallbacks preserve custom commands")

"""GTK 3 preview of the original GnoMenu 2.9.1 XML layout.

This is a standalone preview, not yet a MATE panel applet.
Run: python3 -m tilomenu.menu /path/to/Menu/Vista
"""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gtk, Gio

from .applications import application_categories, installed_applications, launch_application
from .themes import load_menu_theme
from .themes.renderer import render_theme_buttons
from .icons import load_icon
from .themes.app_list import ThemeAppList


class MenuWindow(Gtk.Window):
    def __init__(self, theme):
        super().__init__(title="Tilo Menu")
        self.theme = theme
        self.themes_dir = theme.directory.parent
        self.set_default_size(theme.width, theme.height)
        self.set_resizable(False)
        self.set_decorated(False)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)
        self.get_style_context().add_class("tilo-window")
        self.connect("destroy", Gtk.main_quit)
        self.connect("button-press-event", self._theme_context_menu)

        layout = Gtk.Fixed()
        layout.get_style_context().add_class("tilo-layout")
        self.add(layout)
        background = theme.directory / theme.background
        if background.is_file():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(background), theme.width, theme.height, False
            )
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            layout.put(image, 0, 0)
        else:
            layout.put(Gtk.Label(label="Missing theme background: " + theme.background), 0, 0)

        program = theme.program_list
        self.all_apps = installed_applications()
        self.favorites_path = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'tilo-menu' / 'favorites.json'
        self.favorites = self._load_favorites()
        self.category = "All Applications"
        self.query = ""
        category_names = sorted({
            category for app in self.all_apps
            for category in application_categories(app)
        })
        self.categories = ["All Applications", "Favorites", *category_names]
        self.show_categories = False
        # A single Cairo drawing area paints the original theme's pixels,
        # avoiding GTK light/dark controls inside the application list.
        self.apps = ThemeAppList(
            theme, self._launch_from_list, self._select_from_list, self._favorite_from_list
        )
        layout.put(self.apps, program.integer("X"), program.integer("Y"))
        self._populate()

        search = theme.search
        if search.attributes.get("Widget") != "None":
            entry = Gtk.SearchEntry()
            entry.get_style_context().add_class("tilo-search")
            entry.set_placeholder_text(search.attributes.get("InitialText", "Search"))
            entry.set_size_request(search.integer("Width"), search.integer("Height"))
            layout.put(entry, search.integer("X"), search.integer("Y"))
            entry.connect("search-changed", self._change_search)

        render_theme_buttons(layout, theme, self._activate_shortcut)

    def _theme_context_menu(self, _widget, event):
        if event.button != 3 or event.window != self.get_window():
            return False
        menu = Gtk.Menu()
        submenu = Gtk.Menu()
        for path in sorted(self.themes_dir.iterdir(), key=lambda p: p.name.casefold()):
            if not path.is_dir() or not (path / "themedata.xml").is_file():
                continue
            item = Gtk.MenuItem(label=path.name)
            item.set_sensitive(path != self.theme.directory)
            item.connect("activate", self._switch_theme, path)
            submenu.append(item)
        parent = Gtk.MenuItem(label="Change Theme")
        parent.set_submenu(submenu)
        menu.append(parent)
        menu.show_all()
        menu.popup_at_pointer(event)
        return True

    def _switch_theme(self, _item, path):
        settings = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "tilo-menu" / "settings.json"
        try:
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps({"theme": path.name}, indent=2) + "\n", encoding="utf-8")
            subprocess.Popen([str(Path.home() / ".local/bin/tilo-menu")], start_new_session=True)
            self.close()
        except OSError as error:
            print(f"Tilo Menu: theme switch failed: {error}")

    def _activate_shortcut(self, name):
        """Open MATE destinations using a fixed allowlist, never theme commands."""
        action = name.strip().lower().replace("_", " ").strip(":")
        if action in ("power", "shutdown", "shut down", "power off", "reboot", "restart", "lock", "lock screen", "logout", "log out", "logoff"):
            return self._system_action(action)
        home = Path.home()
        folders = {
            "Home Folder": home,
            "Documents": home / "Documents",
            "Pictures": home / "Pictures",
            "Music": home / "Music",
            "Videos": home / "Videos",
            "Computer": Path("/"),
            "Network": "network:///",
        }
        if name in folders:
            target = folders[name]
            uri = target.as_uri() if isinstance(target, Path) else target
            try:
                Gio.AppInfo.launch_default_for_uri(uri, None)
                self.close()
            except Exception as error:
                print(f"Tilo Menu: unable to open {name}: {error}")
            return True

        commands = {
            "Search": ("mate-search-tool",),
            "Show History": ("mate-search-tool",),
            "Control Center": ("mate-control-center",),
            "Package Manager": ("dnfdragora", "gnome-software"),
            "Help": ("yelp",),
            "Connect To": ("caja",),
        }
        for command in commands.get(name, ()):
            executable = shutil.which(command)
            if executable:
                try:
                    subprocess.Popen([executable], start_new_session=True)
                    self.close()
                except OSError as error:
                    print(f"Tilo Menu: unable to start {command}: {error}")
                return True
        return True

    def _system_action(self, action):
        """Confirm session actions and delegate to MATE or logind."""
        if action in ("power", "shutdown", "shut down", "power off"):
            title, command = "Shut down", ["systemctl", "poweroff"]
        elif action in ("reboot", "restart"):
            title, command = "Restart", ["systemctl", "reboot"]
        elif action in ("logout", "log out", "logoff"):
            title, command = "Log out", ["mate-session-save", "--logout"]
        else:
            title, command = "Lock screen", ["xdg-screensaver", "lock"]

        if title in ("Shut down", "Restart"):
            dialog = Gtk.MessageDialog(
                transient_for=self, modal=True,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.NONE,
                text=f"{title} the computer?",
            )
            dialog.format_secondary_text("Unsaved work may be lost.")
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button(title, Gtk.ResponseType.OK)
            response = dialog.run()
            dialog.destroy()
            if response != Gtk.ResponseType.OK:
                return True
        if not shutil.which(command[0]):
            print(f"Tilo Menu: {command[0]} is not installed")
            return True
        try:
            subprocess.Popen(command, start_new_session=True)
            self.close()
        except OSError as error:
            print(f"Tilo Menu: {title} failed: {error}")
        return True

    def _load_favorites(self):
        try:
            data = json.loads(self.favorites_path.read_text(encoding="utf-8"))
            return set(data) if isinstance(data, list) else set()
        except (OSError, ValueError, TypeError):
            return set()

    def _toggle_favorite(self, _item, app):
        app_id = app.get_id()
        if not app_id:
            return
        if app_id in self.favorites:
            self.favorites.remove(app_id)
        else:
            self.favorites.add(app_id)
        try:
            self.favorites_path.parent.mkdir(parents=True, exist_ok=True)
            self.favorites_path.write_text(
                json.dumps(sorted(self.favorites), indent=2) + "\n", encoding="utf-8"
            )
        except OSError as error:
            print(f"Tilo Menu: unable to save favorites: {error}")
        self._populate()

    def _select_from_list(self, category, show_categories):
        if category is not None:
            self.category = category
        self.show_categories = show_categories
        self._populate()

    def _launch_from_list(self, app):
        self._launch(None, app)

    def _favorite_from_list(self, app):
        self._toggle_favorite(None, app)

    def _change_search(self, widget):
        self.query = widget.get_text().casefold()
        self._populate()

    def _populate(self):
        if self.show_categories:
            rows = self.categories
        else:
            rows = []
            for app in self.all_apps:
                name = app.get_display_name() or app.get_name()
                if self.category == "Favorites" and app.get_id() not in self.favorites:
                    continue
                if (self.category not in ("All Applications", "Favorites")
                        and self.category not in application_categories(app)):
                    continue
                if self.query and self.query not in (
                        name + " " + (app.get_description() or "")).casefold():
                    continue
                rows.append(app)
        self.apps.set_content(rows, self.category, self.show_categories, self.favorites)

    def _launch(self, _button, app):
        launch_application(app)
        self.close()


def main():
    parser = argparse.ArgumentParser(description="Preview a GnoMenu XML menu theme")
    parser.add_argument("theme_directory", nargs="?", type=Path)
    parser.add_argument("--themes-dir", type=Path)
    parser.add_argument("--theme", help="Select a theme by directory name")
    parser.add_argument("--list-themes", action="store_true")
    parser.add_argument("--color", default="white")
    args = parser.parse_args()
    themes_dir = args.themes_dir or (args.theme_directory.parent if args.theme_directory else Path.home() / ".local/share/tilo-menu/data/themes/Menu")
    themes = {p.name: p for p in themes_dir.iterdir() if p.is_dir() and (p / "themedata.xml").is_file()} if themes_dir.is_dir() else {}
    if args.list_themes:
        print("\n".join(sorted(themes)))
        return
    settings = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "tilo-menu" / "settings.json"
    try:
        saved = json.loads(settings.read_text(encoding="utf-8")).get("theme", "Vista")
    except (OSError, ValueError, AttributeError):
        saved = "Vista"
    chosen = args.theme or saved
    path = args.theme_directory or themes.get(chosen) or themes.get("Vista")
    if path is None:
        parser.error("No installed menu themes found. Run make install.")
    window = MenuWindow(load_menu_theme(path, args.color))
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

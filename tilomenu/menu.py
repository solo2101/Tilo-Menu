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
from gi.repository import GdkPixbuf, Gtk, Gio

from .applications import application_categories, installed_applications, launch_application
from .themes import load_menu_theme
from .themes.renderer import render_theme_buttons
from .icons import load_icon


class MenuWindow(Gtk.Window):
    def __init__(self, theme):
        super().__init__(title="Tilo Menu")
        self.theme = theme
        self.themes_dir = theme.directory.parent
        self.set_default_size(theme.width, theme.height)
        self.set_resizable(False)
        self.set_decorated(False)
        self.connect("destroy", Gtk.main_quit)
        self.connect("button-press-event", self._theme_context_menu)

        layout = Gtk.Fixed()
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
        self.category_select = Gtk.ComboBoxText()
        for name in ["All Applications", "Favorites", *category_names]:
            self.category_select.append_text(name)
        self.category_select.set_active(0)
        self.category_select.set_size_request(program.integer("Width"), 30)
        layout.put(self.category_select, program.integer("X"), program.integer("Y"))
        self.category_select.connect("changed", self._change_category)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(program.integer("Width"), max(50, program.integer("Height") - 32))
        layout.put(scroll, program.integer("X"), program.integer("Y") + 32)
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            listbox, listbox row, scrolledwindow, viewport { background: transparent; border: none; }
            listbox row { padding: 0; min-height: 0; }
            button.tilo-app { background: transparent; background-image: none; border: none;
                box-shadow: none; border-radius: 0; padding: 3px 5px; min-height: 26px; }
            button.tilo-app:hover { background: rgba(90, 145, 210, 0.35); }
            button.tilo-app label { font-size: 12px; color: #f4f4f4; text-shadow: 0 1px 1px #111; }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.apps = Gtk.ListBox()
        self.apps.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self.apps)
        self._populate("")

        search = theme.search
        if search.attributes.get("Widget") != "None":
            entry = Gtk.SearchEntry()
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

    def _app_context_menu(self, widget, event, app):
        if event.button != 3 or not app.get_id():
            return False
        menu = Gtk.Menu()
        label = "Remove from Favorites" if app.get_id() in self.favorites else "Add to Favorites"
        item = Gtk.MenuItem(label=label)
        item.connect("activate", self._toggle_favorite, app)
        menu.append(item)
        menu.show_all()
        menu.popup_at_widget(widget, 2, 3, event)
        return True

    def _change_category(self, widget):
        self.category = widget.get_active_text() or "All Applications"
        self._populate()

    def _change_search(self, widget):
        self.query = widget.get_text().casefold()
        self._populate()

    def _populate(self, query=None):
        for child in self.apps.get_children():
            self.apps.remove(child)
        for app in self.all_apps:
            name = app.get_display_name() or app.get_name()
            if self.category == "Favorites" and app.get_id() not in self.favorites:
                continue
            if self.category not in ("All Applications", "Favorites") and self.category not in application_categories(app):
                continue
            if self.query and self.query not in (name + " " + (app.get_description() or "")).casefold():
                continue
            button = Gtk.Button()
            button.get_style_context().add_class("tilo-app")
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.set_halign(Gtk.Align.FILL)
            content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            content.set_halign(Gtk.Align.FILL)
            image = load_icon(app.get_icon(), 20)
            if image is not None:
                content.pack_start(image, False, False, 0)
            label = Gtk.Label(label=name, xalign=0)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            label.set_ellipsize(3)
            content.pack_start(label, True, True, 0)
            button.add(content)
            button.connect("clicked", self._launch, app)
            button.connect("button-press-event", self._app_context_menu, app)
            self.apps.add(button)
        self.apps.show_all()

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

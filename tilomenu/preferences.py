"""GTK3 successor to the original GnoMenu-Settings.py interface.

The original arrangement is preserved: Themes, Preferences, Commands and
About pages, Menu Selection preview/credits and an Install button. Theme
artwork and themedata.xml remain unchanged. Unsupported legacy controls are
shown as information, not as inert settings.
"""
import json
import os
import shutil
from pathlib import Path

from gi.repository import GdkPixbuf, Gio, Gtk

from .themes import load_menu_theme
from .themes.importer import ThemeImportError, import_theme_archive


def preferences_file():
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "tilo-menu" / "settings.json"


def load_settings():
    try:
        data = json.loads(preferences_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_settings(data):
    path = preferences_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(pending, path)


def selected_theme():
    return load_settings().get("theme", "Vista")


def save_theme(name):
    settings = load_settings()
    settings["theme"] = name
    save_settings(settings)


def installed_themes(directory):
    directory = Path(directory)
    return sorted(
        (p for p in directory.iterdir()
         if p.is_dir() and (p / "themedata.xml").is_file()),
        key=lambda p: p.name.casefold(),
    ) if directory.is_dir() else []


def _label(text, wrap=False):
    label = Gtk.Label(label=text)
    label.set_xalign(0)
    if wrap:
        label.set_line_wrap(True)
    return label


class PreferencesWindow(Gtk.Window):
    def __init__(self, themes_dir):
        super().__init__(title="Tilo-Menu Settings")
        self.themes_dir = Path(themes_dir).expanduser()
        self.settings = load_settings()
        self.imported = set(self.settings.get("imported_themes", []))
        self.set_default_size(720, 650)
        self.set_border_width(8)
        self.connect("destroy", Gtk.main_quit)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(body)
        self.notebook = Gtk.Notebook()
        body.pack_start(self.notebook, True, True, 0)
        self.notebook.append_page(self._themes_page(), Gtk.Label(label="Themes"))
        self.notebook.append_page(self._preferences_page(), Gtk.Label(label="Preferences"))
        self.notebook.append_page(self._commands_page(), Gtk.Label(label="Commands"))
        self.notebook.append_page(self._about_page(), Gtk.Label(label="About"))

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        body.pack_start(separator, False, False, 0)
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        body.pack_end(buttons, False, False, 0)
        self.status = _label("")
        self.status.set_ellipsize(3)
        buttons.pack_start(self.status, True, True, 0)
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda _button: self.close())
        buttons.pack_end(cancel, False, False, 0)
        apply = Gtk.Button(label="Apply")
        apply.connect("clicked", self._apply)
        buttons.pack_end(apply, False, False, 0)
        ok = Gtk.Button(label="OK")
        ok.connect("clicked", self._ok)
        buttons.pack_end(ok, False, False, 0)
        self._refresh_themes(self.settings.get("theme", "Vista"))

    def _frame(self, title):
        frame = Gtk.Frame()
        frame.set_label(title)
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        return frame

    def _themes_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)

        menu_frame = self._frame("Menu Selection")
        page.pack_start(menu_frame, True, True, 0)
        frame_contents = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame_contents.set_border_width(10)
        menu_frame.add(frame_contents)

        preview_line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        frame_contents.pack_start(preview_line, True, True, 0)
        self.preview = Gtk.Image()
        self.preview.set_halign(Gtk.Align.CENTER)
        self.preview.set_valign(Gtk.Align.CENTER)
        self.preview.set_size_request(230, 240)
        preview_line.pack_start(self.preview, False, False, 0)
        credits = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_line.pack_start(credits, True, True, 0)
        self.credits = _label("", True)
        credits.pack_start(self.credits, False, False, 8)
        self.dimensions = _label("")
        credits.pack_start(self.dimensions, False, False, 0)

        choices = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        frame_contents.pack_end(choices, False, False, 0)
        install = Gtk.Button(label="Install")
        install.set_tooltip_text("Install an original GnoMenu theme archive")
        install.connect("clicked", self._install)
        choices.pack_start(install, False, False, 0)
        self.uninstall_button = Gtk.Button(label="Uninstall")
        self.uninstall_button.set_tooltip_text("Remove only themes installed through Tilo-Menu Settings")
        self.uninstall_button.connect("clicked", self._uninstall)
        choices.pack_start(self.uninstall_button, False, False, 0)
        self.choice = Gtk.ComboBoxText()
        self.choice.connect("changed", self._preview)
        choices.pack_start(self.choice, True, True, 0)

        other = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        page.pack_start(other, False, False, 0)
        for title, explanation in (
            ("Button Selection", "Original button themes. Panel integration is pending."),
            ("Icon Selection", "Original icon packs. Menu icon mapping is pending."),
        ):
            frame = self._frame(title)
            other.pack_start(frame, True, True, 0)
            information = _label(explanation, True)
            information.set_margin_top(10)
            information.set_margin_bottom(10)
            information.set_margin_start(10)
            information.set_margin_end(10)
            frame.add(information)
        sound = self._frame("Sound Theme")
        page.pack_start(sound, False, False, 0)
        note = _label("Original GnoMenu sound themes will be supported when sound actions are implemented.", True)
        note.set_margin_top(8)
        note.set_margin_bottom(8)
        note.set_margin_start(10)
        sound.add(note)
        return page

    def _preferences_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_border_width(18)
        intro = _label("Options supported by the modern MATE menu renderer", True)
        page.pack_start(intro, False, False, 0)
        self.tab_hover = Gtk.CheckButton(label="Tab Selection on Mouse Hover")
        self.tab_hover.set_active(bool(self.settings.get("tab_hover", False)))
        page.pack_start(self.tab_hover, False, False, 0)
        self.tooltips = Gtk.CheckButton(label="Show tooltips in program list")
        self.tooltips.set_active(bool(self.settings.get("show_tooltips", True)))
        page.pack_start(self.tooltips, False, False, 0)
        icon_line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        page.pack_start(icon_line, False, False, 0)
        self.icon_size = Gtk.SpinButton.new_with_range(16, 48, 2)
        self.icon_size.set_value(max(16, min(48, int(self.settings.get("icon_size", 20)))))
        icon_line.pack_start(self.icon_size, False, False, 0)
        icon_line.pack_start(_label("Icon Size in Program List"), False, False, 0)
        frame = self._frame("Program List Type")
        page.pack_start(frame, False, False, 0)
        info = _label("Cairo rendering (original XML theme artwork, independent of GTK light/dark colors)", True)
        info.set_margin_top(12)
        info.set_margin_bottom(12)
        info.set_margin_start(12)
        frame.add(info)
        page.pack_start(_label("Legacy Compiz blur and GNOME 2 panel options are not applicable to MATE.", True), False, False, 0)
        return page

    def _commands_page(self):
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(14)
        scroller.add(page)
        page.pack_start(_label("MATE command mappings (read-only for safety)", True), False, False, 0)
        commands = (
            ("Search", "mate-search-tool"),
            ("Network Config", "caja network:///"),
            ("Control Panel", "mate-control-center"),
            ("Package Manager", "dnfdragora / gnome-software"),
            ("Help", "yelp"),
            ("Shutdown Dialog", "Confirmation, then systemctl poweroff"),
            ("Lock Screen", "xdg-screensaver lock"),
            ("Logout", "mate-session-save --logout"),
            ("Restart", "Confirmation, then systemctl reboot"),
            ("User About", "mate-about-me"),
        )
        grid = Gtk.Grid()
        grid.set_row_spacing(9)
        grid.set_column_spacing(14)
        page.pack_start(grid, False, False, 0)
        for i, (name, value) in enumerate(commands):
            label = _label(name)
            grid.attach(label, 0, i, 1, 1)
            field = Gtk.Entry()
            field.set_text(value)
            field.set_editable(False)
            field.set_hexpand(True)
            grid.attach(field, 1, i, 1, 1)
        page.pack_start(_label(
            "The original GnoMenu accepted arbitrary command strings. "
            "Tilo-Menu uses known MATE actions and confirmation dialogs.", True
        ), False, False, 0)
        return scroller

    def _about_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_border_width(18)
        title = Gtk.Label()
        title.set_markup("<span size='x-large'><b>Tilo-Menu</b></span>")
        title.set_xalign(0)
        page.pack_start(title, False, False, 0)
        page.pack_start(_label("A GTK3 / MATE continuation of the original GnoMenu 2.9.1", True), False, False, 0)
        page.pack_start(_label(
            "The original GnoMenu project was developed by Whise and its contributors. "
            "Tilo-Menu keeps its XML artwork, layout and theme selection workflow.", True
        ), False, False, 0)
        link = Gtk.LinkButton.new_with_label("https://launchpad.net/gnomenu", "Original GnoMenu project")
        link.set_halign(Gtk.Align.START)
        page.pack_start(link, False, False, 0)
        page.pack_start(_label(
            "Modern additions include application discovery, favorites, MATE account portraits, "
            "secure theme archive import and Cairo rendering.", True
        ), False, False, 0)
        return page

    def _refresh_themes(self, preferred=None):
        self.choice.remove_all()
        choices = installed_themes(self.themes_dir)
        for theme in choices:
            self.choice.append_text(theme.name)
        names = [theme.name for theme in choices]
        if names:
            self.choice.set_active(names.index(preferred) if preferred in names else 0)
        else:
            self.credits.set_text("No Menu themes installed. Click Install.")
            self.preview.clear()
            self.uninstall_button.set_sensitive(False)

    def _preview(self, _widget):
        name = self.choice.get_active_text()
        if not name:
            return
        self.uninstall_button.set_sensitive(name in self.imported)
        try:
            theme = load_menu_theme(self.themes_dir / name)
            preview = theme.directory / "themepreview.png"
            if not preview.is_file():
                preview = theme.directory / theme.background
            # The original settings applet displays themepreview.png.
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(preview), 230, 240, True)
            self.preview.set_from_pixbuf(pixbuf)
            author = theme.metadata.get("Author", "Unknown")
            display = theme.metadata.get("Name", name)
            copyright_notice = theme.metadata.get("Copyright", "")
            self.credits.set_text(f"{display}\nby: {author}\n{copyright_notice}".strip())
            self.dimensions.set_text(f"Theme size: {theme.width} × {theme.height}")
        except (OSError, ValueError, KeyError) as error:
            self.preview.clear()
            self.credits.set_text(f"{name}: {error}")

    def _error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE, text="Unable to install theme",
        )
        dialog.format_secondary_text(str(message))
        dialog.run()
        dialog.destroy()

    def _install(self, _button):
        dialog = Gtk.FileChooserDialog(
            title="Install a new theme", transient_for=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                           "Install", Gtk.ResponseType.OK)
        filt = Gtk.FileFilter()
        filt.set_name("GnoMenu archive (.tar, .tar.gz, .tar.bz2, .tar.xz, .zip)")
        for pattern in ("*.tar", "*.tar.gz", "*.tar.bz2", "*.tar.xz", "*.tgz", "*.zip"):
            filt.add_pattern(pattern)
        dialog.add_filter(filt)
        downloads = Path.home() / "Downloads"
        if downloads.is_dir():
            dialog.set_current_folder(str(downloads))
        result = dialog.run()
        filename = dialog.get_filename() if result == Gtk.ResponseType.OK else None
        dialog.destroy()
        if filename is None:
            return
        try:
            created = import_theme_archive(filename, self.themes_dir)
        except (ThemeImportError, OSError) as error:
            self._error(error)
            return
        self.imported.update(created)
        # Imported artwork is immutable. Install tracking is stored beside
        # user settings, not written into third-party themedata.xml files.
        self.settings["imported_themes"] = sorted(self.imported)
        save_settings(self.settings)
        self._refresh_themes(created[0])
        self.status.set_text("Installed " + ", ".join(created) + ". Click Apply or OK to select.")

    def _uninstall(self, _button):
        name = self.choice.get_active_text()
        if not name or name not in self.imported:
            return
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO, text=f"Uninstall {name}?"
        )
        dialog.format_secondary_text("Only themes imported by Tilo-Menu Settings are removable here.")
        approved = dialog.run() == Gtk.ResponseType.YES
        dialog.destroy()
        if not approved:
            return
        location = self.themes_dir / name
        if location.parent.resolve() != self.themes_dir.resolve() or location.is_symlink():
            self._error("Theme directory is not safe to remove")
            return
        try:
            shutil.rmtree(location)
        except OSError as error:
            self._error(error)
            return
        self.imported.remove(name)
        self.settings["imported_themes"] = sorted(self.imported)
        if self.settings.get("theme") == name:
            self.settings["theme"] = "Vista"
        save_settings(self.settings)
        self._refresh_themes(self.settings.get("theme", "Vista"))
        self.status.set_text(f"{name} uninstalled.")

    def _apply(self, _button):
        name = self.choice.get_active_text()
        if not name:
            return
        self.settings["theme"] = name
        self.settings["tab_hover"] = self.tab_hover.get_active()
        self.settings["show_tooltips"] = self.tooltips.get_active()
        self.settings["icon_size"] = self.icon_size.get_value_as_int()
        save_settings(self.settings)
        self.status.set_text(f"{name} selected. Changes take effect when the menu is reopened.")

    def _ok(self, button):
        self._apply(button)
        self.close()


def show_preferences(themes_dir):
    window = PreferencesWindow(themes_dir)
    window.show_all()
    Gtk.main()

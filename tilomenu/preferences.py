"""Original GnoMenu-style Menu theme preferences for GTK3/MATE.

The XML and original artwork remain authoritative. This window only chooses,
previews and installs themes, then persists the chosen directory name.
"""
import json
import os
import subprocess
from pathlib import Path

from gi.repository import GdkPixbuf, Gio, Gtk

from .themes import load_menu_theme
from .themes.importer import ThemeImportError, import_theme_archive


def preferences_file():
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "tilo-menu" / "settings.json"


def selected_theme():
    try:
        data = json.loads(preferences_file().read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("theme"), str):
            return data["theme"]
    except (OSError, ValueError, TypeError):
        pass
    return "Vista"


def save_theme(name):
    path = preferences_file()
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(old, dict):
            old = {}
    except (OSError, ValueError):
        old = {}
    old["theme"] = name
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")
    os.replace(pending, path)


def installed_themes(directory):
    return sorted(
        (p for p in directory.iterdir()
         if p.is_dir() and (p / "themedata.xml").is_file()),
        key=lambda p: p.name.casefold(),
    ) if directory.is_dir() else []


class PreferencesWindow(Gtk.Window):
    def __init__(self, themes_dir):
        super().__init__(title="Tilo-Menu Preferences")
        self.themes_dir = Path(themes_dir).expanduser()
        self.set_default_size(540, 510)
        self.set_resizable(True)
        self.set_border_width(16)
        self.connect("destroy", Gtk.main_quit)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(outer)
        header = Gtk.Label()
        header.set_markup("<b>Menu Themes</b>")
        header.set_xalign(0)
        outer.pack_start(header, False, False, 0)

        description = Gtk.Label(
            label="Select an original GnoMenu XML theme, or import a downloaded theme archive."
        )
        description.set_line_wrap(True)
        description.set_xalign(0)
        outer.pack_start(description, False, False, 0)

        self.choice = Gtk.ComboBoxText()
        self.choice.connect("changed", self._preview)
        outer.pack_start(self.choice, False, False, 0)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        outer.pack_start(frame, True, True, 0)
        self.preview = Gtk.Image()
        self.preview.set_halign(Gtk.Align.CENTER)
        self.preview.set_valign(Gtk.Align.CENTER)
        frame.add(self.preview)

        self.details = Gtk.Label()
        self.details.set_xalign(0)
        self.details.set_line_wrap(True)
        self.details.set_max_width_chars(66)
        outer.pack_start(self.details, False, False, 0)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.pack_start(actions, False, False, 0)
        add = Gtk.Button(label="Import Theme…")
        add.connect("clicked", self._import_archive)
        actions.pack_start(add, False, False, 0)
        open_folder = Gtk.Button(label="Open Theme Folder")
        open_folder.connect("clicked", self._open_folder)
        actions.pack_start(open_folder, False, False, 0)
        actions.pack_end(Gtk.Button.new_with_label("Close"), False, False, 0)
        close = actions.get_children()[0]
        # pack_end places Close first in Gtk.Box's child collection.
        for child in actions.get_children():
            if child.get_label() == "Close":
                child.connect("clicked", lambda _button: self.close())

        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.pack_start(bottom, False, False, 0)
        self.status = Gtk.Label()
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        bottom.pack_start(self.status, True, True, 0)
        apply = Gtk.Button(label="Apply Theme")
        apply.connect("clicked", self._apply)
        bottom.pack_end(apply, False, False, 0)

        self._refresh_themes(selected_theme())

    def _refresh_themes(self, preferred=None):
        self.choice.remove_all()
        choices = installed_themes(self.themes_dir)
        for theme in choices:
            self.choice.append_text(theme.name)
        names = [theme.name for theme in choices]
        if not names:
            self.details.set_text("No Menu themes installed. Choose Import Theme.")
            self.status.set_text("Theme folder: " + str(self.themes_dir))
            return
        self.choice.set_active(names.index(preferred) if preferred in names else 0)

    def _preview(self, _widget):
        name = self.choice.get_active_text()
        if not name:
            return
        try:
            theme = load_menu_theme(self.themes_dir / name)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(theme.directory / theme.background), 315, 320, True,
            )
            self.preview.set_from_pixbuf(pixbuf)
            author = theme.metadata.get("Author", "Unknown author")
            version = theme.metadata.get("Version", "")
            self.details.set_text(
                f"{name}  |  {theme.width} × {theme.height}  |  {author}"
                + (f"  |  v{version}" if version else "")
            )
        except (OSError, ValueError, KeyError) as error:
            self.preview.clear()
            self.details.set_text(f"{name}: {error}")

    def _error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE, text="Unable to import theme",
        )
        dialog.format_secondary_text(str(message))
        dialog.run()
        dialog.destroy()

    def _import_archive(self, _button):
        dialog = Gtk.FileChooserDialog(
            title="Import Original GnoMenu Theme", transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                           "Import", Gtk.ResponseType.OK)
        filt = Gtk.FileFilter()
        filt.set_name("GnoMenu archives (.tar, .tar.gz, .tar.bz2, .tar.xz, .zip)")
        for pattern in ("*.tar", "*.tar.gz", "*.tar.bz2", "*.tar.xz", "*.zip", "*.tgz"):
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
            imported = import_theme_archive(filename, self.themes_dir)
        except (ThemeImportError, OSError, ValueError) as error:
            self._error(error)
            return
        self._refresh_themes(imported[0])
        self.status.set_text(
            "Imported " + ", ".join(imported) + ". Click Apply Theme to select."
        )

    def _apply(self, _button):
        name = self.choice.get_active_text()
        if not name:
            return
        save_theme(name)
        self.status.set_text(f"{name} selected. The next Tilo-Menu opens with this theme.")

    def _open_folder(self, _button):
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        try:
            Gio.AppInfo.launch_default_for_uri(self.themes_dir.resolve().as_uri(), None)
        except Exception as error:
            self._error(error)


def show_preferences(themes_dir):
    window = PreferencesWindow(themes_dir)
    window.show_all()
    Gtk.main()

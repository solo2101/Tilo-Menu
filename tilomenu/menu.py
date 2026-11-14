"""GTK 3 preview of the original GnoMenu 2.9.1 XML layout.

This is a standalone preview, not yet a MATE panel applet.
Run: python3 -m tilomenu.menu /path/to/Menu/Vista
"""

import argparse
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gtk

from .applications import application_categories, installed_applications, launch_application
from .themes import load_menu_theme
from .themes.renderer import render_theme_buttons
from .icons import load_icon


class MenuWindow(Gtk.Window):
    def __init__(self, theme):
        super().__init__(title="Tilo Menu")
        self.theme = theme
        self.set_default_size(theme.width, theme.height)
        self.set_resizable(False)
        self.set_decorated(False)
        self.connect("destroy", Gtk.main_quit)

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
        self.category = "All Applications"
        self.query = ""
        category_names = sorted({
            category for app in self.all_apps
            for category in application_categories(app)
        })
        self.category_select = Gtk.ComboBoxText()
        for name in ["All Applications", *category_names]:
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

        render_theme_buttons(layout, theme)

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
            if self.category != "All Applications" and self.category not in application_categories(app):
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
            self.apps.add(button)
        self.apps.show_all()

    def _launch(self, _button, app):
        launch_application(app)
        self.close()


def main():
    parser = argparse.ArgumentParser(description="Preview a GnoMenu XML menu theme")
    parser.add_argument("theme_directory", type=Path)
    parser.add_argument("--color", default="white")
    args = parser.parse_args()
    window = MenuWindow(load_menu_theme(args.theme_directory, args.color))
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

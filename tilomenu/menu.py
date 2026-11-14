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

from .applications import installed_applications, launch_application
from .themes import load_menu_theme


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
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(program.integer("Width"), program.integer("Height"))
        layout.put(scroll, program.integer("X"), program.integer("Y"))
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            listbox, listbox row, scrolledwindow, viewport { background: transparent; border: none; }
            listbox row { padding: 0; min-height: 0; }
            button.tilo-app { background: transparent; background-image: none; border: none;
                box-shadow: none; border-radius: 0; padding: 3px 5px; min-height: 26px; }
            button.tilo-app:hover { background: rgba(90, 145, 210, 0.35); }
            button.tilo-app label { font-size: 12px; color: #222; }
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
            entry.connect("search-changed", lambda widget: self._populate(widget.get_text()))

        # Render theme-defined artwork. Legacy commands are intentionally not executed.
        for button in theme.buttons:
            filename = button.attributes.get("Image", "")
            path = theme.directory / filename
            if not filename or not path.is_file():
                continue
            image = Gtk.Image.new_from_file(str(path))
            box = Gtk.Fixed()
            box.put(image, 0, 0)
            markup = button.attributes.get("Markup", "")
            if markup:
                label = Gtk.Label()
                label.set_markup(markup)
                box.put(label, button.integer("TextX"), button.integer("TextY"))
            layout.put(box, button.integer("ButtonX"), button.integer("ButtonY"))
            box.set_tooltip_text(button.attributes.get("Name", ""))

    def _populate(self, query):
        for child in self.apps.get_children():
            self.apps.remove(child)
        for app in installed_applications():
            name = app.get_display_name() or app.get_name()
            if query and query.casefold() not in (name + " " + (app.get_description() or "")).casefold():
                continue
            button = Gtk.Button()
            button.get_style_context().add_class("tilo-app")
            button.set_relief(Gtk.ReliefStyle.NONE)
            content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            icon = app.get_icon()
            if icon is not None:
                image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
                image.set_pixel_size(20)
                content.pack_start(image, False, False, 0)
            label = Gtk.Label(label=name, xalign=0)
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

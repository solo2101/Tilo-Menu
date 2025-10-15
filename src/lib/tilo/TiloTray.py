#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

import sys, os, subprocess

# prefix and i18n
try:
    with open("/etc/tilo/prefix", "r") as f:
        INSTALL_PREFIX = f.read().strip() or "/usr"
except Exception:
    INSTALL_PREFIX = "/usr"

sys.path.append(os.path.join(INSTALL_PREFIX, "lib", "tilo"))

import gettext
gettext.textdomain("tilo")
gettext.install("tilo", os.path.join(INSTALL_PREFIX, "share", "locale"))
gettext.bindtextdomain("tilo", os.path.join(INSTALL_PREFIX, "share", "locale"))

import backend
import Globals
from Menu_Main import Main_Menu


class Tilo:
    def __init__(self):
        # tray icon
        self.tray = Gtk.StatusIcon()
        self.tray.connect("activate", self.on_left_click)
        self.tray.connect("popup-menu", self.on_right_click)
        self.tray.set_tooltip_text("Tilo")
        self.tray.set_visible(True)
        self._set_tray_icon()

        # menu window
        self.hwg = Main_Menu(self.hide_menu)
        self.showing = False

        # right click menu
        self.menu = Gtk.Menu()
        self._add_item(_("Preferences"), self.on_prefs)
        self._add_item(_("About"), self.on_about)
        self._add_item(_("Edit Menus"), self.on_edit)
        self._add_item(_("Quit"), self.on_quit)

        Gtk.main()

    # ------------- icon helpers -------------
    def _set_tray_icon(self):
        try:
            if Globals.Settings.get("Distributor_Logo"):
                import IconFactory as iconfactory
                icon_path = iconfactory.GetSystemIcon("distributor-logo") or Globals.Applogo
            else:
                icon_path = Globals.Applogo
            if icon_path and os.path.isfile(icon_path):
                pb = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                self.tray.set_from_pixbuf(pb)
            else:
                self.tray.set_from_icon_name("applications-system")
        except Exception:
            self.tray.set_from_icon_name("applications-system")

    def _add_item(self, label, cb):
        mi = Gtk.MenuItem.new_with_label(label)
        mi.connect("activate", cb)
        self.menu.append(mi)
        self.menu.show_all()

    # ------------- geometry -------------
    def _tray_xy(self, for_menu_height=0):
        ok, screen, area, orient = self.tray.get_geometry()
        if not ok or screen is None or area is None:
            # fallback to pointer
            display = Gdk.Display.get_default()
            seat = display.get_default_seat()
            device = seat.get_pointer()
            screen, px, py = device.get_position()
            return int(px), int(py), screen
        # anchor under or above the tray area
        if area.y < screen.get_height() / 2:
            backend.save_setting("orientation", "top")
            x = area.x
            y = area.y + area.height
        else:
            backend.save_setting("orientation", "bottom")
            x = area.x
            y = max(0, area.y - int(for_menu_height))
        return int(x), int(y), screen

    def _position_menu(self, menu, *args):
        x, y, screen = self._tray_xy(for_menu_height=menu.get_allocated_height())
        menu.set_screen(screen)
        return (x, y, True)  # x, y, push_in

    # ------------- tray signals -------------
    def on_right_click(self, _icon, button, activate_time):
        # Avoid Gtk.StatusIcon.position_menu to prevent tray glitches
        self.menu.popup(None, None, self._position_menu, None, button, activate_time)

    def on_left_click(self, _icon):
        if not self.showing:
            x, y, _screen = self._tray_xy(for_menu_height=getattr(Globals, "MenuHeight", 300))
            self.hwg.Adjust_Window_Dimensions(x, y)
            self.hwg.show_window()
            self.showing = True
        else:
            self.hide_menu()

    # ------------- actions -------------
    def on_quit(self, *_):
        try:
            self.hwg.destroy()
        except Exception:
            pass
        Gtk.main_quit()

    def on_edit(self, *_):
        cmd = Globals.Settings.get("MenuEditor") or "menulibre"
        subprocess.Popen(["sh", "-c", f"{cmd} &"])

    def on_about(self, *_):
        subprocess.Popen(["sh", "-c", f"{INSTALL_PREFIX}/lib/{Globals.appdirname}/Tilo-Settings.py --about &"])

    def on_prefs(self, *_):
        # fixed quoting
        subprocess.Popen(["sh", "-c", f"'{Globals.ProgramDirectory}Tilo-Settings.py' &"])

    def hide_menu(self):
        self.showing = False
        self.hwg.hide_window()


if __name__ == "__main__":
    Tilo()
    sys.exit(0)

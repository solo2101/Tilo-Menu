#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk

import os
import sys

# install prefix
try:
    with open("/etc/tilo/prefix", "r") as f:
        INSTALL_PREFIX = f.read().strip() or "/usr"
except Exception:
    INSTALL_PREFIX = "/usr"

sys.path.append(os.path.join(INSTALL_PREFIX, "lib", "tilo"))

import Globals
import backend
from Menu_Main import Main_Menu


class TiloDO:
    def __init__(self):
        # read saved panel hints
        self.orientation = backend.load_setting("orientation") or "bottom"
        try:
            self.panel_size = int(backend.load_setting("size") or 32)
        except Exception:
            self.panel_size = 32

        # menu window
        self.menu = Main_Menu(self._on_hide)

        # place and show
        x, y = self._anchor_xy()
        self.menu.Adjust_Window_Dimensions(x, y)
        self.menu.show_window()

    def _on_hide(self):
        self.menu.hide_window()
        Gtk.main_quit()

    def _primary_monitor_geo(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        if not monitor:
            monitor = display.get_monitor(0)
        geo = monitor.get_geometry()
        scale = monitor.get_scale_factor() if hasattr(monitor, "get_scale_factor") else 1
        return geo.x, geo.y, geo.width, geo.height, scale

    def _anchor_xy(self):
        px, py, pw, ph, scale = self._primary_monitor_geo()
        m_w = int(getattr(Globals, "MenuWidth", 400))
        m_h = int(getattr(Globals, "MenuHeight", 300))

        # center on primary, offset from panel edge
        x = px + max(0, (pw - m_w) // 2)
        if (self.orientation or "bottom").lower() == "top":
            y = py + int(self.panel_size)
        else:
            y = py + max(0, ph - m_h - int(self.panel_size))

        return int(x), int(y)


def main():
    # if spawned with --toggle in the future, handle here
    _ = TiloDO()
    Gtk.main()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License
# v3 (or, at your option, any later version). See http://www.gnu.org/licenses/gpl.txt
#
# (c) Whise 2010 <helderfraga@gmail.com>
# Updated for Python 3 + XDG-only by <you/2025>
#
# Menu parser (XDG only)

import os
import gc

import gi
from gi.repository import GObject, Gio, GLib

import xdg.Menu
import xdg.BaseDirectory as bd

import Globals


class MenuParser(GObject.GObject):
    __gsignals__ = {
        'menu-changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()

        # We’ve dropped matemenu support; keep this flag for compatibility with callers.
        self.has_matemenu = False

        # Expose these types so isinstance() checks elsewhere keep working.
        self.MenuInstance = xdg.Menu.Menu
        self.EntryInstance = xdg.Menu.MenuEntry

        # Parsed menus
        self.CacheApplications = None
        self.CacheSettings = None

        # Menu filenames (pyxdg provides .Filename on parsed menus)
        self.AppsFile = None
        self.SetFile = None

        # Update debounce
        self._updating = False
        self._timeout_id = None

        # Gio monitors we keep alive
        self._monitors = []

        self.ParseMenus()

    # -----------------------
    # Public API used by callers
    # -----------------------

    def ParseMenus(self):
        """Parse menus using pyxdg (XDG-only). Also (re)arm Gio monitors."""
        # Cancel old monitors before re-parsing (avoid duplicate callbacks)
        self._cancel_monitors()

        # Applications
        self.CacheApplications = None
        try_order = [
            os.environ.get("XDG_MENU_PREFIX", "") + "applications.menu",
            "mate-applications.menu",
        ]
        for candidate in try_order:
            try:
                self.CacheApplications = xdg.Menu.parse(candidate)
                break
            except Exception:
                continue
        if self.CacheApplications is None:
            print("MenuParser: unable to parse applications.menu")
        else:
            self.AppsFile = getattr(self.CacheApplications, "Filename", None)

        # Settings
        self.CacheSettings = None
        try_order = [
            "settings.menu",
            "mate-settings.menu",
            os.environ.get("XDG_MENU_PREFIX", "") + "settings.menu",
        ]
        for candidate in try_order:
            try:
                self.CacheSettings = xdg.Menu.parse(candidate)
                break
            except Exception:
                continue
        if self.CacheSettings is None:
            print("MenuParser: unable to parse settings.menu")
        else:
            self.SetFile = getattr(self.CacheSettings, "Filename", None)

        # Arm Gio monitors for .desktop changes and the menu files themselves
        self._setup_monitors()

    def GetMenuEntries(self, menu):
        """Return entries for a given xdg.Menu.Menu."""
        return menu.getEntries()

    def GetDirProps(self, entry):
        """
        For a 'directory' (submenu) entry:
        returns (name, icon, path, comment)
        path is the menu path string, used later with BaseMenu.getMenu(path)
        """
        # pyxdg Menu objects
        if hasattr(entry, "getName"):
            name = entry.getName()
            icon = entry.getIcon()
            # getPath(True) returns a string path suitable for getMenu()
            path = entry.getPath(True)
            comment = entry.getComment() if Globals.Settings.get('Show_Tips') else ''
            return name, icon, path, comment
        # Fallback
        return "", "", "", ""

    def GetEntryProps(self, entry):
        """
        For an application (desktop entry):
        returns (name, icon, exec, comment)
        """
        de = entry.DesktopEntry
        name = de.getName()
        icon = de.getIcon()
        execute = de.getExec()
        comment = de.getComment() if Globals.Settings.get('Show_Tips') else ''
        return name, icon, execute, comment

    # -----------------------
    # Gio monitoring
    # -----------------------

    def _setup_monitors(self):
        """Monitor XDG applications dirs and the actual .menu files for changes."""
        # 1) Monitor every .../applications directory in XDG data dirs
        dirs = list(bd.xdg_data_dirs)
        if bd.xdg_data_home not in dirs:
            dirs.append(bd.xdg_data_home)

        for d in dirs:
            appdir = os.path.join(d, "applications")
            if os.path.isdir(appdir):
                f = Gio.File.new_for_path(appdir)
                mon = f.monitor_directory(Gio.FileMonitorFlags.NONE, None)
                mon.connect("changed", self._monitor_callback)
                self._monitors.append(mon)

        # 2) Monitor the actual menu files if we know their paths
        for path in (self.AppsFile, self.SetFile):
            if path and os.path.isfile(path):
                f = Gio.File.new_for_path(path)
                mon = f.monitor_file(Gio.FileMonitorFlags.NONE, None)
                mon.connect("changed", self._monitor_callback)
                self._monitors.append(mon)

    def _cancel_monitors(self):
        for mon in self._monitors:
            try:
                mon.cancel()
            except Exception:
                pass
        self._monitors = []

    def _monitor_callback(self, monitor, file, other_file, event_type):
        """Debounce filesystem changes and re-emit 'menu-changed'."""
        if not self._updating:
            self._updating = True
            # debounce rapid bursts
            self._timeout_id = GLib.timeout_add(1000, self._menu_changed)

    def _menu_changed(self):
        print("MenuParser: menu changed, reparsing …")
        self.ParseMenus()
        self.emit('menu-changed')
        gc.collect()
        self._updating = False
        self._timeout_id = None
        return False  # stop timeout

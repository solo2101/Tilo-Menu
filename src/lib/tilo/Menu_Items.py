#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GNU GPL v3+ — Tilo (Menu Items)
# Modernized for Python 3 / Gtk 3 / Gio

import os
import gc
from urllib.parse import unquote

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, GObject, Gio, Gdk, GLib

import backend
import utils
from Popup_Menu import add_menuitem, add_image_menuitem
import Globals
import MenuParser
import IconFactory
import Launcher

try:
    import bookmarks
except Exception:
    print("warning: bookmarks module not available")

try:
    import zg  # zeitgeist (optional)
except Exception:
    zg = None

try:
    INSTALL_PREFIX = open("/etc/tilo/prefix", "r", encoding="utf-8").read().strip()
except Exception:
    INSTALL_PREFIX = "/usr"

if getattr(Globals, "FirstUse", False):
    os.system(f"/bin/sh -c '{INSTALL_PREFIX}/lib/{Globals.appdirname}/Tilo-Settings.py --welcome' &")

import gettext
gettext.textdomain('tilo')
gettext.bindtextdomain('tilo', INSTALL_PREFIX + '/share/locale')
gettext.install('tilo', INSTALL_PREFIX + '/share/locale')

def _(s):
    return gettext.gettext(s)


# --------------------------
# Helpers
# --------------------------

def _uri_to_path(uri_or_path: str) -> str:
    """Return a local filesystem path for file:/// URIs or passthrough paths."""
    if not uri_or_path:
        return ""
    if uri_or_path.startswith("file://"):
        return unquote(uri_or_path[7:])
    return unquote(uri_or_path)


# --------------------------
# XDG/MATE Menu
# --------------------------

class XDMateMenu(GObject.GObject):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()
        if not os.path.isdir(Globals.AutoStartDirectory):
            os.makedirs(Globals.AutoStartDirectory, exist_ok=True)

        self.notifier = utils.Notifier()
        self.menuparser = MenuParser.MenuParser()
        self.menuparser.connect('menu-changed', self.MenuChanged)

        self.menucache = {}
        self.nonMenuitems = (
            '<Bookmarks>', '<AuxiliaryFunctions>', '<RecentItems>',
            '<RecentApps>', '<WebBookmarks>', '<Favorites>', '<Shutdown>'
        )

        if Globals.OnlyShowFavs:
            self.BaseMenu = '<Favorites>'
            self.menuparser.CacheApplications = None
            self.menuparser.CacheSettings = None
        elif Globals.OnlyShowRecentApps:
            self.BaseMenu = '<RecentApps>'
            self.menuparser.CacheApplications = None
            self.menuparser.CacheSettings = None
        else:
            self.menuparser.ParseMenus()
            self.BaseMenu = self.menuparser.CacheApplications

        # Gio monitors & app-info
        self.monitor = Gio.VolumeMonitor.get()
        # Refresh bookmarks on relevant signals
        for sig in ("mount-added", "mount-removed", "volume-added", "volume-removed", "drive-changed"):
            try:
                self.monitor.connect(sig, self.on_drive_changed)
            except Exception:
                pass

        try:
            self.allgio = Gio.AppInfo.get_all()
        except Exception:
            self.allgio = None

        self.Launcher = Launcher.Launcher()
        self.recent_manager = Gtk.RecentManager.get_default()
        self.recent_manager.connect("changed", self.onRecentChanged)
        self.recents_changed = True
        self.recent = None

        self.ItemComments = {}
        self.Menu = self.BaseMenu
        self.PrevMenu = []
        self.searchresults = 0

        # Icon factory
        self.IconFactory = IconFactory.IconFactory()

        # Web bookmarks
        try:
            self.webbookmarker = bookmarks.BookmarksMenu().getBookmarks()
        except Exception:
            self.webbookmarker = None

        # Preload common “root” menus
        self.menuitems = (
            'settings', 'places', 'auxiliary', 'recent', 'recentapps',
            'webbookmarks', 'favorites', 'shutdown', 'all'
        )
        for item in self.menuitems:
            self.Restart(item)
        gc.collect()

    # --------- change & restart ----------

    def MenuChanged(self, _event):
        # Drop all cached menus except nonMenuitems
        for item in list(self.menucache.keys()):
            if item not in self.nonMenuitems:
                del self.menucache[item]

        # Keep current BaseMenu pointer consistent with parser caches
        if isinstance(self.Menu, self.menuparser.MenuInstance) and self.menuparser.has_matemenu:
            if self.BaseMenu.get_name() == self.menuparser.CacheApplications.get_name():
                self.BaseMenu = self.menuparser.CacheApplications
            elif self.BaseMenu.get_name() == self.menuparser.CacheSettings.get_name():
                self.BaseMenu = self.menuparser.CacheSettings
        else:
            if self.BaseMenu == self.menuparser.CacheApplications:
                self.BaseMenu = self.menuparser.CacheApplications
            elif self.BaseMenu == self.menuparser.CacheSettings:
                self.BaseMenu = self.menuparser.CacheSettings

        self.emit('changed')
        gc.collect()

    def Restart(self, menu='all'):
        """Switch base menu target and rebuild."""
        if Globals.OnlyShowFavs and (menu in ('all', 'settings')):
            menu = 'favorites'
        if Globals.OnlyShowRecentApps and (menu in ('all', 'settings')):
            menu = 'recentapps'

        if menu == 'all':
            self.Menu = self.BaseMenu = self.menuparser.CacheApplications
            self.ConstructMenu()
            return True
        elif menu == 'settings':
            self.Menu = self.BaseMenu = self.menuparser.CacheSettings
            self.ConstructMenu()
            return True
        elif menu == 'places':
            self.Menu = self.BaseMenu = "<Bookmarks>"
            self.ConstructMenu()
            return True
        elif menu == 'auxiliary':
            self.Menu = self.BaseMenu = "<AuxiliaryFunctions>"
            self.ConstructMenu()
            return True
        elif menu == 'recent':
            self.Menu = self.BaseMenu = "<RecentItems>"
            self.ConstructMenu()
            return True
        elif menu == 'recentapps':
            self.Menu = self.BaseMenu = "<RecentApps>"
            self.ConstructMenu()
            return True
        elif menu == 'webbookmarks':
            self.Menu = self.BaseMenu = "<WebBookmarks>"
            self.ConstructMenu()
            return True
        elif menu == 'favorites':
            self.Menu = self.BaseMenu = "<Favorites>"
            self.ConstructMenu()
            return True
        elif menu == 'shutdown':
            self.Menu = self.BaseMenu = "<Shutdown>"
            self.ConstructMenu()
            return True
        elif menu == 'previous':
            self.Menu = self.BaseMenu
            self.ConstructMenu()
            return True
        return False

    # --------- list building helpers ----------

    def addtomenu(self, names, icons, types, paths, execs):
        """Append one item into the working lists."""
        if icons is None:
            icons = 'image-missing'
        self.L_Names.append(names)
        self.L_Icons.append(self.IconFactory.geticonfile(icons))
        self.L_Icons_menu.append(icons)
        self.L_Types.append(types)
        self.L_Paths.append(paths)
        self.L_Execs.append(execs)

    # --------- signals/caches ----------

    def onRecentChanged(self, _manager):
        """Recent files changed."""
        self.recents_changed = True
        try:
            del self.menucache["<RecentItems>"]
            del self.menucache["<RecentApps>"]
        except Exception:
            pass
        if self.BaseMenu == "<RecentItems>":
            self.emit('changed')

    def on_drive_changed(self, *_args):
        """Volumes/mounts changed."""
        try:
            del self.menucache["<Bookmarks>"]
        except Exception:
            pass
        if self.BaseMenu == "<Bookmarks>":
            self.emit('changed')

    # --------- building the menu ----------

    def ConstructMenu(self):
        key = str(self.Menu)
        if key in self.menucache:
            (self.L_Names, self.L_Icons, self.L_Icons_menu,
             self.L_Types, self.L_Paths, self.L_Execs) = self.menucache[key]
            return

        self.L_Names = []
        self.L_Icons = []
        self.L_Types = []
        self.L_Paths = []
        self.L_Execs = []
        self.L_Icons_menu = []
        self.searchresults = 0

        # --- XDG programs (normal navigation) ---
        if isinstance(self.Menu, self.menuparser.MenuInstance):

            if Globals.Settings.get('Shownetandemail', 0) == 1:
                if self.BaseMenu == self.menuparser.CacheApplications:
                    self.AddInternetButtons()

            for entry in self.menuparser.GetMenuEntries(self.Menu):
                if isinstance(entry, self.menuparser.MenuInstance):  # folder
                    name, icon, path, comment = self.menuparser.GetDirProps(entry)
                    self.addtomenu(name, icon, 0, path, "")
                    if Globals.Settings.get('Show_Tips'):
                        self.ItemComments[name] = comment
                elif isinstance(entry, self.menuparser.EntryInstance):  # app
                    name, icon, execute, comment = self.menuparser.GetEntryProps(entry)
                    self.addtomenu(name, icon, 1, "", execute)
                    if Globals.Settings.get('Show_Tips'):
                        self.ItemComments[name] = comment

            if self.Menu == self.menuparser.CacheApplications and int(Globals.Settings.get('Disable_PS', 0)) == 0:
                self.AddPlacesButton()
                self.AddSystemButton()

        # --- Auxiliary functions ---
        elif self.Menu == "<AuxiliaryFunctions>":
            self.addtomenu(_("About Me"), "user-info", 5, "", "mate-about-me")
            self.addtomenu(_("Appearance"), "mate-settings-theme", 5, "", "mate-appearance-properties")
            self.addtomenu(_("Menu editor"), "mozo", 6, "", "mozo")
            self.addtomenu(_("Screensaver"), "preferences-desktop-screensaver", 5, "", "mate-screensaver-preferences")
            self.addtomenu(_("System Monitor"), "utilities-system-monitor", 5, "", "mate-system-monitor")
            self.addtomenu(_("Tilo settings utility"), f"{Globals.GraphicsDirectory}logo.png", 7, "", f"{Globals.ProgramDirectory}Tilo-Settings.py")

        # --- Favorites ---
        elif self.Menu == "<Favorites>":
            favs = backend.load_setting("favorites") or []
            try:
                favs.sort(key=str.upper)
            except Exception:
                pass

            for elem in favs:
                try:
                    name, exe, ico, typ = elem.split('::')
                    self.addtomenu(name, ico, int(typ), "", exe)
                except Exception:
                    backend.save_setting("favorites", [])

            if not favs:
                self.addtomenu(
                    _('No favorites\nUse the mouse right button\nto add or remove favorites'),
                    'image-missing', 9, "", ""
                )

        # --- Web Bookmarks ---
        elif self.Menu == "<WebBookmarks>":
            try:
                if self.webbookmarker is None:
                    self.webbookmarker = bookmarks.BookmarksMenu().getBookmarks()
                for item in map(list, self.webbookmarker):
                    # item: [title, url, ???, icon]
                    self.addtomenu(item[0], item[3], 3, item[1], item[1])
            except Exception:
                print("Error reading web bookmarks")

        # --- Shutdown actions ---
        elif self.Menu == "<Shutdown>":
            self.addtomenu(_('Shutdown'), 'system-shutdown', 1, "", Globals.Settings['Shutdown'])
            self.addtomenu(_('Reboot'), 'system-reboot', 1, "", Globals.Settings['Restart'])
            self.addtomenu(_('Suspend'), 'system-suspend', 1, "", Globals.Settings['Suspend'])
            self.addtomenu(_('Hibernate'), 'system-hibernate', 1, "", Globals.Settings['Hibernate'])
            self.addtomenu(_('Logout'), 'system-log-out', 1, "", Globals.Settings['LogoutNow'])
            self.addtomenu(_('Lock Screen'), 'system-lock-screen', 1, "", Globals.Settings['Lock'])

        # --- Recent items (files) ---
        elif self.Menu == "<RecentItems>":
            if self.recents_changed or self.recent is None:
                self.recent = self.recent_manager.get_items()
                self.recents_changed = False
                # newest first
                self.recent.sort(key=lambda it: it.get_modified(), reverse=True)

            x = 0
            for item in self.recent:
                name = item.get_display_name() or item.get_short_name()
                self.L_Names.append(name)
                self.L_Icons.append(self.IconFactory.getthumb(item))
                self.L_Icons_menu.append(name)
                self.L_Types.append(3)
                self.L_Paths.append("")
                self.L_Execs.append(item.get_uri())
                x += 1
                if x == Globals.RI_numberofitems:
                    break
            self.addtomenu(_('Clear recent documents'), 'edit-clear', 10, "", "")
            self.sorted_list = []

        # --- Recent apps (derived from recent files) ---
        elif self.Menu == "<RecentApps>":
            if self.recents_changed or self.recent is None:
                self.recent = self.recent_manager.get_items()
                self.recents_changed = False
                self.recent.sort(key=lambda it: it.get_modified(), reverse=True)

            seen = set()
            x = 0
            for item in self.recent:
                mime = item.get_mime_type()
                try:
                    app = Gio.AppInfo.get_default_for_type(mime, False)
                except Exception:
                    app = None
                if app:
                    name = app.get_name()
                    if name not in seen:
                        seen.add(name)
                        icon = self.IconFactory.getgicon(app.get_icon())
                        self.addtomenu(name, icon, 1, "", app.get_executable())
                        x += 1
                        if x == Globals.RI_numberofitems:
                            break
            self.sorted_list = []

        # --- Bookmarks / Places ---
        elif self.Menu == "<Bookmarks>":
            self.addtomenu(_("File System"), "drive-harddisk", 3, "/", "/")

            # Drives & volumes
            try:
                for drive in self.monitor.get_connected_drives():
                    if drive.has_media():
                        for volume in drive.get_volumes():
                            ico = volume.get_icon()
                            a = self.IconFactory.getgicon(ico)
                            self.L_Names.append(volume.get_name())
                            self.L_Icons.append(self.IconFactory.geticonfile(a))
                            self.L_Icons_menu.append(a)
                            self.L_Types.append(3)
                            self.L_Paths.append("")
                            try:
                                mount = volume.get_mount()
                                root = mount.get_root() if mount else None
                                self.L_Execs.append(
                                    _uri_to_path(root.get_uri()) if root else ""
                                )
                            except Exception:
                                self.L_Execs.append("")
            except Exception:
                pass

            self.addtomenu(_('Home Folder'), "user-home", 3, "", Globals.HomeDirectory)
            self.addtomenu(_('Computer'), "computer", 3, "", 'computer:///')
            self.addtomenu(_('Network'), "network", 3, "", 'network:///')
            self.addtomenu(_('Trash'), 'user-trash', 3, "", 'trash:///')

            # Legacy GTK bookmarks (~/.gtk-bookmarks)
            gtk_bm = os.path.join(Globals.HomeDirectory, ".gtk-bookmarks")
            if os.path.isfile(gtk_bm):
                try:
                    with open(gtk_bm, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            bm = line.strip()
                            if not bm:
                                continue
                            if ' ' in bm:
                                folder, name = bm.split(' ', 1)
                                folder = _uri_to_path(folder)
                                name = unquote(name)
                            else:
                                folder = bm
                                name = os.path.basename(_uri_to_path(bm))
                            try:
                                gfile = Gio.File.new_for_path(folder) if not folder.startswith("file://") else Gio.File.new_for_uri(folder)
                                info = gfile.query_info("standard::*", Gio.FileQueryInfoFlags.NONE, None)
                                ico = info.get_icon()
                                self.addtomenu(name, self.IconFactory.getgicon(ico), 3, "", folder)
                            except Exception:
                                self.addtomenu(name, "folder", 3, "", folder)
                except Exception:
                    pass

        # --- Search mode ---
        else:
            for i in [self.menuparser.CacheApplications, self.menuparser.CacheSettings]:
                for entry in self.menuparser.GetMenuEntries(i):
                    if isinstance(entry, self.menuparser.MenuInstance):
                        if self.menuparser.has_matemenu:
                            self.SearchMenu(self.menuparser.GetDirProps(entry)[2])
                        else:
                            self.SearchMenu(i.getMenu(entry.getPath(True)))
                    elif isinstance(entry, self.menuparser.EntryInstance):
                        name, icon, execute, comment = self.menuparser.GetEntryProps(entry)
                        if self.Menu in name.upper() or self.Menu in execute.upper():
                            self.addtomenu(name, icon, 1, "", execute)
                            self.searchresults += 1

            if self.searchresults == 0:
                self.addtomenu("<separator>", "", 8, "", "")
                self.addtomenu(_("No items matched your search criteria"), "", 9, "", "")
            else:
                self.addtomenu("<separator>", "", 8, "", "")
                self.addtomenu(_("Found %s results to your search") % str(self.searchresults), "", 9, "", "")

        # Add Back button when appropriate
        if isinstance(self.Menu, self.menuparser.MenuInstance):
            if self.Menu != self.menuparser.CacheApplications:
                self.AddBackButton()
        else:
            if Globals.MenuTabCount == 0:
                if not Globals.OnlyShowFavs and not Globals.OnlyShowRecentApps:
                    self.AddBackButton()
                else:
                    if self.Menu not in ("<Favorites>", "<RecentApps>"):
                        self.AddBackButton()

        self.menucache[key] = (
            self.L_Names, self.L_Icons, self.L_Icons_menu,
            self.L_Types, self.L_Paths, self.L_Execs
        )

    def SearchMenu(self, folder):
        for entry in self.menuparser.GetMenuEntries(folder):
            if isinstance(entry, self.menuparser.MenuInstance):
                if self.menuparser.has_matemenu:
                    self.SearchMenu(self.menuparser.GetDirProps(entry)[2])
                else:
                    self.SearchMenu(self.BaseMenu.getMenu(entry.getPath(True)))
            elif isinstance(entry, self.menuparser.EntryInstance):
                name, icon, execute, comment = self.menuparser.GetEntryProps(entry)
                if self.Menu in name.upper() or self.Menu in execute.upper():
                    self.addtomenu(name, icon, 1, "", execute)
                    self.searchresults += 1

    # --------- convenience adders ----------

    def AddInternetButtons(self):
        # add a trailing space to avoid name collision with “Internet” section
        self.addtomenu(_("Browse Internet") + " ", "web-browser", 1, "", backend.get_default_internet_browser())
        self.addtomenu(_("E-mail") + " ", "emblem-mail", 1, "", backend.get_default_mail_client())

    def AddBackButton(self):
        self.addtomenu(_("Back"), "go-previous", 2, "", "")

    def AddPlacesButton(self):
        self.addtomenu(_("Places"), "drive-harddisk", 2, "", "")

    def AddSystemButton(self):
        self.addtomenu(_("System"), "preferences-system", 2, "", "")

    # --------- activation & context menu ----------

    def ButtonClick(self, index, event=None):
        """Handle activation based on L_Types."""
        etype = self.L_Types[index]

        # Normalize event/button
        event_button = 1
        if event is not None:
            if event.type == Gdk.EventType.KEY_PRESS:
                event_button = 1
            elif hasattr(event, "button"):
                event_button = event.button

        if event_button == 1:
            if etype == 0:  # folder
                self.PrevMenu.append(self.Menu)
                if self.menuparser.has_matemenu:
                    self.Menu = self.L_Paths[index]
                else:
                    self.Menu = self.BaseMenu.getMenu(self.L_Paths[index])
                self.ConstructMenu()

            elif etype in (1, 3, 4):  # app or recent
                self.Launcher.Launch(self.L_Execs[index], etype)
                self.Restart('previous')
                return 1

            elif etype == 2:  # special buttons: places/settings/back
                name = self.L_Names[index]
                if name == _('Back'):
                    try:
                        self.Menu = self.PrevMenu.pop()
                    except Exception:
                        self.Menu = self.BaseMenu = self.menuparser.CacheApplications
                    if self.Menu == self.menuparser.CacheApplications:
                        self.BaseMenu = self.Menu
                    self.ConstructMenu()
                elif name == _("System"):
                    self.PrevMenu.append(self.Menu)
                    self.Restart('settings')
                elif name == _("Places"):
                    self.PrevMenu.append(self.Menu)
                    self.Restart('places')

            elif etype in (5, 6):  # items changed (menu editor, etc.)
                self.Launcher.Launch(self.L_Execs[index], etype)

            elif etype == 7:  # properties changed
                self.Launcher.Launch(self.L_Execs[index], etype)
                Globals.ReloadSettings()

            elif etype == 10:  # clear recent
                self.recent_manager.purge_items()
                self.Restart('previous')

        elif event_button == 3:
            # Context menu
            m = Gtk.Menu()
            name = self.L_Names[index]
            favlist = backend.load_setting("favorites") or []

            try:
                thismenu = add_image_menuitem(m, self.L_Icons_menu[index], name, self.dummy, '1')
            except Exception:
                return

            # Zeitgeist recent/most used for this app (optional)
            if zg and self.allgio is not None:
                recent_files = None
                most_used_files = None
                for z in self.allgio:
                    if z.get_name() == name:
                        desk = z.get_id()
                        recent_files = zg.get_recent_for_app(desk, Globals.RI_numberofitems)
                        most_used_files = zg.get_most_used_for_app(desk, Globals.RI_numberofitems)
                        break
                if recent_files or most_used_files:
                    add_menuitem(m, "-")
                for files, menu_name in ((recent_files, _('Recently Used')), (most_used_files, _('Most Used'))):
                    if files:
                        submenu = Gtk.Menu()
                        menu_item = Gtk.MenuItem.new_with_label(menu_name)
                        menu_item.set_submenu(submenu)
                        m.append(menu_item)
                        menu_item.show()
                        for ev in files:
                            for subject in ev.get_subjects():
                                label = subject.text or subject.uri
                                submenu_item = Gtk.MenuItem.new_with_label(label)
                                submenu.append(submenu_item)
                                submenu_item.connect("button-press-event", self.launch_item, subject.uri)
                                submenu_item.show()

            if etype != 0 and name != _('Back'):
                if etype != 3:
                    add_menuitem(m, "-")
                    add_image_menuitem(
                        m, 'dialog-password', _("Open as Administrator"),
                        self.runasadmin, name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index]
                    )
                else:
                    # Recent file submenu: list folder entries and open-with
                    f = os.path.abspath(_uri_to_path(self.L_Execs[index]))
                    if os.path.exists(f):
                        if os.path.isdir(f):
                            submenu = Gtk.Menu()
                            thismenu.set_submenu(submenu)

                            def searchfolder(folder, me):
                                try:
                                    entries = sorted(os.listdir(folder), key=str.upper)
                                except Exception:
                                    entries = []
                                for item in entries:
                                    if item.startswith('.'):
                                        continue
                                    full = os.path.join(folder, item)
                                    if os.path.isdir(full):
                                        add_image_menuitem(me, 'folder', item, self.launch_item, '"' + full + '"')
                                    else:
                                        submenu_item = Gtk.MenuItem.new_with_label(item)
                                        me.append(submenu_item)
                                        submenu_item.connect("button-press-event", self.launch_item, '"' + full + '"')
                                        submenu_item.show()

                            searchfolder(f, submenu)

                        elif os.path.isfile(f):
                            add_menuitem(m, "-")
                            openwith = add_image_menuitem(m, 'document-open', _("Open with"))
                            # Query content-type and list apps
                            try:
                                gfile = Gio.File.new_for_path(f)
                                info = gfile.query_info("standard::*", Gio.FileQueryInfoFlags.NONE, None)
                                ctype = info.get_content_type()
                                apps = Gio.AppInfo.get_all_for_type(ctype) or []
                                submenu = Gtk.Menu()
                                openwith.set_submenu(submenu)
                                for app in apps:
                                    add_menuitem(
                                        submenu, app.get_name(), self.custom_launch,
                                        "'" + f + "'", app.get_executable()
                                    )
                            except Exception:
                                pass

                    if name == _('Trash'):
                        add_menuitem(m, "-")
                        add_image_menuitem(m, 'edit-clear', _("Empty Trash"), self.emptytrash)

                # Favorites add/remove
                fav_key = f"{name}::{self.L_Execs[index]}::{self.L_Icons_menu[index]}::{str(self.L_Types[index])}"
                add_menuitem(m, "-")
                if fav_key not in favlist:
                    add_image_menuitem(m, 'list-add', _("Add to Favorites"),
                                       self.addfav, name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])
                else:
                    add_image_menuitem(m, 'list-remove', _("Remove from Favorites"),
                                       self.removefav, name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])

                # Desktop shortcut
                add_menuitem(m, "-")
                add_image_menuitem(m, 'go-home', _("Create Desktop Shortcut"),
                                   self.addshort, name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])

                # Autostart add/remove
                add_menuitem(m, "-")
                autostarter = f"{Globals.AutoStartDirectory}{name}.desktop"
                if os.path.basename(autostarter) in os.listdir(Globals.AutoStartDirectory):
                    add_image_menuitem(m, 'list-remove', _("Remove from System Startup"),
                                       self.remove_autostarter, name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])
                else:
                    add_image_menuitem(m, 'list-add', _("Add to System Startup"),
                                       self.create_autostarter, name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])

            m.show_all()
            # Gtk 3: prefer popup_at_pointer if available
            try:
                m.popup_at_pointer(event)
            except Exception:
                m.popup(None, None, None, None, getattr(event, "button", 0), getattr(event, "time", 0))
            gc.collect()

    # --------- context helpers ----------

    def emptytrash(self, *_args):
        trash1 = os.path.join(Globals.HomeDirectory, ".local/share/Trash")
        trash2 = os.path.join(Globals.HomeDirectory, ".Trash")
        if os.path.exists(trash1):
            os.system(f"rm -rf '{trash1}/info/*' &")
            os.system(f"rm -rf '{trash1}/files/*' &")
        elif os.path.exists(trash2):
            os.system(f"rm -rf '{trash2}/*' &")

    def custom_launch(self, _widget, _event, uri, app):
        os.system(f'{app} {uri} &')

    def launch_item(self, _button, _event, uri):
        os.system(f'xdg-open {uri} &')

    def run(self, *_args):
        pass

    def dummy(self, *_args):
        pass

    def runasadmin(self, _widget, _event, _name, execs, _ico, _typ):
        os.system(f'{Globals.Settings["AdminRun"]} "{execs}" &')

    def addfav(self, _widget, _event, name, execs, ico, typ):
        typ = str(typ)
        favlist = backend.load_setting("favorites") or []
        key = f"{name}::{execs}::{ico}::{typ}"
        if key not in favlist:
            favlist.append(key)
            backend.save_setting("favorites", favlist)
            try:
                del self.menucache["<Favorites>"]
            except Exception:
                pass
            self.notifier.notify(f'{name} {_("added to favorites list")}', Globals.name, Globals.Applogo, 5000)

    def removefav(self, _widget, _event, name, execs, ico, typ):
        typ = str(typ)
        favlist = backend.load_setting("favorites") or []
        key = f"{name}::{execs}::{ico}::{typ}"
        if key in favlist:
            favlist.remove(key)
            backend.save_setting("favorites", favlist)
            try:
                del self.menucache["<Favorites>"]
            except Exception:
                pass
            self.emit('changed')
            self.notifier.notify(f'{name} {_("removed from favorites list")}', Globals.name, Globals.Applogo, 5000)

    def create_autostarter(self, _widget, _event, name, execs, ico, typ):
        if not os.path.isdir(Globals.AutoStartDirectory):
            os.makedirs(Globals.AutoStartDirectory, exist_ok=True)
        if f'{name}.desktop' not in os.listdir(Globals.AutoStartDirectory):
            self.addshort(_widget, _event, name, execs, ico, typ, Globals.AutoStartDirectory)
            self.notifier.notify(f'{name} {_("added to system startup")}', Globals.name, Globals.Applogo, 5000)

    def remove_autostarter(self, _widget, _event, name, _execs, _ico, _typ):
        if not os.path.isdir(Globals.AutoStartDirectory):
            os.makedirs(Globals.AutoStartDirectory, exist_ok=True)
        path = os.path.join(Globals.AutoStartDirectory, f"{name}.desktop")
        if os.path.basename(path) in os.listdir(Globals.AutoStartDirectory):
            try:
                os.remove(path)
            except Exception:
                pass
            self.notifier.notify(f'{name} {_("removed from system startup")}', Globals.name, Globals.Applogo, 5000)

    def addshort(self, _widget, _event, name, execs, ico, typ, desk='desktop'):
        if desk == 'desktop':
            desk = utils.xdg_dir("XDG_DESKTOP_DIR") or os.path.join(Globals.HomeDirectory, "Desktop")
        os.makedirs(desk, exist_ok=True)
        starter = os.path.join(desk, f"{name}.desktop")
        lines = [
            '#!/usr/bin/env xdg-open',
            '[Desktop Entry]',
            f'Name={name}',
            'StartupNotify=true',
            'Terminal=false',
            'Version=1.0',
            f'Icon={ico}',
            'Type=Application',
            f'Exec={execs}' if int(typ) == 1 else f'Exec=xdg-open {execs}',
            'X-MATE-Autostart-enabled=true',
        ]
        with open(starter, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")

    # --------- special commands ----------

    def CallSpecialMenu(self, command, data=None):
        command = int(command)
        a = str(self.Menu)
        if command == 0:  # Back
            if self.PrevMenu:
                self.Menu = self.PrevMenu.pop()
                self.ConstructMenu()
        elif command == 1:  # Home
            self.PrevMenu = []
            self.Restart()
        elif command == 2:  # Recent Apps
            if a != '<RecentApps>':
                self.PrevMenu.append(self.Menu)
                self.Restart('recentapps')
        elif command == 3:  # Auxiliary
            if a != '<AuxiliaryFunctions>':
                self.PrevMenu.append(self.Menu)
                self.Restart('auxiliary')
        elif command == 4:  # Recent Items
            if a != '<RecentItems>':
                self.PrevMenu.append(self.Menu)
                self.Restart('recent')
        elif command == 5:  # Search
            if data:
                self.PrevMenu = [self.BaseMenu]
                self.Menu = data.upper()
                self.ConstructMenu()
            else:
                self.PrevMenu = []
                self.Menu = self.BaseMenu
                self.ConstructMenu()
        elif command == 6:  # Launch first search result
            if self.searchresults != 0:
                if Globals.Settings.get('Shownetandemail', 0) == 1:
                    self.ButtonClick(3)
                else:
                    self.ButtonClick(0)
        elif command == 7:  # Favorites
            if a != '<Favorites>':
                self.PrevMenu.append(self.Menu)
                self.Restart('favorites')
        elif command == 8:  # Places
            if a != '<Bookmarks>':
                self.PrevMenu.append(self.Menu)
                self.Restart('places')
        elif command == 9:  # Shutdown
            if a != '<Shutdown>':
                self.PrevMenu.append(self.Menu)
                self.Restart('shutdown')
        elif command == 10:  # WebBookmarks
            if a != '<WebBookmarks>':
                self.PrevMenu.append(self.Menu)
                self.Restart('webbookmarks')

    def Icon_change(self):
        self.IconFactory.Icon_change()

    def destroy(self):
        pass

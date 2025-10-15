
#!/usr/bin/env python3
# MATE menu reimplementation (Python 3, GTK 3)

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GObject, GdkPixbuf

import os
import gc

import MenuParser
import IconFactory
import Globals
import backend
import utils
import Launcher

from Popup_Menu import add_menuitem, add_image_menuitem


class MateMenu(GObject.GObject):
    __gsignals__ = {
        "unmap": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, scan: bool = False):
        super().__init__()
        self.notifier = utils.Notifier()
        self.Launcher = Launcher.Launcher()

        self.menu = MenuParser.MenuParser()
        self.menu.ParseMenus()
        self.menu.connect("menu-changed", self.MenuChanged)

        self.menus = {}
        self.IconFactory = IconFactory.IconFactory()

        self.m = Gtk.Menu()
        self.m.connect("unmap", self.unmap)
        self.menushow(self.menu.CacheApplications, self.m)
        self.menushow(self.menu.CacheSettings, self.m)

    # ---- actions for submenu ----
    def addshort(self, widget, event, name, execs, ico, typ, desk="desktop"):
        if desk == "desktop":
            desk = utils.xdg_dir("XDG_DESKTOP_DIR")
        starter = f"{desk}/{name}.desktop"
        lines = [
            "#!/usr/bin/env xdg-open",
            "[Desktop Entry]",
            f"Name={name}",
            "StartupNotify=true",
            "Terminal=false",
            "Version=1.0",
            f"Icon={ico}",
            "Type=Application",
            f"Exec={execs}" if int(typ) == 1 else f"Exec=xdg-open {execs}",
            "X-MATE-Autostart-enabled=true",
        ]
        with open(starter, "w") as f:
            f.write("\n".join(lines) + "\n")

    def runasadmin(self, widget, event, name, execs, ico, typ):
        os.system(f'{Globals.Settings["AdminRun"]} "{execs}" &')

    def addfav(self, widget, event, name, execs, ico, typ):
        favlist = backend.load_setting("favorites")
        entry = f"{name}::{execs}::{ico}::{typ}"
        if entry not in favlist:
            favlist.append(entry)
            backend.save_setting("favorites", favlist)
            self.notifier.notify(f"{name} " + _("added to favorites list"), Globals.name, Globals.Applogo, 5000)

    def removefav(self, widget, event, name, execs, ico, typ):
        favlist = backend.load_setting("favorites")
        entry = f"{name}::{execs}::{ico}::{typ}"
        if entry in favlist:
            favlist.remove(entry)
            backend.save_setting("favorites", favlist)
            self.emit("changed")
            self.notifier.notify(f"{name} " + _("removed from favorites list"), Globals.name, Globals.Applogo, 5000)

    def create_autostarter(self, widget, event, name, execs, ico, typ):
        if not os.path.isdir(Globals.AutoStartDirectory):
            os.system(f"mkdir -p '{Globals.AutoStartDirectory}'")
        target = os.path.join(Globals.AutoStartDirectory, f"{name}.desktop")
        if os.path.basename(target) not in os.listdir(Globals.AutoStartDirectory):
            self.addshort(widget, event, name, execs, ico, typ, Globals.AutoStartDirectory)
            self.notifier.notify(f"{name} " + _("added to system startup"), Globals.name, Globals.Applogo, 5000)

    def remove_autostarter(self, widget, event, name, execs, ico, typ):
        if not os.path.isdir(Globals.AutoStartDirectory):
            os.system(f"mkdir -p '{Globals.AutoStartDirectory}'")
        target = os.path.join(Globals.AutoStartDirectory, f"{name}.desktop")
        if os.path.basename(target) in os.listdir(Globals.AutoStartDirectory):
            os.system(f"rm -f '{target}'")
            self.notifier.notify(f"{name} " + _("removed from system startup"), Globals.name, Globals.Applogo, 5000)

    # ---- app submenu ----
    def submenushow(self, parent, name, ico, exe):
        favlist = backend.load_setting("favorites")
        sm = Gtk.Menu()

        add_menuitem(sm, name)
        add_menuitem(sm, "-")
        add_image_menuitem(sm, Gtk.STOCK_DIALOG_AUTHENTICATION, _("Open as Administrator"),
                           self.runasadmin, name, exe, ico, "1")

        if f"{name}::{exe}::{ico}::1" not in favlist:
            add_menuitem(sm, "-")
            add_image_menuitem(sm, Gtk.STOCK_ADD, _("Add to Favorites"),
                               self.addfav, name, exe, ico, "1")
        else:
            add_menuitem(sm, "-")
            add_image_menuitem(sm, Gtk.STOCK_REMOVE, _("Remove from Favorites"),
                               self.removefav, name, exe, ico, "1")

        add_menuitem(sm, "-")
        add_image_menuitem(sm, Gtk.STOCK_HOME, _("Create Desktop Shortcut"),
                           self.addshort, name, exe, ico, "1")

        add_menuitem(sm, "-")
        if f"{name}.desktop" in os.listdir(Globals.AutoStartDirectory):
            add_image_menuitem(sm, Gtk.STOCK_REMOVE, _("Remove from System Startup"),
                               self.remove_autostarter, name, exe, ico, "1")
        else:
            add_image_menuitem(sm, Gtk.STOCK_ADD, _("Add to System Startup"),
                               self.create_autostarter, name, exe, ico, "1")

        sm.show_all()
        sm.popup_at_pointer(None)
        gc.collect()

    # ---- launch handlers ----
    def launch(self, widget, event, parent, name, ico, exe):
        if event.button == 1:
            self.Launcher.Launch(exe, 1)
            self.emit("unmap")
        elif event.button == 3:
            self.m.popdown()
            self.submenushow(parent, name, ico, exe)
        gc.collect()

    # ---- menu construction ----
    def menushow(self, folder, m: Gtk.Menu):
        for entry in self.menu.GetMenuEntries(folder):
            self.menus[str(entry)] = Gtk.Menu()
            if isinstance(entry, self.menu.MenuInstance):
                name, icon, path, comment = self.menu.GetDirProps(entry)
                item = add_image_menuitem(m, "", name)
                item.set_submenu(self.menus[str(entry)])
                item.connect("activate", self.activatemenu, entry)
                if icon is None:
                    icon = Gtk.STOCK_MISSING_IMAGE
                try:
                    item.set_image_from_pixbuf(self.IconFactory.geticonfile(icon))
                except Exception:
                    pass
                try:
                    item.set_tooltip_text(comment)
                except Exception:
                    pass

            elif isinstance(entry, self.menu.EntryInstance):
                name, icon, execute, comment = self.menu.GetEntryProps(entry)
                item = add_image_menuitem(m, "", name, self.launch, m, name, icon, execute)
                try:
                    item.set_tooltip_text(comment)
                except Exception:
                    pass
                if icon is None:
                    icon = Gtk.STOCK_MISSING_IMAGE
                try:
                    item.set_image_from_pixbuf(self.IconFactory.geticonfile(icon))
                except Exception:
                    pass

        gc.collect()

    def activatemenu(self, widget, menu):
        if len(widget.get_submenu()) == 0:
            self.menushow(menu, widget.get_submenu())

    def MenuChanged(self, _event):
        self.m = Gtk.Menu()
        self.menushow(self.menu.CacheApplications, self.m)
        self.menushow(self.menu.CacheSettings, self.m)

    def showmenu(self):
        self.m.show_all()
        self.m.popup_at_pointer(None)
        gc.collect()

    # stubs for signal compatibility
    def detach(self, widget, event):
        pass

    def unmap(self, widget):
        pass


if __name__ == "__main__":
    men = MateMenu()
    # men.showmenu()
    # Gtk.main()

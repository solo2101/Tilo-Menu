#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GNU GPL v3+ — Popup menu helpers for Tilo

import glob
import os
import xml.dom.minidom
from xml.dom.minidom import Node

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

try:
    INSTALL_PREFIX = open("/etc/tilo/prefix", "r", encoding="utf-8").read().strip()
except Exception:
    INSTALL_PREFIX = "/usr"

import gettext
gettext.textdomain('tilo')
gettext.bindtextdomain('tilo', INSTALL_PREFIX + '/share/locale')
gettext.install('tilo', INSTALL_PREFIX + '/share/locale')

def _(s):
    return gettext.gettext(s)


# ---------------------------
# Public helpers
# ---------------------------

def add_menuitem(menu, label, callback=None, cb_data=None, *args):
    """Create a menu item (or separator when label=='-'), attach optional callback, append to menu."""
    if label == "-":
        item = Gtk.SeparatorMenuItem()
    else:
        item = Gtk.MenuItem.new_with_label(label)
    return add_menuitem_with_item(menu, item, callback, cb_data, *args)

def add_image_menuitem(menu, icon_name, label=None, callback=None, cb_data=None, *args):
    """Create an ImageMenuItem-like row (Gtk.MenuItem with image+label)."""
    item = ImageMenuItem(icon_name, label)
    return add_menuitem_with_item(menu, item, callback, cb_data, *args)

def add_menuitem_with_item(menu, item, callback=None, cb_data=None, *args):
    """Append a ready-made menu item and connect a button-press callback if provided."""
    if callback:
        if cb_data is not None:
            item.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            item.connect('button-press-event', callback, cb_data, *args)
        else:
            item.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            item.connect('button-press-event', callback)
    menu.append(item)
    item.show()
    return item


# ---------------------------
# XML-driven menu builder
# ---------------------------

def create_menu_from_file(filename, callback):
    """Create a Gtk.Menu from a simple XML file."""
    try:
        doc = xml.dom.minidom.parse(filename)
    except Exception as e:
        print(_("XML-Error: %s") % str(e))
        return None
    return create_menu_from_xml(doc.firstChild, callback)

def create_menu_from_xml(node, callback, icon_size=22):
    """Create a Gtk.Menu from an XML DOM node."""
    menu = Gtk.Menu()
    for child in node.childNodes:
        if child.nodeType != Node.ELEMENT_NODE:
            continue

        label = child.getAttribute("label")
        item_id = child.getAttribute("id")
        item = None

        # <item>
        if child.nodeName == "item":
            item = Gtk.MenuItem.new_with_label(label)

        # <checkitem>
        elif child.nodeName == "checkitem":
            item = Gtk.CheckMenuItem.new_with_label(label)
            if child.hasAttribute("checked"):
                item.set_active(True)

        # <imageitem>
        elif child.nodeName == "imageitem":
            icon = child.getAttribute("icon")
            item = imageitem_from_name(icon, label, icon_size)

        # <separator>
        elif child.nodeName == "separator":
            item = Gtk.SeparatorMenuItem()

        # <appdir path="" cats="...">  (kept for compatibility)
        elif child.nodeName == "appdir":
            from_path = child.getAttribute("path")
            cats = child.getAttribute("cats").split(",")
            appmenu = ApplicationMenu(from_path)
            for cat in cats:
                mi = Gtk.MenuItem.new_with_label(cat)
                submenu = appmenu.get_menu_for_category(cat, callback)
                mi.set_submenu(submenu)
                mi.show()
                menu.append(mi)
            item = None  # avoid appending again below

        # <scandir>
        elif child.nodeName == "scandir":
            directory = child.getAttribute("directory").replace('$HOME', os.environ.get('HOME', ''))
            idprfx = child.getAttribute("id_prefix")
            idsufx = child.getAttribute("id_suffix")
            srch = child.getAttribute("search").split(',')
            repl = child.getAttribute("replace").split(',')
            skp = child.getAttribute("skip").split(',')
            flt = child.getAttribute("filter") or '*'
            fill_menu_from_directory(directory, menu, callback, filter=flt,
                                     id_prefix=idprfx, id_suffix=idsufx, search=srch,
                                     replace=repl, skip=skp)

        # attach submenu/activation
        if item:
            if child.hasChildNodes():
                submenu = create_menu_from_xml(child, callback, icon_size)
                item.set_submenu(submenu)
            item.show()
            if item_id:
                item.connect("activate", callback, item_id)
            menu.append(item)

    return menu


def fill_menu_from_directory(dirname, menu, callback, filter='*',
                             id_prefix='', id_suffix='', search=None, replace=None, skip=None):
    """Add simple items from a directory listing."""
    search = search or []
    replace = replace or []
    skip = skip or []
    entries = glob.glob(os.path.join(dirname, filter))
    entries.sort()
    base_len = len(dirname) + 1
    for filename in entries:
        fname = filename[base_len:]
        if fname in skip:
            continue
        # replacements
        if search and len(search) == len(replace):
            for s, r in zip(search, replace):
                fname = fname.replace(s, r)
        item_id = f"{id_prefix}{fname}{id_suffix}"
        item = Gtk.MenuItem.new_with_label(fname)
        item.connect("activate", callback, item_id)
        item.show()
        menu.append(item)


# ---------------------------
# Image menu item (GTK3)
# ---------------------------

def _load_icon_image(icon_name_or_path, icon_size):
    img = Gtk.Image()
    if not icon_name_or_path:
        img.set_from_icon_name("image-missing", Gtk.IconSize.MENU)
        return img
    try:
        if icon_name_or_path.startswith('/'):
            # from file; scale if needed
            pb = GdkPixbuf.Pixbuf.new_from_file(icon_name_or_path)
            if pb.get_width() > icon_size or pb.get_height() > icon_size:
                pb = pb.scale_simple(icon_size, icon_size, GdkPixbuf.InterpType.BILINEAR)
            img.set_from_pixbuf(pb)
        else:
            img.set_from_icon_name(icon_name_or_path, Gtk.IconSize.MENU)
    except Exception:
        img.set_from_icon_name("image-missing", Gtk.IconSize.MENU)
    return img

def imageitem_from_name(filename, label, icon_size=32):
    item = ImageMenuItem(filename, label, icon_size=icon_size)
    return item


class ImageMenuItem(Gtk.MenuItem):
    """GTK3-friendly 'image + label' menu row."""
    def __init__(self, icon_name=None, label=None, icon_size=22):
        super().__init__()
        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._image = _load_icon_image(icon_name, icon_size)
        self._label = Gtk.Label(label or "", xalign=0)

        self._box.pack_start(self._image, False, False, 0)
        self._box.pack_start(self._label, True, True, 0)
        self.add(self._box)
        self._box.show_all()

    # Compatibility helpers
    def set_image_from_file(self, filename):
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file(filename)
            self._image.set_from_pixbuf(pb)
        except Exception:
            self._image.set_from_icon_name("image-missing", Gtk.IconSize.MENU)

    def set_image_from_pixbuf(self, pixbuf):
        self._image.set_from_pixbuf(pixbuf)

    def set_label(self, text):
        self._label.set_text(text)

    # kept for API parity; no-op in Gtk3 context
    def set_image_from_stock(self, name):
        self._image.set_from_icon_name(name, Gtk.IconSize.MENU)

    def set_image_size(self, width, height):
        self._image.set_pixel_size(max(width, height))


# ---------------------------
# .desktop reader (simple)
# ---------------------------

def read_desktop_file(filename):
    """Very simple .desktop reader into a dict (sufficient for old XML menus)."""
    data = {}
    try:
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line or line[0] in "#\n[":
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip()
    except Exception:
        print(_("Error: file %s not found.") % filename)
    return data


# ---------------------------
# ApplicationMenu (legacy)
# ---------------------------

class ApplicationMenu:
    """Builds submenus from directories containing .desktop files (legacy support)."""
    def __init__(self, path):
        self._path = path
        self._applications = []
        self._read_directory(path)

    def _read_directory(self, path):
        for file in glob.glob(os.path.join(path, '*')):
            if not file.endswith('.desktop'):
                continue
            df = read_desktop_file(file)
            try:
                # Basic keys; ignore entries missing essentials
                _ = df['Name'], df['Icon'], df['Exec']
                # Will sort later by Name
                self._applications.append(df)
            except Exception as ex:
                print(_("Exception: %s") % str(ex))
                print(_("An error occured with desktop-file: %s") % file)

    def get_menu_for_category(self, cat_name, callback):
        applist = []
        for app in self._applications:
            cats = app.get('Categories', '')
            if (';' + cats).count(';' + cat_name + ';') > 0:
                applist.append(app)

        # de-dup by (Name, Exec)
        seen = set()
        uniq = []
        for a in applist:
            key = (a.get('Name', ''), a.get('Exec', ''))
            if key not in seen:
                seen.add(key)
                uniq.append(a)

        uniq.sort(key=lambda a: a.get('Name', '').lower())

        menu = Gtk.Menu()
        for app in uniq:
            item = imageitem_from_name(app.get('Icon', ''), app.get('Name', ''), 24)
            if item:
                item.connect("activate", callback, "exec:" + app.get('Exec', ''))
                item.show()
                menu.append(item)
        return menu


# ---------------------------
# DefaultMenuItem constants (kept for compatibility)
# ---------------------------

class DefaultMenuItem:
    NONE        = 0
    DELETE      = 1
    THEMES      = 2
    INFO        = 4
    SIZE        = 8
    WINDOW_MENU = 16
    PROPERTIES  = 32
    DELETE2     = 64
    QUIT        = 128
    QUIT_ALL    = 256
    XML         = 512
    STANDARD    = 1 | 2 | 8 | 16 | 32 | 64 | 128 | 256

#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license.
# Thank you for using free software!
#
#(c) Whise 2010 <helderfraga@gmail.com>
#
# Icon factory
# Part of the GnoMenu

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk as gtk, GObject as gobject, Gio as gio, GdkPixbuf
import os
import xml.dom.minidom
import utils
import Globals
import gc
import urllib.request as urllib
import xdg.IconTheme
import xdg.BaseDirectory as bd
isgio = True

Icontype = ["png", "xpm", "svg"]

try:
        INSTALL_PREFIX = open("/etc/tilomenu/prefix").read()[:-1] 
except:
        INSTALL_PREFIX = '/usr'

import gettext
gettext.textdomain('gnomenu')
gettext.install('gnomenu', INSTALL_PREFIX +  '/share/locale')
gettext.bindtextdomain('gnomenu', INSTALL_PREFIX +  '/share/locale')

def _(s):
        return gettext.gettext(s)

def GetSystemIcon(icon):
        # GTK theme indexes can contain missing files. Return a verified path,
        # falling back to the stock hicolor icon theme.
        name = os.path.splitext(os.path.basename(str(icon)))[0]
        for theme in (gtk.IconTheme.get_default(), _hicolor_theme()):
                try:
                        info = theme.lookup_icon(name, 48, gtk.IconLookupFlags.FORCE_SIZE)
                        path = info.get_filename() if info else None
                        if path and os.path.isfile(path):
                                return path
                except (Exception):
                        pass
        return None


def _hicolor_theme():
        theme = gtk.IconTheme.new()
        theme.set_custom_theme('hicolor')
        return theme

class IconFactory(gobject.GObject):
        __gsignals__ = {"icons-changed" : (gobject.SignalFlags.RUN_LAST, None, ()),
        }
        def __init__(self):
                gobject.GObject.__init__(self)

                if Globals.Settings['Show_Thumb']:
                        self.thumbnailer = utils.thumbnailengine(Globals.PG_iconsize)
                        self.thumbnailer.connect("worklist-finished", lambda m: self.emit('icons-changed'))

                ##### looksup icon theme in gtk, we could also use : gconf.client_get_default().get_string('/desktop/gnome/interface/icon_theme')
                self.gtkicontheme = gtk.IconTheme.get_default()
                self.icontheme = Globals.DefaultIconTheme
                self.old_icontheme = self.icontheme
                ###### Check if icon theme is stored in cache#################
                #self.LoadIconCache()


        def Icon_change(self):
                """Icons have changed"""

                print('icons changed')
                self.icontheme = gtk.Settings.get_default().get_property("gtk-icon-theme-name")
                self.gtkicontheme = gtk.IconTheme.get_default()

        def getgicon(self,gico):
                """Return the original Gio icon name or file path.

                Do not discard names merely because a custom icon theme has
                a missing/stale lookup entry. geticonfile handles fallback.
                """
                if isinstance(gico, gio.FileIcon):
                        return gico.get_file().get_path()
                if isinstance(gico, gio.ThemedIcon):
                        names = gico.get_names()
                        if names:
                                return names[0]
                return 'application-x-executable'

        def getthumb(self,item):
                path = urllib.url2pathname(item.get_uri().replace('file://',''))
                if Globals.Settings['Show_Thumb']:
                        if not os.path.exists(path): 
                                return item.get_icon(Globals.PG_iconsize)
                        if isgio:
                                self.gfile = gio.File.new_for_path(path)
                                self.info = self.gfile.query_info(gio.FILE_ATTRIBUTE_THUMBNAIL_PATH, gio.FileQueryInfoFlags.NONE)
                                thumbfile = self.info.get_attribute_as_string(gio.FILE_ATTRIBUTE_THUMBNAIL_PATH)
                                if thumbfile:
                                        if os.path.isfile(thumbfile): 
                                                return GdkPixbuf.Pixbuf.new_from_file_at_size(thumbfile, Globals.PG_iconsize, Globals.PG_iconsize)
                                        else:return item.get_icon(Globals.PG_iconsize)
                                else:return item.get_icon(Globals.PG_iconsize)

                        else:
                                icon, isthumbnail = self.thumbnailer.CheckWorkList(path)
                                if not icon:
                                        self.thumbnailer.AddToWorkList(path, item.get_mime_type())
                                        return item.get_icon(Globals.PG_iconsize)
                                else:
                                        if isthumbnail:
                                                return icon
                                        else: return item.get_icon(Globals.PG_iconsize)
                else:
                        return item.get_icon(Globals.PG_iconsize)

        def geticonfile(self,icon):
                # Preserve original icon names, absolute paths and Gio icons.
                size = Globals.PG_iconsize
                flags = gtk.IconLookupFlags.FORCE_SIZE
                if isinstance(icon, gio.Icon):
                        icon = self.getgicon(icon)
                icon = str(icon) if icon else ''

                if os.path.isfile(icon):
                        try:
                                return GdkPixbuf.Pixbuf.new_from_file_at_size(icon, size, size)
                        except Exception:
                                pass

                names = [icon]
                if icon.endswith(('.png', '.svg', '.xpm')):
                        names.append(os.path.splitext(icon)[0])
                # An icon theme may reference a removed SVG even when
                # has_icon() returns True. Try the standard fallback theme.
                for name in names:
                        if not name:
                                continue
                        for theme in (self.gtkicontheme, _hicolor_theme()):
                                try:
                                        return theme.load_icon(name, size, flags)
                                except Exception:
                                        pass

                for dir_ in bd.xdg_data_dirs:
                        for subdir in ('pixmaps', 'icons'):
                                path = os.path.join(dir_, subdir, icon)
                                if os.path.isfile(path):
                                        try:
                                                return GdkPixbuf.Pixbuf.new_from_file_at_size(
                                                        path, size, size)
                                        except Exception:
                                                pass

                for name in ('application-x-executable', 'image-missing', 'gtk-missing-image'):
                        for theme in (self.gtkicontheme, _hicolor_theme()):
                                try:
                                        return theme.load_icon(name, size, flags)
                                except Exception:
                                        pass
                return GdkPixbuf.Pixbuf.new_from_file_at_size(
                        Globals.BrokenImage, size, size)

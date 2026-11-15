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
        for n in Icontype:
                icon = str(icon).replace('.' + n,'')
        ico = Globals.GtkIconTheme.lookup_icon(icon,48,gtk.IconLookupFlags.FORCE_SVG)
        if ico:
                ico = ico.get_filename()
        else:
                ico = None
        return ico

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
                """Returns gio icon"""
                try:
                        names = gico.get_names()
                        for x in range(0,len(names)):
                                if self.gtkicontheme.has_icon(names[x]):
                                        return names[x]
                except:pass
                return 'gtk-execute'

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
                # Gtk.IconTheme.has_icon() can report stale, missing files.
                # Keep the original lookup order while falling back safely.
                size = Globals.PG_iconsize
                flags = gtk.IconLookupFlags.FORCE_SIZE
                if icon and self.gtkicontheme.has_icon(icon):
                        try:
                                return self.gtkicontheme.load_icon(icon, size, flags)
                        except (Exception) as error:
                                print('Unable to load themed icon %s: %s' % (icon, error))
                for dir_ in bd.xdg_data_dirs:
                        for subdir in ('pixmaps', 'icons'):
                                path = os.path.join(dir_, subdir, icon or '')
                                if os.path.isfile(path):
                                        try:
                                                return GdkPixbuf.Pixbuf.new_from_file_at_size(path, size, size)
                                        except Exception:
                                                pass
                if icon and os.path.isfile(icon):
                        try:
                                return GdkPixbuf.Pixbuf.new_from_file_at_size(icon, size, size)
                        except Exception:
                                pass
                for name in ('image-missing', 'gtk-missing-image'):
                        if self.gtkicontheme.has_icon(name):
                                try:
                                        return self.gtkicontheme.load_icon(name, size, flags)
                                except Exception:
                                        pass
                return GdkPixbuf.Pixbuf.new_from_file_at_size(
                        Globals.BrokenImage, size, size)

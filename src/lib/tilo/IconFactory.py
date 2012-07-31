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

import gtk
import os
import xml.dom.minidom
import gobject
import utils
import Globals
import gc
import urllib
import xdg.IconTheme
import xdg.BaseDirectory as bd
try:
	import gio
	isgio = True
except:
	print 'gio not found'
	isgio = False

Icontype = ["png", "xpm", "svg"]

try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'

import gettext
gettext.textdomain('tilo')
gettext.install('tilo', INSTALL_PREFIX +  '/share/locale')
gettext.bindtextdomain('tilo', INSTALL_PREFIX +  '/share/locale')

def _(s):
	return gettext.gettext(s)

def GetSystemIcon(icon):
	for n in Icontype:
		icon = str(icon).replace('.' + n,'')
	ico = Globals.GtkIconTheme.lookup_icon(icon,48,gtk.ICON_LOOKUP_FORCE_SVG)
	if ico:
		ico = ico.get_filename()
	else:
		ico = None
	return ico

class IconFactory(gobject.GObject):
	__gsignals__ = {"icons-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }
	def __init__(self):
		gobject.GObject.__init__(self)

		if Globals.Settings['Show_Thumb']:
			self.thumbnailer = utils.thumbnailengine(Globals.PG_iconsize)
			self.thumbnailer.connect("worklist-finished", lambda m: self.emit('icons-changed'))

		##### looksup icon theme in gtk, we could also use : mateconf.client_get_default().get_string('/desktop/mate/interface/icon_theme')
		self.gtkicontheme = gtk.icon_theme_get_default()
		self.icontheme = Globals.DefaultIconTheme
		self.old_icontheme = self.icontheme
		###### Check if icon theme is stored in cache#################
		#self.LoadIconCache()


	def Icon_change(self):
		"""Icons have changed"""

		print 'icons changed'
		self.icontheme = gtk.settings_get_default().get_property("gtk-icon-theme-name")
		self.gtkicontheme = gtk.icon_theme_get_default()

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
				self.gfile = gio.File(path)
				self.info = self.gfile.query_info(gio.FILE_ATTRIBUTE_THUMBNAIL_PATH, gio.FILE_QUERY_INFO_NONE)
				thumbfile = self.info.get_attribute_as_string(gio.FILE_ATTRIBUTE_THUMBNAIL_PATH)
				if thumbfile:
					if os.path.isfile(thumbfile): 
						return gtk.gdk.pixbuf_new_from_file_at_size(thumbfile, Globals.PG_iconsize, Globals.PG_iconsize)
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
			if self.gtkicontheme.has_icon(icon):
				pix = self.gtkicontheme.load_icon(icon,Globals.PG_iconsize,gtk.ICON_LOOKUP_FORCE_SIZE)
				return pix
			# lockup icon in xdg icon theme
			else:
				for dir_ in bd.xdg_data_dirs:
					for subdir in ('pixmaps', 'icons'):
						path = os.path.join(dir_, subdir, icon)
						if os.path.isfile(path):
							pix = gtk.gdk.pixbuf_new_from_file_at_size(path,Globals.PG_iconsize,Globals.PG_iconsize)
							return pix
			if os.path.isfile(icon):
				pix = gtk.gdk.pixbuf_new_from_file_at_size(icon, Globals.PG_iconsize, Globals.PG_iconsize)
				return pix
			pix = self.gtkicontheme.load_icon('gtk-missing-image',Globals.PG_iconsize,gtk.ICON_LOOKUP_FORCE_SIZE)
			return pix



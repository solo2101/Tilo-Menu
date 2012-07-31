#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2008,2009 <helderfraga@gmail.com>
#
# utils
# Part of the GnoMenu



import gtk
import pygtk
pygtk.require('2.0')
import gobject
import os
import dbus
BUS = dbus.SessionBus()
try:
	import mate.ui
	MATEUI = True
except:
	MATEUI = False
try:
	import xdg.BaseDirectory as bd
except:pass

		
def show_message (message, title='Tilo'):

	md = gtk.MessageDialog(None, type=gtk.MESSAGE_INFO, 
			buttons=gtk.BUTTONS_OK)
	md.set_title(title)
	md.set_markup(str(message))
	md.run()
	md.destroy()

def show_warning (message, title='Tilo'):

	md = gtk.MessageDialog(None, type=gtk.MESSAGE_WARNING, 
			buttons=gtk.BUTTONS_OK)
	md.set_title(title)
	print message
	md.set_markup(str(message))
	md.run()
	md.destroy()


def show_question (message, title='Tilo'):
	md = gtk.MessageDialog(None, type=gtk.MESSAGE_QUESTION, 
			buttons=gtk.BUTTONS_YES_NO)
	md.set_title(title)
	md.set_markup(message)
	response = md.run()
	md.destroy()
	if response == gtk.RESPONSE_YES:
		return True
	return False

def emit_notification(title,message):
		bus = dbus.SessionBus()
		notifications = dbus.Interface(\
			bus.get_object('org.freedesktop.Notifications', 
			'/org/freedesktop/Notifications'), 'org.freedesktop.Notifications')
		notifications.Notify('Screenlets', 0, 'drive-harddisk', title, message, 
				[], {}, 1000)


def sys_get_window_manager():
	"""Returns window manager name"""
	root = gtk.gdk.get_default_root_window()
	try:
		ident = root.property_get("_NET_SUPPORTING_WM_CHECK", "WINDOW")[2]
		_WM_NAME_WIN = gtk.gdk.window_foreign_new(long(ident[0]))
	except TypeError, exc:
		_WM_NAME_WIN = ""
	
	name = ""
	win = _WM_NAME_WIN
	if (win != None):
		try:
			name = win.property_get("_NET_WM_NAME")[2]
		except TypeError, exc:
	
			return name
	return name


def get_image_size(pix):
	"""Gets a picture width and height"""
	pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
	iw = pixbuf.get_width()
	ih = pixbuf.get_height()
	puxbuf = None
	return iw,ih


def xdg_dir(key):
	"""http://www.freedesktop.org/wiki/Software/xdg-user-dirs"""
	try:
		user_dirs = '%s/user-dirs.dirs' % bd.xdg_config_home
	except:
		user_dirs = os.path.expanduser("~/.config/user-dirs.dirs")
	if os.path.exists(user_dirs):
		f = open(user_dirs, "r")
		for line in f.readlines():
			if line.startswith(key):
				return os.path.expandvars(line[len(key)+2:-2])
	return False


def readMountFile(filename):
	"""Reads fstab file"""
	fstab = []
	f = open(filename, 'r')
	for line in f:
		if (not line.isspace() and not line.startswith('#') and not line.lower().startswith('none')) :
			fstabline = line.split()
			if fstabline[1] != 'none' and fstabline[1] != '/proc': fstab.append(fstabline[1])

	fstab.sort()
	return fstab

def compiz_call(obj_path, func_name, *args):
	# Returns a compiz function call.
	# No errors are dealt with here,
	# error handling are left to the calling function.
	try:
		path = '/org/freedesktop/compiz'
		if obj_path:
			path += '/' + obj_path
		obj = BUS.get_object('org.freedesktop.compiz', path)
		iface = dbus.Interface(obj, 'org.freedesktop.compiz')
		func = getattr(iface, func_name)
		if func:
			return func(*args)
		return ''
	except:
		return ''



class Notifier(object):
	"""A simple and conveniet wrapper for the notification-service"""
	import dbus
	def __init__ (self):
		self.bus = dbus.SessionBus()
		try:
			self.notifications = dbus.Interface(\
				self.bus.get_object('org.freedesktop.Notifications', 
				'/org/freedesktop/Notifications'), 'org.freedesktop.Notifications')
		except:pass

	def notify (self, message, title='', icon='', timeout=-1):
		"""Send a notification to org.freedesktop.Notifications. The message
		should contain the text you want to display, title may define a title
		(summary) for the message, icon can be the full path to an icon,
		timeout can be set to the desired displaying time in milliseconds."""
		try:
			if self.bus and self.notifications:
				self.notifications.Notify('Tilo', 0, icon, title, message, 
					[], {}, timeout)
				return True
			else:
				print "Notify: No DBus running or notifications-daemon unavailable."
			return False
		except:pass

class thumbnailengine(gobject.GObject):
	__gsignals__ = {"thumbnail-finished" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
					"worklist-finished" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}

	def __init__(self,icon_size):
		gobject.GObject.__init__(self)
		if not MATEUI: return None
		self.icon_size = icon_size
		self.thumbFactory = mate.ui.ThumbnailFactory(mate.ui.THUMBNAIL_SIZE_LARGE)
		self.WorkList = []
		self.DoneList = []
		self.stockimage = "/usr/share/icons/application-default-icon.png"
		self.Timer = None
		
	def lookup(self, uri):
		icon = self.thumbFactory.lookup(uri,0)
		if not icon:
			icon = "/usr/share/icons/application-default-icon.png"
		return icon
			
	def Process(self,uri,mime_type):
		# Check availability of thumbnail and create one if necessary
		if self.thumbFactory.can_thumbnail(uri,mime_type, 0):
			# Check for existing thumbnail
			thumbnail = self.thumbFactory.lookup(uri, 0)
			if not thumbnail:
				thumbnail = self.thumbFactory.generate_thumbnail(uri, mime_type)
				if thumbnail != None:
					self.thumbFactory.save_thumbnail(thumbnail, uri, 0)
			icon = uri
		else:
			icon = "/usr/share/icons/application-default-icon.png"
		return icon
		
	def ProcessWorkList(self):
		processitem = self.WorkList.pop(0)
		image = self.Process(*processitem)
		if isinstance(image, str):
			if image.startswith("file://"):
				image = self.lookup(image)
				isthumbnail = True
			else:
				isthumbnail = False
		self.DoneList.append([processitem[0], image, isthumbnail])
		self.emit("thumbnail-finished", processitem[0])
		if self.WorkList == []:
			self.emit("worklist-finished")
			self.Timer = None
			return False
		else:
			return True	
	
				
	def CheckWorkList(self,uri):
		for item in self.DoneList:
			if item[0] == uri:
				return item[1], item[2]
		return None, False

	def AddToWorkList(self, uri, mime_type):
		if self.WorkList.count([uri, mime_type]):
			return
		self.WorkList.append([uri,mime_type])
		if not self.Timer:
			self.Timer = gobject.timeout_add(50, self.ProcessWorkList)


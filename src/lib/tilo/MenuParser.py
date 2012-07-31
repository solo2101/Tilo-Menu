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
# Menu parser
# Part of the GnoMenu

try:
	import matemenu
	print 'matemenu found, using it as default menu parser'
	has_matemenu = True
except:
	has_matemenu = False
	import xdg.Menu
	print 'xdg found, using it as default menu parser'

import gobject
import xdg.BaseDirectory as bd

try:
	import gio
	isgio = True
except:
	print 'gio not found'
	isgio = False
import os
import Globals

import gc

class MenuParser(gobject.GObject):
	__gsignals__ = {
        'menu-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

	def __init__(self):
		gobject.GObject.__init__(self)
		self.has_matemenu = has_matemenu
		if has_matemenu:
			self.MenuInstance = matemenu.Directory
			self.EntryInstance = matemenu.Entry
		else:
			self.MenuInstance = xdg.Menu.Menu
			self.EntryInstance = xdg.Menu.MenuEntry
		self.updating = False


	def ParseMenus(self):
		"""parse menus using xdg"""

		if has_matemenu:
			self.CacheGmenuApplications = matemenu.lookup_tree(os.environ.get("XDG_MENU_PREFIX", "") + "applications.menu")		
			self.CacheApplications = self.CacheGmenuApplications.get_root_directory()
			if self.CacheApplications is None:
				self.CacheGmenuApplications = matemenu.lookup_tree("mate-applications.menu")		
				self.CacheApplications = self.CacheGmenuApplications.get_root_directory()

			if self.CacheApplications is None:
				print 'unable to parse the menu'
			else:
				self.CacheGmenuApplications.add_monitor(self.monitor_callback)

			self.CacheGmenuSettings = matemenu.lookup_tree("settings.menu")		
			self.CacheSettings = self.CacheGmenuSettings.get_root_directory()
			if self.CacheSettings is None:
				self.CacheGmenuSettings = matemenu.lookup_tree("mate-settings.menu")		
				self.CacheSettings = self.CacheGmenuSettings.get_root_directory()
			if self.CacheSettings is None:
				self.CacheGmenuSettings = matemenu.lookup_tree(os.environ.get("XDG_MENU_PREFIX", "") + "settings.menu")		
				self.CacheSettings = self.CacheGmenuSettings.get_root_directory()
			else:
				self.CacheGmenuSettings.add_monitor(self.monitor_callback)
		
			self.MenuInstance = matemenu.Directory
			self.EntryInstance = matemenu.Entry


		else:
			#http://www.rkblog.rk.edu.pl/w/p/pyxdg-freedesktoporg-specifications-support/
			try:
				#standard applications.menu with XDG_MENU_PREFIX that may be null
				self.CacheApplications = xdg.Menu.parse(os.environ.get("XDG_MENU_PREFIX", "") + "applications.menu")
			except:
				print 'Error parsing'
				try:
					# Some distros rename applications.menu without setting XDG_MENU_PREFIX.
					self.CacheApplications = xdg.Menu.parse("mate-applications.menu")
				except:
					print 'unable to parse the menu'
	
	
			try:
				self.CacheSettings = xdg.Menu.parse("settings.menu")
			except:
				try:
					self.CacheSettings = xdg.Menu.parse("mate-settings.menu")
				except: 
					try:
						self.CacheSettings = xdg.Menu.parse(os.environ.get("XDG_MENU_PREFIX", "") + "settings.menu")
					except:
						print 'unable to parse the settings menu'

			self.AppsFile = self.CacheApplications.Filename
			self.SetFile = self.CacheSettings.Filename

			if isgio:
				dirs = bd.xdg_data_dirs
				if bd.xdg_data_home not in dirs:
					dirs.append(bd.xdg_data_home)
				for d in dirs:
					self.parentfile = d + '/applications'
					if os.path.isdir(self.parentfile) and os.path.exists(self.parentfile):
						self.current_file1 = gio.File(self.parentfile).monitor_directory()
						self.current_file1.connect_after("changed", self.monitor_callback)
	
				self.current_file = gio.File(self.AppsFile).monitor_file()
				self.current_file.connect_after("changed", self.monitor_callback)

			self.MenuInstance = xdg.Menu.Menu
			self.EntryInstance = xdg.Menu.MenuEntry
	

	def GetMenuEntries(self,menu):

		if has_matemenu:
			return menu.contents
		else:
			return menu.getEntries()

	def GetDirProps(self,entry):

		if has_matemenu:
			if Globals.Settings['Show_Tips']:
				comment = entry.get_comment()
			else:
				comment = ''
			return entry.get_name(), entry.get_icon(),entry,comment
		else:
			if Globals.Settings['Show_Tips']:
				comment = entry.getComment()
			else:
				comment = ''
			return entry.getName(),	entry.getIcon(), entry.getPath(True),comment

	def GetEntryProps(self,entry):

		if has_matemenu:
			if Globals.Settings['Show_Tips']:
				comment = entry.get_comment()
			else:
				comment = ''
			return entry.get_name(), entry.get_icon(),entry.get_exec(),comment#,entry.get_desktop_file_path()
		else:
			entry = entry.DesktopEntry
			if Globals.Settings['Show_Tips']:
				comment = entry.getComment()
			else:
				comment = ''
			return entry.getName(),	entry.getIcon(),entry.getExec(), comment#,entry.getFileName()


	def monitor_callback(self, monitor=None, Gfile=None, event=None, data=None):
		"""Callback for when directories change"""
		
		if not self.updating:
			self.updating = True
			self.timeout = gobject.timeout_add(1000,self.MenuChanged)

	def MenuChanged(self):
		"""Called 1 second after menu changes"""

		print 'Menu Changed'
		#self.current_file.disconnect_by_func(self.monitor_callback)
		self.ParseMenus()
		self.emit('menu-changed')
		gc.collect()
		self.updating = False



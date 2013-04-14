#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license.
# Thank you for using free software!
#
#(c) QB89Dragon 2007/8 <hughescih@hotmail.com>
#(c) Whise 2008,2009 <helderfraga@gmail.com>
#
# XDG Menu Functions
# Part of the Tilo
import gi
gi.require_version("Gtk", "2.0")
from gi.repository import Gtk
from gi.repository import GObject

import backend
import os
import urllib
import utils
from Popup_Menu import add_menuitem, add_image_menuitem
import gc
import Globals
import MenuParser
import IconFactory
import Launcher
#import time

try:
	import bookmarks
	
except:print 'error importing webbookmarks'

try:
	from gi.repository import Gio
	isgio = True
except:
	print 'gio not found'
	isgio = False
try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'
try:
	import zg
except: zg = None

if Globals.FirstUse:
	os.system("/bin/sh -c %s'/lib/%s/Tilo-Settings.py --welcome' &" % (INSTALL_PREFIX, Globals.appdirname))

import gettext
gettext.textdomain('tilo')
gettext.install('tilo', INSTALL_PREFIX +  '/share/locale')
gettext.bindtextdomain('tilo', INSTALL_PREFIX +  '/share/locale')

def _(s):
	return gettext.gettext(s)


class XDMateMenu(GObject.GObject):

	__gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ()),
        }
	def __init__(self):
		GObject.GObject.__init__ (self)
		if not os.path.isdir(Globals.AutoStartDirectory):
			os.system('mkdir %s' % Globals.AutoStartDirectory)
		self.notifier = utils.Notifier()
		self.menuparser = MenuParser.MenuParser()
		self.menuparser.connect('menu-changed',self.MenuChanged)
		self.AppsFile = None
		self.SetFile = None
		self.menucache = {}
		self.nonMenuitems = '<Bookmarks>','<AuxiliaryFunctions>','<RecentItems>','<RecentApps>','<WebBookmarks>','<Favorites>','<Shutdown>'

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
		if isgio:
			self.monitor=Gio.volume_monitor_get()
			self.monitor.connect("drive-changed",self.on_drive_changed)
			self.allgio =  Gio.app_info_get_all()
		else:self.allgio = None
		self.Launcher = Launcher.Launcher()
		self.recent_manager = Gtk.recent_manager_get_default()
		self.recent_manager.connect("changed", self.onRecentChanged)
		self.recents_changed = True
		self.recents = None
		self.ItemComments = {}
		self.Menu = self.BaseMenu
		self.PrevMenu = []
		self.searchresults = 0
		##### Load IconFactory##################################
		self.IconFactory = IconFactory.IconFactory()
		##### Load webbookmarks##################################
		try:
			self.webbookmarker = bookmarks.BookmarksMenu().getBookmarks()
		except:
			self.webbookmarker = None
		##### Construct the menu###########################
		self.menuitems = 'settings','places','auxiliary','recent','recentapps','webbookmarks','favorites','shutdown','all'
		for item in self.menuitems:
			#print 'Loading item to memory: ',item
			self.Restart(item)
		gc.collect()

	def MenuChanged(self,event):
		"""menu changes"""
		#self.current_file.disconnect_by_func(self.monitor_callback)
		#del self.menucache[self.menuparser.CacheApplications]
		#del self.menucache[self.menuparser.CacheSettings]
		for item in self.menucache.copy():
			if item not in self.nonMenuitems:
				del self.menucache[item]
		if isinstance(self.Menu, self.menuparser.MenuInstance) and self.menuparser.has_matemenu:
			if self.BaseMenu.get_name() ==self.menuparser.CacheApplications.get_name():self.BaseMenu = self.menuparser.CacheApplications
			elif self.BaseMenu.get_name() ==self.menuparser.CacheSettings.get_name():self.BaseMenu = self.menuparser.CacheSettings
		else:
			if self.BaseMenu ==self.menuparser.CacheApplications:self.BaseMenu = self.menuparser.CacheApplications
			elif self.BaseMenu ==self.menuparser.CacheSettings:self.BaseMenu = self.menuparser.CacheSettings
		self.emit('changed')
		gc.collect()

	def Restart(self,menu='all'):
		"""Issues a restart on the menu"""
		if Globals.OnlyShowFavs: 
			if menu == 'all' or menu == 'settings':
				menu = 'favorites'
		if Globals.OnlyShowRecentApps: 
			if menu == 'all' or menu == 'settings':
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
		elif menu == 'recentapps':
			self.Menu = self.BaseMenu = "<RecentApps>"
			self.ConstructMenu()
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


	def addtomenu(self,names,icons,types,paths,execs):
		"""adds item to menu"""
		if icons is None: icons = Gtk.STOCK_MISSING_IMAGE
		self.L_Names.append(names)
		self.L_Icons.append(self.IconFactory.geticonfile(icons))
		self.L_Icons_menu.append(icons)
		self.L_Types.append(types)
		self.L_Paths.append(paths)
		self.L_Execs.append(execs)

        def recentSortCriterium(self, item1, item2):
		"""Sort files"""
                return cmp(item2.get_modified(), item1.get_modified())

	def onRecentChanged(self, manager):
		"""Recent files have changed"""
		print 'recents changed'
		self.recents_changed = True
		try:
			del self.menucache["<RecentItems>"]
			del self.menucache["<RecentApps>"]
		except:pass
		if self.BaseMenu == "<RecentItems>":
			self.emit('changed')

	def on_drive_changed (self,widget,drive):
		"""Bookmarks have changed"""
		print 'drives changed'
		del self.menucache["<Bookmarks>"]
		if self.BaseMenu == "<Bookmarks>":
			self.emit('changed')

	def ConstructMenu(self):
		"""Construct the menu"""
		#aaa = time.clock()
		self.menustring = str(self.Menu)
		if self.menustring in self.menucache:
			self.L_Names, self.L_Icons, self.L_Icons_menu, self.L_Types,self.L_Paths, self.L_Execs= self.menucache[self.menustring]
			return

		self.L_Names = []
		self.L_Icons = []
		self.L_Types = []
		self.L_Paths = []
		self.L_Execs = []
		self.L_Icons_menu = []
		self.searchresults = 0

		#==============================================================
		#XDG PROGRAMS MENU
		#==============================================================
		if isinstance(self.Menu, self.menuparser.MenuInstance):
			
			if Globals.Settings['Shownetandemail'] == 1:
				if self.BaseMenu ==self.menuparser.CacheApplications:
					self.AddInternetButtons()
			#if self.BaseMenu ==self.menuparser.CacheSettings or self.BaseMenu ==self.menuparser.CacheApplications:
			for entry in self.menuparser.GetMenuEntries(self.Menu):	
				if isinstance(entry, self.menuparser.MenuInstance):
					name,icon, path ,comment = self.menuparser.GetDirProps(entry)		#Folder
					self.addtomenu(name,icon,0,path,"")
					if Globals.Settings['Show_Tips']:
						self.ItemComments[name] = comment
				elif isinstance(entry, self.menuparser.EntryInstance):	#Application
					name,icon, execute ,comment = self.menuparser.GetEntryProps(entry)
					self.addtomenu(name,icon,1,"",execute)
					if Globals.Settings['Show_Tips']:
						self.ItemComments[name] = comment
			if self.Menu ==self.menuparser.CacheApplications and int(Globals.Settings['Disable_PS']) == 0:
				self.AddPlacesButton()
				self.AddSystemButton()
			
		#==============================================================
		#AUXILIARY FUNCTIONS MENU
		#==============================================================
		elif self.Menu == "<AuxiliaryFunctions>":

			self.addtomenu(_("About Me"),"user-info",5,"","mate-about-me")
			self.addtomenu(_("Appearance"),"mate-settings-theme",5,"","mate-appearance-properties")
			self.addtomenu(_("Menu editor"),"mozo",6,"","mozo")
			self.addtomenu(_("Screensaver"),"preferences-desktop-screensaver",5,"","mate-screensaver-preferences")
			self.addtomenu(_("System Monitor"),"utilities-system-monitor",5,"","mate-system-monitor")
			self.addtomenu(_("Tilo settings utility"),"%slogo.png" % Globals.GraphicsDirectory,7,"","%sTilo-Settings.py" % Globals.ProgramDirectory)
		#==============================================================
		#FAVORITES ITEMS MENU
		#==============================================================
		elif self.Menu == "<Favorites>":
			client = []
			x = backend.load_setting("favorites")
			if x != None:
				client = x
			try:
				client.sort(key=str.upper)
			except:pass
			
			for elem in client:
				try:
					name, exe,ico,typ = elem.split('::')
					self.addtomenu(name,ico,int(typ),"",exe)
				except:backend.save_setting("favorites",[])
				
			if client == []:
				self.addtomenu(_('No favorites\nUse the mouse right button\nto add or remove favorites'),Gtk.STOCK_MISSING_IMAGE,9,"","")
		#==============================================================
		#WEB BOOKMARKS MENU
		#==============================================================
		elif self.Menu == "<WebBookmarks>":
			
			try:
				if self.webbookmarker is None:
					self.webbookmarker = bookmarks.BookmarksMenu().getBookmarks()
				for item in map(list,self.webbookmarker):
					self.addtomenu(item[0],item[3],3,item[1],item[1])	
			except:print 'Error reading web bookmarks'
			
		#==============================================================
		#SHUTDOWN MENU
		#==============================================================
		elif self.Menu == "<Shutdown>":
			self.addtomenu(_('Shutdown'),'gtk-quit',1,"",Globals.Settings['Shutdown'])
			self.addtomenu(_('Reboot'),'mate-session-reboot',1,"",Globals.Settings['Restart'])
			self.addtomenu(_('Suspend'),'mate-session-suspend',1,"",Globals.Settings['Suspend'])	
			self.addtomenu(_('Hibernate'),'mate-session-hibernate',1,"",Globals.Settings['Hibernate'])	
			self.addtomenu(_('Logout'),'mate-session-logout',1,"",Globals.Settings['LogoutNow'])
			self.addtomenu(_('Lock Screen'),'system-lock-screen',1,"",Globals.Settings['Lock'])	
		#==============================================================
		#RECENT ITEMS MENU
		#==============================================================
		elif self.Menu == "<RecentItems>":
			
		        #self.recent_manager.set_limit(Globals.RI_numberofitems)
			if self.recents_changed or self.recents is None:
				self.recent = self.recent_manager.get_items()
				self.recents_changed = False	
				self.recent.sort(self.recentSortCriterium)
			x = 0
			for item in self.recent:
				name = item.get_short_name()
				self.L_Names.append(name)
				self.L_Icons.append(self.IconFactory.getthumb(item))
				self.L_Icons_menu.append(name)
				self.L_Types.append(3)
				self.L_Paths.append("")
				self.L_Execs.append(item.get_uri())
				#self.addtomenu(item.get_short_name(),self.IconFactory.getthumb(item),3,"",item.get_uri())
				x = x +1
				if x == Globals.RI_numberofitems:break			
			self.addtomenu(_('Clear recent documents'),Gtk.STOCK_CLEAR,10,"","")
			self.sorted_list = []
			
		#==============================================================
		#RECENT APPS MENU
		#==============================================================
		elif self.Menu == "<RecentApps>":
			
		        #self.recent_manager.set_limit(Globals.RI_numberofitems)
			if self.recents_changed or self.recents is None:
				self.recent = self.recent_manager.get_items()
				self.recents_changed = False	
				self.recent.sort(self.recentSortCriterium)
			x = 0
			for item in self.recent:
				if isgio:
					mime = item.get_mime_type()
					app = Gio.app_info_get_default_for_type(mime, 0)
					if app:
						if app.get_name() not in self.L_Names:
							self.addtomenu(app.get_name(),self.IconFactory.getgicon(app.get_icon()),1,"",app.get_executable())
							x = x +1
							if x == Globals.RI_numberofitems:break
				else:
					app = item.last_application()
					appinfo = item.get_application_info(app)
					#print appinfo[0].split(' ')[0]
					if app not in self.L_Names:
						self.addtomenu(app,appinfo[0].split(' ')[0],1,"",appinfo[0].split(' ')[0])
						x = x +1
						if x == Globals.RI_numberofitems:break
			self.sorted_list = []
			
		#==============================================================
		#RECENT BOOKMARKS / PLACES MENU
		#==============================================================
		elif self.Menu == "<Bookmarks>":
			
			self.addtomenu(_("File System"),"drive-harddisk",3,"/","/")
			if isgio:
				self.drives = self.monitor.get_connected_drives()
				for drive in self.drives:			
					if drive.has_media():
						self.mounts = drive.get_volumes()
						for mount in self.mounts:
							ico = mount.get_icon()
							a = self.IconFactory.getgicon(ico)
							self.L_Names.append(mount.get_name())
							self.L_Icons.append(self.IconFactory.geticonfile(a))
							self.L_Icons_menu.append(a)
							self.L_Types.append(3)
							self.L_Paths.append("")
							try:
								self.L_Execs.append(str(mount.get_mount().get_root().get_uri()).replace("file://",""))
							except:
								self.L_Execs.append("")

			self.addtomenu(_('Home Folder'),"user-home",3,"",Globals.HomeDirectory)
			self.addtomenu(_('Computer'),"computer",3,"",'computer:///')
			self.addtomenu(_('Network'),"network",3,"",'network:///')
			self.addtomenu(_('Trash'),'user-trash',3,"",'trash:///')
			if os.path.isfile("%s/.gtk-bookmarks" % Globals.HomeDirectory):
				f = open("%s/.gtk-bookmarks" % Globals.HomeDirectory, "r")
				data = f.readlines(600)
				f.close()
				f = None
				for i in data:		
					self.bm = str(i).replace("\n","")
					if self.bm.find(' ') != -1:
						self.folder =  urllib.url2pathname(self.bm[:self.bm.find(' ')])
						self.name = urllib.url2pathname(self.bm[self.bm.find(' ')+1:])
					else: 
						self.folder = self.bm
						self.name = urllib.url2pathname(str(self.bm).split("/").pop()) 
					try:
						if isgio:
							Gfile = Gio.File(self.folder)
							tuble = [Gfile, Gfile.query_info("standard::*"), []]
							ico = tuble[1].get_icon()
							self.addtomenu(self.name,self.IconFactory.getgicon(ico),3,"",self.folder)
						else:
							self.addtomenu(self.name,"folder",3,"",self.folder)
					except:pass
			
		else:
		#==============================================================
		#XDG PROGRAMS MENU (SEARCH)
		#==============================================================
			#self.searchresults = 0
			for i in [self.menuparser.CacheApplications,self.menuparser.CacheSettings]:
				for entry in self.menuparser.GetMenuEntries(i):
					
					if isinstance(entry, self.menuparser.MenuInstance):		#Folder
						name,icon, path ,comment = self.menuparser.GetDirProps(entry)		#Folder
						
						if self.menuparser.has_matemenu :
							self.SearchMenu(path)
						else:
							self.SearchMenu(i.getMenu(entry.getPath(True)))
	
					elif isinstance(entry, self.menuparser.EntryInstance):	#Application
						name,icon, execute ,comment = self.menuparser.GetEntryProps(entry)
						if name.upper().count(self.Menu) != 0 or execute.upper().count(self.Menu) != 0:
							self.addtomenu(name,icon,1,"",execute)
							self.searchresults=self.searchresults+1

			if self.searchresults==0:
				self.addtomenu("<separator>","",8,"","")
				self.addtomenu(_("No items matched your search criteria"),"",9,"","")
			else:
				self.addtomenu
				self.addtomenu("<separator>","",8,"","")
				self.addtomenu(_("Found %s results to your search") % str(self.searchresults),"",9,"","")
		#Add back button so long as it isn't the base XDG menu
		if isinstance(self.Menu, self.menuparser.MenuInstance):
			if self.Menu !=self.menuparser.CacheApplications:
				self.AddBackButton()
		else:
			if Globals.MenuTabCount == 0:
				if Globals.OnlyShowFavs == False and Globals.OnlyShowRecentApps == False:
					self.AddBackButton()
				else:
					if self.Menu != "<Favorites>" and self.Menu != "<RecentApps>":
						self.AddBackButton()
		#gc.collect()

		#print time.clock() -aaa
		self.menucache[self.menustring] = self.L_Names, self.L_Icons, self.L_Icons_menu, self.L_Types, self.L_Paths, self.L_Execs

	def SearchMenu(self, folder):
		"""search the menu"""
		for entry in self.menuparser.GetMenuEntries(folder):
			
			if isinstance(entry, self.menuparser.MenuInstance):		#Folder
				name,icon, path ,comment = self.menuparser.GetDirProps(entry)		#Folder
				#if self.BaseMenu == self.menuparser.CacheApplications or self.BaseMenu == self.menuparser.CacheSettings:
				if self.menuparser.has_matemenu :
					self.SearchMenu(path)
				else:
					self.SearchMenu(self.BaseMenu.getMenu(entry.getPath(True)))
			elif isinstance(entry, self.menuparser.EntryInstance):	#Application
				name,icon, execute ,comment = self.menuparser.GetEntryProps(entry)
				if name.upper().count(self.Menu) != 0 or execute.upper().count(self.Menu) != 0:
					self.addtomenu(name,icon,1,"",execute)
					self.searchresults=self.searchresults+1

	def AddInternetButtons(self):
		"""Add Internet and Email buttons"""
		# the  " " bellow is necessary to avoid iqual names of this item and the internet section in some translations
		self.addtomenu(_("Browse Internet") + " ","web-browser",1,"",backend.get_default_internet_browser())
		self.addtomenu(_("E-mail")+ " ","emblem-mail",1,"",backend.get_default_mail_client())
		#self.addtomenu("<separator>","",8,"","")
		
	def AddBackButton(self):
		"""Add Back buttons"""
		self.addtomenu(_("Back"),"stock_left",2,"","")

	def AddPlacesButton(self):
		"""Add Places buttons"""
		self.addtomenu(_("Places"),"drive-harddisk",2,"","")

	def AddSystemButton(self):
		"""Add System buttons"""
		self.addtomenu(_("System"),"stock_properties",2,"","")

	def ButtonClick(self,index,event=0):
		"""Callback when buttons are clicked"""
		# 0 Subfolder
		# 1 Application
		# 2 places, settings, back.
		# 3,4 Recents
		self.etype = self.L_Types[index]
		if event == 0:event_button = 1
		else:
			if event.type == Gdk.KEY_PRESS:event_button = 1
			elif event.type == Gdk.EventType.BUTTON_PRESS:event_button = event.button
			elif event.type == Gdk.BUTTON_RELEASE:event_button = event.button
		if event_button == 1:	
			if self.etype == 0:     				#Subfolder
				self.PrevMenu.append(self.Menu)			
				if self.menuparser.has_matemenu :
					self.Menu = self.L_Paths[index]
				else:
					self.Menu = self.BaseMenu.getMenu(self.L_Paths[index])
				self.ConstructMenu()
			elif self.etype == 1 or self.etype == 3 or self.etype == 4:                   #Application
				self.Launcher.Launch(self.L_Execs[index],self.etype)
				self.Restart('previous')
				return 1
			elif self.etype == 2:                              #Menu special buttons places, settings, back.
				if self.L_Names[index] == _('Back'):
					try:
						self.Menu = self.PrevMenu.pop()
					except:
						self.Menu = self.BaseMenu = self.menuparser.CacheApplications
					if self.Menu == self.menuparser.CacheApplications:
						self.BaseMenu = self.Menu
					self.ConstructMenu()
				elif self.L_Names[index] == _("System"):
					self.PrevMenu.append(self.Menu)
					self.Restart('settings')
				elif self.L_Names[index] == _("Places"):
					self.PrevMenu.append(self.Menu)
					self.Restart('places')	
			elif self.etype == 5 or self.etype == 6:                                                   #Items in the menu have changed
				self.Launcher.Launch(self.L_Execs[index],self.etype)
			elif self.etype == 7:                                                   #Properties of the menu have changed
				self.Launcher.Launch(self.L_Execs[index],self.etype)
				Globals.ReloadSettings()
			elif self.etype == 10: #Clear Recent 
				self.recent_manager.purge_items()
				self.Restart('previous')
		elif event_button == 3:
			self.m = Gtk.Menu()
			name = self.L_Names[index]
			favlist = backend.load_setting("favorites")
			try:
				thismenu = add_image_menuitem(self.m,self.L_Icons_menu[index], name, self.dummy,'1')
			except:return
			if zg and self.allgio is not None:	
				self.recent_files = None
				self.most_used_files = None
				for z in self.allgio:
					if z.get_name() == name:
						desk = z.get_id()	
						self.recent_files = zg.get_recent_for_app(desk,Globals.RI_numberofitems)
						self.most_used_files = zg.get_most_used_for_app(desk,Globals.RI_numberofitems)
						break
				if self.recent_files or self.most_used_files:
					self.menuitem = add_menuitem(self.m, "-")
				for files, menu_name in ((self.recent_files, _('Recently Used')), (self.most_used_files, _('Most Used'))):
					if files:
						self.submenu = Gtk.Menu()
						menu_item = Gtk.MenuItem(menu_name)
						menu_item.set_submenu(self.submenu)
						self.m.append(menu_item)
						menu_item.show()
						for ev in files:
							for subject in ev.get_subjects():
								label = subject.text or subject.uri
								submenu_item = Gtk.MenuItem(label, use_underline=False)
								self.submenu.append(submenu_item)
								# "activate" doesn't seem to work on sub menus
								# so "button-press-event" is used instead.
								submenu_item.connect("button-press-event", self.launch_item, subject.uri)
								submenu_item.show()
			if self.etype != 0 and name != _('Back'):
				if self.etype != 3:
					self.menuitem = add_menuitem(self.m, "-")
					self.menuitem = add_image_menuitem(self.m, Gtk.STOCK_DIALOG_AUTHENTICATION, _("Open as Administrator"), self.runasadmin,name, self.L_Execs[index],self.L_Icons_menu[index],self.L_Types[index])
				else:

					def searchfolder(folder,me):
						dirs = os.listdir(folder)
						dirs.sort(key=str.upper)
						for item in dirs:
							if not item.startswith('.'):
								if os.path.isdir(os.path.abspath(folder) + '/'+item):
									add_image_menuitem(me,Gtk.STOCK_DIRECTORY, item,self.launch_item, 	'"'+os.path.abspath(folder.replace('file://','')) + '/'+item +'"')
								else:
									submenu_item = Gtk.MenuItem(item, use_underline=False)
									me.append(submenu_item)
									# "activate" doesn't seem to work on sub menus
									# so "button-press-event" is used instead.
									submenu_item.connect("button-press-event", self.launch_item, 	'"'+os.path.abspath(folder) + '/'+item +'"')
									submenu_item.show()
					f = os.path.abspath(urllib.url2pathname(self.L_Execs[index]).replace('file://',''))
					if os.path.exists(f):
						if os.path.isdir(f):
							self.submenu = Gtk.Menu()
							thismenu.set_submenu(self.submenu)
							
							searchfolder(f,self.submenu)
						elif os.path.isfile(f):
							if isgio:
								add_menuitem(self.m, "-")
								self.openwith = add_image_menuitem(self.m,Gtk.STOCK_OPEN, _("Open with"))
								Gfile = Gio.File(f)
								tuble = [Gfile, Gfile.query_info("standard::*"), []]
								name = tuble[1].get_name()
								#ff =  Gio.file_parse_name(f)
								apps = Gio.app_info_get_all_for_type(tuble[1].get_content_type())
								self.submenu = Gtk.Menu()
								self.openwith.set_submenu(self.submenu)
								for app in apps:
									self.menuitem = add_menuitem(self.submenu, app.get_name(),self.custom_launch, "'" +f+ "'",app.get_executable())								

					if name == _('Trash'):
						self.menuitem = add_menuitem(self.m, "-")
						self.menuitem = add_image_menuitem(self.m, Gtk.STOCK_CLEAR, _("Empty Trash"), self.emptytrash)
				if '%s::%s::%s::%s' % (name,self.L_Execs[index],self.L_Icons_menu[index],str(self.L_Types[index])) not in favlist:
					self.menuitem = add_menuitem(self.m, "-")
					self.menuitem = add_image_menuitem(self.m, Gtk.STOCK_ADD, _("Add to Favorites"), self.addfav,name,self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])
				else:
					self.menuitem = add_menuitem(self.m, "-")
					self.menuitem = add_image_menuitem(self.m, Gtk.STOCK_REMOVE, _("Remove from Favorites"), self.removefav,name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])
				self.menuitem = add_menuitem(self.m, "-")
				self.menuitem = add_image_menuitem(self.m, Gtk.STOCK_HOME, _("Create Desktop Shortcut"), self.addshort,name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])
				self.menuitem = add_menuitem(self.m, "-")
				if ('%s.desktop' % name) in os.listdir(Globals.AutoStartDirectory):
					self.menuitem = add_image_menuitem(self.m, Gtk.STOCK_REMOVE, _("Remove from System Startup"), self.remove_autostarter,name,  self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])
				else:
					self.menuitem = add_image_menuitem(self.m, Gtk.STOCK_ADD, _("Add to System Startup"), self.create_autostarter,name, self.L_Execs[index], self.L_Icons_menu[index], self.L_Types[index])
			self.m.show_all()
			self.m.popup(None, None, None, event.button, event.time)
			self.submenu = None
			self.menuitem = None
			gc.collect()

	def emptytrash(self,widget,event):

		if os.path.exists("%s/.local/share/Trash" % Globals.HomeDirectory):
			os.system("rm -rf %s/.local/share/Trash/info/* &" % Globals.HomeDirectory)
			os.system("rm -rf %s/.local/share/Trash/files/* &" % Globals.HomeDirectory)
		elif os.path.exists("%s/.Trash" % Globals.HomeDirectory):
			os.system("rm -rf %s/.Trash/* &" % Globals.HomeDirectory)


	def custom_launch(self,widget,event, uri,app):
		os.system('%s %s &' % (app,uri))
			
	def launch_item(self, button, event, uri):
		os.system('xdg-open %s &' %uri)

	def run(self,widget,event,name, execs,ico,typ):
		pass

	def dummy(self,widget,event,data):
		pass

	def runasadmin(self,widget,event,name, execs,ico,typ):
		os.system('%s "%s" &' % (Globals.Settings['AdminRun'],execs))

	def addfav(self,widget,event,name, execs,ico,typ):
		"""Add to Favorites"""
		typ = str(typ)
		favlist = backend.load_setting("favorites")
		if '%s::%s::%s::%s' % (name, execs, ico, typ) not in favlist:
			favlist.append('%s::%s::%s::%s' % (name, execs, ico, typ))
			backend.save_setting("favorites",favlist)
			del self.menucache["<Favorites>"]
			self.notifier.notify('%s %s' % (name, _('added to favorites list')),Globals.name,Globals.Applogo,5000)
		
	def removefav(self,widget,event,name, execs,ico,typ):
		"""Remove from Favorites"""
		typ = str(typ)
		favlist = backend.load_setting("favorites")
		if '%s::%s::%s::%s' % (name, execs, ico, typ) in favlist:
			favlist.remove('%s::%s::%s::%s' % (name, execs, ico, typ))
			backend.save_setting("favorites",favlist)
			del self.menucache["<Favorites>"]
			self.emit('changed')
			self.notifier.notify('%s %s' % (name, _('removed from favorites list')),Globals.name,Globals.Applogo,5000)

	def create_autostarter (self,widget,event,name, execs,ico,typ):
		"""Create Autostarter"""
		if not os.path.isdir(Globals.AutoStartDirectory):
			os.system('mkdir %s' % Globals.AutoStartDirectory)
		if ('%s.desktop' % name) not in os.listdir(Globals.AutoStartDirectory):
			self.addshort(widget,event,name,execs,ico,typ,Globals.AutoStartDirectory)
			self.notifier.notify('%s %s' % (name, _('added to system startup')),Globals.name,Globals.Applogo,5000)

	def remove_autostarter (self,widget,event,name, execs,ico,typ):
		"""Remove Autostarter"""
		if not os.path.isdir(Globals.AutoStartDirectory):
			os.system('mkdir %s' % Globals.AutoStartDirectory)
		if ('%s.desktop' % name)  in os.listdir(Globals.AutoStartDirectory):
			os.system('rm "%s%s.desktop"' % (Globals.AutoStartDirectory,name))
			self.notifier.notify('%s %s' % (name, _('removed from system startup')),Globals.name,Globals.Applogo,5000)			
					
	def addshort(self,widget,event,name, execs,ico,typ,desk='desktop'):
		"""Add Desktop shortcut"""
		if desk =='desktop':desk = utils.xdg_dir("XDG_DESKTOP_DIR")
		starter = '%s/%s.desktop' % (desk, name)
		code = ['#!/usr/bin/env xdg-open','[Desktop Entry]']
		code.append('Name=%s' % name)
		code.append('StartupNotify=true')
		code.append('Terminal=false')
		code.append('Version=1.0')
		code.append('Icon=%s' % ico)
		code.append('Type=Application')
		if int(typ) == 1:
			code.append('Exec= %s' % execs)
		else:
			code.append('Exec= xdg-open %s' % execs)
		code.append('X-MATE-Autostart-enabled=true')
		#print code
		f = open(starter, 'w')
		if f:
			for l in code:
				f.write(l + '\n')
			f.close()

	def CallSpecialMenu(self,command,data=None):
		"""Call was placed on the menu"""
		command = int(command)
		a = str(self.Menu)
		if command==0:	#Back button
			if self.PrevMenu:
				self.Menu = self.PrevMenu.pop()
				self.ConstructMenu()
		elif command==1:	#Go to base menu and reload it
			self.PrevMenu = []
			self.Restart()
		elif command==2:	#Go to unmount drives menu
			if a != '<RecentApps>':
				self.PrevMenu.append(self.Menu)
				self.Restart('recentapps')
		elif command==3:	#Auxiliary functions menu
			if a != '<AuxiliaryFunctions>':
				self.PrevMenu.append(self.Menu)
				self.Restart('auxiliary')
		elif command==4:	#Recent Items Menu
			if a != '<RecentItems>':
				self.PrevMenu.append(self.Menu)
				self.Restart('recent')
		elif command==5:	#Search
			if data!="":
				self.PrevMenu = [self.BaseMenu]
				self.Menu=data.upper()
				self.ConstructMenu()
			else:
				self.PrevMenu = []
				self.Menu=self.BaseMenu
				self.ConstructMenu()
		elif command==6:	#Launch first item in search list
			if self.searchresults!=0:
				if Globals.Settings['Shownetandemail'] == 1:
					self.ButtonClick(3)
				else:
					self.ButtonClick(0)
		elif command==7:	#Recent Items Menu
			if a != '<Favorites>':
				self.PrevMenu.append(self.Menu)
				self.Restart('favorites')
		elif command==8:	#Recent Items Menu
			if a != '<Bookmarks>':
				self.PrevMenu.append(self.Menu)
				self.Restart('places')
		elif command==9:	#Recent Items Menu
			if a != '<Shutdown>':
				self.PrevMenu.append(self.Menu)
				self.Restart('shutdown')
		elif command==10:	#Recent Items Menu
			if a != '<WebBookmarks>':
				self.PrevMenu.append(self.Menu)
				self.Restart('webbookmarks')

	def Icon_change(self):
		self.IconFactory.Icon_change()

	def destroy(self):
		pass

#! /usr/bin/python

import sys
import os
import pygtk
pygtk.require('2.0')
import gtk
import mateconf

try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'
sys.path.append(INSTALL_PREFIX + '/lib/tilo')

import utils
from awn.extras import awnlib, __version__

class Tilo ():
	icons = {}
	def __init__(self, applet):
		self.applet = applet
		self.applet.set_tooltip_text("Tilo")
		mateconf_app_key = '/apps/tilo'
		self.dokey = '/apps/mate-do/Docky/Utilities/DockPreferences'
		self.mateconf_client = mateconf.client_get_default()
		#print self.applet.get_size()
		#print self.applet.get_position()
		self.orient = self.mateconf_client.get_string(mateconf_app_key + '/Orientation')
		if self.orient == 'Top':
			self.mateconf_client.set_string(mateconf_app_key + '/orientation', 'top')
		else:
			self.mateconf_client.set_string(mateconf_app_key + '/orientation', 'bottom')
		proc = os.popen("""ps axo "%p,%a" | grep "Tilo.py" | grep -v grep|cut -d',' -f1""").read()
		procs = proc.split('\n')
		if len(procs) > 2:
			import wnck
			try:
				wnck.set_client_type(wnck.CLIENT_TYPE_PAGER)
			except AttributeError:
				print "Error: Failed to set libwnck client type, window " \
						"activation may not work"
			screen = wnck.screen_get_default()
			while gtk.events_pending():
				gtk.main_iteration()
			wins = screen.get_windows_stacked()
			
			for win in wins:
				name = win.get_name()
				if name == 'GnoMeny.py':
		
					if win and win.is_hidden():
						sys.exit(1)
					elif win and win.is_minimized():
						win.unminimize(1)
					elif win and win.is_active() == False:
						win.activate(1)
		#Get the default icon theme
		import Globals as Globals
		self.Globals = Globals
		#self.theme.connect('changed', self.icon_theme_changed)
		from Menu_Main import Main_Menu
		self.hwg = Main_Menu(self.HideMenu)
		#print self.hwg.window.window.is_visible()
		self.ShowMenu()


	def size_changed(self):
		self.applet.icon.file(self.Globals.Applogo, size=awnlib.Icon.APPLET_SIZE)


	def button_press(self, widget, event):
		if event.button in (1, 2):
			if not self.hwg.window.window:
				self.ShowMenu()
			else:
				if not self.hwg.window.window.is_visible():
					self.ShowMenu()
				else: self.HideMenu()

		elif event.button == 3:
			self.HideMenu()
			self.show_menu(event)

	def ShowMenu(self):
		# Display the start menu!!!
		origin = self.applet.get_window().get_origin()
		
		self.hwg.Adjust_Window_Dimensions(origin[0] - (self.Globals.MenuWidth/2),origin[1]+self.applet.get_size())#self.applet.get_window().get_geometry()[3]/2 -10)
		self.hwg.show_window()

	def HideMenu(self):
		if self.hwg:
			if self.hwg.window.window:
				if self.hwg.window.window.is_visible()== True:
					self.hwg.hide_window()

	def show_menu(self,event):

		#Create the items for Preferences and About
		self.prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		self.edit = gtk.ImageMenuItem(gtk.STOCK_EDIT)
	
		#Connect the two items to functions when clicked
		self.prefs.connect("activate", self.properties)
		self.about.connect("activate", self.about_info)
		self.edit.connect("activate", self.edit_menus)

	
		#Now create the menu to put the items in and show it
		self.menu = self.applet.create_default_menu()
		self.menu.append(self.prefs)
		self.menu.append(self.about)
		self.menu.append(self.edit)
		self.menu.show_all()
		self.menu.popup(None, None, None, event.button, event.time)
		

	def properties(self,event=0,data=None):
		#os.spawnvp(os.P_WAIT,Globals.ProgramDirectory+"Tilo-Settings.py",[Globals.ProgramDirectory+"Tilo-Settings.py"])
		os.system("/bin/sh -c '"+self.Globals.ProgramDirectory+"Tilo-Settings.py' &")
		# Fixme, reload stuff properly
		self.Globals.ReloadSettings()
		
	def about_info(self,event=0,data=None):
		os.system("/bin/sh -c " + INSTALL_PREFIX +"'/lib/"+self.Globals.appdirname+"/Tilo-Settings.py --about' &")

	def edit_menus(self,event=0, data=None):
		os.spawnvp(os.P_WAIT,"mozo",["mozo"])
		#ConstructMainMenu()

applet_name = "Tilo"
applet_description = "Consolidated menu for Mate"
applet_theme_logo = INSTALL_PREFIX + "/lib/tilo/graphics/" + "logo.png"

if __name__ == "__main__":
    awnlib.init_start(Tilo, {"name": applet_name,
        "short": "Tilo",
        "version": __version__,
        "description": applet_description,
        "theme": applet_theme_logo,
        "author": "Helder Fraga aka Whise",
        "copyright-year": "2008 - 2009",
        "authors": ["Helder Fraga <helderfraga@gmail.com"]},
        ["settings-per-instance"])


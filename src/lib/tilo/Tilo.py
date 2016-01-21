#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) QB89Dragon 2007/8 <hughescih@hotmail.com>
#(c) Whise 2008,2009,2010 <helderfraga@gmail.com>
#
# Consolidated Gnome Menu
# This is free software made available under the GNU public license.
# Use 'run-in-window' command switch for development testing")

import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk
from gi.repository import MatePanelApplet

import pygtk
pygtk.require('2.0')
import commands
import sys
import gobject
import os

if not os.path.exists(os.path.expanduser("~") + '/.tilo') or not os.path.isdir(os.path.expanduser("~") + '/.tilo'):
	os.system('mkdir ~/.tilo')

try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'

#sys.path.append(INSTALL_PREFIX + '/lib/tilo/') #is this causing the oafiid error???

import Globals
import backend
from Menu_Main import Main_Menu
import utils
import gettext

gettext.textdomain('tilo')
gettext.install('tilo', INSTALL_PREFIX +  '/share/locale')
gettext.bindtextdomain('tilo', INSTALL_PREFIX +  '/share/locale')

def _(s):
	return gettext.gettext(s)

class Tilo(MatePanelApplet.Applet):

	def __init__(self,applet,iid):
		self.panel_size = 24
		self.Button_state = 0 # 0 = No change  1 = Mouse over  2 = Depressed
		self.applet = applet
		self.applet.set_name(Globals.name)
		self.remove_applet_border()
		self.panel_id = None
		self.hwg = None
		orient = None
		try:
			orient = self.applet.get_orient()
		except:pass

		self.orientation = None
		if orient == 1:
			self.orientation = 'top'
		else:
			self.orientation = 'bottom'

		self.mateconf_client = mateconf.client_get_default()
		self.mateconfkey = self.applet.get_preferences_key()
		if self.orientation == 'top':
			Globals.flip = False
		elif self.orientation == 'bottom':
			Globals.flip = None
		else : self.size = 30
		self.size = self.get_panel_size()
		self.store_settings()
		self.Fixed = gtk.Fixed()
		self.EBox = gtk.EventBox()
		self.EBox.set_tooltip_text(Globals.name)
		self.Fixed.put(self.EBox,0,0)
		self.applet.add(self.Fixed)
		self.EBox.set_border_width(0)
		self.EBox.set_visible_window(0)
		self.Fixed.set_border_width(0)
		self.size = self.get_panel_size()
		self.Image = gtk.Image()
		if Globals.Settings["Distributor_Logo"] == 1:
			im = gtk.gdk.pixbuf_new_from_file_at_size(Globals.distro_logo,self.size,self.size)
			if self.Button_state == 1:
				im.saturate_and_pixelate(im, 1.5, False)
			elif self.Button_state == 2:
				im.saturate_and_pixelate(im, 0.0, False)
			pixmap = im

		else:			
			im = gtk.gdk.pixbuf_new_from_file(Globals.StartButton[self.Button_state])

		w = im.get_width()
		h = im.get_height()
		self.scale = float(self.size)/float(h)
		if Globals.ButtonLabelCount == 1 and Globals.Settings["Distributor_Logo"] == 0:
			self.set_button_label()

		pixmap = im.scale_simple(int(w*self.scale),int(self.size),gtk.gdk.INTERP_HYPER)
		im = None
		if Globals.flip == False and Globals.ButtonHasTop == 1:
			pixmap = pixmap.flip(Globals.flip)

		self.Image.set_from_pixbuf(pixmap)
		self.EBox.add(self.Image)
		self.applet.set_background_widget(self.applet)
		self.applet.set_events(gtk.gdk.ALL_EVENTS_MASK)
		self.applet.connect("destroy",self.cleanup)
	        self.applet.connect("destroy-event",self.cleanup)
	        self.applet.connect("delete-event",self.cleanup)
	        self.applet.connect("change-orient",self.change_orientation)
      		self.applet.connect("size-allocate", self.size_allocate_event)
      		self.applet.connect("map-event", self.map_event)
		self.EBox.connect("button-press-event",self.button_press)
		self.EBox.connect("enter-notify-event", self.select_box)
		self.EBox.connect("leave-notify-event", self.deselect_box)
		self.old_origin = None
		self.oldsize = 0
		self.x,self.y = 0,0
		self.oldx,self.oldy = 0,0
		self.aux = None
		self.applet.show_all()
		self.applet.realize()
		self.EBox.realize()
		#self.callback = gobject.timeout_add(1000,self.timeout_callback)
		self.EBox.set_size_request(-1,self.size)
		self.Fixed.set_size_request(-1,self.size )
		self.Image.set_size_request(-1,self.size)



	def store_settings(self):
		"""Stores orientation in settings"""
		if self.orientation != backend.load_setting("orientation"):
			if self.orientation is None:
				backend.save_setting('orientation', 'bottom')
				backend.save_setting('size', self.size)
			else:
				utils.show_message(_('Menu needs to restart , restart now?'))
				backend.save_setting('orientation', self.orientation)
				backend.save_setting('size', self.size)
				sys.exit()
		try:
			backend.save_setting('orientation', self.orientation)
			backend.save_setting('size', self.size)
		except:pass


	def get_panel_size(self):
		if self.mateconfkey != None:
			self.mateconfkey = str(self.mateconfkey).replace('/prefs','')
			self.panel_id = self.mateconf_client.get_string(self.mateconfkey + "/toplevel_id")			

		if self.panel_id != None:				
			self.size = int(self.mateconf_client.get_int("/apps/panel/toplevels/" + self.panel_id + "/size"))
			self.mateconf_client.add_dir("/apps/panel/toplevels/" + self.panel_id + "/size",mateconf.CLIENT_PRELOAD_NONE)
			self.mateconf_client.notify_add("/apps/panel/toplevels/" + self.panel_id + "/size", self.update_panel_size) 
			return int(self.size)
		else: 

			try:
				self.size= self.applet.get_size()
			except:
				self.size = 30
			return self.size


	def set_button_label(self):
		self.Label = gtk.Label()
		self.txt = Globals.ButtonLabelMarkup
		try:
			self.txt = self.txt.replace(Globals.ButtonLabelName,_(Globals.ButtonLabelName))
		except:pass
		self.Fixed.put(self.Label,int(self.scale*Globals.ButtonLabelX),int(self.scale*Globals.ButtonLabelY))
		self.set_button_label_size()

	def set_button_label_size(self):
		if Globals.Settings["Distributor_Logo"] == 0:
			im = gtk.gdk.pixbuf_new_from_file(Globals.StartButton[self.Button_state])
			w = im.get_width()
			h = im.get_height()
			im = None
			self.txt = Globals.ButtonLabelMarkup
			try:
				self.txt = self.txt.replace(Globals.ButtonLabelName,_(Globals.ButtonLabelName))
			except:pass
			self.scale = float(self.size)/float(h)
			self.Fixed.move(self.Label,int(self.scale*Globals.ButtonLabelX),int(self.scale*Globals.ButtonLabelY))
			self.Label.set_size_request(-1,self.size)
			self.txt_font = self.txt[self.txt.find("font_desc='")+11:]
			self.txt_size = int(self.txt_font[:self.txt_font.find("'")].split(' ').pop())
			self.txt_all = self.txt_font.replace(str(self.txt_size),str(int(self.txt_size*self.scale)))
			self.txt = self.txt.replace(self.txt_font,self.txt_all)
			self.Label.set_markup(self.txt)	

	def remove_applet_border(self):
      		gtk.rc_parse_string ("""
	               style \"Tilo-style\"
	               {
	                 GtkWidget::focus-line-width = 0
	                 GtkWidget::focus-padding = 0
	               }
	               widget \"*.Tilo\" style \"Tilo-style\"
	               """)

	def change_orientation(self,arg1,data):
		orient = self.applet.get_orient()
		self.orientation = None
		if orient == 1:
			self.orientation = 'top'
		else:
			self.orientation = 'bottom'
		if self.orientation != backend.load_setting("orientation"):
			if self.orientation is None:
				backend.save_setting('orientation', 'bottom')
				backend.save_setting('size', self.size)
			else:
				utils.show_message(_('Menu needs to restart , restart now?'))
				backend.save_setting('orientation', self.orientation)
				backend.save_setting('size', self.size)
				sys.exit()

	def map_event(self, widget, event):
		print 'map'
		if Globals.ShowTop == 1 and  Globals.Settings["Distributor_Logo"] == 0:
			#Create auxiliary window (CAIRO)
			from Panel_Top import PanelTopWindow
			self.aux = PanelTopWindow()
			self.aux.aux_window.connect("enter-notify-event", self.select_box)
			self.aux.aux_window.connect("leave-notify-event", self.deselect_box)
			self.aux.aux_window.connect("button-press-event",self.button_press)
		self.Redraw_graphics()
		self.Update_Panel_Top()
		if Globals.ShowTop == 1 and Globals.Settings["Distributor_Logo"] == 0:
			self.aux.updateimage(Globals.StartButtonTop[self.Button_state ])
		self.hwg = Main_Menu(self.HideMenu)
		self.hwg.connect('state-changed',self.button_changed)
		self.hwg.Adjust_Window_Dimensions(self.x,self.y)
		Globals.SavedOriginState = self.x,self.y

	def size_allocate_event(self, widget, allocation):
		if widget.window:		
			self.x, self.y = widget.window.get_origin()
			self.update_panel_position()
		else:
			self.x, self.y = 0,0		
		return True

	def update_panel_position(self):
		if self.x != self.oldx and self.hwg != None:
			print 'position changed'
			self.Redraw_graphics()
			self.Update_Panel_Top()
			if Globals.ShowTop == 1 and self.aux != None and Globals.Settings["Distributor_Logo"] == 0:
				self.aux.updateimage(Globals.StartButtonTop[self.Button_state ])
			#self.hwg = Main_Menu(self.HideMenu)
			self.hwg.Adjust_Window_Dimensions(self.x,self.y)
			Globals.SavedOriginState = self.x,self.y
			self.oldx= self.x
			if Globals.ButtonLabelCount == 1:
				self.set_button_label_size()

	def update_panel_size(self,client, connection_id, entry, args):
		if entry.get_key() == "/apps/panel/toplevels/%s/size" % self.panel_id:
			try:
				self.size = entry.get_value().get_int()
			except:self.size = 30
		if self.size != self.oldsize and self.hwg :
			print 'size changed'
			self.Redraw_graphics()
			self.Update_Panel_Top()
			if Globals.ShowTop == 1 and self.aux != None and Globals.Settings["Distributor_Logo"] == 0:
				self.aux.updateimage(Globals.StartButtonTop[self.Button_state ])
			#self.hwg = Main_Menu(self.HideMenu)
			self.hwg.Adjust_Window_Dimensions(self.x,self.y)
			Globals.SavedOriginState = self.x,self.y
			self.oldsize= self.size
			if Globals.ButtonLabelCount == 1:
				self.set_button_label_size()
					
		return True

	def auxdestroyed(self):	
		#Respawn point for the aux window if it has been Alt-F4ed
		if Globals.ShowTop == 1:
			#Used in this instance for providing delay for window to be created
			self.aux = PanelTopWindow()
			#self.aux.Create(self, 0)	 #Create the orb top
			self.aux.updateimage(Globals.StartButtonTop[self.Button_state ])
				

	def button_press(self,widget,event):
		if event.button == 1:
			# Remove this next line when orb top repositioning on widget move is fixed
			if Globals.ShowTop == 1:
				pass
				#self.window_moved(self.aux)
			if not self.hwg.window.window:
				self.hwg.Adjust_Window_Dimensions(self.x,self.y)
				self.ShowMenu()
				self.Button_state = 2
			else:
				if self.Button_state == 2:
					self.HideMenu()
					self.Button_state = 1

				else:
					self.hwg.Adjust_Window_Dimensions(self.x,self.y)
					self.ShowMenu()
					self.Button_state = 2

	
			self.Redraw_graphics()
			#self.Update_Panel_Top()
		elif event.button == 3:
			self.create_menu()
					
	def create_menu(self):

		self.propxml="""
		<popup name="button3">
		<menuitem name="Preferences" verb="Props" stockid="gtk-properties"/>
		<menuitem name="About Item" verb="About" stockid="gtk-about"/>
		<menuitem name="Edit Menus" verb="Edit" stockid="gtk-edit"/>
		</popup>
		"""
		self.verbs = [ ( "Props", self.properties ),
					   ( "About", self.about_info ),
					   ( "Edit", self.edit_menus) ]
		self.applet.setup_menu(self.propxml,self.verbs,None)
			

	def edit_menus(self,event, data=None):
		os.spawnvp(os.P_WAIT,Globals.Settings['MenuEditor'],[Globals.Settings['MenuEditor']])
		#ConstructMainMenu()

	def about_info(self,event,data=None):

		os.system("/bin/sh -c '%s/lib/%s/Tilo-Settings.py --about' &" %( INSTALL_PREFIX, Globals.appdirname))

	def properties(self,event,data=None):

		os.system("/bin/sh -c '%sTilo-Settings.py' &" % Globals.ProgramDirectory)
		# Fixme, reload stuff properly
		Globals.ReloadSettings()
		
	def select_box(self,widget,event):
		if self.Button_state == 0:
			self.Button_state = 1
		self.Redraw_graphics()
		
	def deselect_box(self,widget,event):
		if self.Button_state == 1:
			self.Button_state = 0
		self.Redraw_graphics()
		
	def button_changed(self,event,button,button1):
		self.Button_state = button
		self.Redraw_graphics()
		self.Update_Panel_Top()
		if Globals.ShowTop == 1 and Globals.Settings["Distributor_Logo"] == 0:
			self.aux.updateimage(Globals.StartButtonTop[self.Button_state ])
		print button

		
	def cleanup(self,event):
		print "cleanup"

		self.hwg.destroy()
		if Globals.ShowTop == 1:
			Globals.ShowTop = 0
			self.aux.destroy()
		#gtk.main_quit()
		del self.applet
	
	def ShowMenu(self):
		# Display the start menu!!!
		origin = self.applet.window.get_origin()
		try:
			if origin != Globals.SavedOriginState:
				self.hwg.Adjust_Window_Dimensions(origin[0],origin[1])
		except:pass
		if self.hwg:
			self.hwg.show_window()
		try:
			self.aux.aux_window.window.set_transient_for(self.hwg.window)
			self.hwg.window.window.set_transient_for(self.applet.window)
		except:pass

	def HideMenu(self):
		if self.hwg:
			if self.hwg.window.window:
				if self.hwg.window.window.is_visible()== True:
					self.hwg.hide_window()

		self.Button_state = 0
		self.Redraw_graphics()

	def Redraw_graphics (self):
		self.Fixed.set_size_request(-1,self.size)
		self.EBox.set_size_request(-1,self.size)
		self.Image.set_size_request(-1,self.EBox.allocation.height)
		if Globals.Settings["Distributor_Logo"] == 1:
			im = gtk.gdk.pixbuf_new_from_file_at_size(Globals.distro_logo,self.size,self.size)
			if self.Button_state == 1:
				im.saturate_and_pixelate(im, 1.5, False)
			elif self.Button_state == 2:
				im.saturate_and_pixelate(im, 0.0, False)
			pixmap = im

		else:
			im = gtk.gdk.pixbuf_new_from_file(Globals.StartButton[self.Button_state])
			w = im.get_width()
			h = im.get_height()
			self.scale = float(self.size)/float(h)
			pixmap = im.scale_simple(int(w*self.scale),self.size,gtk.gdk.INTERP_HYPER)

		if Globals.flip == False and Globals.ButtonHasTop == 1:
			pixmap = pixmap.flip(Globals.flip)
			
		self.Image.set_from_pixbuf(pixmap)
		if Globals.ShowTop == 1 and self.aux != None and Globals.Settings["Distributor_Logo"] == 0:
			self.aux.updateimage(Globals.StartButtonTop[self.Button_state ])
		im = None
		pixmap = None

	def Update_Panel_Top(self,widget=None, event=None):

		if Globals.ShowTop == 1 and self.aux != None and Globals.Settings["Distributor_Logo"] == 0:
			self.aux.updateimage(Globals.StartButtonTop[self.Button_state ])
			self.applet.queue_draw()
			self.aux.aux_window.window.set_transient_for(self.applet.window)
			if self.scale:
				self.aux.set_scale(self.scale)
			StartButtonTopHeight = self.aux.get_height()
			print "Reorientating Orb top!! (Don't let this happen too often!!)"
			Window_x =  self.x
			if self.orientation == 'top':
				Window_y =  0 + self.size
			else:
				Window_y =  Globals.screenheight - self.size - StartButtonTopHeight
			# Calculate midpoint of screen
			self.screenmidpty = int(Globals.screenheight / 2)
			# Work out orientation of panel 
			self.aux.move(Window_x,Window_y)
		
try:
	gobject.type_register(Tilo)
except:pass

# MateComponent factory of Menu
def Tilo_factory(applet, iid):
	# Start the applet
	app = Tilo(applet,iid)
	return True

def showmenu(a):
	g.ToggleMenu()


if len(sys.argv) == 2:

	if sys.argv[1] == "run-in-window" or sys.argv[1] == "run-in-console":
		# Start the applet in windowed mode
		main_window = Gtk.Window()
		main_window.set_decorated(1)
		main_window.set_title("Tilo Testing Sandpit")
		main_window.connect("destroy", Gtk.main_quit) 
		app = MatePanelApplet.Applet()
		Tilo(app,"")
		app.reparent(main_window)
		main_window.show_all()
		gtk.main()
		sys.exit()


	
if __name__ == '__main__':

	MatePanelApplet.Applet.factory_main("OAFIID:MATE_Tilo_Factory", True,
	           MatePanelApplet.Applet.__gtype__,
	           Tilo_factory, None)


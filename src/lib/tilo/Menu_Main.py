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
# Menu window
# Part of the GnoMenu

import gi
gi.require_version("Gtk", "2.0")

#from gi.repository import Gtk, GObject
from gi.repository import Gtk, Gdk, GObject

import sys
import pygtk
pygtk.require("2.0")
#import gtk
#import gobject
import cairo
import os
#import pango
from Menu_Widgets import MenuButton , Separator, ImageFrame, ProgramList, IconProgramList,MenuTab, MenuLabel, MenuImage,TreeProgramList, CairoProgramList
import Globals
import cairo_drawing
import utils
import Launcher
import commands
import IconFactory


try:
	has_gst = True
	import gst
except:
	has_gst = False

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

# Class for a button object from menu

try:
	import psyco
	psyco.profile()

except:pass

import time

class Main_Menu(GObject.GObject):
	__gsignals__ = {
        'state-changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,(GObject.TYPE_INT,GObject.TYPE_INT)),
        }

	first_time = True
	def __init__(self, hide_method):
		GObject.GObject.__init__(self)
		print 'start'
		self.searchitem = ''
		self.hide_method = hide_method
		#Set the main working directory to home
		os.chdir(Globals.HomeDirectory)
		self.window = Gtk.Window()
		self.window.set_title('Tilo')
		self.window.set_focus_on_map(1)
		self.window.set_app_paintable(1)
		self.window.set_skip_taskbar_hint(1)
		self.window.set_skip_pager_hint(1)
		self.window.set_decorated(0)
		self.window.set_keep_above(0) #Make this always above other windows
		self.window.stick() #Make this appear on all desktops
		self.window.set_default_size(Globals.MenuWidth,Globals.MenuHeight)
		#self.window.set_events(Gdk.ALL_EVENTS_MASK)
                try:    # Workaround for Ubuntu Natty
                        self.window.set_property('has-resize-grip', False)
                except TypeError:
                        pass
		#if not self.window.window:
		self.colorpb = None
		self.setup()
		self.window.connect("composited-changed", self.composite_changed)
		self.window.connect("expose_event", self.expose)
		self.window.connect("destroy", gtk.main_quit)	#Fixme?
		self.window.connect("focus-out-event", self.lose_focus)
		self.window.connect("key-press-event", self.key_down)
		self.gtk_screen = self.window.get_screen()
		self.Launcher = Launcher.Launcher()
		self.Launcher.connect('special-command',self.special_command)
		colormap = self.gtk_screen.get_rgba_colormap()
		if colormap is None:
			colormap = self.gtk_screen.get_rgb_colormap()
		gtk.widget_set_default_colormap(colormap)  
		if not self.window.is_composited():

			self.supports_alpha = False
		else:
			self.supports_alpha = True
		#print self.sys_get_window_manager()
		#try:
		#	if self.sys_get_window_manager() == 'compiz':
		#		pass#self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_MENU)
		#except:pass
		self.w,self.h = self.window.get_size()
		self.leave_focus = True
		self.callback_search = None
		self.MateMenu = None
		self.visible = False
		if Globals.Settings['SuperL'] == 1:
			self.bind_with_keybinder()

	def special_command(self,event):
		if not self.MateMenu:
			import Mate_Me
			self.MateMenu = Mate_Me.MateMenu()
			self.MateMenu.connect_after('unmap',self.MateMenu_unmap)
		self.leave_focus = False
		self.MateMenu.showmenu()
		self.callback = gobject.timeout_add(1500,self.timeout_callback)

	def MateMenu_unmap(self,event):
		if not self.window.is_active():
			self.emit('state-changed',0,0)
			self.hide_window()
	
	def auxdestroyed(self):
		#dummy sub for module compatibility
		pass
	
	def destroy(self):
		# External Obliterator
		self.PGL.destroy()
		
		#if Globals.MenuHasIcon==1:
			#self.usericon.destroy(None)
		#self.window.destroy()
		#gtk.main_quit()
		
	def internal_destroy(self,widget,event):
		# Internal Obliterator (event driven)
		self.PGL.destroy()
		
		#if Globals.MenuHasIcon==1:
		 #   self.usericon.destroy(None)
		#self.window.destroy()
		#gtk.main_quit()


	def ToggleMenu(self):
		print self.visible
		if not self.window.window:
			self.emit('state-changed',2,2)
			self.show_window()
			self.visible = True
		else:
			if not self.visible:
				self.emit('state-changed',2,2)
				self.show_window()
				self.visible = True
			else:
				self.emit('state-changed',0,0)
				self.hide_window()
				self.visible = False

#=================================================================
#Key binding
#=================================================================
	def bindkey_callback(self,keybinding):
		print 'key'
		self.ToggleMenu()

	def bind_with_keybinder(self):
		x = commands.getoutput('xmodmap')
		if x.find('Super_L') == '-1' and Globals.Settings['Bind_Key'] == 'Super_L':
			os.system("xmodmap -e 'keycode 115 = Super_L'")
			os.system('xmodmap -e "add mod4 = Super_L"')
		try:
			import keybinder as bindkey
			bindkey.bind(Globals.Settings['Bind_Key'], self.ToggleMenu)			
			print 'python keybinder found - binding'
		except:
			self.bind_with_deskbar()

	def bind_with_deskbar(self):
		path = str(commands.getoutput('locate _keybinder.so')).split('\n')[0]
		if path != '':
			x = commands.getoutput('xmodmap')
			if x.find('Super_L') == '-1' and Globals.Settings['Bind_Key'] == 'Super_L':
				os.system("xmodmap -e 'keycode 115 = Super_L'")
				os.system('xmodmap -e "add mod4 = Super_L"')
			path = path.replace('_keybinder.so','')
			sys.path.append(path)
			try:
				from _keybinder import tomboy_keybinder_bind as bindkey
				bindkey(Globals.Settings['Bind_Key'], self.ToggleMenu)			
				print 'deskbar found - binding'
			except:
				self.bind_with_custom()
		else:
			self.bind_with_custom()

	def bind_with_custom(self):
		print 'Using own key method - binding'
		x = commands.getoutput('xmodmap')
		if x.find('Super_L') == '-1' and Globals.Settings['Bind_Key'] == 'Super_L':
			os.system("xmodmap -e 'keycode 115 = Super_L'")
			os.system('xmodmap -e "add mod4 = Super_L"')
		try:
			from Xlib.display import Display
			from Xlib import X
			from globalkeybinding import GlobalKeyBinding
			gtk.gdk.threads_init ()
			keybinding = GlobalKeyBinding (Globals.Settings['Bind_Key'])
			keybinding.connect ('activate', self.bindkey_callback)
			keybinding.grab ()
			keybinding.start ()
		except:
			if Globals.FirstUse:
				utils.show_message('Please install python xlib')
			else:
				print 'Please install python xlib'

#=================================================================
#WINDOW SETUP
#=================================================================
	def expose (self, widget, event):
		self.ctx = widget.window.cairo_create()
		# set a clip region for the expose event
		if self.supports_alpha == False:
			self.ctx.set_source_rgb(1, 1, 1)
		else:
			self.ctx.set_source_rgba(1, 1, 1,0)
		self.ctx.set_operator (cairo.OPERATOR_SOURCE)
		self.ctx.paint()
		if Globals.Settings['GtkColors'] == 1:
			cairo_drawing.draw_image_gtk(self.ctx,0,0,Globals.ImageDirectory + Globals.StartMenuTemplate,self.w,self.h,Globals.GtkColorCode,self.colorpb)
		else:	
			cairo_drawing.draw_image(self.ctx,0,0,Globals.ImageDirectory + Globals.StartMenuTemplate)



	def shape(self):
		#Standard shape setup of window
		print 'shaping window'
		w,h = self.window.get_size()
		if w==0: w = 100
		if h==0: h = 100
		self.w = w
		self.h = h
		self.pixmap = Gdk.Pixmap()
		ctx = self.pixmap.cairo_create()
		self.bgpb = gtk.gdk.pixbuf_new_from_file(Globals.ImageDirectory + Globals.StartMenuTemplate)
		if Globals.Settings['GtkColors'] == 1 and Globals.Has_Numpy:
			if not self.colorpb:
				bgcolor = Globals.GtkColorCode
				r = (bgcolor.red*255)/65535.0
				g = (bgcolor.green*255)/65535.0
				b = (bgcolor.blue*255)/65535.0
				self.colorpb= self.bgpb.copy()
				for row in self.colorpb.get_pixels_array():
					for pix in row:
						pix[0] = r
						pix[1] = g
				  		pix[2] = b
				self.bgpb.composite(self.colorpb, 0, 0, self.w, self.h, 0, 0, 1, 1, gtk.gdk.INTERP_BILINEAR, 70)
			self.bgpb = self.colorpb

		ctx.save()
		ctx.set_source_rgba(1, 1, 1,0)
		ctx.set_operator (cairo.OPERATOR_SOURCE)
		ctx.paint()
		ctx.restore()
		if Globals.MenuHasIcon==1:
			cairo_drawing.draw_image(ctx,Globals.UserIconFrameOffsetX,Globals.UserIconFrameOffsetY,Globals.UserImageFrame)
			w,h = utils.get_image_size(Globals.UserImageFrame)
			cairo_drawing.draw_scaled_image(ctx,Globals.IconInX +Globals.UserIconFrameOffsetX,Globals.UserIconFrameOffsetY+Globals.IconInY,Globals.UserImage,Globals.IconInW ,Globals.IconInH)
		cairo_drawing.draw_enhanced_image(ctx,0,0,Globals.ImageDirectory + Globals.StartMenuTemplate)

		if self.window.is_composited():
			self.window.input_shape_combine_mask(self.pixmap,0,0)
		else:
			self.window.shape_combine_mask(self.pixmap, 0, 0)


	def setup(self):
		self.menuframe = Gtk.Fixed()
		self.window.add (self.menuframe)
		self.background =  Gtk.Image()
		self.menuframe.put(self.background,0,0)
		w,h = self.window.get_size()
		if w==0: w = 100
		if h==0: h = 100
		self.w = w
		self.h = h
		self.shape()
		self.window.set_opacity(0.99)
		if Globals.MenuHasIcon==1:
			self.usericon = ImageFrame(Globals.IconW,Globals.IconH,Globals.IconInX,Globals.IconInY,Globals.IconInW,Globals.IconInH,self.menuframe,self.bgpb)
			self.usericonstate = 0
			self.LastUserPicName = ""
		
		
		#Menu Buttons
		self.MenuButtons = []
		for i in range(0,Globals.MenuButtonCount):
			if Globals.MenuButtonNames[i] == ":SEPARATOR:":
				self.MenuButtons.append(Separator(i,self.menuframe))
			else:
				self.MenuButtons.append(MenuButton(i,self.menuframe,self.bgpb))
				
				self.MenuButtons[i].Button.connect("enter-notify-event", self.Button_enter,i)
				self.MenuButtons[i].Button.connect("leave-notify-event", self.Button_leave,i)
				self.MenuButtons[i].Button.connect("button-release-event", self.Button_click,i)

		#Menu Labels
		self.MenuLabels = []
		for i in range(0,Globals.MenuLabelCount):
			self.MenuLabels.append(MenuLabel(i,self.menuframe))

			
		# Configure the Program List
		if Globals.Settings['Prog_List'] == 0:
			self.PGL = TreeProgramList()
			self.PGL.connect ('menu', self.menu_callback)
			self.PGL.connect ('clicked', self.menu_clicked)
			self.PGL.connect ('right-clicked', self.menu_right_clicked)
		elif Globals.Settings['Prog_List'] == 1 or Globals.Settings['Prog_List'] == 2:
			self.PGL = ProgramList()
			self.PGL.connect ('menu', self.menu_callback)
			self.PGL.connect ('clicked', self.menu_clicked)
			self.PGL.connect ('right-clicked', self.menu_right_clicked)
		elif Globals.Settings['Prog_List'] == 3:
			self.PGL = IconProgramList()
			self.PGL.connect ('menu', self.menu_callback)
			self.PGL.connect ('clicked', self.menu_clicked)
			self.PGL.connect ('right-clicked', self.menu_right_clicked)
		else:	
			self.PGL = CairoProgramList()

		
		self.PGL.ProgramListPopulate(self.menuframe, self.hide_method)
		# Pass widget focus to the text entry box
		if Globals.MenuHasSearch:

			if Globals.SearchWidget.upper() == "CUSTOM":
				if Globals.SearchBackground:
					from Menu_Widgets import  CustomSearchBar
					gobject.type_register(CustomSearchBar)
					self.SearchBar =  CustomSearchBar(Globals.ImageDirectory + Globals.SearchBackground,Globals.SearchInitialText,Globals.SearchTextColor,Globals.SearchX,Globals.SearchY,Globals.SearchW,Globals.SearchH,Globals.SearchIX,Globals.SearchIY,self.bgpb)
				else:
					self.SearchBar =  CustomSearchBar(None,Globals.SearchInitialText,Globals.SearchTextColor,Globals.SearchX,Globals.SearchY,Globals.SearchW,Globals.SearchH,Globals.SearchIX,Globals.SearchIY,self.bgpb)

			elif Globals.SearchWidget.upper() == "GTK":
				from Menu_Widgets import  GtkSearchBar
				gobject.type_register(GtkSearchBar)
				self.SearchBar = GtkSearchBar()
				self.SearchBar.set_text('')
				self.SearchBar.set_inner_border(None)
				

			elif Globals.SearchWidget.upper() == "CAIRO":
				from Menu_Widgets import  CairoSearchBar
				gobject.type_register(CairoSearchBar)
				self.SearchBar =  CairoSearchBar(Globals.CairoSearchBackColor,Globals.CairoSearchBorderColor,Globals.CairoSearchTextColor)
				self.SearchBar.set_text('')
				self.SearchBar.set_inner_border(None)
				


			try:
				self.SearchBar.set_size_request(Globals.SearchW, Globals.SearchH)
				self.menuframe.put(self.SearchBar, Globals.SearchX, Globals.SearchY)
				#self.SearchBar.connect("activate",self.SearchBarActivate)
	
				self.SearchBar.connect_after("key-release-event",self.SearchBarActivate)
			except:print 'wait'
			self.prevsearchitem = ""

		#Tab Buttons
		self.MenuTabs = []
		for i in range(0,Globals.MenuTabCount):
			self.MenuTabs.append(MenuTab(i,self.menuframe,self.bgpb))
			if Globals.Settings['TabHover']:
				self.MenuTabs[i].Tab.connect("enter-notify-event", self.Tab_hover,i)
			else:
				self.MenuTabs[i].Tab.connect("enter-notify-event", self.Tab_enter,i)
				self.MenuTabs[i].Tab.connect("leave-notify-event", self.Tab_leave,i)
				self.MenuTabs[i].Tab.connect("button-release-event", self.Tab_click,i)

			if i == 0:
				self.PGL.CallSpecialMenu(Globals.MenuTabCommands[i])
				self.MenuTabs[i].SetSelectedTab(True)
			else:
				self.MenuTabs[i].SetSelectedTab(False)
		#Standalone images
		self.MenuImages = []
		for i in range(0,Globals.MenuImageCount):
			self.MenuImages.append(MenuImage(i,self.menuframe,self.bgpb))

		if has_gst:
			self.StartEngine()
			

	def menu_callback(self,event):
		
		self.leave_focus = False
		if self.leave_focus == False:
			self.callback = gobject.timeout_add(500,self.timeout_callback)

	def menu_clicked(self,event):
		self.PlaySound(2)


	def menu_right_clicked(self,event):

		self.leave_focus = False
		self.callback = gobject.timeout_add(500,self.timeout_callback)


	def Adjust_Window_Dimensions(self, win_x, win_y):
		self.window.move(win_x, win_y)


	def composite_changed(self,widget):
		self.hide_method()
		self.show_window()	
		if not self.window.is_composited():
 
			self.supports_alpha = False
		else:
			self.supports_alpha = True
		self.shape()

	def show_window(self):
		# This will fail if focus stealing prevention is enabled!
		print 'show'
		self.window.set_keep_above(1)
		if not self.window.window:
			self.window.show_all()
		else: 
			try:
				self.window.present_with_time(int(time.time())/100)
			except:
				self.window.present()
				self.window.window.focus(int(time.time())/100)
		self.window.set_urgency_hint(1)
		self.window.activate_focus()
		#self.window.set_keep_above(0)
		self.ChangeUserPic_Normalise()
		self.PGL.SetFirstButton(0)
		self.PlaySound(0)
		
	def lose_focus(self,widget,event):
		print 'focus lost'
		if self.leave_focus is True:
			self.hide_method()

	def hide_window(self):
		print 'hide'

		self.window.hide()
		if Globals.MenuTabCount == 0:
			self.PGL.Restart()
		if Globals.MenuHasSearch:
			if self.searchitem != '':
				self.SearchBar.set_text('')
				self.PGL.Restart('previous')
		self.PlaySound(1)
		
	def key_down (self,widget,event):
		# Focus mapping and key press management
		# (this is not the only key event routine set for the menu, also check the PMateMenu routines)
		key = event.hardware_keycode
		if key == 9:	#Escape Key, hides window
			self.hide_method()
		elif key == 98 or key == 104 or key == 102 or key == 100 or key == 36 or key == 116 or key ==111 or key == 113 or key == 114 or key == 23:
			# Menu naviagation keys give focus to program list
			if Globals.MenuHasSearch:
				if self.SearchBar.is_focus() is True:
					if key==36 and self.PGL.XDG.searchresults!=0: # Enter on searchbar launches first item in search list
						self.PGL.CallSpecialMenu(6)
						self.hide_method()
					self.PGL.BanFocusSteal = False
					self.PGL.SetInputFocus()
			if key == 23 :
				for i in range(0,Globals.MenuTabCount):
					if self.MenuTabs[i].GetSelectedTab():
						c = i+1
						if c > Globals.MenuTabCount-1:
							c = 0
				for i in range(0,Globals.MenuTabCount):
					if i == c:
						self.MenuTabs[i].SetSelectedTab(True)
						if Globals.MenuTabSub[i] == 0:
			
							self.Launcher.Launch(Globals.MenuTabCommands[i])
			
					 	else:
							self.PGL.CallSpecialMenu(int(Globals.MenuTabCommands[i]))
			
						# Close menu if specified by theme
						if Globals.MenuTabClose[i] == 1 and self.leave_focus is True:
							self.hide_method()
						#self.PGL.Restart()
						if self.leave_focus == False:
							self.callback = gobject.timeout_add(3000,self.timeout_callback)
					else:
						self.MenuTabs[i].SetSelectedTab(False)

				self.PlaySound(3)

			if key == 36:

				self.PlaySound(2)

		else:	#Any other key passes through to search bar
			if Globals.MenuHasSearch:
				if self.SearchBar.is_focus() == False:
					self.SearchBar.grab_focus()
				self.SearchBarActivate()

#=================================================================
#Menu Buttons
#=================================================================
	def Button_enter(self,widget,event,i):
		# Change button background
		self.MenuButtons[i].Setimage(Globals.ImageDirectory + Globals.MenuButtonImage[i])
		if Globals.MenuButtonIconSel[i]:
			self.MenuButtons[i].SetIcon(Globals.ImageDirectory + Globals.MenuButtonIconSel[i])
		try:
			gobject.source_remove(self.timeout_button)
		except:pass
		self.timeout_button = gobject.timeout_add(300,self.button_has_entered,widget,event,i)

	def button_has_entered(self,widget,event,i):
		# User Icon Code 
		# fixme: no support for non fade icons

		if Globals.MenuButtonExecOnHover[i]:

			self.Button_click(widget,event,i)
		self.UpdateUserImage(i,Globals.MenuCairoIconButton[i])

	def button_has_leave(self,widget,event,i):
		# User Icon code
		if Globals.MenuHasFade == 1:
			self.LeaveCustomState()

	def Button_leave(self,widget,event,i):
		# Button background
		self.MenuButtons[i].SetBackground()
		if Globals.MenuButtonIcon[i]:
			self.MenuButtons[i].SetIcon(Globals.ImageDirectory + Globals.MenuButtonIcon[i])
		gobject.source_remove(self.timeout_button)
		self.timeout_button = gobject.timeout_add(300,self.button_has_leave,widget,event,i)
	
	def Button_click(self,widget,event,i):
		# Launch standard menu command
		if Globals.MenuButtonSub[i] == 0:
			self.Launcher.Launch(Globals.MenuButtonCommands[i])
	 	else:
			self.PGL.CallSpecialMenu(int(Globals.MenuButtonCommands[i]))
	
		# Close menu if specified by theme
		if Globals.MenuButtonClose[i] == 1 and self.leave_focus is True:
			self.hide_method()
		#self.PGL.Restart()
		if self.leave_focus == False:
			self.callback = gobject.timeout_add(3000,self.timeout_callback)

		self.PlaySound(2)
		
#=================================================================
#Menu Tabs
#=================================================================
	def Tab_enter(self,widget,event,i):
		try:
			gobject.source_remove(self.timeout_tab)
		except:pass
		self.timeout_tab = gobject.timeout_add(300,self.tab_has_entered,widget,event,i)

	def tab_has_entered(self,widget,event,i):
		self.UpdateUserImage(i,Globals.MenuCairoIconTab[i])

	def Tab_leave(self,widget,event,i):
		self.timeout_tab = gobject.timeout_add(300,self.tab_has_leave,widget,event,i)

	def tab_has_leave(self,widget,event,i):
		# User Icon code
		if Globals.MenuHasFade == 1:
			self.LeaveCustomState()
		

	def Tab_hover(self,widget,event,i):
		for ii in range(0,Globals.MenuTabCount):
			if i != ii:
				self.MenuTabs[ii].SetSelectedTab(False)
		self.MenuTabs[i].SetSelectedTab(True)
		# Launch standard menu command
		if Globals.MenuTabSub[i] == 0:
			self.Launcher.Launch(Globals.MenuTabCommands[i])
	 	else:
			self.PGL.CallSpecialMenu(int(Globals.MenuTabCommands[i]))
		# Close menu if specified by theme
		if Globals.MenuTabClose[i] == 1 and self.leave_focus is True:
			self.hide_method()
		#self.PGL.Restart()
		if self.leave_focus == False:
			self.callback = gobject.timeout_add(3000,self.timeout_callback)

	def Tab_click(self,widget,event,i):
		for ii in range(0,Globals.MenuTabCount):
			if i != ii:
				self.MenuTabs[ii].SetSelectedTab(False)
			
		self.MenuTabs[i].SetSelectedTab(True)
		# Launch standard menu command
		if Globals.MenuTabSub[i] == 0:
			self.Launcher.Launch(Globals.MenuTabCommands[i])
	 	else:
			self.PGL.CallSpecialMenu(int(Globals.MenuTabCommands[i]))
		# Close menu if specified by theme
		if Globals.MenuTabClose[i] == 1 and self.leave_focus is True:
			self.hide_method()
		#self.PGL.Restart()
		if self.leave_focus == False:
			self.callback = gobject.timeout_add(3000,self.timeout_callback)
		self.PlaySound(3)

	def timeout_callback(self):
		self.leave_focus = True
		return False

#=================================================================
#USERICON METHODS
#=================================================================
	def UpdateUserImage(self,i,image=None):
		if image:
			if Globals.MenuHasIcon==1 and Globals.MenuHasFade == 1:

				if Globals.Settings['System_Icons']:
					ico = IconFactory.GetSystemIcon(image)
					if not ico: 
						ico = Globals.IconDirectory + image
				
				else: 
					ico = Globals.IconDirectory + image

				self.UserPicName =  ico
				if self.LastUserPicName!=self.UserPicName and self.supports_alpha:
					self.LastUserPicName=self.UserPicName
					#self.usericon.iconopacity = [0,0,1,0]
					if self.usericonstate == 0:
						self.usericon.updateimage(2,self.UserPicName)
						self.usericon.transition([-1,-1,1,-1],Globals.TransitionS,Globals.TransitionQ,None)
					elif self.usericonstate == 1:
						self.usericon.updateimage(3,self.UserPicName)
						self.usericon.transition([-1,-1,-1,1],Globals.TransitionS,Globals.TransitionQ,None)
					elif self.usericonstate == 2:
						self.usericon.updateimage(2,self.UserPicName)
						self.usericon.transition([-1,-1,1,-1],Globals.TransitionS,Globals.TransitionQ,None)
					if self.usericonstate == 1:
						self.usericonstate = 2
					else:
						self.usericonstate = 1


	def LeaveCustomState(self):	#FIXME This is for fade back to normal, CUP_Norm is for quick switching
		if self.LastUserPicName != "":self.ChangeUserPic_Normalise()

	def ChangeUserPic_Normalise(self):
		# Restore userpic to mode 2  (speed lag if overwriting already current values)
		# Place the usericon		
		if Globals.MenuHasIcon==1:
			self.usericon.move(Globals.UserIconFrameOffsetX,Globals.UserIconFrameOffsetY)
			self.usericon.updateimage(0,Globals.UserImageFrame)
			self.usericon.updateimage(1,Globals.UserImage)
			self.usericon.transition([1,1,-1,-1],Globals.TransitionS,Globals.TransitionQ,None)
			self.usericonstate == 0
			self.LastUserPicName = ""
			
#=================================================================
#PLAY SOUND
#=================================================================			
	def StartEngine(self):
		self.player = gst.element_factory_make("playbin", "player")
		fakesink = gst.element_factory_make('fakesink', "my-fakesink")
		self.player.set_property("video-sink", fakesink)
		self.player_bus = self.player.get_bus()
		self.player_bus.add_signal_watch()
		self.player_bus.connect('message', self.on_message)

	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
			#self.button.set_label("Start")
		elif t == gst.MESSAGE_ERROR:
			self.player.set_state(gst.STATE_NULL)
			#self.button.set_label("Start")

	def PlaySound(self,sound):

		if Globals.Settings['Sound_Theme'] != 'None':
			if sound == 0:
				uri = 'file://%s/share/tilo/Themes/Sound/%s/show-menu.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])
			elif sound == 1:
				uri = 'file://%s/share/tilo/Themes/Sound/%s/hide-menu.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])
			elif sound == 2:
				uri = 'file://%s/share/tilo/Themes/Sound/%s/button-pressed.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])
			elif sound == 3:
				uri = 'file://%s/share/tilo/Themes/Sound/%s/tab-pressed.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])

			if has_gst:
				self.player.set_state(gst.STATE_NULL)
				self.player.set_property('uri',uri)
				self.player.set_state(gst.STATE_PLAYING)
			else:
				os.system('mplayer %s &' % uri)

#=================================================================
#SEARCH BAR
#=================================================================
	def SearchBarActivate(self,widget=None,event=None):
		self.searchitem = self.SearchBar.get_text()
		if self.prevsearchitem != self.searchitem:
			self.PGL.BanFocusSteal = True
			self.prevsearchitem = self.searchitem
			if self.callback_search:
					gobject.source_remove(self.callback_search)
			self.callback_search = gobject.timeout_add(500,self.timeout_callback_search)

	def timeout_callback_search(self):
		self.PGL.CallSpecialMenu(5,self.searchitem)
		print 'search'
		return False

# Code to launch menu standalone of base classes

def destroy():
	hwg.destroy()
	sys.exit()
	
if __name__ == "__main__":
	hwg = Main_Menu(destroy)
	hwg.setup()
	hwg.show_window()
	gtk.main()
	




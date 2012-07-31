#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2009,2010 <helderfraga@gmail.com>

# Matenu settings manager
# Part of the GnoMenu


import pygtk
pygtk.require('2.0')
import gtk
import os
import commands
import sys
import pango
import Globals
if len(sys.argv) == 2 and sys.argv[1] == "--welcome":
	Globals.FirstUse = True
import xml.dom.minidom
import utils
import backend
import IconFactory
try:
	import tarfile as tarfile
	hastar = True
except:
	hastar = False
import urllib

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


class TiloSettings:


	def delete(self, widget, event=None):
		gtk.main_quit()
		return False

	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title(_('Tilo Settings'))
		self.window.set_icon(gtk.gdk.pixbuf_new_from_file(Globals.Applogo))
		self.window.connect("delete_event", self.delete)
		self.window.set_border_width(4)
		self.load_settings
		self.folder = os.environ['HOME']
		self.notebook = gtk.Notebook()
		self.vbox = gtk.VBox()
		self.vbox.pack_start(self.notebook, True, True)
		self.window.add(self.vbox)
		self.window.set_position(gtk.WIN_POS_CENTER)
		self.notebook.show()
		# TAB 1
		self.add_theme_tab()
		# TAB 2
		self.add_preferences_tab()
		#TAB 3
		self.add_commands_tab()
		# TAB4
		self.add_about_tab()
		self.hbox1 = gtk.HBox()
		self.vbox.pack_end(self.hbox1, False, False)
		self.button1 = gtk.Button(_('Ok'))
		self.button1.connect("clicked", self.buttonpress,'ok')
		self.button2 = gtk.Button(_('Apply'))
		self.button2.connect('clicked', self.buttonpress,'apply')
		self.button3 = gtk.Button(_('Cancel'))
		self.button3.connect('clicked', self.buttonpress,'cancel')
		self.hbox1.pack_start(self.button3, True, True)
		#self.hbox1.pack_start(self.button2, True, True)
		self.hbox1.pack_end(self.button1, True, True)
		self.label_tab1 = gtk.Label(_('Themes'))
		self.label_tab2 = gtk.Label(_('Preferences'))
		self.label_tab3 = gtk.Label(_('About'))
		self.label_tab4 = gtk.Label(_('Commands'))
		self.notebook.append_page(self.vbox_theme,self.label_tab1)
		self.notebook.append_page(self.vbox_prefs,self.label_tab2)
		self.notebook.append_page(self.vbox_comm,self.label_tab4)
		self.notebook.append_page(self.vbox_about,self.label_tab3)
		self.window.show_all()
		if self.window.size_request()[1] +50 > gtk.gdk.screen_height():
			self.notebook.set_tab_pos(0)
		if len(sys.argv) == 2 and sys.argv[1] == "--about":
			self.notebook.set_current_page(3)


	def add_theme_tab(self):

		self.vbox_theme = gtk.VBox()
		self.vbox_theme2 = gtk.VBox()
		self.hbox_theme = gtk.HBox()

		# MENU 
		self.frame_menu = gtk.Frame('<b>%s</b>' % _('Menu Selection'))
		self.frame_menu.get_label_widget().set_use_markup(1)
		self.vbox_theme.pack_start(self.frame_menu,True,True)
		self.vbox_theme.pack_start(self.vbox_theme2,False,False)
		self.vbox_theme2.pack_start(self.hbox_theme, False,False)
		self.hbox_menu = gtk.HBox()
		self.vbox_menu = gtk.VBox()
		self.vbox_menu2 = gtk.VBox()
		self.vbox_menu3 = gtk.VBox()
		self.vbox_menu = gtk.VBox()
		self.frame_menu.add(self.vbox_menu)
		self.image_menu = gtk.Image()
		self.label_credits_menu = gtk.Label()
		self.label_credits_menu.set_size_request(250,-1)
		self.label_credits_menu.set_line_wrap(True)
		self.hbox_menu = gtk.HBox()
		self.vbox_menu.set_border_width(10)
		self.hbox_menu.pack_start(self.image_menu, True, True)
		self.hbox_menu.pack_start(self.vbox_menu3, 1,1)
		self.vbox_menu3.pack_start(self.label_credits_menu, True, True)
		self.vbox_menu.pack_start(self.vbox_menu2, True, True)
		self.vbox_menu2.pack_start(self.hbox_menu,1,1)
		self.hbox_menu2 = gtk.HBox()
		self.button_menu = gtk.Button(_('Install'))
		self.button_menu.connect('clicked', self.button_clicked, 'install_menu')
		self.button_menu2 = gtk.Button(_('Uninstall'))
		self.button_menu2.connect('clicked', self.button_clicked, 'uninstall_menu')
		self.combo_menu = gtk.combo_box_new_text()
		self.hbox_menu2.pack_start(self.button_menu,0,0)
		self.hbox_menu2.pack_start(self.button_menu2,0,0)
		self.hbox_menu2.pack_start(self.combo_menu,1,1)
		self.vbox_menu3.pack_start(self.hbox_menu2, 0,0)
		self.reload_themes('Menu')
		self.redraw_image(self.combo_menu,'Menu')
		self.combo_menu.connect("changed",self.redraw_image, 'Menu')

		# BUTTON
		self.frame_button = gtk.Frame('<b>%s</b>' % _('Button Selection'))
		self.frame_button.get_label_widget().set_use_markup(1)
		self.hbox_theme.pack_start(self.frame_button,True,True)
		self.vbox_button = gtk.VBox()
		self.image_button = gtk.Image()
		self.label_credits_button = gtk.Label()
		self.label_credits_button.set_size_request(150,-1)
		self.label_credits_button.set_line_wrap(True)
		self.hbox_button = gtk.HBox()
		self.hbox_button.pack_start(self.image_button, True, True)
		self.hbox_button.pack_start(self.label_credits_button, True, True)
		self.vbox_button.pack_start(self.hbox_button, True, True)
		self.vbox_button.set_border_width(6)
		self.hbox_button2 = gtk.HBox()
		self.button_button = gtk.Button(_('Install'))
		self.button_button.connect('clicked', self.button_clicked, 'install_but')
		self.button_button2 = gtk.Button(_('Uninstall'))
		self.button_button2.connect('clicked', self.button_clicked, 'uninstall_but')
		self.combo_button = gtk.combo_box_new_text()
		self.hbox_button2.pack_start(self.button_button, False, False)
		self.hbox_button2.pack_start(self.button_button2, False, False)
		self.hbox_button2.pack_start(self.combo_button, True, True)
		self.reload_themes('Button')
		self.redraw_image(self.combo_button,'Button')
		self.combo_button.connect("changed",self.redraw_image, 'Button')
		self.vbox_button.pack_start(self.hbox_button2, False, False)
		self.frame_button.add(self.vbox_button)
		self.image_button.set_size_request(64,64)

		#ICON
		self.frame_icon = gtk.Frame('<b>%s</b>' % _('Icon Selection'))
		self.frame_icon.get_label_widget().set_use_markup(1)
		self.hbox_theme.pack_start(self.frame_icon, True,True)
		self.vbox_icon = gtk.VBox()
		self.image_icon = gtk.Image()
		self.label_credits_icon = gtk.Label()
		self.label_credits_icon.set_size_request(150,-1)
		self.label_credits_icon.set_line_wrap(True)
		self.hbox_icon = gtk.HBox()
		self.hbox_icon.pack_start(self.image_icon, True, True)
		self.hbox_icon.pack_start(self.label_credits_icon, True, True)
		self.vbox_icon.pack_start(self.hbox_icon, True, True)
		self.vbox_icon.set_border_width(6)
		self.hbox_icon2 = gtk.HBox()
		self.button_icon = gtk.Button(_('Install'))
		self.button_icon.connect('clicked', self.button_clicked, 'install_ico')
		self.button_icon2 = gtk.Button(_('Uninstall'))
		self.button_icon2.connect('clicked', self.button_clicked, 'uninstall_ico')
		self.combo_icon = gtk.combo_box_new_text()
		self.hbox_icon2.pack_start(self.button_icon, False, False)
		self.hbox_icon2.pack_start(self.button_icon2, False, False)
		self.hbox_icon2.pack_start(self.combo_icon, True, True)
		self.reload_themes('Icon')
		self.redraw_image(self.combo_icon,'Icon')
		self.combo_icon.connect("changed",self.redraw_image, 'Icon')
		self.vbox_icon.pack_start(self.hbox_icon2, False, False)
		self.frame_icon.add(self.vbox_icon)
		self.image_icon.set_size_request(64,64)

		#SOUND
		self.combo_sound = gtk.combo_box_new_text()
		self.reload_themes('Sound')
		self.frame_sound = gtk.Frame('<b>%s</b>' % _('Sound theme'))
		self.frame_sound.get_label_widget().set_use_markup(1)
		self.hbox_sound = gtk.HBox()
		self.button_sound = gtk.Button(_('Install'))
		self.button_sound.connect('clicked', self.button_clicked, 'install_sou')
		self.button_sound2 = gtk.Button(_('Uninstall'))
		self.button_sound2.connect('clicked', self.button_clicked, 'uninstall_sou')
		self.hbox_sound.pack_start(self.button_sound, False, False)
		self.hbox_sound.pack_start(self.button_sound2, False, False)
		self.hbox_sound.pack_start(self.label_credits_sound, True, True)
		self.hbox_sound.pack_start(self.combo_sound, False,False)
		self.hbox_sound.set_border_width(6)
		self.frame_sound.add(self.hbox_sound)
		self.vbox_theme2.pack_start(self.frame_sound, True,True)
		self.combo_sound.connect("changed",self.redraw_image, 'Sound')



	def add_preferences_tab(self):

		self.vbox_prefs = gtk.VBox()
		self.vbox_prefs.set_border_width(10)
		self.check1 = gtk.CheckButton(_('Bind keyboad key') + ' ex: <Alt>F11, <Control>F1')
		self.hbox_check1 = gtk.HBox()
		self.entry_check1 = gtk.Entry()
		self.entry_check1.set_text(Globals.Settings['Bind_Key'])		
		self.hbox_check1.pack_start(self.check1,1,1)
		self.hbox_check1.pack_end(self.entry_check1,1,1)
		self.check1.set_active(int(Globals.Settings['SuperL']))
		self.check2 = gtk.CheckButton(_('Show Internet and Email Buttons'))
		self.check2.set_active(int(Globals.Settings['Shownetandemail']))
		self.check3 = gtk.CheckButton(_('Use Gtk Theme Colors in Program List'))
		self.check3.set_active(int(Globals.Settings['GtkColors']))
		self.check4 = gtk.CheckButton(_('Tab Selection on Mouse Hover'))
		self.check4.set_active(int(Globals.Settings['TabHover']))
		self.hbox12 = gtk.HBox()
		self.hbox13 = gtk.HBox()
		self.hbox14 = gtk.HBox()
		self.hbox15 = gtk.HBox()
		self.hbox16 = gtk.HBox()
		self.label11 = gtk.Label(_('Icon Size in Program List'))
		self.label11.set_justify(gtk.JUSTIFY_LEFT)
		self.label12 = gtk.Label(_('Number of Items in Recent Items List'))
		self.label12.set_justify(gtk.JUSTIFY_LEFT)
		self.spinbutton1 = gtk.SpinButton()
		self.spinbutton1.set_digits(1)
		self.spinbutton1.set_increments(1, int(256))
		self.spinbutton1.set_range(16, 256)
		self.spinbutton1.set_value(Globals.Settings['IconSize'])
		#self.spinbutton1.connect("value-changed", self.options_callback, option)
		self.spinbutton2 = gtk.SpinButton()
		self.spinbutton2.set_digits(1)
		self.spinbutton2.set_increments(1, int(100))
		self.spinbutton2.set_range(1, 50)
		self.spinbutton2.set_value(Globals.Settings['ListSize'])
		self.combo4 = gtk.combo_box_new_text()
		self.combo4.append_text(_('Listview'))
		self.combo4.append_text(_('Buttons (expanded)'))
		self.combo4.append_text(_('Buttons (fixed)'))
		self.combo4.append_text(_('Iconview (fastest)'))
		self.combo4.append_text(_('Cairo (experimental)'))
		self.combo4.set_active(Globals.Settings['Prog_List'])

		self.label14 = gtk.Label(_('Tab hover effect'))
		self.combo6 = gtk.combo_box_new_text()
		self.combo6.append_text(_('None'))
		self.combo6.append_text(_('Grow'))
		self.combo6.append_text(_('Black and White'))
		self.combo6.append_text(_('Blur'))
		self.combo6.append_text(_('Glow'))
		self.combo6.append_text(_('Saturate'))
		self.combo6.set_active(Globals.Settings['Tab_Efect'])

		self.label13 = gtk.Label(_('Program list type'))
		self.check5 = gtk.CheckButton(_('Use system icons instead of theme icons'))
		self.check5.set_active(int(Globals.Settings['System_Icons']))
		self.check51 = gtk.CheckButton(_('Use distributor logo instead of button theme'))
		self.check51.set_active(int(Globals.Settings['Distributor_Logo']))
		self.check6 = gtk.CheckButton(_('Show thumbnails in recent items when available'))
		self.check6.set_active(int(Globals.Settings['Show_Thumb']))
		self.check7 = gtk.CheckButton(_('Show tooltips in program list'))
		self.check7.set_active(int(Globals.Settings['Show_Tips']))

		self.check8 = gtk.CheckButton(_('Activate Compiz blur effect on Tilo window'))
		self.Compiz_Blur =  utils.compiz_call('blur/screen0/focus_blur_match','get')
		if self.Compiz_Blur == '' :self.check8.set_sensitive(0)
		if self.Compiz_Blur.find('class=Tilo.py') != -1:
			self.check8.set_active(True)
		else:
			self.check8.set_active(False)
		self.check9 = gtk.CheckButton(_('Disable Places and System in program list'))
		self.check9.set_active(int(Globals.Settings['Disable_PS']))

		self.hbox12.pack_start(self.spinbutton1, False, False)
		self.hbox12.pack_start(self.label11, False,False,10)
		self.hbox13.pack_start(self.spinbutton2, False, False)
		self.hbox13.pack_start(self.label12, False, False,10)
		self.hbox14.pack_start(self.combo4, False, False)
		self.hbox14.pack_start(self.label13, False, False,10)

		self.hbox16.pack_start(self.combo6, False, False)
		self.hbox16.pack_start(self.label14, False, False,10)
		#self.spinbutton1.connect("value-changed", self.options_callback, option)


		self.vbox_prefs.pack_start(self.hbox_check1, False, False,3)
		self.vbox_prefs.pack_start(self.check2, False, False,3)
		self.vbox_prefs.pack_start(self.check3, False, False,3)
		self.vbox_prefs.pack_start(self.check5, False, False,3)
		self.vbox_prefs.pack_start(self.check51, False, False,3)
		self.vbox_prefs.pack_start(self.check4, False, False,3)
		self.vbox_prefs.pack_start(self.check6, False, False,3)
		self.vbox_prefs.pack_start(self.check7, False, False,3)
		self.vbox_prefs.pack_start(self.check8, False, False,3)
		self.vbox_prefs.pack_start(self.check9, False, False,3)
		self.vbox_prefs.pack_start(self.hbox12, False, False,3)
		self.vbox_prefs.pack_start(self.hbox13, False, False,3)
		self.vbox_prefs.pack_start(self.hbox14, False, False,3)
		self.vbox_prefs.pack_start(self.hbox16, False, False,3)



	def add_commands_tab(self):


		self.vbox_comm = gtk.VBox()
		self.vbox_comm.set_border_width(5)
		self.hbox2 = gtk.HBox()
		self.hbox2.set_border_width(0)
		self.label1 = gtk.Label(_('Search'))
		self.label1.set_justify(gtk.JUSTIFY_LEFT)
		self.label1.set_size_request(50,-1)
		self.entry1 = gtk.Entry()
		self.entry1.set_text(Globals.Settings['Search'])
		self.hbox2.pack_start(self.label1, True, True)
		self.hbox2.pack_start(self.entry1, True,True)
		
		self.hbox4 = gtk.HBox()
		self.hbox4.set_border_width(0)
		self.label3 = gtk.Label(_('Network Config'))
		self.label3.set_justify(gtk.JUSTIFY_LEFT)
		self.label3.set_size_request(50,-1)
		self.entry3 = gtk.Entry()
		self.entry3.set_text(Globals.Settings['Network_Config'])
		self.hbox4.pack_start(self.label3, True, True)
		self.hbox4.pack_start(self.entry3, True,True)

		self.hbox5 = gtk.HBox()
		self.hbox5.set_border_width(0)
		self.label4 = gtk.Label(_('Control Panel'))
		self.label4.set_justify(gtk.JUSTIFY_LEFT)
		self.label4.set_size_request(50,-1)
		self.entry4 = gtk.Entry()
		self.entry4.set_text(Globals.Settings['Control_Panel'])
		self.hbox5.pack_start(self.label4, True, True)
		self.hbox5.pack_start(self.entry4, True,True)

		self.hbox6 = gtk.HBox()
		self.hbox6.set_border_width(0)
		self.label5 = gtk.Label(_('Package Manager'))
		self.label5.set_justify(gtk.JUSTIFY_LEFT)
		self.label5.set_size_request(50,-1)
		self.entry5 = gtk.Entry()
		self.entry5.set_text(Globals.Settings['Package_Manager'])
		self.hbox6.pack_start(self.label5, True, True)
		self.hbox6.pack_start(self.entry5, True,True)

		self.hbox7 = gtk.HBox()
		self.hbox7.set_border_width(0)
		self.label6 = gtk.Label(_('Help'))
		self.label6.set_justify(gtk.JUSTIFY_LEFT)
		self.label6.set_size_request(50,-1)
		self.entry6 = gtk.Entry()
		self.entry6.set_text(Globals.Settings['Help'])
		self.hbox7.pack_start(self.label6, True, True)
		self.hbox7.pack_start(self.entry6, True,True)

		self.hbox8 = gtk.HBox()
		self.hbox8.set_border_width(0)
		self.label7 = gtk.Label(_('Shutdown Dialog'))
		self.label7.set_justify(gtk.JUSTIFY_LEFT)
		self.label7.set_size_request(50,-1)
		self.entry7 = gtk.Entry()
		self.entry7.set_text(Globals.Settings['Power'])
		self.hbox8.pack_start(self.label7, True, True)
		self.hbox8.pack_start(self.entry7, True,True)

		self.hbox9 = gtk.HBox()
		self.hbox9.set_border_width(0)
		self.label8 = gtk.Label(_('Lock Screen'))
		self.label8.set_justify(gtk.JUSTIFY_LEFT)
		self.label8.set_size_request(50,-1)
		self.entry8 = gtk.Entry()
		self.entry8.set_text(Globals.Settings['Lock'])
		self.hbox9.pack_start(self.label8, True, True)
		self.hbox9.pack_start(self.entry8, True,True)

		self.hbox36 = gtk.HBox()
		self.hbox36.set_border_width(0)
		self.label26 = gtk.Label(_("Logout"))
		self.label26.set_justify(gtk.JUSTIFY_LEFT)
		self.label26.set_size_request(50,-1)
		self.entry26 = gtk.Entry()
		self.entry26.set_text(Globals.Settings['LogoutNow'])
		self.hbox36.pack_start(self.label26, True, True)
		self.hbox36.pack_start(self.entry26, True,True)

		self.hbox10= gtk.HBox()
		self.hbox10.set_border_width(0)
		self.label9 = gtk.Label(_('Logout Dialog'))
		self.label9.set_justify(gtk.JUSTIFY_LEFT)
		self.label9.set_size_request(50,-1)
		self.entry9 = gtk.Entry()
		self.entry9.set_text(Globals.Settings['Logout'])
		self.hbox10.pack_start(self.label9, True, True)
		self.hbox10.pack_start(self.entry9, True,True)

		self.hbox3 = gtk.HBox()
		self.hbox3.set_border_width(0)
		self.label2 = gtk.Label(_('Restart'))
		self.label2.set_justify(gtk.JUSTIFY_LEFT)
		self.label2.set_size_request(50,-1)
		self.entry2 = gtk.Entry()
		self.entry2.set_text(Globals.Settings['Restart'])
		self.hbox3.pack_start(self.label2, True, True)
		self.hbox3.pack_start(self.entry2, True,True)


		self.hbox30 = gtk.HBox()
		self.hbox30.set_border_width(0)
		self.label20 = gtk.Label(_('Suspend'))
		self.label20.set_justify(gtk.JUSTIFY_LEFT)
		self.label20.set_size_request(50,-1)
		self.entry20 = gtk.Entry()
		self.entry20.set_text(Globals.Settings['Suspend'])
		self.hbox30.pack_start(self.label20, True, True)
		self.hbox30.pack_start(self.entry20, True,True)

		self.hbox31 = gtk.HBox()
		self.hbox31.set_border_width(0)
		self.label21 = gtk.Label(_('Hibernate'))
		self.label21.set_justify(gtk.JUSTIFY_LEFT)
		self.label21.set_size_request(50,-1)
		self.entry21 = gtk.Entry()
		self.entry21.set_text(Globals.Settings['Hibernate'])
		self.hbox31.pack_start(self.label21, True, True)
		self.hbox31.pack_start(self.entry21, True,True)


		self.hbox32 = gtk.HBox()
		self.hbox32.set_border_width(0)
		self.label22 = gtk.Label(_('Run'))
		self.label22.set_justify(gtk.JUSTIFY_LEFT)
		self.label22.set_size_request(50,-1)
		self.entry22 = gtk.Entry()
		self.entry22.set_text(Globals.Settings['Run'])
		self.hbox32.pack_start(self.label22, True, True)
		self.hbox32.pack_start(self.entry22, True,True)

		self.hbox33 = gtk.HBox()
		self.hbox33.set_border_width(0)
		self.label23 = gtk.Label(_('Shutdown'))
		self.label23.set_justify(gtk.JUSTIFY_LEFT)
		self.label23.set_size_request(50,-1)
		self.entry23 = gtk.Entry()
		self.entry23.set_text(Globals.Settings['Shutdown'])
		self.hbox33.pack_start(self.label23, True, True)
		self.hbox33.pack_start(self.entry23, True,True)

		self.hbox34 = gtk.HBox()
		self.hbox34.set_border_width(0)
		self.label24 = gtk.Label(_('User about'))
		self.label24.set_justify(gtk.JUSTIFY_LEFT)
		self.label24.set_size_request(50,-1)
		self.entry24 = gtk.Entry()
		self.entry24.set_text(Globals.Settings['User'])
		self.hbox34.pack_start(self.label24, True, True)
		self.hbox34.pack_start(self.entry24, True,True)

		self.hbox35 = gtk.HBox()
		self.hbox35.set_border_width(0)
		self.label25 = gtk.Label(_("Open as Administrator"))
		self.label25.set_justify(gtk.JUSTIFY_LEFT)
		self.label25.set_size_request(50,-1)
		self.entry25 = gtk.Entry()
		self.entry25.set_text(Globals.Settings['AdminRun'])
		self.hbox35.pack_start(self.label25, True, True)
		self.hbox35.pack_start(self.entry25, True,True)

		self.hbox37 = gtk.HBox()
		self.hbox37.set_border_width(0)
		self.label27 = gtk.Label(_("Menu Editor"))
		self.label27.set_justify(gtk.JUSTIFY_LEFT)
		self.label27.set_size_request(50,-1)
		self.entry27 = gtk.Entry()
		self.entry27.set_text(Globals.Settings['MenuEditor'])
		self.hbox37.pack_start(self.label27, True, True)
		self.hbox37.pack_start(self.entry27, True,True)

		self.vbox_comm.pack_start(self.hbox2, False, False)
		self.vbox_comm.pack_start(self.hbox4, False, False)
		self.vbox_comm.pack_start(self.hbox5, False, False)
		self.vbox_comm.pack_start(self.hbox6, False, False)
		self.vbox_comm.pack_start(self.hbox7, False, False)
		self.vbox_comm.pack_start(self.hbox8, False, False)
		self.vbox_comm.pack_start(self.hbox9, False, False)
		self.vbox_comm.pack_start(self.hbox36, False, False)
		self.vbox_comm.pack_start(self.hbox10, False, False)
		#self.vbox_comm.pack_start(self.hbox11, False, False)
		self.vbox_comm.pack_start(self.hbox3, False, False)
		self.vbox_comm.pack_start(self.hbox30, False, False)
		self.vbox_comm.pack_start(self.hbox31, False, False)
		self.vbox_comm.pack_start(self.hbox32, False, False)
		self.vbox_comm.pack_start(self.hbox33, False, False)
		self.vbox_comm.pack_start(self.hbox34, False, False)
		self.vbox_comm.pack_start(self.hbox35, False, False)
		self.vbox_comm.pack_start(self.hbox37, False, False)


	def add_about_tab(self):

		self.vbox_about = gtk.VBox()
		self.image_logo = gtk.Image()
		self.image_logo.set_size_request(80,80)
		self.Applogo = gtk.gdk.pixbuf_new_from_file_at_size(Globals.Applogo,80,80)
		self.image_logo.set_from_pixbuf(self.Applogo)
		self.label_app = gtk.Label("Tilo-Menu %s" % Globals.version)
		self.label_credits = gtk.Label("Tilo-Menu is base on GnoMenu a Consolidated menu for the GnoMenu desktop.\nBy Helder Fraga aka Whise <helderfraga@gmail.com>\n Please Donate")
		self.font_desc = pango.FontDescription('sans bold 14')
		self.label_app.modify_font(self.font_desc)
		self.label_credits.set_justify(gtk.JUSTIFY_CENTER)
		self.button3 = gtk.Button(_('Donate'))
		self.button3.set_border_width(5)
		self.button3.connect('clicked', self.button_clicked, 'Donate')
		self.button4 = gtk.Button(_('Download More Themes'))
		self.button4.set_border_width(5)
		self.button4.connect('clicked', self.button_clicked, 'Download')
		self.button9 = gtk.Button(_('GnoMenu Themes Specifications'))
		self.button9.set_border_width(5)
		self.button9.connect('clicked', self.button_clicked, 'Specs')
		self.button5 = gtk.Button(_('Report Bug'))
		self.button5.set_border_width(5)
		self.button5.connect('clicked', self.button_clicked, 'Bug')
		self.button6 = gtk.Button(_('Help Translate'))
		self.button6.set_border_width(5)
		self.button6.connect('clicked', self.button_clicked, 'Translate')
		self.button7 = gtk.Button(_('Visit Homepage'))
		self.button7.set_border_width(5)
		self.button7.connect('clicked', self.button_clicked, 'Homepage')
		self.button8 = gtk.Button(_('Credits'))
		self.button8.set_border_width(5)
		self.button8.connect('clicked', self.button_clicked, 'Credits')
		self.vbox_about.pack_start(self.image_logo, False, False)
		self.vbox_about.pack_start(self.label_app, False, False,10)
		self.vbox_about.pack_start(self.label_credits, False, False,10)
		self.vbox_about.pack_start(self.button3, False, False)
		self.vbox_about.pack_start(self.button4, False, False)
		self.vbox_about.pack_start(self.button9, False, False)
		self.vbox_about.pack_start(self.button5, False, False)
		self.vbox_about.pack_start(self.button6, False, False)
		self.vbox_about.pack_start(self.button7, False, False)
		self.vbox_about.pack_start(self.button8, False, False)


	def buttonpress(self,widget,id):
		if id == 'ok':
			self.SaveSettings()
			if utils.show_question(_('Menu needs to restart , restart now?')) is True:
				x = commands.getoutput("""ps axo "%p,%a" | grep "Tilo.py" | grep -v grep|cut -d',' -f1""")
				os.system('kill -9 ' + x)
			gtk.main_quit()

		elif id == 'apply':
			self.SaveSettings()

		elif id == 'cancel':
			gtk.main_quit()
	
	def button_clicked (self, widget, id):



		if id == 'Donate':
			os.system('xdg-open http://Gnome-look.org/content/donate.php?content=93057 &')
		elif id == 'Download':
			os.system('xdg-open http://Gnome-look.org/index.php?xcontentmode=189 &')
		elif id == 'Specs':
			os.system('xdg-open http://launchpad.net/GnoMenu/trunk/2.3/+download/GnoMenuThemeSpec.pdf &')
		elif id == 'Bug':
			os.system('xdg-open https://bugs.launchpad.net/GnoMenu &')
		elif id == 'Translate':
			os.system('xdg-open https://translations.launchpad.net/GnoMenu/trunk &')
		elif id == 'Homepage':
			os.system('xdg-open https://launchpad.net/gnomenu &')

		elif id == 'Credits':
			try:
				import mate.ui
				self.Applogo = gtk.gdk.pixbuf_new_from_file_at_size(Globals.Applogo,80,80)
				about = mate.ui.About(Globals.name,Globals.version,"GPL","Tilo-Menu is base on GnoMenu a consolidated menu for the GNOME desktop.",["Helder Fraga aka Whise <helderfraga@gmail.com>" , "https://launchpad.net/~gnomenu-team"],["https://launchpad.net/~gnomenu-team"],"https://translations.launchpad.net/gnomenu/trunk/+pots/gnomenu", self.Applogo)
				about.show()
			except:pass
		elif id == 'install_menu':
			self.show_install_dialog()
		elif id == 'install_ico':
			self.show_install_dialog()
		elif id == 'install_but':
			self.show_install_dialog()
		elif id == 'install_sou':
			self.show_install_dialog()
		elif id == 'uninstall_menu':
			self.show_uninstall_dialog('Menu',self.combo_menu)
		elif id == 'uninstall_ico':
			self.show_uninstall_dialog('Icon',self.combo_icon)
		elif id == 'uninstall_but':
			self.show_uninstall_dialog('Button',self.combo_button)
		elif id == 'uninstall_sou':
			self.show_uninstall_dialog('Icon',self.combo_sound)




	def reload_themes(self,id):

		if id == 'Menu':


			themes = os.listdir('%s/share/tilo/Themes/Menu/' % INSTALL_PREFIX)
			themes.sort(key=str.upper)
			x = 0
			self.combo_menu.get_model().clear()
			for folder in themes: 
				self.combo_menu.append_text(folder)	
				if folder == Globals.Settings['Menu_Name']:
					self.combo_menu.set_active(x)
				x = x + 1
		elif id == 'Button':

			themes = os.listdir('%s/share/tilo/Themes/Button/' % INSTALL_PREFIX)
			themes.sort(key=str.upper)
			x = 0
			self.combo_button.get_model().clear()
			for folder in themes: 
				self.combo_button.append_text(folder)
				if folder == Globals.Settings['Button_Name']:
					self.combo_button.set_active(x)
				x = x + 1
		elif id == 'Icon':
			themes = os.listdir('%s/share/tilo/Themes/Icon/' % INSTALL_PREFIX)
			themes.sort(key=str.upper)
			x = 0
			self.combo_icon.get_model().clear()
			for folder in themes: 
				self.combo_icon.append_text(folder)
				if folder == Globals.Settings['Icon_Name']:
					self.combo_icon.set_active(x)
				x = x + 1

		elif id == 'Sound':
			themes = os.listdir('%s/share/tilo/Themes/Sound/' % INSTALL_PREFIX)
			self.combo_sound.get_model().clear()
			self.combo_sound.append_text('None')
			self.combo_sound.set_active(0)
			x = 1
			for folder in themes: 
				self.combo_sound.append_text(folder)
				if folder == Globals.Settings['Sound_Theme']:
					self.combo_sound.set_active(x)
				x = x + 1

			if self.combo_sound.get_active() != 0:
				XMLCredits = xml.dom.minidom.parse("%sSound/%s/themedata.xml" % (Globals.ThemeDirectory, Globals.Settings['Sound_Theme']))
				XBase = XMLCredits.childNodes[0]
				SBase = XBase.getElementsByTagName("ContentData")
		
				Name = SBase[0].attributes["Name"].value
				Author = SBase[0].attributes["Author"].value
				Right = SBase[0].attributes["Copyright"].value
	
				self.label_credits_sound = gtk.Label('%s by: %s %s' % (Name, Author, Right))
	
			else:self.label_credits_sound = gtk.Label('')




	def redraw_image(self,widget,id):
		if widget.get_active_text() is None: return
		if id == 'Menu':
			try:
				Pixbuf = gtk.gdk.pixbuf_new_from_file_at_size("%sMenu/%s/themepreview.png" % (Globals.ThemeDirectory, widget.get_active_text()),200,230)
				#self.image_menu.set_
			except:
				Pixbuf = gtk.gdk.pixbuf_new_from_file("%stheme.png" % Globals.GraphicsDirectory)
			XMLCredits = xml.dom.minidom.parse("%sMenu/%s/themedata.xml" % (Globals.ThemeDirectory, widget.get_active_text()))
			XBase = XMLCredits.childNodes[0]
			SBase = XBase.getElementsByTagName("ContentData")
	
			Name = SBase[0].attributes["Name"].value
			Author = SBase[0].attributes["Author"].value
			Right = SBase[0].attributes["Copyright"].value
			self.label_credits_menu.set_text('%s by: %s\n\n%s' % (Name, Author, Right))
			self.image_menu.set_from_pixbuf(Pixbuf)
			self.image_menu.set_size_request(200,230)
		elif id == 'Button':
			try:
				Pixbuf = gtk.gdk.pixbuf_new_from_file_at_size("%sButton/%s/themepreview.png" % (Globals.ThemeDirectory, widget.get_active_text()),64,64)
			except:
				Pixbuf = gtk.gdk.pixbuf_new_from_file("%stheme.png" % Globals.GraphicsDirectory)
			XMLCredits = xml.dom.minidom.parse("%sButton/%s/themedata.xml" % (Globals.ThemeDirectory, widget.get_active_text()))
			XBase = XMLCredits.childNodes[0]
			SBase = XBase.getElementsByTagName("ContentData")
	
			Name = SBase[0].attributes["Name"].value
			Author = SBase[0].attributes["Author"].value
			Right = SBase[0].attributes["Copyright"].value
			self.label_credits_button.set_text('%s by: %s\n\n%s' % (Name, Author, Right))
			self.image_button.set_from_pixbuf(Pixbuf)
			self.image_button.set_size_request(64,64)
		elif id == 'Icon':
			try:
				Pixbuf = gtk.gdk.pixbuf_new_from_file_at_size("%sIcon/%s/themepreview.png" % (Globals.ThemeDirectory, widget.get_active_text()),64,64)
			except:
				Pixbuf = gtk.gdk.pixbuf_new_from_file("%stheme.png" % Globals.GraphicsDirectory)
			XMLCredits = xml.dom.minidom.parse("%sIcon/%s/themedata.xml" % (Globals.ThemeDirectory, widget.get_active_text()))
			XBase = XMLCredits.childNodes[0]
			SBase = XBase.getElementsByTagName("ContentData")
	
			Name = SBase[0].attributes["Name"].value
			Author = SBase[0].attributes["Author"].value
			Right = SBase[0].attributes["Copyright"].value
			self.label_credits_icon.set_text('%s by: %s\n\n%s' % (Name, Author, Right))
			self.image_icon.set_from_pixbuf(Pixbuf)
			self.image_icon.set_size_request(64,64)


		elif id == 'Sound':
			if self.combo_sound.get_active_text() == 'None': 
				self.label_credits_sound.set_label('')
			else:
				XMLCredits = xml.dom.minidom.parse("%sSound/%s/themedata.xml" % (Globals.ThemeDirectory, widget.get_active_text()))
				XBase = XMLCredits.childNodes[0]
				SBase = XBase.getElementsByTagName("ContentData")
		
				Name = SBase[0].attributes["Name"].value
				Author = SBase[0].attributes["Author"].value
				Right = SBase[0].attributes["Copyright"].value
	
				self.label_credits_sound.set_label('%s by: %s %s' % (Name, Author, Right))

		#self.reload_themes(id)

	
		
		


	def show_uninstall_dialog (self,typ,data):
		if utils.show_question('%s %s %s %s' % (_('Uninstall'),typ, _('theme'), data.get_active_text())) is True:
			install_prefix = '%s ' % Globals.Settings['AdminRun']
			os.system('%s%srm -rf %s%s%s/%s%s%s' % (install_prefix,chr(34), chr(39), Globals.ThemeDirectory, typ, data.get_active_text(), chr(39), chr(34)))
			data.remove_text(data.get_active())
			data.set_active(0)			
		
	def show_install_dialog (self):
		"""Craete/Show the install-dialog."""
		# create filte
		flt = gtk.FileFilter()
		flt.add_pattern('*.tar.bz2')
		flt.add_pattern('*.tar.gz')
		flt.add_pattern('*.tar')
		# create dialog
		dlg = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, 
				gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dlg.set_current_folder(self.folder)
		dlg.set_title(_('Install a new theme'))
		dlg.set_filter(flt)
		# run
		resp		= dlg.run()
		filename	= dlg.get_filename()
		self.folder = dlg.get_current_folder()
		dlg.destroy()
		if resp == gtk.RESPONSE_OK:
			# create new installer
			
			# try installing and show result dialog
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			self.install (filename)	
			self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
			

	def install(self,filename):
		if hastar:
			try:
				base = os.path.basename(filename)
				tar = tarfile.open(urllib.url2pathname(filename))
				for tarinfo in tar:
					print tarinfo.name
			except:
				utils.show_warning('0%s' % _('Error - Theme package is corrupt!'))
				return	

		ext = str(filename)[len(str(filename)) -3:]
		# prepend "tar." if we have a bz2 or gz archive
		tar_opts = 'xfz'
		if ext == 'bz2':
			tar_opts = 'xfj'
		if not os.path.isdir('/tmp/tilo/'):
			os.system('mkdir /tmp/tilo/')
		tmpdir = '/tmp/tilo/'
		os.system('tar %s "%s" -C %s' % (tar_opts, filename, tmpdir))
		for d in os.listdir(tmpdir) : #for each item in folders
	
			if os.path.exists(tmpdir + d) and os.path.isdir(tmpdir + d): 
				
				name = d

		try:
			XMLBase = xml.dom.minidom.parse('/tmp/tilo/%s/themedata.xml' % name)
		except:
			utils.show_warning('1%s' % _('Error - theme not installed\nMaybe the Theme was packaged incorrectly\nTry to install the Theme manually'))
			os.system('rm -rf /tmp/tilo')
			return
		#XBase = XMLBase.childNodes[0]
		try:
			SBase = XMLBase.getElementsByTagName("content")
			type = SBase[0].attributes["type"].value
		except:
			
			utils.show_warning('2%s' % _('Error - theme not installed\nMaybe the Theme was packaged incorrectly\nTry to install the Theme manually'))
			os.system('rm -rf /tmp/tilo')
			return
		
		try:
			print type
		except:
			utils.show_warning('3%s' % _('Error - theme not installed\nMaybe the Theme was packaged incorrectly\nTry to install the Theme manually'))
			os.system('rm -rf /tmp/tilo')
			return
		install_dir = '%s/share/tilo/Themes/%s/' % (INSTALL_PREFIX, type)

		if self.is_installed('%s/%s' % (type, name)):
			if utils.show_question(_('Theme exists. Continue?')) == False:
				os.system('rm -rf /tmp/tilo')
				return
		
		install_prefix = Globals.Settings['AdminRun'] +' '
		os.system('%s"tar %s %s%s%s -C %s%s%s"' % (install_prefix,tar_opts, chr(39), filename, chr(39), chr(39), install_dir, chr(39)))
		if self.is_installed('%s/%s' % (type, name)):
			self.reload_themes(type)
			utils.show_message(_('Theme installed'))
		else:
			utils.show_warning('4%s' % _('Error - theme not installed\nMaybe the Theme was packaged incorrectly\nTry to install the Theme manually'))
		if type == 'Icon':
			x = 0
			for i in Globals.MenuCairoSystemIcon:
				for n in IconFactory.Icontype:
					if os.path.exists('/tmp/tilo/%s/%s.%s' % (name, i, n)):
						x = 1
						os.system(Globals.Settings['AdminRun'] +' ' + chr(34) + 'mv ' + "'"+ install_dir + name + '/' + i+  '.' + n + "'" + ' ' + "'" + install_dir + name + '/' + Globals.MenuCairoSystemIcon[i] +  '.' + n + "'" + chr(34))
			if x != 0:
				utils.show_message(_('This theme was created for a previous version of GnoMenu.\nThe theme was automaticly updated in order to work properly.'))

		elif type == 'Menu':
			x = 0
			fh = open('/tmp/tilo/%s/themedata.xml' % name)
			fhh = fh.read()
			fh.close()
			for i in Globals.MenuCairoSystemIcon:
				if fhh.find(i) != -1: x = 1
				fhh = fhh.replace('"' + i + '.','"' + Globals.MenuCairoSystemIcon[i] + '.')
				for n in IconFactory.Icontype:
					if os.path.exists('/tmp/tilo/' + name + '/' + i+  '.' + n):
						os.system(Globals.Settings['AdminRun'] +' ' + chr(34) + 'mv ' + "'"+ install_dir + name + '/' + i+  '.' + n + "'" + ' ' + "'" + install_dir + name + '/' + Globals.MenuCairoSystemIcon[i] +  '.' + n + "'" + chr(34))
						x = 1
			fi = open('/tmp/tilo/%s/themedata.xml' % name,'w')
			fi.write(fhh)
			fi.close()
			if x != 0:
				os.system(Globals.Settings['AdminRun'] +' ' + chr(34) + 'cp ' + "'"+ '/tmp/tilo/' + name + '/themedata.xml' + "'" + ' ' + "'" + install_dir + name + '/themedata.xml' + "'" + chr(34))
				utils.show_message(_('This theme was created for a previous version of GnoMenu.\nThe theme was automaticly updated in order to work properly.'))
			
		os.system('rm -rf /tmp/tilo')
	

	def load_settings(self):
		pass
	
	def is_installed (self,name):
		return os.path.isdir(Globals.ThemeDirectory +  name)


	def SaveSettings(self):


		backend.save_setting("Bind_Key",self.entry_check1.get_text())
		backend.save_setting("Show_Thumb",int(self.check6.get_active()))
		backend.save_setting("Show_Tips",int(self.check7.get_active()))
		backend.save_setting("Disable_PS",int(self.check9.get_active()))
		backend.save_setting("System_Icons",int(self.check5.get_active()))
		backend.save_setting("Distributor_Logo",int(self.check51.get_active()))
		backend.save_setting("Sound_Theme",self.combo_sound.get_active_text())
		backend.save_setting("Tab_Efect",self.combo6.get_active())
		backend.save_setting("Menu_Name",self.combo_menu.get_active_text())
		backend.save_setting("IconSize",int(self.spinbutton1.get_value()))
		backend.save_setting("ListSize",int(self.spinbutton2.get_value()))
		backend.save_setting("SuperL",int(self.check1.get_active()))
		backend.save_setting("Icon_Name",self.combo_icon.get_active_text())
		backend.save_setting("Prog_List",self.combo4.get_active())
		backend.save_setting("Button_Name",self.combo_button.get_active_text())
		backend.save_setting("Shownetandemail",int(self.check2.get_active()))
		backend.save_setting("GtkColors",int(self.check3.get_active()))
		backend.save_setting("TabHover",int(self.check4.get_active()))
		backend.save_setting("Search",self.entry1.get_text())
		backend.save_setting("Network_Config",self.entry3.get_text())
		backend.save_setting("Control_Panel",self.entry4.get_text())
		backend.save_setting("Package_Manager",self.entry5.get_text())
		backend.save_setting("Help", self.entry6.get_text())
		backend.save_setting("Power",self.entry7.get_text())
		backend.save_setting("Lock",self.entry8.get_text())
		backend.save_setting("Logout",self.entry9.get_text())
		backend.save_setting("Restart",self.entry2.get_text())		
		backend.save_setting("Suspend",self.entry20.get_text())
		backend.save_setting("Hibernate",self.entry21.get_text())
		backend.save_setting("Run",self.entry22.get_text())	
		backend.save_setting("Shutdown",self.entry23.get_text())
		backend.save_setting("User",self.entry24.get_text())
		backend.save_setting("AdminRun",self.entry25.get_text())
		backend.save_setting("LogoutNow",self.entry26.get_text())

		if self.check8.get_active():
			
			if self.Compiz_Blur.find('class=Tilo.py') == -1:
				utils.compiz_call('blur/screen0/focus_blur_match','set',self.Compiz_Blur + "| class=Tilo.py")		
		else: 
			if self.Compiz_Blur.find('class=Tilo.py') != -1:
				utils.compiz_call('blur/screen0/focus_blur_match','set',self.Compiz_Blur.replace("class=Tilo.py",''))


def main():
	gtk.main()
	return 0

if __name__ == "__main__":
	TiloSettings()
	main()


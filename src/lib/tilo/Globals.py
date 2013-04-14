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
# Global menu settings
# Part of the Tilo
import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk, Gdk, GdkPixbuf
import gc
import os
import xml.dom.minidom
import backend
import sys
try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'
import utils
try:
	import numpy
	Has_Numpy = True
except:
	Has_Numpy = False
	print 'python numpy not installed , some effects and gtk native colors wont be available'
import gettext
gettext.textdomain('tilo')
gettext.install('tilo', INSTALL_PREFIX +  '/share/locale')
gettext.bindtextdomain('tilo', INSTALL_PREFIX +  '/share/locale')

def _(s):
	return gettext.gettext(s)

global name,version,appdirname 
name = "Tilo"
version = "0.3.1"
appdirname="tilo"
print '%s %s' % (name, version)
############ Set up global directories #########################
################################################################
HomeDirectory = os.path.expanduser("~")
if not os.path.exists('%s/.%s' % (HomeDirectory, appdirname)) or not os.path.isdir('%s/.%s' % (HomeDirectory,appdirname)):
	os.system('mkdir ~/.%s' % appdirname)
ConfigDirectory = '%s/.%s'  % (HomeDirectory,appdirname)
AutoStartDirectory = '%s/.config/autostart/' % HomeDirectory
ProgramDirectory = "%s/lib/%s/" % (INSTALL_PREFIX, appdirname)
ThemeDirectory = "%s/share/%s/Themes/" % (INSTALL_PREFIX,appdirname)
GraphicsDirectory = "%s/lib/%s/graphics/"  % (INSTALL_PREFIX,appdirname)
########### Definitions ########################################
################################################################
ThemeCategories = ["Menu","Icon","Button"]
gconf_app_key = '/apps/%s' % appdirname
TransitionS = 	25 #step update speed in miliseconds
TransitionQ = 0.05 #step update transparency 0 to 1
FirstUse = False

DefaultSettings = { "Tab_Efect":1 , "Bind_Key":"Super_L" , "Sound_Theme":"None" , "Show_Thumb":0 ,"Disable_PS":0, "Show_Tips":0 , "Prog_List":3 , "System_Icons":0 , "Distributor_Logo":0, "Menu_Name":"Menu" , "IconSize":28 , "ListSize":10 , "SuperL":0 , "Icon_Name":"Newstyles" , "Button_Name":"GnoBlue" , "Shownetandemail":1 , "GtkColors":0 , "TabHover":0 , "Search":"mate-search-tool" , "Network_Config":"nm-connection-editor" , "Control_Panel":"mate-control-center" , "Package_Manager":"gksu synaptic" , "Help":"yelp" , "Power":"mate-session-save --shutdown-dialog" , "Lock":"mate-screensaver-command --lock" , "Suspend":'python -u ' + ProgramDirectory + "session-manager.py suspend" , "Shutdown":'python -u ' + ProgramDirectory + "session-manager.py shutdown" , "Hibernate":'python -u ' + ProgramDirectory + "session-manager.py hibernate" , "Run":'python -u ' + ProgramDirectory + "Mate_run_dialog.py" , "Logout":"mate-session-save --logout-dialog" , "LogoutNow":"mate-session-save --logout" , "Restart":'python -u ' + ProgramDirectory + "session-manager.py reboot" , "User":"mate-about-me" , "AdminRun":"gksu", "MenuEditor":"mozo"}

Settings = DefaultSettings.copy()
MaliciousStrings =['rm ','sudo ','gksudo ','gksu ','su ','mkfs','/dev',':(){:|:','wget','chmod','os.system','fork']

def SecurityCheck(command):
	for st in MaliciousStrings:
		if command.find(st) != -1:
			utils.show_warning(_('Tilo detected a malicious script in this theme.\nThe script was blocked!\nYou should uninstall the selected theme and contact the website where you got it.\n\nThe script that tried to run was:')+ ' ' + command.replace('&',''))
			return ''
	return command

def SetDefaultSettings():
	"""Sets Default Settings using the backend"""
	for x in DefaultSettings:
		backend.save_setting(x,DefaultSettings[x])
	FirstUse = True

# Load settings stored in XML
def ReloadSettings():

	def SetDefaultSettings():
		for x in DefaultSettings:
			backend.save_setting(x,DefaultSettings[x])
		FirstUse = True

	def GetSettings():
		print 'settings load'
		for x in DefaultSettings:
			Settings[x] = backend.load_setting(x)

# Loads the main configuration and settings file to their respective values
	global orientation, panel_size, flip, MenuActions, MenuCommands, ImageDirectory, Actions, IconDirectory, MenuButtonDirectory, ThemeColor, ShowTop, FirstUse, Hibernate, StartMenuTemplate, ThemeColorCode,ThemeColorHtml, NegativeThemeColorCode, MenuWidth, MenuHeight, IconW, IconH, IconInX, IconInY, IconInW, IconInH, SearchX, SearchY, SearchW, SearchH, SearchIX, SearchIY, SearchInitialText,SearchTextColor, SearchBackground, SearchWidget, SearchWidgetPath, UserIconFrameOffsetX, UserIconFrameOffsetY, UserIconFrameOffsetH, UserIconFrameOffsetW, PG_buttonframe, PG_buttonframedimensions, MenuHasSearch, MenuHasIcon, MenuHasFade , OnlyShowFavs, OnlyShowRecentApps, CairoSearchTextColor, CairoSearchBackColor, CairoSearchBorderColor, CairoSearchRoundAngle, PG_iconsize,RI_numberofitems, MenuButtonCount, MenuButtonNames, MenuButtonMarkup, MenuButtonNameOffsetX, MenuButtonNameOffsetY, MenuButtonCommands, MenuButtonX,MenuButtonY, MenuButtonImage, MenuButtonImageBack, MenuButtonIcon, MenuButtonIconSel, MenuButtonIconX,MenuButtonIconY,MenuButtonIconSize,MenuButtonExecOnHover, MenuButtonSub,MenuButtonClose, MenuCairoIconButton, MenuLabelCount, MenuLabelNames, MenuLabelMarkup, MenuLabelX, MenuLabelY, MenuLabelCommands, MenuTabCount, MenuTabNames, MenuTabMarkup, MenuTabNameOffsetX, MenuTabNameOffsetY, MenuTabCommands,MenuTabX,MenuTabY,MenuTabImage, MenuTabIcon, MenuTabImageSel, MenuTabSub,MenuTabClose, MenuCairoIconTab, MenuCairoIcontabX, MenuCairoIcontabY,MenuCairoIcontabSize, MenuTabInvertTextColorSel, MenuImageCount, MenuImageNames, MenuImageX, MenuImageY, MenuImage, ButtonHasTop, ButtonLabelCount, ButtonBackground, ButtonTop, StartButton, StartButtonTop, ButtonHasBottom, ButtonLabelName, ButtonLabelMarkup, ButtonLabelX, ButtonLabelY, MenuButtonNameAlignment, MenuTabNameAlignment,MenuLabelNameAlignment, GtkColorCode

	menubar = Gtk.MenuBar()
	try:
		GtkColorCode = Gtk.RcStyle()
	except:
		GtkColorCode = menubar.get_style().bg[Gtk.StateType.NORMAL]
	orientation = None
	panel_size = 30
	flip = None
	orientation = backend.load_setting("orientation")
	panel_size = backend.load_setting("size")
	if orientation == 'top':
		flip = False
	elif orientation == 'bottom':
		flip = None
	GetSettings()
	for x in DefaultSettings:
		if Settings[x] is None:
			#logging.debug('Error - 7')
			SetDefaultSettings()
			#logging.debug('Error - 8')
			FirstUse = True
			GetSettings()
			break
	MenuActions = []
	MenuCommands = []
	MenuActions.append('Search')
	MenuCommands.append(Settings['Search'])
	MenuActions.append('Network Config')
	MenuCommands.append(Settings['Network_Config'])
	MenuActions.append('Control Panel')
	MenuCommands.append(Settings['Control_Panel'])
	MenuActions.append('Package Manager')
	MenuCommands.append(Settings['Package_Manager'])
	MenuActions.append('Help')
	MenuCommands.append(Settings['Help'])
	MenuActions.append('Power')
	MenuCommands.append(Settings['Power'])
	MenuActions.append('Shutdown')
	MenuCommands.append(Settings['Shutdown'])
	MenuActions.append('Lock')
	MenuCommands.append(Settings['Lock'])
	MenuActions.append('Suspend')
	MenuCommands.append(Settings['Suspend'])
	MenuActions.append('Hibernate')
	MenuCommands.append(Settings['Hibernate'])
	MenuActions.append('Run')
	MenuCommands.append(Settings['Run'])
	MenuActions.append('Logout')
	MenuCommands.append(Settings['Logout'])
	MenuActions.append('LogoutNow')
	MenuCommands.append(Settings['LogoutNow'])
	MenuActions.append('Restart')
	MenuCommands.append(Settings['Restart'])
	ThemeColor = 'white'
	ImageDirectory = "%s/share/%s/Themes/Menu/%s/" % (INSTALL_PREFIX, appdirname, Settings['Menu_Name'])
	IconDirectory =  "%s/share/%s/Themes/Icon/%s/" % (INSTALL_PREFIX, appdirname, Settings['Icon_Name'])
	MenuButtonDirectory = "%s/share/%s/Themes/Button/%s/" % (INSTALL_PREFIX, appdirname, Settings['Button_Name'])
	PG_iconsize = int(float(Settings['IconSize']))
	RI_numberofitems = int(float(Settings['ListSize']))
	try:
		XMLSettings = xml.dom.minidom.parse("%sthemedata.xml" % ImageDirectory)
	except:
		print "Error loading Menu theme, reverting to default"
		SetDefaultSettings()
		XMLSettings = xml.dom.minidom.parse("%sthemedata.xml" % ImageDirectory)
	XContent = XMLSettings.childNodes[0].getElementsByTagName("theme")
	# Identify correct theme style element
	Found = 0
	for node in XContent:
		if node.attributes["color"].value == ThemeColor or node.attributes["color"].value == "All":
			XBase = node
			ThemeColorHtml = node.attributes["colorvalue"].value
			ThemeColorCode = Gdk.color_parse(ThemeColorHtml)
			color = ThemeColorCode
			color_r = 65535 - int(color.red)
			color_g = 65535 - int(color.green)
			color_b = 65535 - int(color.blue)
			NegativeThemeColorCode = Gdk.Color(color_r,color_g,color_b)
			Found = 1
			break
	if Found==0:
		print "Error: Failed to find theme color: %s" % ThemeColor
		print "The available values are:"
		for node in XContent:
			print node.attributes["color"].value
		sys.exit()
		
	# Load Background Image
	SBase = XBase.getElementsByTagName("Background")
	StartMenuTemplate = SBase[0].attributes["Image"].value
	
	try:
		im = GdkPixbuf.Pixbuf.new_from_file('%s%s' % (ImageDirectory, StartMenuTemplate))
		MenuWidth = im.get_width()
		MenuHeight = im.get_height()
	except:
	# Load WindowDimensions
		SBase = XBase.getElementsByTagName("WindowDimensions")
		MenuWidth = int(SBase[0].attributes["Width"].value)
		MenuHeight = int(SBase[0].attributes["Height"].value)

	# Load WindowDimensions
	SBase = XBase.getElementsByTagName("IconSettings")
	try:
		UserIconFrameOffsetX = int(SBase[0].attributes["X"].value)
		UserIconFrameOffsetW = int(SBase[0].attributes["Width"].value)
		UserIconFrameOffsetH = int(SBase[0].attributes["Height"].value)
		if orientation == 'botton':
			UserIconFrameOffsetY = int(SBase[0].attributes["Y"].value)
	
		elif orientation == 'top':
	
			UserIconFrameOffsetY =  MenuHeight - int(SBase[0].attributes["Y"].value) - UserIconFrameOffsetH
		else:
			UserIconFrameOffsetY = int(SBase[0].attributes["Y"].value)
	
		IconW = int(SBase[0].attributes["Width"].value)
		IconH = int(SBase[0].attributes["Height"].value)
		IconInX = int(SBase[0].attributes["InsetX"].value)
		IconInY = int(SBase[0].attributes["InsetY"].value)
		IconInW = int(SBase[0].attributes["InsetWidth"].value)
		IconInH = int(SBase[0].attributes["InsetHeight"].value)
	except:pass
	# Load SearchBarSettings
	SBase = XBase.getElementsByTagName("SearchBarSettings")
	SearchWidget = SBase[0].attributes["Widget"].value
	if SearchWidget != "None":
		# Load universal values
		SearchX = int(SBase[0].attributes["X"].value)
		SearchW = int(SBase[0].attributes["Width"].value)
		SearchH = int(SBase[0].attributes["Height"].value)
		if orientation == 'bottom':
			SearchY = int(SBase[0].attributes["Y"].value)
		elif orientation == 'top':

			SearchY = MenuHeight -  int(SBase[0].attributes["Y"].value) - SearchH
		else:
			SearchY = int(SBase[0].attributes["Y"].value)
		# Load theme-only values
		if SearchWidget == "Custom":
			SearchIX = int(SBase[0].attributes["InsetX"].value) 
			SearchIY = int(SBase[0].attributes["InsetY"].value)
			SearchInitialText = SBase[0].attributes["InitialText"].value
			try:SearchTextColor = SBase[0].attributes["TextColor"].value
			except:SearchTextColor = "#000000"
				
			SearchBackground = SBase[0].attributes["Background"].value
			SearchWidgetPath = SBase[0].attributes["WidgetName"].value
		if SearchWidget == "Cairo":
			try:CairoSearchTextColor = SBase[0].attributes["TextColor"].value
			except:CairoSearchTextColor = "#000000"
			try:CairoSearchBackColor = SBase[0].attributes["BackColor"].value
			except:CairoSearchBackColor = "#FFFFFF"
			try:CairoSearchBorderColor = SBase[0].attributes["BorderColor"].value
			except:CairoSearchBorderColor = "#000000"				
			try:CairoSearchRoundAngle = int(SBase[0].attributes["RoundAngle"].value)
			except:CairoSearchRoundAngle = 0	

	# Load ProgramListSettings
	SBase = XBase.getElementsByTagName("ProgramListSettings")
	PG_buttonframedimensions = int(SBase[0].attributes["Width"].value),int(SBase[0].attributes["Height"].value)
	if orientation == 'botton':
		PG_buttonframe = int(SBase[0].attributes["X"].value),int(SBase[0].attributes["Y"].value)
	elif orientation == 'top':
		PG_buttonframe = int(SBase[0].attributes["X"].value),MenuHeight - int(SBase[0].attributes["Y"].value) - int(PG_buttonframedimensions[1])
	else:
		PG_buttonframe = int(SBase[0].attributes["X"].value),int(SBase[0].attributes["Y"].value)
	try:
		OnlyShowFavs = int(SBase[0].attributes["OnlyShowFavs"].value)
	except:
		OnlyShowFavs = 0

	try:
		OnlyShowRecentApps = int(SBase[0].attributes["OnlyShowRecentApps"].value)
	except:
		OnlyShowRecentApps = 0

	# Load Capabilities
	SBase = XBase.getElementsByTagName("Capabilities")
	MenuHasSearch = int(SBase[0].attributes["HasSearch"].value)
	MenuHasIcon = int(SBase[0].attributes["HasIcon"].value)
	MenuHasFade = int(SBase[0].attributes["HasFadeTransition"].value)

	#Load Menu Button List
	MenuButtons = XBase.getElementsByTagName("Button")
	MenuButtonCount = len(MenuButtons)	
	MenuButtonNames = []
	MenuButtonMarkup = []
	MenuButtonNameOffsetX = []
	MenuButtonNameOffsetY = []
	MenuButtonX = []
	MenuButtonY = []
	MenuButtonImage = []
	MenuButtonImageBack = []
	MenuButtonIcon = []
	MenuButtonIconX = []
	MenuButtonIconY = []
	MenuButtonIconSize = []
	MenuButtonIconSel = []
	MenuButtonExecOnHover = []
	MenuCairoIconButton = []
	MenuButtonSub = []
	MenuButtonCommands = []
	MenuButtonClose = []
	MenuButtonNameAlignment = []

	for node in MenuButtons:
		try:
			im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["Image"].value)
		except:
			print 'Warning - Error loading theme, reverting to defaults'
			SetDefaultSettings()
		h = im.get_height()
		
		MenuButtonNames.append(node.attributes["Name"].value)
		MenuButtonMarkup.append(node.attributes["Markup"].value)
		MenuButtonNameOffsetX.append(int(node.attributes["TextX"].value))
		try:
			MenuButtonNameAlignment.append(int(node.attributes["TextAlignment"].value))
		except:
			MenuButtonNameAlignment.append(0)
		MenuButtonImage.append(node.attributes["Image"].value)    
		try:	    	
			MenuButtonImageBack.append(node.attributes["ImageBack"].value) 
		except: MenuButtonImageBack.append('')
		MenuButtonIcon.append(node.attributes["ButtonIcon"].value)    	    	
		MenuButtonIconSel.append(node.attributes["ButtonIconSel"].value)    	    	
		try:
			MenuButtonExecOnHover.append(int(node.attributes["ExecuteOnHover"].value))
		except: MenuButtonExecOnHover.append(0)	
		try:
			MenuCairoIconButton.append(node.attributes["Icon"].value)  
		except:
			MenuCairoIconButton.append("")  
		try:    	
			MenuButtonIconX.append(int(node.attributes["ButtonIconX"].value)) 
		except:
			MenuButtonIconX.append(0) 
		try:  
			MenuButtonIconY.append(int(node.attributes["ButtonIconY"].value)) 
		except:

			MenuButtonIconY.append(0) 
		try:
			MenuButtonIconSize.append(int(node.attributes["ButtonIconSize"].value)) 
		except:
			MenuButtonIconSize.append(0)    	    	
		MenuButtonX.append(int(node.attributes["ButtonX"].value))
		if orientation == 'botton':
			MenuButtonNameOffsetY.append(int(node.attributes["TextY"].value))
			MenuButtonY.append(int(node.attributes["ButtonY"].value))
		elif orientation == 'top':

			MenuButtonNameOffsetY.append(int(node.attributes["TextY"].value) )
			MenuButtonY.append(MenuHeight - int(node.attributes["ButtonY"].value) -h )
		else:
			MenuButtonNameOffsetY.append(int(node.attributes["TextY"].value))
			MenuButtonY.append(int(node.attributes["ButtonY"].value))

		MenuButtonCommands.append(node.attributes["Command"].value)
		MenuButtonSub.append(int(node.attributes["SubMenu"].value))
		MenuButtonClose.append(int(node.attributes["CloseMenu"].value))

	#Load Menu Label List

	MenuLabels = XBase.getElementsByTagName("Label")
	MenuLabelCount = len(MenuLabels)
	MenuLabelNames = []
	MenuLabelMarkup = []
	MenuLabelCommands = []
	MenuLabelX = []
	MenuLabelY = []
	MenuLabelNameAlignment = []
	for node in MenuLabels:
		MenuLabelNames.append(node.attributes["Name"].value)
		MenuLabelMarkup.append(node.attributes["Markup"].value)	
		MenuLabelX.append(int(node.attributes["LabelX"].value))
		try:
			MenuLabelNameAlignment.append(int(node.attributes["TextAlignment"].value))
		except:
			MenuLabelNameAlignment.append(0)
		if orientation == 'botton':
			MenuLabelY.append(int(node.attributes["LabelY"].value))
		elif orientation == 'top':
			MenuLabelY.append(MenuHeight - int(node.attributes["LabelY"].value))
		else:
			MenuLabelY.append(int(node.attributes["LabelY"].value))
		if SecurityCheck(node.attributes["Command"].value) != '':
			MenuLabelCommands.append(node.attributes["Command"].value)
		else:
			MenuLabelCommands.append('')
	#Load Menu Tab List
	MenuTabs = XBase.getElementsByTagName("Tab")
	MenuTabCount = len(MenuTabs)
	MenuTabNames = []
	MenuTabMarkup = []
	MenuTabNameOffsetX = []
	MenuTabNameOffsetY = []
	MenuTabX = []
	MenuTabY = []
	MenuTabImage = []
	MenuTabIcon = []
	MenuTabImageSel = []
	MenuCairoIconTab = []
	MenuCairoIcontabX = []
	MenuCairoIcontabY = []
	MenuCairoIcontabSize = []
	MenuTabInvertTextColorSel = []
	MenuTabSub = []
	MenuTabCommands = []
	MenuTabClose = []
	MenuTabNameAlignment = []
	for node in MenuTabs:

		try:
			im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["Image"].value)
			h = im.get_height()
		except:
			im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["ImageSel"].value)
			h = im.get_height()		
		MenuTabNames.append(node.attributes["Name"].value)
		MenuTabMarkup.append(node.attributes["Markup"].value)
		MenuTabNameOffsetX.append(int(node.attributes["TextX"].value))
		try:
			MenuTabNameAlignment.append(int(node.attributes["TextAlignment"].value))
		except:
			MenuTabNameAlignment.append(0)
		MenuTabImage.append(node.attributes["Image"].value)    	    	
		MenuTabImageSel.append(node.attributes["ImageSel"].value)    	    	
		MenuTabIcon.append(node.attributes["TabIcon"].value)    	    	
		try:
			MenuCairoIconTab.append(node.attributes["Icon"].value)  
		except:
			MenuCairoIconTab.append("")    	
		try:    	
			MenuCairoIcontabX.append(int(node.attributes["TabIconX"].value)) 
		except:
			try:
				MenuCairoIcontabX.append(int(node.attributes["IconX"].value)) 
				print 'WARNING - IconX is deprecated , use TabIconX instead'
			except:
				MenuCairoIcontabX.append(0) 
		try:
			MenuCairoIcontabY.append(int(node.attributes["TabIconY"].value)) 
		except:
			try:
				MenuCairoIcontabY.append(int(node.attributes["IconY"].value)) 
				print 'WARNING - IconY is deprecated , use TabIconY instead'
			except:
				MenuCairoIcontabY.append(0) 

		try:
			MenuCairoIcontabSize.append(int(node.attributes["TabIconSize"].value)) 
		except:
			try:
				MenuCairoIcontabSize.append(int(node.attributes["IconSize"].value)) 
				print 'WARNING - IconSize is deprecated , use TabIconSize instead'
			except:
				MenuCairoIcontabSize.append(0)

		try:
			MenuTabInvertTextColorSel.append(int(node.attributes["InvertTextColorOnSel"].value)) 
		except:
			MenuTabInvertTextColorSel.append(1)
		MenuTabX.append(int(node.attributes["TabX"].value))
		if orientation == 'botton':
			MenuTabNameOffsetY.append(int(node.attributes["TextY"].value))
			MenuTabY.append(int(node.attributes["TabY"].value))
		elif orientation == 'top':

			MenuTabNameOffsetY.append(int(node.attributes["TextY"].value) )
			MenuTabY.append(MenuHeight - int(node.attributes["TabY"].value) -h )
		else:
			MenuTabNameOffsetY.append(int(node.attributes["TextY"].value))
			MenuTabY.append(int(node.attributes["TabY"].value))

		MenuTabCommands.append(node.attributes["Command"].value)
		MenuTabSub.append(int(node.attributes["SubMenu"].value))
		MenuTabClose.append(int(node.attributes["CloseMenu"].value))

	#Load menu images

	MenuImages = XBase.getElementsByTagName("Image")
	MenuImageCount = len(MenuImages)
	MenuImageNames = []
	MenuImageX = []
	MenuImageY = []
	MenuImage = []
	for node in MenuImages:

		im = GdkPixbuf.Pixbuf.new_from_file(ImageDirectory + node.attributes["Image"].value)
		h = im.get_height()
		
		MenuImageNames.append(node.attributes["Name"].value)
		MenuImage.append(node.attributes["Image"].value)    	    	
		MenuImageX.append(int(node.attributes["ImageX"].value))
		if orientation == 'botton':
			MenuImageY.append(int(node.attributes["ImageY"].value))
		elif orientation == 'top':
			MenuImageY.append(MenuHeight - int(node.attributes["ImageY"].value) -h )
		else:
			MenuImageY.append(int(node.attributes["ImageY"].value))

	# Menu button

	try:
		XMLSettings = xml.dom.minidom.parse(MenuButtonDirectory+"themedata.xml")
	except:
		print "Error loading Menu button theme, reverting to default"
		SetDefaultSettings()
		XMLSettings = xml.dom.minidom.parse(MenuButtonDirectory+"themedata.xml")
	XBase = XMLSettings.getElementsByTagName("theme")

	ButtonHasTop = int(XBase[0].attributes["Top"].value)
	ShowTop = ButtonHasTop

	try:
		XMLSettings = xml.dom.minidom.parse(MenuButtonDirectory+"themedata.xml")
	except:
		SetDefaultSettings()
		XMLSettings = xml.dom.minidom.parse(MenuButtonDirectory+"themedata.xml")
	XBase = XMLSettings.childNodes[0].childNodes[1]
	
	
	ButtonBackground = XMLSettings.getElementsByTagName("Background")
	for node in ButtonBackground:
		StartButton = (MenuButtonDirectory+str(node.attributes["Image"].value),
		        	MenuButtonDirectory+str(node.attributes["ImageHover"].value),
	               		MenuButtonDirectory+str(node.attributes["ImagePressed"].value))

	if not ButtonBackground:
		StartButton = (MenuButtonDirectory+"start-here.png",
			MenuButtonDirectory+"start-here-glow.png",
        		MenuButtonDirectory+"start-here-depressed.png")

	ButtonTop = XMLSettings.getElementsByTagName("Top")
	for node in ButtonTop:
		StartButtonTop = (MenuButtonDirectory+str(node.attributes["Image"].value),
	       	       MenuButtonDirectory+str(node.attributes["ImageHover"].value),
        	       MenuButtonDirectory+str(node.attributes["ImagePressed"].value))

	if not ButtonTop:
		StartButtonTop = (MenuButtonDirectory+"start-here-top.png",
                     MenuButtonDirectory+"start-here-top-glow.png",
                     MenuButtonDirectory+"start-here-top-depressed.png")

	ButtonLabels = XMLSettings.getElementsByTagName("Label")
	ButtonLabelCount = len(ButtonLabels)
	ButtonLabelName = ""
	ButtonLabelMarkup = ""
	ButtonLabelX = 0
	ButtonLabelY = 0
	if ButtonLabelCount != []:
		for node in ButtonLabels:
		
			ButtonLabelName= (node.attributes["Name"].value)
			ButtonLabelMarkup = (node.attributes["MarkupNormal"].value)	
			ButtonLabelX = (int(node.attributes["LabelX"].value))
			ButtonLabelY = (int(node.attributes["LabelY"].value))

	
	#logging.debug('Globals - 9')


String_list = ['Start','Menu','Control Panel','Favorites','Applications','My Computer','Computer','Recently Used','Recent', 'Recent Documents', 'Recent Items', 'Recent Applications','Web Bookmarks','Web Sites','Show History','History','Leave','Shutdown','Lock Screen','Lock','Lock Computer','Home Folder', 'Personal Folder' , 'Home','Network','Connect','Connect To','Connect To Server','Connect to Server','Package Manager','Help','Power','Search','About Me','Log Out','Shutdown Computer','Shut Down...','Shut Down','Run','Run Application', 'Execute Application','All Applications', 'All Programs','Help And Support','Logout','System','Control Center','Install Software','Status','Programs','User','Distro','Hdd','Most Used','Used','Music','Videos', 'Pictures','Documents','Games','Suspend','Hibernate','Search for Files','Help Center']

String_list_translated = [_('Start'),_('Menu'),_('Control Panel'),_('Favorites'),_('Applications'),_('My Computer'),_('Computer'),_('Recently Used'),_('Recent'),_('Recent Documents'),_('Recent Items'),_('Recent Applications'),_('Web Bookmarks'),_('Web Sites'),_('Show History'),_('History'),_('Leave'),_('Shutdown'),_('Lock Screen'),_('Lock'),_('Lock Computer'),_('Home Folder'),_('Personal Folder') ,_('Home'),_('Network'),_('Connect'),_('Connect To'),_('Connect To Server'),_('Connect to Server'),_('Package Manager'),_('Help'),_('Power'),_('Search'),_('About Me'),_('Log Out'),_('Shutdown Computer'),_('Shut Down...'),_('Shut Down'),_('Run'),_('Run Application'),_('Execute Application'),_('All Applications'),_('All Programs'),_('Help And Support'),_('Logout'),_('System'),_('Control Center'),_('Install Software'),_('Status'),_('Programs'),_('User'),_('Distro'),_('Hdd'),_('Most Used'),_('Used'),_('Music'),_('Videos') ,_('Pictures'),_('Documents'),_('Games'),_('Suspend'),_('Hibernate'),_('Search for Files'),_('Help Center')]


try:
	ReloadSettings()
except:
	print '**WARNING** - Unable to load settings, using defaults'
	print "Traceback: \n" , sys.exc_info()
	SetDefaultSettings()
	ReloadSettings()

#logging.debug('Globals - 10')

#Screen width/height
#__screen = Gdk.Screen.get_default()
#geom = Gdk.Screen.get_monitor_geometry(__screen, 0)
screenwidth = Gdk.Screen.width()
screenheight = Gdk.Screen.height() 

# Obtain OS default icon theme
DefaultIconTheme = Gtk.Settings.get_default().get_property("gtk-icon-theme-name")
GtkIconTheme = Gtk.IconTheme.get_default()
#logging.debug('Globals - 11')

distro_logo = Gtk.IconTheme.get_default().lookup_icon('distributor-logo',48,Gtk.IconLookupFlags.FORCE_SVG).get_filename()
#Main Start Button
#States:
# 0 = Normal
# 1 = Glowing (mouse-over)
# 2 = Depressed
              
# Blue glowy orb main

MenuCairoSystemIcon = {'m_webbookmarks':'applications-internet','m_recentapps':'applications-other','m_shutdown':'system-shutdown','m_applications':'applications-accessories','m_favorites':'emblem-favorite','firefox_icon':'web-browser','m_computer':'computer','m_connect':'mate-network-properties','m_controlpanel':'mate-control-center','m_documents':'folder-documents','m_games':'applications-games','m_help':'mate-help','m_home':'folder-home', 'm_music':'folder-music' ,'m_network':'gtk-network','m_pictures':'folder-images','m_recentitems':'document-open-recent' ,'m_search':'search' ,'m_synaptic':'emblem-package' ,'m_videos':'folder-videos' ,'no-user-image':'gtk-missing-image' ,'thunderbird_icon':'evolution','m_trash':'trash','m_trash':'user-trash','m_terminal':'terminal','m_run':'gtk-execute','m_lockscreen':'lock','m_logoutuser':'system-switch-user','m_software':'system-software-install','m_networktools':'preferences-system-network','m_systemmonitor.png':'utilities-system-monitor'}

#logging.debug('Globals - 12')

#User Image
UserImageFrame = ImageDirectory+"user-image-frame.png"
DefaultUserImage = IconDirectory+"gtk-missing-image.png"
UserImage = HomeDirectory + "/.face"
if os.path.isfile(UserImage) == 0 or os.path.exists(UserImage) == 0:
    UserImage=DefaultUserImage

#Application logo
Applogo = GraphicsDirectory +"logo.svg"
BrokenImage = GraphicsDirectory + "/brokenlink.png"

#logging.debug('Globals - 13')

gc.collect()

#logging.debug('Globals - end')
        

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2010 <helderfraga@gmail.com>
#
# Plasmoid
# Part of the Tilo

from PyKDE4.kdeui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
import gtk,os
try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'
import sys
sys.path.append(INSTALL_PREFIX + '/lib/tilo')
import backend
 
class Tilo(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
	self.parent = parent
 
    def init(self):
        self.setHasConfigurationInterface(False)
	#self.setBackgroundHints(Plasma.Applet.TranslucentBackground)
        self.resize(125, 125)
        self.setAspectRatioMode(Plasma.Square)
       # self.theme = Plasma.Svg(self)
      #  self.theme.setImagePath("widgets/background")
      #  self.setBackgroundHints(Plasma.Applet.TranslucentBackground)
        self.layout = QGraphicsLinearLayout(self.applet)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
    #    self.icon = Plasma.IconWidget()
    #    self.layout.addItem(self.icon)
        self.icon = Plasma.IconWidget()
        self.layout.addItem(self.icon)
	self.connect(self.icon, SIGNAL("clicked()"), self.iconClicked)



	print self.package().path() + "contents/icons/logo.png"

	from Menu_Main import Main_Menu
	self.hwg = Main_Menu(self.HideMenu)
	import Globals as Globals
	self.Globals = Globals
	if Globals.Settings['Distributor_Logo']:
		import IconFactory as iconfactory
		self.iconfactory = iconfactory
	        self.icon.setIcon(KIcon('distributor-logo'))

	else:
		self.icon.setIcon(KIcon(self.package().path() + "contents/icons/logo.svg"))
        self.icon.update()


	self.show = False
	print self.popupPosition(QSize(Globals.MenuWidth,Globals.MenuHeight))


    def contextualActions(self):
	newActions = []

	loop1 = QAction("", self.applet)
	loop1.setSeparator(True)

	EditMenus = QAction(KIcon(""), "Edit Menus" , self.applet )
	self.connect(EditMenus, SIGNAL("triggered()"), self.edit_menus )
	EditMenus.setIconVisibleInMenu(False)

	Properties = QAction(KIcon(""), "Properties" , self.applet )
	self.connect(Properties, SIGNAL("triggered()"), self.properties)
	Properties.setIconVisibleInMenu(False)

	About = QAction(KIcon(""), "About" , self.applet )
	self.connect(About, SIGNAL("triggered()"), self.about_info )
	About.setIconVisibleInMenu(False)


	newActions.append(loop1)
	newActions.append(EditMenus)
	newActions.append(Properties)
	newActions.append(About)


        return newActions

    def edit_menus(self):
	os.system(self.Globals.Settings['MenuEditor'] + ' &')
		#ConstructMainMenu()

    def about_info(self):
	os.system("/bin/sh -c " + INSTALL_PREFIX +"'/lib/"+self.Globals.appdirname+"/Tilo-Settings.py --about' &")

    def properties(self):

	#os.spawnvp(os.P_WAIT,Globals.ProgramDirectory+"Tilo-Settings.py",[Globals.ProgramDirectory+"Tilo-Settings.py"])
	os.system("/bin/sh -c '"+self.Globals.ProgramDirectory+"Tilo-Settings.py' &")
	# Fixme, reload stuff properly


    def iconClicked(self):
	print 'clicked'
	self.ShowMenu()


    def ShowMenu(self):
	if self.show == False:

		#rootwin = self.hwg.window.get_screen().get_root_window()
		#x, y, mods = rootwin.get_pointer()
		x = self.popupPosition(QSize(self.Globals.MenuWidth,self.Globals.MenuHeight)).x()
		y = self.popupPosition(QSize(self.Globals.MenuWidth,self.Globals.MenuHeight)).y()
		screen = QDesktopWidget().screenGeometry()
		if self.hwg:
			if not self.hwg.window.window:
				print y + (self.Globals.MenuHeight/2) , screen.height()/2
				if y + (self.Globals.MenuHeight/2) < screen.height()/2:
					backend.save_setting('orientation', 'top')
				else:
					backend.save_setting('orientation', 'bottom')				
		self.hwg.Adjust_Window_Dimensions(x,y)
		self.hwg.show_window()
		self.show = True
	else:
		self.HideMenu()

    def HideMenu(self):
	self.show = False
	if self.hwg:
		if self.hwg.window.window:
			if self.hwg.window.window.is_visible()== True:
				self.hwg.hide_window()

 
    def paintInterface(self, painter, option, rect):
	pass


        #painter.save()
        #painter.setPen(Qt.white)
        #painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, "Hello Python!")
        #painter.restore()
 
def CreateApplet(parent):
    return Tilo(parent)

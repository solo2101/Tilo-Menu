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
# Reimplementation of gnome menu
# Part of the GnoMenu

import MenuParser
import gtk
import IconFactory
import os
import Globals
import backend
import utils
import gc
import gobject
import Launcher

from Popup_Menu import add_menuitem, add_image_menuitem


class MateMenu(gobject.GObject):
	__gsignals__ = {
        'unmap': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

	def __init__(self,scan=False):
		gobject.GObject.__init__(self)
		self.notifier = utils.Notifier()
		self.Launcher = Launcher.Launcher()
		self.menu = MenuParser.MenuParser()
		self.menu.ParseMenus()
		self.menu.connect('menu-changed',self.MenuChanged)
		self.menus = {}
		#self.widget = widget
		self.IconFactory = IconFactory.IconFactory()
		self.m = gtk.Menu()
		self.m.connect('unmap',self.unmap)
		self.menushow(self.menu.CacheApplications,self.m)
		self.menushow(self.menu.CacheSettings,self.m)




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
	

	def runasadmin(self,widget,event,name, execs,ico,typ):
		os.system('%s "%s" &' % (Globals.Settings['AdminRun'],execs))

	def addfav(self,widget,event,name, execs,ico,typ):
		"""Add to Favorites"""
		typ = str(typ)
		favlist = backend.load_setting("favorites")
		if '%s::%s::%s::%s' % (name, execs, ico, typ) not in favlist:
			favlist.append('%s::%s::%s::%s' % (name, execs, ico, typ))
			backend.save_setting("favorites",favlist)
		
			self.notifier.notify('%s %s' % (name, _('added to favorites list')),Globals.name,Globals.Applogo,5000)
		
	def removefav(self,widget,event,name, execs,ico,typ):
		"""Remove from Favorites"""
		typ = str(typ)
		favlist = backend.load_setting("favorites")
		if '%s::%s::%s::%s' % (name, execs, ico, typ) in favlist:
			favlist.remove('%s::%s::%s::%s' % (name, execs, ico, typ))
			backend.save_setting("favorites",favlist)
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

					


	def submenushow(self,parent,name,ico,exe):
		favlist = backend.load_setting("favorites")
		#try:
		#add_image_menuitem(menu,ico, name, None,'1')
		#except:return
		self.sm =  gtk.Menu()
		
		add_menuitem(self.sm,name)
		add_menuitem(self.sm, "-")
		add_image_menuitem(self.sm, gtk.STOCK_DIALOG_AUTHENTICATION, _("Open as Administrator"), self.runasadmin,name, exe,ico,'1')
	
		if ('%s::%s::%s::1' %(name, exe, ico)) not in favlist:
			add_menuitem(self.sm, "-")
			add_image_menuitem(self.sm, gtk.STOCK_ADD, _("Add to Favorites"), self.addfav,name,exe, ico, '1')
	
		else:
			add_menuitem(self.sm, "-")
			add_image_menuitem(self.sm, gtk.STOCK_REMOVE, _("Remove from Favorites"), self.removefav,name, exe, ico, '1')

		add_menuitem(self.sm, "-")
		add_image_menuitem(self.sm, gtk.STOCK_HOME, _("Create Desktop Shortcut"), self.addshort,name, exe, ico, '1')
	
		add_menuitem(self.sm, "-")
		if ('%s.desktop' % name) in os.listdir(Globals.AutoStartDirectory):
			add_image_menuitem(self.sm, gtk.STOCK_REMOVE, _("Remove from System Startup"), self.remove_autostarter,name,  exe, ico, '1')
		else:
			add_image_menuitem(self.sm, gtk.STOCK_ADD, _("Add to System Startup"), self.create_autostarter,name, exe, ico, '1')
		self.sm.show_all()
		
		self.sm.popup(None, None, None, 0,0)
		gc.collect()
	#	parent.hide()




	def launch(self,widget,event,parent,name,ico,exe):
		if event.button == 1:
			self.Launcher.Launch(exe,1)
			self.emit('unmap')
		elif event.button == 3:
			print 'right click'
			self.m.popdown()
			self.submenushow(parent,name,ico,exe)

		gc.collect()
		


	def menushow(self,folder,m):

		for entry in self.menu.GetMenuEntries(folder):
			self.menus[str(entry)] = gtk.Menu()
			if isinstance(entry, self.menu.MenuInstance):		#Folder
				name,icon, path ,comment = self.menu.GetDirProps(entry)	
				
				item = add_image_menuitem(m, "", name)
				item.set_submenu(self.menus[str(entry)])
				item.connect('activate',self.activatemenu,entry)
				if icon == None: icon = gtk.STOCK_MISSING_IMAGE
				item.set_image_from_pixbuf(self.IconFactory.geticonfile(icon))
				item.set_tooltip_text(comment)
				#self.menushow(entry,self.menus[str(entry)])

			elif isinstance(entry, self.menu.EntryInstance):	#Application
				name,icon, execute ,comment = self.menu.GetEntryProps(entry)
				item = add_image_menuitem(m, "", name,self.launch,m,name,icon,execute)
				item.set_tooltip_text(comment)
				if icon == None: icon = gtk.STOCK_MISSING_IMAGE
				item.set_image_from_pixbuf(self.IconFactory.geticonfile(icon))


		gc.collect()

	def activatemenu(self,widget,menu):
		if len(widget.get_submenu()) == 0:
			self.menushow(menu,widget.get_submenu())

	def MenuChanged(self,event):
		self.m = gtk.Menu()
		self.menushow(self.menu.CacheApplications,self.m)
		self.menushow(self.menu.CacheSettings,self.m)

	def showmenu(self):
			#self.m.attach_to_widget(self.widget,self.detach)
		self.m.show_all()
		self.m.popup(None, None, None, 0,0)
		gc.collect()

	def detach(self,widget,event):
		pass


	def unmap(self,widget):
		pass

if __name__ == "__main__":
	men = MateMenu()
	#men.showmenu()
	
	#gtk.main()


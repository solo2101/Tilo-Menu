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

# Original GnoMenu fallback: pyxdg parses the freedesktop menu.
# The obsolete Python 2 libgnome-menu "gmenu" binding is not available.
import xdg.Menu
has_gmenu = False

from gi.repository import GObject as gobject, Gio as gio, GLib
import xdg.BaseDirectory as bd

isgio = True
import os
import Globals

import gc

class MenuParser(gobject.GObject):
        __gsignals__ = {
        'menu-changed': (gobject.SignalFlags.RUN_LAST, None, ()),
        }

        def __init__(self):
                gobject.GObject.__init__(self)
                self.has_gmenu = has_gmenu
                if has_gmenu:
                        self.MenuInstance = gmenu.Directory
                        self.EntryInstance = gmenu.Entry
                else:
                        self.MenuInstance = xdg.Menu.Menu
                        self.EntryInstance = xdg.Menu.MenuEntry
                self.updating = False
                self.CacheApplications = None
                self.CacheSettings = None


        def ParseMenus(self):
                """parse menus using xdg"""

                if has_gmenu:
                        self.CacheGmenuApplications = gmenu.lookup_tree(os.environ.get("XDG_MENU_PREFIX", "") + "applications.menu")            
                        self.CacheApplications = self.CacheGmenuApplications.get_root_directory()
                        if self.CacheApplications is None:
                                self.CacheGmenuApplications = gmenu.lookup_tree("gnome-applications.menu")              
                                self.CacheApplications = self.CacheGmenuApplications.get_root_directory()

                        if self.CacheApplications is None:
                                print('unable to parse the menu')
                        else:
                                self.CacheGmenuApplications.add_monitor(self.monitor_callback)

                        self.CacheGmenuSettings = gmenu.lookup_tree("settings.menu")            
                        self.CacheSettings = self.CacheGmenuSettings.get_root_directory()
                        if self.CacheSettings is None:
                                self.CacheGmenuSettings = gmenu.lookup_tree("gnome-settings.menu")              
                                self.CacheSettings = self.CacheGmenuSettings.get_root_directory()
                        if self.CacheSettings is None:
                                self.CacheGmenuSettings = gmenu.lookup_tree(os.environ.get("XDG_MENU_PREFIX", "") + "settings.menu")            
                                self.CacheSettings = self.CacheGmenuSettings.get_root_directory()
                        else:
                                self.CacheGmenuSettings.add_monitor(self.monitor_callback)
                
                        self.MenuInstance = gmenu.Directory
                        self.EntryInstance = gmenu.Entry


                else:
                        #http://www.rkblog.rk.edu.pl/w/p/pyxdg-freedesktoporg-specifications-support/
                        try:
                                #standard applications.menu with XDG_MENU_PREFIX that may be null
                                self.CacheApplications = xdg.Menu.parse(os.environ.get("XDG_MENU_PREFIX", "") + "applications.menu")
                        except:
                                print('Error parsing')
                                try:
                                        # Some distros rename applications.menu without setting XDG_MENU_PREFIX.
                                        self.CacheApplications = xdg.Menu.parse("gnome-applications.menu")
                                except:
                                        try:
                                                # Fedora MATE uses mate-applications.menu even
                                                # if XDG_MENU_PREFIX was not propagated.
                                                self.CacheApplications = xdg.Menu.parse("mate-applications.menu")
                                        except:
                                                print('unable to parse the menu')
        
        
                        try:
                                self.CacheSettings = xdg.Menu.parse("settings.menu")
                        except:
                                try:
                                        self.CacheSettings = xdg.Menu.parse("gnome-settings.menu")
                                except: 
                                        try:
                                                self.CacheSettings = xdg.Menu.parse(os.environ.get("XDG_MENU_PREFIX", "") + "settings.menu")
                                        except:
                                                print('unable to parse the settings menu')

                        if self.CacheApplications is None:
                                raise RuntimeError("No XDG applications.menu found. Install mate-menus and set XDG_MENU_PREFIX=mate-")
                        self.AppsFile = self.CacheApplications.Filename
                        self._monitors = []
                        self.SetFile = self.CacheSettings.Filename if getattr(self, 'CacheSettings', None) else None

                        if isgio:
                                dirs = list(bd.xdg_data_dirs)
                                if bd.xdg_data_home not in dirs:
                                        dirs.append(bd.xdg_data_home)
                                for d in dirs:
                                        self.parentfile = d + '/applications'
                                        if os.path.isdir(self.parentfile) and os.path.exists(self.parentfile):
                                                self.current_file1 = gio.File.new_for_path(self.parentfile).monitor_directory(gio.FileMonitorFlags.NONE, None)
                                                self.current_file1.connect_after("changed", self.monitor_callback)
                                                self._monitors.append(self.current_file1)
        
                                self.current_file = gio.File.new_for_path(self.AppsFile).monitor_file(gio.FileMonitorFlags.NONE, None)
                                self.current_file.connect_after("changed", self.monitor_callback)
                                self._monitors.append(self.current_file)

                        self.MenuInstance = xdg.Menu.Menu
                        self.EntryInstance = xdg.Menu.MenuEntry
        

        def GetMenuEntries(self,menu):

                if has_gmenu:
                        return menu.contents
                else:
                        return menu.getEntries()

        def GetDirProps(self,entry):

                if has_gmenu:
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
                        return entry.getName(), entry.getIcon(), entry.getPath(True),comment

        def GetEntryProps(self,entry):

                if has_gmenu:
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
                        return entry.getName(), entry.getIcon(),entry.getExec(), comment#,entry.getFileName()


        def monitor_callback(self, monitor=None, Gfile=None, event=None, data=None):
                """Callback for when directories change"""
                
                if not self.updating:
                        self.updating = True
                        self.timeout = GLib.timeout_add(1000,self.MenuChanged)

        def MenuChanged(self):
                """Called 1 second after menu changes"""

                print('Menu Changed')
                #self.current_file.disconnect_by_func(self.monitor_callback)
                self.ParseMenus()
                self.emit('menu-changed')
                gc.collect()
                self.updating = False



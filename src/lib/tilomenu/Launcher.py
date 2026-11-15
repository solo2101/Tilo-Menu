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
# Menu window
# Part of the GnoMenu

import utils
import Globals
import os
import shlex
import subprocess
import urllib.parse as urllib
from gi.repository import GObject as gobject


class Launcher(gobject.GObject):
        __gsignals__ = {
        'special-command': (gobject.SignalFlags.RUN_LAST, None, ()),
        }

        def __init__(self):
                gobject.GObject.__init__(self)
                self.GnomeMenu = None


        def Launch(self,command,tag=0):
                if tag == 0:
                        c = self.LookUpCommand(command)
                        if c != '':
                                os.system(c)
                elif tag == 1:
                        # Original .desktop Exec syntax includes quoted
                        # arguments and placeholders such as %f, %u and %F.
                        # Splitting on spaces breaks both. Preserve shell
                        # quoting, and drop placeholders without a file/URL.
                        try:
                                args = shlex.split(command)
                                args = [value.replace('%%', '%') for value in args
                                        if value not in ('%f', '%F', '%u', '%U',
                                                         '%i', '%c', '%k')]
                                if args:
                                        subprocess.Popen(args, start_new_session=True)
                        except (OSError, ValueError) as error:
                                print('TiloMenu application launch failed:', error)

                elif tag == 3 or tag == 4:
                        try:
                                subprocess.Popen(['xdg-open', command],
                                                 start_new_session=True)
                        except OSError as error:
                                print('TiloMenu open failed:', error)
                elif tag == 5 or tag == 6 or tag == 7:
                        try:
                                subprocess.Popen(['/bin/sh', '-c', command],
                                                 start_new_session=True)
                        except OSError as error:
                                print('TiloMenu command failed:', error)


        def LookUpCommand(self,command):
                print(command)
                if command.lower() == 'home':
                        command= os.path.expanduser("~")
                        return 'xdg-open %s &' % shlex.quote(command)
                if command.lower() == 'network':
                        command = "network:///"
                        return 'xdg-open %s &' % command
                elif command.lower() == 'computer':
                        command = "computer:///"
                        return 'xdg-open %s &' % command
                elif command.lower() == 'trash':
                        command = "trash:///"
                        return 'xdg-open %s &' % command
                
                if utils.xdg_dir("XDG_%s_DIR" % str(command).upper()) != False:
                        command = utils.xdg_dir("XDG_%s_DIR" % str(command).upper())
                        command = urllib.unquote(command)
                        return 'xdg-open %s &' % command
                
                for i in range(0,len(Globals.MenuActions)):
                        if Globals.MenuActions[i]==command:
                                return '%s &' % Globals.MenuCommands[i]
                if command.find(':ALLAPPS:') != -1:

                        self.emit('special-command')
                        return ""
                        
                print("%s - Running custom command" % str(command))
                return Globals.SecurityCheck('%s &' % command)



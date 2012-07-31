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
import string
import os
import urllib
import gobject


class Launcher(gobject.GObject):
	__gsignals__ = {
        'special-command': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

	def __init__(self):
		gobject.GObject.__init__(self)
		self.MateMenu = None


	def Launch(self,command,tag=0):
		if tag == 0:
			c = self.LookUpCommand(command)
			if c != '':
				os.system(c)
		elif tag == 1:
			print "launching Application"
			self.expl = command.split()
			#if last item in list begins with the character "%" then remove it and add it after the ' mark
			self.outcommand = ""
			if "%" in self.expl[len(self.expl)-1]:
				self.outcommand = " %s" %  self.expl.pop()
			self.expls = string.join(self.expl,' ')	
			os.system('%s &' % self.expls)

		elif tag == 3 or tag == 4:
			os.system("xdg-open '%s' &" % command)
		elif tag == 5 or tag == 6 or tag == 7:
			os.system("/bin/sh -c '%s' &" % command)


	def LookUpCommand(self,command):
		print command
		if command.lower() == 'home':
			command= os.path.expanduser("~")
			return 'xdg-open %s &' % command
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
			
		print "%s - Running custom command" % str(command)
		return Globals.SecurityCheck('%s &' % command)



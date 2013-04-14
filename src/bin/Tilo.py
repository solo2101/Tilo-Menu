#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2008,2009 <helderfraga@gmail.com>
#
# Consolidated Mate Menu
# This is free software made available under the GNU public license.

# Standalone launcher

import sys
import os

try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'
if len(sys.argv) == 2:

	if (sys.argv[1] == 'run-in-tray'):
		os.system('python -u ' + INSTALL_PREFIX + '/lib/tilo/TiloTray.py')
	elif (sys.argv[1] == 'unity'):
		os.system('python -u ' + INSTALL_PREFIX + '/lib/tilo/TiloUnity.py')
	elif (sys.argv[1] == 'settings'):
		os.system('python -u ' + INSTALL_PREFIX + '/lib/tilo/Tilo-Settings.py')
	else:
		after = sys.argv[1]
		os.system('python -u ' + INSTALL_PREFIX + '/lib/tilo/Tilo.py ' + after)

if len(sys.argv) != 2 or sys.argv[1] == '--help':
	print "\nUsage: Tilo.py [Command] \n"
	print "Command:\tWhat it does:\n"

	print "run-in-window\truns independant of mate-panel"
	print "run-in-tray\truns in system tray"
	print "settings\topens settings window"
	print "debug\t\truns in debug mode in mate-panel"
	print "--help\t\tdisplay this help text"




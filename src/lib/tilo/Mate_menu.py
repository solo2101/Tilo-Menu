#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2008, 2009 <helderfraga@gmail.com>
#
# MATE MENU DIALOG
# Part of the GnoMenu
 
import sys
try:
	from Xlib import X, display, Xatom
	import Xlib
except:
	import utils
	utils.show_message("Dependency missing: python-xlib not installed.")
	sys.exit ()

def get_atom(display, atom_name):

	atom = XInternAtom(disp, atom_name, False)
	if atom == None:
		print "This action requires python xlib installed, please install it for the menu to appear"
		sys.exit ()
	return atom

# Get display
disp =  Xlib.display.Display()
# Get atoms for panel and run dialog menu
mate_panel_atom = disp.intern_atom("_MATE_PANEL_ACTION")
run_atom = disp.intern_atom("_MATE_PANEL_ACTION_MAIN_MENU") #"_MATE_PANEL_ACTION_RUN_DIALOG"

args = [0,0,0]
time = X.CurrentTime
data = (32,([run_atom,time]+args))
event = Xlib.protocol.event.ClientMessage(window = disp.screen().root,client_type = mate_panel_atom, data = data)
# Send event to display
disp.send_event(disp.screen().root,event, event_mask=X.StructureNotifyMask, propagate=0)
# Show menu
disp.sync()

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
# MATE RUN DIALOG
# Part of the Tilo
 
import sys
try:
	from Xlib import X, display, Xatom
	import Xlib
except:
	print "Critical Error: python-xlib not installed. Cannot continue."
	sys.exit ()

def get_atom(display, atom_name):

	atom = XInternAtom(disp, atom_name, False)
	if atom == None:
		print "Critical Error: Panel objects (atom) not found"
		sys.exit ()
	return atom

# Get display
disp =  Xlib.display.Display()
# Get atoms for panel and run dialog menu
mate_panel_atom = disp.intern_atom("_MATE_PANEL_ACTION")
run_atom = disp.intern_atom("_MATE_PANEL_ACTION_RUN_DIALOG")

args = [0,0,0]
time = X.CurrentTime
data = (32,([run_atom,time]+args))
event = Xlib.protocol.event.ClientMessage(window = disp.screen().root,client_type = mate_panel_atom, data = data)
# Send event to display
disp.send_event(disp.screen().root,event, event_mask=X.StructureNotifyMask, propagate=0)
# Show menu
disp.sync()

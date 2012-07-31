# Copyright (C) 2008  Luca Bruno <lethalman88@gmail.com>
# Copyright (C) 2009  whise <helderfraga@gmail.com>
#
# This a slightly modified version of the globalkeybinding.py
#   
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell   
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#   
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#   
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER    
# DEALINGS IN THE SOFTWARE.

from Xlib.display import Display
from Xlib import X
import gobject
import gtk.gdk
import threading

class GlobalKeyBinding (gobject.GObject, threading.Thread):
    __gsignals__ = {
        'activate': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

    def __init__ (self,  key):
        gobject.GObject.__init__ (self)
        threading.Thread.__init__ (self)
        self.setDaemon (True)

        self.key = key

        self.keymap = gtk.gdk.keymap_get_default ()
        self.display = Display ()
        self.screen = self.display.screen ()
        self.root = self.screen.root
	self.e = True
        self.map_modifiers ()

    def map_modifiers (self):
        gdk_modifiers = (gtk.gdk.CONTROL_MASK, gtk.gdk.SHIFT_MASK, gtk.gdk.MOD1_MASK,
                         gtk.gdk.MOD2_MASK, gtk.gdk.MOD3_MASK, gtk.gdk.MOD4_MASK, gtk.gdk.MOD5_MASK,
                         gtk.gdk.SUPER_MASK, gtk.gdk.HYPER_MASK,gtk.gdk.LOCK_MASK)
        self.known_modifiers_mask = 0
        for modifier in gdk_modifiers:
            # Do you know how to handle unknown "Mod*" keys?
            # They are usually Locks and something like that
            if "Mod" not in gtk.accelerator_name (0, modifier):
                self.known_modifiers_mask |= modifier

    def on_key_changed (self, *args):
        self.regrab ()

    def regrab (self):
        self.ungrab ()
        self.grab ()

    def grab (self):
	
        accelerator = (self.key)
        keyval, modifiers = gtk.accelerator_parse (accelerator)
        if not accelerator or (not keyval and not modifiers):
            self.keycode = None
            self.modifiers = None
	    print 'Unable to bind the selected key'
            return
        self.keycode = self.keymap.get_entries_for_keyval(keyval)[0][0]
        self.modifiers = int (modifiers)
        return self.root.grab_key (self.keycode, X.AnyModifier, True, X.GrabModeAsync, X.GrabModeSync)

    def ungrab (self):
        if self.keycode:
            self.root.ungrab_key (self.keycode, X.AnyModifier, self.root)
        
    def idle (self):
        # Clipboard requests will hang without locking the GDK thread
        gtk.gdk.threads_enter ()
	# Workarround to only send signal every 2 times needed by tilo
	if self.e == True: 
	        self.emit ("activate")
		self.e = False
	elif self.e == False:
		self.e = True
        gtk.gdk.threads_leave ()
        return False

    def run (self):
        self.running = True
        wait_for_release = False
        while self.running:
            event = self.display.next_event ()
            if event.detail == self.keycode and event.type == X.KeyPress and not wait_for_release:
                modifiers = event.state & self.known_modifiers_mask
                if modifiers == self.modifiers:
                    wait_for_release = True
                    self.display.allow_events (X.AsyncKeyboard, event.time)
                else:
                    self.display.allow_events (X.ReplayKeyboard, event.time)
            elif event.detail == self.keycode and wait_for_release:
                if event.type == X.KeyRelease:
                    wait_for_release = False
                    gobject.idle_add (self.idle)
                self.display.allow_events (X.AsyncKeyboard, event.time)
            else:
                self.display.allow_events (X.ReplayKeyboard, event.time)

    def stop (self):
        self.running = False
        self.ungrab ()
        self.display.close ()

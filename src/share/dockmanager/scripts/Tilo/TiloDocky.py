#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2010 <helderfraga@gmail.com>

# Dbus Tilo interface
import sys
import gobject
import dbus
import dbus.mainloop.glib
import os

try:
	INSTALL_PREFIX = open("/etc/tilo/prefix").read()[:-1] 
except:
	INSTALL_PREFIX = '/usr'
sys.path.append(INSTALL_PREFIX + '/lib/tilo')

def handle_reply(msg):
    print msg

def handle_error(e):
    print str(e)

def emit_signal():
   #call the emitActivate method 
   object.emitActivate(dbus_interface="com.tilo.Tilo")
                          #reply_handler = handle_reply, error_handler = handle_error)
   # exit after waiting a short time for the signal
   gobject.timeout_add(2000, loop.quit)

   if sys.argv[1:] == ['--exit-service']:
      object.Exit(dbus_interface='com.tilo.Tilo')

   return False

def hello_signal_handler(hello_string):
    pass

def catchall_signal_handler(*args, **kwargs):
    pass

def catchall_hello_signals_handler(hello_string):
    print "Tilo activate"
    
def catchall_testservice_interface_handler(hello_string, dbus_message):
    pass


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SessionBus()
    try:
        object  = bus.get_object("com.tilo.Tilo","/com/tilo/Tilo/object")

        object.connect_to_signal("Activate", hello_signal_handler, dbus_interface="com.tilo.Tilo", arg0="Hello")
    except dbus.DBusException:
        os.system('python -u ' + INSTALL_PREFIX + '/share/dockmanager/scripts/Tilo.py')
    try:
        object  = bus.get_object("com.tilo.Tilo","/com/tilo/Tilo/object")

        object.connect_to_signal("Activate", hello_signal_handler, dbus_interface="com.tilo.Tilo", arg0="Hello")
    except dbus.DBusException:
        sys.exit(1)
    #lets make a catchall
    bus.add_signal_receiver(catchall_signal_handler, interface_keyword='dbus_interface', member_keyword='member')

    bus.add_signal_receiver(catchall_hello_signals_handler, dbus_interface = "com.tilo.Tilo", signal_name = "Activate")

    bus.add_signal_receiver(catchall_testservice_interface_handler, dbus_interface = "com.tilo.Tilo", message_keyword='dbus_message')

    # Tell the remote object to emit the signal after a short delay
    gobject.timeout_add(1, emit_signal)

    loop = gobject.MainLoop()
    loop.run()

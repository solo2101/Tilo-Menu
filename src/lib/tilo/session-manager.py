#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2009,2010 <helderfraga@gmail.com>
#
# Handles session Shutdown, Logout, Suspend and Hibernate.
# Part of GnoMenu

import sys,os

if len(sys.argv) < 2 or sys.argv[1] == "--help":
	print "Tilo session manager HELP====================="
	print "Command:		 What it does:\n"
	print "shutdown		 Shutdown the PC"
	print "reboot		 Reboot the PC"
	print "hibernate	 Hibernate the PC"
	print "suspend		 Suspend the PC"
	print "================================================="

else:

	import dbus
	bus = dbus.SessionBus()
	bus2 = dbus.SystemBus()
	power = None
	power2 = None
	power4 = None
	try:
		devobj = bus.get_object('org.mate.PowerManagement', 'org/mate/PowerManagement')
		power = dbus.Interface(devobj, "org/mate/PowerManagement")
		print "using mate < 2.28"
	except:
		try:
			# patched version http://www.electric-spoon.com/doc/mate-session/dbus/mate-session.html#org.mate.SessionManager.RequestReboot
			# normal version http://people.gnome.org/~mccann/mate-session/docs/mate-session.html
			devobj = bus.get_object('org.mate.SessionManager', '/org/mate/SessionManager')
			power2 = dbus.Interface(devobj, "org.mate.SessionManager")
			print "using mate >= 2.28"
		except:
			devobj = bus.get_object('org.kde.ksmserver', '/KSMServer')
			power4 = dbus.Interface(devobj, "org.kde.KSMServerInterface")	
			print "using kde"
		try:
			#http://hal.freedesktop.org/docs/DeviceKit-power/Power.html
			devobj2 = bus2.get_object('org.freedesktop.DeviceKit.Power', '/org/freedesktop/DeviceKit/Power')
			power3 = dbus.Interface(devobj2, "org.freedesktop.DeviceKit.Power")
			print "using Devicekit.Power"
		except:
			#http://upower.freedesktop.org/docs/UPower.html
			devobj2 = bus2.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower')
			power3 = dbus.Interface(devobj2, "org.freedesktop.UPower")
			print "using UPower"



	if power:
		if sys.argv[1] == "suspend":
			power.Suspend()
		elif sys.argv[1] == "hibernate":
			power.Hibernate()
		elif sys.argv[1] == "reboot":
			power.Reboot()
		elif sys.argv[1] == "shutdown":
			power.Shutdown()

	if power2:

		if sys.argv[1] == "suspend":
			power3.Suspend()
		elif sys.argv[1] == "hibernate":
			power3.Hibernate()
		elif sys.argv[1] == "reboot":
			try:
				power2.RequestReboot() #this works only for a pathed version ...
			except:
				power2.Shutdown() #if it doesnt have the patched version show
		elif sys.argv[1] == "shutdown":
			try:
				power2.RequestShutdown() #this works only for a pathed version ...
			except:
				power2.Shutdown() #if it doesnt have the patched version show

	if power4:

		if sys.argv[1] == "suspend":
			power3.Suspend()
		elif sys.argv[1] == "hibernate":
			power3.Hibernate()
		elif sys.argv[1] == "reboot":
			power4.logout(0,1,0)
		elif sys.argv[1] == "shutdown":
			power4.logout(0,2,0)

#LOGOUT_CMD = ("xfce4-session-logout --logout", )
#SHUTDOWN_CMD = ("xfce4-session-logout", )
#LOCKSCREEN_CMD = ("xdg-screensaver lock", )

#$1 = method name
#execute_dbus_method ()
#{
#	dbus-send --print-reply --dest=org.mate.SessionManager /org/mate/SessionManager org.mate.SessionManager.$1
#	if [ $? -ne 0 ]; then
#		echo "Failed"
#	fi 
#}
#
#if [ "$1" = "suspend" ]; then
#	echo "Suspending"
#	execute_dbus_method "Suspend"
#elif [ "$1" = "hibernate" ]; then
#	echo "Hibernating"
#	execute_dbus_method "Hibernate"
#elif [ "$1" = "reboot" ]; then
#	echo "Rebooting"
#	execute_dbus_method "Reboot"
#elif [ "$1" = "shutdown" ]; then
#	echo "Shutting down"
#	execute_dbus_method "RequestShutdown"
#elif [ "$1" = "" ]; then
#	echo "command required: suspend, shutdown, hibernate or reboot"
#else
#	echo "command '$1' not recognised, only suspend, shutdown, hibernate or reboot are valid"
#	exit 1
#fi

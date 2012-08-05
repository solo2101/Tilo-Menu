# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) QB89Dragon 2007/8 <hughescih@hotmail.com>
#(c) Whise 2009 <helderfraga@gmail.com>
#
# A simple makefile to allow installing/uninstalling 
# Part of the GnoMenu

PREFIX = /usr
AWNPREFIX = $(PREFIX)
CAIRODOCKPREFIX = $(PREFIX)
DOCKYPREFIX = $(PREFIX)
INSTALL_LOG = install.log
LIBDIR = $(PREFIX)/lib

.PHONY : install
.PHONY : uninstall

all:
	@echo "Makefile: Available actions: install, uninstall,"
	@echo "Makefile: Available variables: PREFIX, DESTDIR, AWNPREFIX, CAIRODOCKPREFIX"

# install
install:

	-install -d $(DESTDIR)/etc/tilo $(DESTDIR)$(PREFIX)/bin/ $(DESTDIR)$(LIBDIR) \
	$(DESTDIR)$(PREFIX)/share $(DESTDIR)$(LIBDIR)/matecomponent/servers $(DESTDIR)$(CAIRODOCKPREFIX)/share/cairo-dock/plug-ins/Dbus/third-party/Tilo $(DESTDIR)$(PREFIX)/share/kde4/apps/plasma
	@echo $(PREFIX) > $(DESTDIR)/etc/tilo/prefix
	python -u setup.py
	
	#-install src/bin/Tilo.py $(DESTDIR)$(PREFIX)/bin/
	-cp -r src/lib/tilo $(DESTDIR)$(LIBDIR)
	-cp -r src/share/tilo $(DESTDIR)$(PREFIX)/share
	-cp -r src/share/avant-window-navigator $(DESTDIR)$(AWNPREFIX)/share
	-install src/share/dockmanager/scripts/Tilo.py $(DESTDIR)$(DOCKYPREFIX)/share/dockmanager/scripts/
	-cp -r src/share/dockmanager/scripts/Tilo $(DESTDIR)$(DOCKYPREFIX)/share/dockmanager/scripts/
	#-cp -r src/share/xfce4 $(DESTDIR)$(PREFIX)/share
	-cp -r src/share/locale $(DESTDIR)$(PREFIX)/share
	#-cp -r src/share/plasma/plasmoids $(DESTDIR)$(PREFIX)/share/kde4/apps/plasma
	-install src/share/cairo-dock/third-party/Tilo/* $(DESTDIR)$(CAIRODOCKPREFIX)/share/cairo-dock/plug-ins/Dbus/third-party/Tilo/
	#-cp -r src/share/cairo-dock ~/.config/
	-install src/bin/Tilo.py $(DESTDIR)$(PREFIX)/bin/
	-install src/lib/matecomponent/MATE_Tilo.server $(DESTDIR)$(LIBDIR)/matecomponent/servers
	#-plasmapkg -i src/share/plasma/plasmoids/Tilo.zip -p $(DESTDIR)$(PREFIX)/share/kde4/apps/plasma/plasmoids # Try running the "-plasmapkg -i src/share/plasma/plasmoids/Tilo.zip" as normal user
	@echo "Makefile: Tilo installed."


# uninstall
uninstall:

	rm -rf $(LIBDIR)/tilo
	rm -rf $(PREFIX)/share/tilo
	rm -rf $(PREFIX)/share/avant-window-navigator/applets/Tilo.desktop
	rm -rf $(PREFIX)/share/avant-window-navigator/applets/Tilo
	#rm -rf $(PREFIX)/share/xfce4/panel-plugins/Tilo.desktop
	rm -rf $(PREFIX)/bin/Tilo.py
	#rm -rf $(PREFIX)/share/kde4/apps/plasma/plasmoids/Tilo
	rm -rf $(LIBDIR)/matecomponent/servers/MATE_Tilo.server
	rm -rf /etc/tilo/prefix
	rm -rf ~/.tilo
	rm -rf ~/.config/cairo-dock/third-party/Tilo
	rm -rf $(PREFIX)/share/dockmanager/scripts/Tilo
	rm -rf $(PREFIX)/share/dockmanager/scripts/Tilo.py
	#plasmapkg -r Tilo





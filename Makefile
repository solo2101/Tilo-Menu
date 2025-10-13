# GPLv3. Minimal Makefile for Tilo-Menu (MATE only)

PREFIX  ?= /usr
LIBDIR  ?= $(PREFIX)/lib
DATADIR ?= $(PREFIX)/share
BINDIR  ?= $(PREFIX)/bin

TILO_LIBDIR := $(LIBDIR)/tilo
TILO_SHARE  := $(DATADIR)/tilo
APPLET_DIR  := $(DATADIR)/mate-panel/applets
DBUS_DIR    := $(DATADIR)/dbus-1/services

.PHONY: all install uninstall

all:
	@echo "Targets: install, uninstall"

install:
	install -d \
		$(DESTDIR)/etc/tilo \
		$(DESTDIR)$(TILO_LIBDIR) \
		$(DESTDIR)$(TILO_SHARE) \
		$(DESTDIR)$(BINDIR) \
		$(DESTDIR)$(APPLET_DIR) \
		$(DESTDIR)$(DBUS_DIR)
	# remember prefix for runtime lookups
	printf '%s\n' '$(PREFIX)' > $(DESTDIR)/etc/tilo/prefix
	# core code and data
	cp -a src/lib/tilo/* $(DESTDIR)$(TILO_LIBDIR)/
	cp -a src/share/tilo   $(DESTDIR)$(DATADIR)/
	# applet descriptors
	install -Dm644 src/lib/applet/org.mate.panel.TiloMenuApplet.mate-panel-applet \
		$(DESTDIR)$(APPLET_DIR)/org.mate.panel.TiloMenuApplet.mate-panel-applet
	install -Dm644 src/lib/applet/org.mate.panel.applet.TiloMenuAppletFactory.service \
		$(DESTDIR)$(DBUS_DIR)/org.mate.panel.applet.TiloMenuAppletFactory.service
	# optional helper script if present
	-[ -f src/lib/applet/tilo-menu-applet.py ] && \
		install -Dm755 src/lib/applet/tilo-menu-applet.py $(DESTDIR)$(TILO_LIBDIR)/tilo-menu-applet.py || true
	# CLI wrappers (generated)
	printf '%s\n' '#!/usr/bin/env bash' \
	'exec /usr/bin/python3 $(TILO_LIBDIR)/Tilo.py --show' \
	| install -Dm755 /dev/stdin $(DESTDIR)$(BINDIR)/tilo-menu
	printf '%s\n' '#!/usr/bin/env bash' \
	'exec /usr/bin/python3 $(TILO_LIBDIR)/Tilo-Settings.py' \
	| install -Dm755 /dev/stdin $(DESTDIR)$(BINDIR)/tilo-settings
	@echo "Installed."

uninstall:
	rm -rf $(DESTDIR)/etc/tilo
	rm -rf $(DESTDIR)$(TILO_LIBDIR)
	rm -rf $(DESTDIR)$(TILO_SHARE)
	rm -f  $(DESTDIR)$(BINDIR)/tilo-menu
	rm -f  $(DESTDIR)$(BINDIR)/tilo-settings
	rm -f  $(DESTDIR)$(APPLET_DIR)/org.mate.panel.TiloMenuApplet.mate-panel-applet
	rm -f  $(DESTDIR)$(DBUS_DIR)/org.mate.panel.applet.TiloMenuAppletFactory.service
	@echo "Uninstalled."

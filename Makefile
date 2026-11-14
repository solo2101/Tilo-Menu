# Source-first GnoMenu 2.9.1 -> TiloMenu port.
# Original src/bin, src/lib, src/share layout is retained.
SOURCE_ARCHIVE ?= $(HOME)/Downloads/gnomenu-2.9.1.tar.gz
PREFIX ?= /usr
LIBDIR = $(PREFIX)/lib/tilomenu
DATADIR = $(PREFIX)/share/tilomenu
MENU_DIR = src/share/tilomenu/Themes

.PHONY: prepare install uninstall check

# Extract original graphics, themes and GPL license without editing them.
# Ported Python modules are committed in src/lib/tilomenu, not overwritten.
prepare:
	@test -f "$(SOURCE_ARCHIVE)" || { echo "Missing original source: $(SOURCE_ARCHIVE)"; exit 1; }
	@set -e; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	  tar -xzf "$(SOURCE_ARCHIVE)" -C "$$tmp" \
	    gnomenu/COPYING \
	    gnomenu/src/lib/gnomenu/graphics \
	    gnomenu/src/share/gnomenu/Themes/Menu/Menu \
	    gnomenu/src/share/gnomenu/Themes/Button/GnoBlue \
	    gnomenu/src/share/gnomenu/Themes/Icon/Newstyles \
	    gnomenu/src/share/gnomenu/Themes/Sound/Default; \
	  mkdir -p "$(MENU_DIR)" src/lib/tilomenu/graphics; \
	  cp -a "$$tmp/gnomenu/src/share/gnomenu/Themes/." "$(MENU_DIR)/"; \
	  cp -a "$$tmp/gnomenu/src/lib/gnomenu/graphics/." src/lib/tilomenu/graphics/; \
	  cp "$$tmp/gnomenu/COPYING" COPYING
	@echo 'Extracted untouched original Menu, Button, Icon, Sound themes, graphics and GPL license.'

# Install the complete original-source module set and MATE panel metadata.
install:
	@test -f "$(MENU_DIR)/Menu/Menu/themedata.xml" || { echo "Run make prepare first."; exit 1; }
	install -d "$(LIBDIR)" "$(DATADIR)/Themes" "$(PREFIX)/share/glib-2.0/schemas"
	install -m644 src/lib/tilomenu/*.py "$(LIBDIR)/"
	install -m755 src/lib/tilomenu/TiloMenu.py "$(LIBDIR)/TiloMenu.py"
	install -m755 src/bin/TiloMenu.py "$(PREFIX)/bin/tilomenu"
	cp -a src/lib/tilomenu/graphics "$(LIBDIR)/"
	cp -a "$(MENU_DIR)/." "$(DATADIR)/Themes/"
	install -Dm644 src/lib/mate-panel/applets/org.mate.panel.TiloMenu.mate-panel-applet "$(PREFIX)/share/mate-panel/applets/org.mate.panel.TiloMenu.mate-panel-applet"
	install -Dm644 src/share/dbus-1/services/org.mate.panel.applet.TiloMenuFactory.service "$(PREFIX)/share/dbus-1/services/org.mate.panel.applet.TiloMenuFactory.service"
	install -Dm644 src/share/glib-2.0/schemas/org.tilomenu.gschema.xml "$(PREFIX)/share/glib-2.0/schemas/org.tilomenu.gschema.xml"
	glib-compile-schemas "$(PREFIX)/share/glib-2.0/schemas"

uninstall:
	rm -f "$(PREFIX)/bin/tilomenu"
	rm -rf "$(LIBDIR)" "$(DATADIR)"
	rm -f "$(PREFIX)/share/mate-panel/applets/org.mate.panel.TiloMenu.mate-panel-applet"
	rm -f "$(PREFIX)/share/dbus-1/services/org.mate.panel.applet.TiloMenuFactory.service"
	rm -f "$(PREFIX)/share/glib-2.0/schemas/org.tilomenu.gschema.xml"
	glib-compile-schemas "$(PREFIX)/share/glib-2.0/schemas"

check:
	/usr/bin/python3 -m compileall -q src/lib/tilomenu src/bin
	/usr/bin/python3 -c "import xml.etree.ElementTree as E; E.parse('src/share/glib-2.0/schemas/org.tilomenu.gschema.xml')"

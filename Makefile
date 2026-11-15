# Source-first GnoMenu 2.9.1 -> TiloMenu port.
# Original src/bin, src/lib, src/share layout is retained.
PREFIX ?= /usr
LIBDIR = $(PREFIX)/lib/tilomenu
DATADIR = $(PREFIX)/share/tilomenu
MENU_DIR = src/share/tilomenu/Themes

.PHONY: prepare install uninstall check

# Original themes and graphics are stored in the source tree.
# The prepare target validates them without downloading an old archive.
prepare:
	@test -f "$(MENU_DIR)/Menu/Menu/themedata.xml" || { echo "Missing bundled menu theme files."; exit 1; }
	@test -f "$(MENU_DIR)/Button/GnoBlue/start-here.png" || { echo "Missing bundled button artwork."; exit 1; }
	@test -f src/lib/tilomenu/graphics/logo.png || { echo "Missing bundled graphics."; exit 1; }
	@echo 'Bundled GnoMenu assets are ready.'

# Install the complete original-source module set and MATE panel metadata.
install:
	@test -f "$(MENU_DIR)/Menu/Menu/themedata.xml" || { echo "Run make prepare first."; exit 1; }
	install -d "$(LIBDIR)" "$(DATADIR)/Themes" "$(PREFIX)/share/glib-2.0/schemas"
	install -m644 src/lib/tilomenu/*.py "$(LIBDIR)/"
	install -m755 src/lib/tilomenu/TiloMenu.py "$(LIBDIR)/TiloMenu.py"
	install -m755 src/bin/TiloMenu.py "$(PREFIX)/bin/tilomenu"
	cp -a src/lib/tilomenu/graphics "$(LIBDIR)/"
	cp -a "$(MENU_DIR)/." "$(DATADIR)/Themes/"
	@if test -d data/themes/Menu; then cp -a data/themes/Menu/. "$(DATADIR)/Themes/Menu/"; fi
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

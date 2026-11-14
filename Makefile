# Keep original src/lib and src/share layout. Extract GnoMenu 2.9.1 assets unchanged.
SOURCE_ARCHIVE ?= $(HOME)/Downloads/gnomenu-2.9.1.tar.gz
THEME_DIR = src/share/tilomenu/Themes/Button/GnoBlue
SOURCE_THEME = gnomenu/src/share/gnomenu/Themes/Button/GnoBlue

.PHONY: prepare install uninstall check

prepare:
	@test -f "$(SOURCE_ARCHIVE)" || { echo "Missing original source: $(SOURCE_ARCHIVE)"; exit 1; }
	@mkdir -p "$(THEME_DIR)"
	@for file in themedata.xml start-here.png start-here-glow.png start-here-depressed.png themepreview.png; do \
	  tar -xOzf "$(SOURCE_ARCHIVE)" "$(SOURCE_THEME)/$$file" > "$(THEME_DIR)/$$file" || exit 1; \
	done
	@tar -xOzf "$(SOURCE_ARCHIVE)" gnomenu/COPYING > COPYING
	@echo 'Original GnoBlue artwork and GPL license extracted unchanged.'

install:
	@test -f "$(THEME_DIR)/themedata.xml" || { echo 'Run make prepare as your user first.'; exit 1; }
	install -Dm755 src/lib/tilomenu/TiloMenu.py /usr/lib/tilomenu/TiloMenu.py
	install -Dm755 src/bin/TiloMenu.py /usr/bin/tilomenu
	install -Dm644 src/lib/mate-panel/applets/org.mate.panel.TiloMenu.mate-panel-applet /usr/share/mate-panel/applets/org.mate.panel.TiloMenu.mate-panel-applet
	install -Dm644 src/share/dbus-1/services/org.mate.panel.applet.TiloMenuFactory.service /usr/share/dbus-1/services/org.mate.panel.applet.TiloMenuFactory.service
	install -d /usr/share/tilomenu/Themes/Button/GnoBlue
	install -m644 "$(THEME_DIR)/"* /usr/share/tilomenu/Themes/Button/GnoBlue/

uninstall:
	rm -f /usr/lib/tilomenu/TiloMenu.py /usr/bin/tilomenu
	rm -f /usr/share/mate-panel/applets/org.mate.panel.TiloMenu.mate-panel-applet
	rm -f /usr/share/dbus-1/services/org.mate.panel.applet.TiloMenuFactory.service
	rm -rf /usr/share/tilomenu/Themes/Button/GnoBlue

check:
	/usr/bin/python3 -m py_compile src/lib/tilomenu/TiloMenu.py src/bin/TiloMenu.py

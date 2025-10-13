Tilo Menu — MATE panel menu (Python 3)

Overview
--------
Tilo Menu is a modernized, Python-3 port of the old GnoMenu-style app menu,
packaged as a MATE panel applet with a simple standalone tester.

What’s here
-----------
- src/lib/tilo/           → core Python modules (Tilo.py, Menu_Main.py, etc.)
- src/lib/applet/         → applet descriptors (DBus + mate-panel .applet)
- src/bin/tilo-menu       → tiny CLI wrapper (runs the menu)
- Makefile                → install / uninstall helpers

Quick install
-------------
1) Make sure deps are present (Fedora/Ubuntu names shown):
   - python3, python3-gobject, python3-dbus, mate-panel, dconf
   - optional: python3-numpy (some visual effects), python3-lxml or xml.sax
2) From the project root:
      sudo make install
3) Log out/in OR restart the panel:
      mate-panel --replace &    (from a terminal)

Add to panel
------------
Right-click the MATE panel → “Add to Panel…” → pick “Tilo Menu”.

If it appears in the list but won’t render:
- restart the panel (see above)
- verify the DBus factory responds:
    gdbus call --session \
      --dest org.mate.panel.applet.TiloMenuAppletFactory \
      --object-path /org/mate/panel/applet/TiloMenuAppletFactory \
      --method org.freedesktop.DBus.Peer.Ping
  Expected output: "()"

Standalone test (no panel)
--------------------------
Useful while theming or debugging:
  tilo-menu --show          # pop the menu window directly
  python3 /usr/lib/tilo/Tilo.py run-in-window   # embed a fake applet in a test window

Install layout (after `make install`)
-------------------------------------
/etc/tilo/prefix                                     (install prefix marker)
/usr/lib/tilo/…                                      (Python sources)
/usr/share/tilo/…                                    (themes/assets)
/usr/share/mate-panel/applets/org.mate.panel.TiloMenuApplet.mate-panel-applet
/usr/share/dbus-1/services/org.mate.panel.applet.TiloMenuAppletFactory.service
/usr/bin/tilo-menu                                   (CLI wrapper)

Bookmarks module
----------------
`bookmarks.py` was updated for Python 3. It supports Firefox (JSON or sqlite
fallback), Chromium/Chrome, Opera (legacy), Epiphany and XBEL. If you still see
“warning: bookmarks module not available”, the menu will still work; install any
missing optional deps (json/sqlite3 are built-in; xml.sax is part of stdlib).

Known tips
----------
- If the applet list shows “Tilo Menu” but adding fails, confirm both files exist:
    /usr/share/mate-panel/applets/org.mate.panel.TiloMenuApplet.mate-panel-applet
    /usr/share/dbus-1/services/org.mate.panel.applet.TiloMenuAppletFactory.service
  and that they reference /usr/lib/tilo/Tilo.py.
- If icons don’t appear, Tilo falls back to a theme icon. Check your theme or
  the StartButton assets in Globals.py/theme folders.

Uninstall
---------
  sudo make uninstall
  mate-panel --replace &   # or log out/in

License
-------
GPLv3 (see original GnoMenu credits).


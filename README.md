# TiloMenu

Direct source port of GnoMenu 2.9.1 to Python 3, GTK3 and the MATE panel.

The original `src/lib`, `src/bin` and `src/share` directory layout is retained.
Original authors, GPL notices, class names and original menu algorithms are preserved.
The ported Python 3 syntax is committed directly, instead of introducing a new menu rendering engine.

## Port status

The original 2.9.1 modules are now tracked under `src/lib/tilomenu`.
Python 2 syntax conversion is complete across the selected core modules.
The original popup, application list and settings window now construct and open under GTK3 in automated Xvfb tests. Fedora MATE testing confirms the Settings window opens and theme selection reloads the menu. Popup rendering still needs work.

Implemented compatibility steps:
- `TiloMenu.py`: original MATE panel button, popup show/hide, state signal and settings command.
- `backend.py`: original `load_setting` and `save_setting` now use GSettings/dconf, with XML fallback and legacy XML read.
- `MenuParser.py`: original freedesktop XDG parser fallback and Gio directory monitoring.
- `Launcher.py`, `IconFactory.py`, `utils.py`: Python3/GTK3 imports and compatibility substitutions.
- `Menu_Main.py`, `Menu_Widgets.py`, `Menu_Items.py`, `Globals.py`, `TiloMenu-Settings.py`, `Popup_Menu.py`, `cairo_drawing.py`: original source with Python 3/GTK3 compatibility fixes. Original Xvfb startup, show/hide and settings window checks are enforced in GitHub Actions. More legacy widget paths remain to port.

Original GnoMenu 2.9.1 themes, graphics and GPL license are bundled in the repository in their retained source paths. These assets were copied unchanged from the original release. `make prepare` validates them, with no separate tarball or old installation required.

## Developer preparation

```bash
clear
cd ~/Downloads/Tilo-Menu
git pull
make prepare
make check
```

When the desktop is available, the next test is the panel applet itself. CI already checks original window initialization and click/close behavior through the GTK3 testing sandpit.

The previous working GTK3 revival is archived at
`archive/gtk3-revival-2026-11-14`.

## Test on Fedora MATE

This is the **original-source port**, not the earlier archived GTK3 recreation.
The source tree still uses `src/bin`, `src/lib/tilomenu`, and
`src/share/tilomenu`. The original theme directories and XML artwork are already included in GitHub.
`make prepare` verifies their presence.

First, ensure the Fedora dependencies are available:

```bash
clear
sudo dnf install -y python3-gobject python3-cairo python3-dbus python3-pyxdg mate-panel mate-panel-libs mate-menus
```

Install the new port after updating the repository:

```bash
clear
cd ~/Downloads/Tilo-Menu
git pull
make prepare
make check
sudo make install
```

Try the **original run-in-window sandbox first**, without adding anything
to your panel yet:

```bash
clear
XDG_MENU_PREFIX=mate- tilomenu run-in-window
```

Click the original GnoBlue image to open/close the original popup. Inspect
the original program list, Search, Places and Favorites.

The original Settings notebook also launches directly:

```bash
clear
tilomenu preferences
```

For the native applet, right-click the existing MATE panel and select
**Add to Panel**, then search for **TiloMenu**. Add it and test left-click
(open/close) and right-click **Preferences**.

The installed command is `tilomenu`. The archived prototype used
`~/.local/bin/tilo-menu`, a different command. The current installer does not modify that older path.

To remove the new system-wide port without touching your archived prototype:

```bash
clear
cd ~/Downloads/Tilo-Menu
sudo make uninstall
```

These tests verify construction and events in an Xvfb GTK3 session.
Visual parity and native panel positioning still require testing on Fedora MATE.

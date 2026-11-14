# TiloMenu

Direct source port of GnoMenu 2.9.1 to Python 3, GTK3 and the MATE panel.

The original `src/lib`, `src/bin` and `src/share` directory layout is retained.
Original authors, GPL notices, class names and original menu algorithms are preserved.
The ported Python 3 syntax is committed directly, instead of introducing a new menu rendering engine.

## Port status

The original 2.9.1 modules are now tracked under `src/lib/tilomenu`.
Python 2 syntax conversion is complete across the selected core modules.
The original popup, application list and settings window now construct and open under GTK3 in automated Xvfb tests. MATE panel integration still needs testing on a real desktop.

Implemented compatibility steps:
- `TiloMenu.py`: original MATE panel button, popup show/hide, state signal and settings command.
- `backend.py`: original `load_setting` and `save_setting` now use GSettings/dconf, with XML fallback and legacy XML read.
- `MenuParser.py`: original freedesktop XDG parser fallback and Gio directory monitoring.
- `Launcher.py`, `IconFactory.py`, `utils.py`: Python3/GTK3 imports and compatibility substitutions.
- `Menu_Main.py`, `Menu_Widgets.py`, `Menu_Items.py`, `Globals.py`, `TiloMenu-Settings.py`, `Popup_Menu.py`, `cairo_drawing.py`: original source with Python 3/GTK3 compatibility fixes. Original Xvfb startup, show/hide and settings window checks are enforced in GitHub Actions. More legacy widget paths remain to port.

Original artwork and XML remain completely unchanged. `make prepare` extracts only the four original default theme sets (Menu, Button, Icon, Sound), graphics and GPL license from `~/Downloads/gnomenu-2.9.1.tar.gz`; it does not download KDE, XFCE, AWN or other desktop integrations.

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

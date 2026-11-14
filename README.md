# Tilo-Menu

A clean, MATE-only application menu for Fedora.

## Status

Early development. Not installable as a panel applet yet.

## Scope

- MATE panel only
- Installed applications, search, and launching
- Favorites and original GnoMenu-inspired themes later

No AWN, Cairo-Dock, Docky, KDE, XFCE, or GNOME 2 integration.

## Source

Rebuild inspired by [original GnoMenu](https://github.com/jindongyang/gnomenu).
The original GTK 2 / Python 2 code is being reviewed, not copied wholesale.
Modern implementation uses Python 3, PyGObject, and GIO.

## Current module

`tilomenu/applications.py` implements application discovery, search, and launching.
Next: implement a MATE panel applet and popup using the panel APIs available on Fedora 43.

# Tilo-Menu

A clean, MATE-only rebuild of the original GnoMenu for Fedora.

The project uses Python 3, GTK 3, GIO, and the original GnoMenu XML theme layout. It does not include AWN, Cairo-Dock, Docky, KDE, XFCE, or GNOME 2/Bonobo integrations.

## Development preview

Install GTK 3 Python bindings on Fedora, then extract your original GnoMenu 2.9.1 archive. From the repository directory:

```bash
sudo dnf install python3-gobject gtk3
python3 -m tilomenu.menu /path/to/gnomenu/src/share/gnomenu/Themes/Menu/Vista
```

The standalone preview draws the theme background and menu artwork, positions the application list and search field using XML coordinates, and launches installed applications through GIO.

This is an early preview, not a panel applet or an installable application. Theme-defined system buttons are decorative until safe MATE actions are implemented. The original theme artwork is not bundled yet.

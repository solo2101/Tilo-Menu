# Tilo-Menu

Python 3 / GTK 3 standalone preview of the original GnoMenu menu for Fedora MATE. The MATE panel applet is not implemented yet.

## Install from GitHub

```bash
sudo dnf install git make curl python3-gobject gtk3
cd ~/Downloads
git clone https://github.com/solo2101/Tilo-Menu.git
cd Tilo-Menu
make install
~/.local/bin/tilo-menu
```

The installer downloads the original GnoMenu 2.9.1 source archive from Launchpad to extract the original menu themes if they are not already in `data/themes/Menu`. If you have `~/Downloads/gnomenu-2.9.1.tar.gz`, it uses that instead. Installation is per-user and does not require sudo.

```bash
make uninstall
```

This is an early preview. System shortcuts and the original themed controls are not fully functional yet. The original theme artwork belongs to its respective authors and is not included in the GitHub source tree.

## Themes

Right-click the menu background and choose **Change Theme**. Your selection is saved for the next launch. Vista remains the default. Run `~/.local/bin/tilo-menu --list-themes` to see installed themes, or `~/.local/bin/tilo-menu --theme Slab` to preview a specific theme without changing the saved choice. Themes use the original XML geometry; visual compatibility varies by theme.

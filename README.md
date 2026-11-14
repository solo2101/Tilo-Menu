# Tilo-Menu

Python 3 / GTK 3 standalone preview of the original GnoMenu menu for Fedora MATE. The MATE panel applet is not implemented yet.

## Install from GitHub

```bash
sudo dnf install git make curl python3-gobject python3-cairo gtk3
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

This is an early preview, not a MATE panel applet. The program list is painted with Cairo, the search entry uses original theme imagery, and button and tab chrome follows the original GnoMenu XML. Some theme-specific actions are not yet implemented. The original theme artwork belongs to its respective authors and is not included in the GitHub source tree.

## Themes

Right-click the menu background and choose **Change Theme**. Your selection is saved for the next launch. Vista remains the default. Run `~/.local/bin/tilo-menu --list-themes` to see installed themes, or `~/.local/bin/tilo-menu --theme Slab` to preview a specific theme without changing the saved choice. Themes use the original XML geometry; visual compatibility varies by theme.

## Rendering regression test

The GitHub Actions workflow downloads the original 2.9.1 theme bundle and starts all 15 themes under Xvfb using Python 3 and GTK 3. This checks for startup, XML, and drawing errors. Visual validation on Fedora MATE is still required for composited transparency and alignment.

## Theme Preferences (original GnoMenu-style)

Run `~/.local/bin/tilo-menu --settings`, or right-click the menu background and choose **Preferences**. The Menu selection tab shows the original `themepreview.png` (when supplied), theme credits, and an **Install Theme** button. The installer reads `themedata.xml` from the archive and installs its unmodified files in `~/.local/share/tilo-menu/data/themes/Menu/<theme>`. It safely rejects archive traversal/symlinks, preserves installed themes, and never selects a theme without clicking **Apply Theme**. This currently supports Menu themes; the original separate Button, Icon and Sound theme selectors are future work. The archive `118852-DarkCandy_2.2_by_jonian.tar` is not installed automatically.

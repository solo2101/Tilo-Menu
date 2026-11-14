# TiloMenu, original-source port (step 1)

Direct port of the **GnoMenu 2.9.1 panel button** to Python 3, GTK3
and MatePanelApplet 4.0. Original class and method names are retained wherever
practical. The project's name is now **TiloMenu**.

The original GnoBlue button theme is loaded through its unchanged XML.
`make prepare` extracts the original artwork and GPL COPYING license
byte-for-byte from the original source archive.

## First test: original panel button only

Run this before installing anything into the panel:

```bash
clear
cd ~/Downloads/Tilo-Menu
git pull
make prepare
/usr/bin/python3 src/lib/tilomenu/TiloMenu.py run-in-window
```

This opens the original testing sandpit with the GnoBlue button. Move the
mouse over the button to check its normal and hover PNGs. The popup menu and
settings are deliberately not yet ported.

## Prepare on Fedora MATE

```bash
clear
cd ~/Downloads/Tilo-Menu
git pull
make prepare
sudo make install
```

The source archive must exist at `~/Downloads/gnomenu-2.9.1.tar.gz`.
In MATE, right-click the panel, select **Add to Panel**, and select **TiloMenu**.

## Current stage

The panel button loads and uses the three original GnoBlue artwork states.
The original right-click menu entries are registered but disabled until
their settings/editor modules are ported. **Left click does not open a menu
yet.** We will port `Menu_Main.py` and `Menu_Widgets.py` from original
GnoMenu next, instead of creating another rendering engine.

No existing user installation or archived branch is modified by this commit.

Original authors: QB89Dragon and Whise. GPL-3.0-or-later. Full license
text is extracted to `COPYING` with `make prepare`.

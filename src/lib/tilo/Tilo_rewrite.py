#!/usr/bin/env python3
# Compatibility shim for legacy factory ID -> use the real applet in Tilo.py

import gi, os, sys
gi.require_version("MatePanelApplet", "4.0")
from gi.repository import MatePanelApplet

# import the real factory from Tilo.py
from Tilo import Tilo_factory as RealFactory

def Tilo_factory(applet, iid, data=None):
    # delegate to the real applet factory
    return RealFactory(applet, iid)

if __name__ == "__main__":
    # run as a factory when mate-panel spawns us
    if "--factory" in sys.argv or os.environ.get("MATE_PANEL_APPLET_ID"):
        MatePanelApplet.Applet.factory_main(
            "OAFIID:MATE_Tilo_Factory",   # legacy ID preserved
            True,
            MatePanelApplet.Applet.__gtype__,
            Tilo_factory,
            None,
        )
        sys.exit(0)

    # dev helper: show the applet button in a window
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    class Fake(Gtk.EventBox):
        def __init__(self):
            super().__init__()
            self._size = 36
            self._orient = 1
        def set_background_widget(self, w): pass
        def get_orient(self): return self._orient
        def get_size(self): return self._size
    win = Gtk.Window(title="Tilo (legacy shim)")
    win.connect("destroy", Gtk.main_quit)
    fake = Fake()
    win.add(fake)
    RealFactory(fake, "")
    win.show_all()
    Gtk.main()

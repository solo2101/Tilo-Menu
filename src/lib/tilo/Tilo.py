#!/usr/bin/env python3
# Tilo MATE panel applet (single-file factory)

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("MatePanelApplet", "4.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, MatePanelApplet

import os
import sys

import Globals
from Menu_Main import Main_Menu
import backend

# ---------- i18n ----------
try:
    with open("/etc/tilo/prefix", "r") as f:
        INSTALL_PREFIX = f.read().strip() or "/usr"
except Exception:
    INSTALL_PREFIX = "/usr"

import gettext
gettext.textdomain("tilo")
gettext.bindtextdomain("tilo", os.path.join(INSTALL_PREFIX, "share", "locale"))
gettext.install("tilo", os.path.join(INSTALL_PREFIX, "share", "locale"))

def _(s: str) -> str:
    return gettext.gettext(s)


# ============================================================
# Applet widget
# ============================================================
class Tilo(MatePanelApplet.Applet):
    def __init__(self, applet, iid):
        self.applet = applet
        self.iid = iid

        self.Button_state = 0          # 0 normal, 1 hover, 2 pressed
        self.orientation = self._get_orientation()
        Globals.flip = False if self.orientation == "top" else None
        self.size = self._get_panel_size()

        self._store_settings()

        # container + clickable area
        self.Fixed = Gtk.Fixed()
        self.EBox = Gtk.EventBox()
        self.EBox.set_tooltip_text(Globals.name)
        # make the area visible so a fallback is obvious
        self.EBox.set_visible_window(True)
        self.EBox.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.Fixed.put(self.EBox, 0, 0)
        self.applet.add(self.Fixed)

        # image (button art)
        self.Image = Gtk.Image()
        self.EBox.add(self.Image)

        # size hints (so panel allocates room)
        try:
            self.applet.set_size_hints(self.size, self.size, self.size, self.size)
        except Exception:
            pass

        # signals (guarded for safety)
        try:
            self.applet.set_background_widget(self.applet)
        except Exception:
            pass
        try:
            self.applet.connect("destroy", self.cleanup)
            self.applet.connect("change-orient", self.change_orientation)
            self.applet.connect("size-allocate", self.size_allocate_event)
            self.applet.connect("map-event", self.map_event)
        except Exception:
            pass

        self.EBox.connect("button-press-event", self.button_press)
        self.EBox.connect("enter-notify-event", self.select_box)
        self.EBox.connect("leave-notify-event", self.deselect_box)

        self.oldsize = 0
        self.x = self.y = 0
        self.hwg = None  # Menu window instance

        self.applet.show_all()
        self._redraw_graphics()

    # ---------- helpers ----------
    def _get_orientation(self) -> str:
        try:
            orient = self.applet.get_orient()
        except Exception:
            orient = None
        # 1 == top on MATE
        return "top" if orient == 1 else "bottom"

    def _get_panel_size(self) -> int:
        try:
            s = int(self.applet.get_size())
        except Exception:
            s = 32
        if s <= 0:
            s = 32
        return s

    def _store_settings(self) -> None:
        backend.save_setting("orientation", self.orientation or "bottom")
        backend.save_setting("size", self.size)

    # ---------- applet signals ----------
    def change_orientation(self, *_args):
        self.orientation = self._get_orientation()
        Globals.flip = False if self.orientation == "top" else None
        self._store_settings()
        self._redraw_graphics()
        if self.hwg:
            self.hwg.Adjust_Window_Dimensions(self.x, self.y)

    def size_allocate_event(self, widget, allocation):
        # track screen origin for menu placement
        if widget.get_window():
            try:
                self.x, self.y = widget.get_window().get_origin()
            except Exception:
                self.x = self.y = 0
        else:
            self.x = self.y = 0

        new_size = self._get_panel_size()
        if new_size != self.oldsize:
            self.size = new_size
            self._redraw_graphics()
            if self.hwg:
                self.hwg.Adjust_Window_Dimensions(self.x, self.y)
            self.oldsize = new_size
        return True

    def map_event(self, _widget, _event):
        self._redraw_graphics()
        self.hwg = Main_Menu(self.HideMenu)
        self.hwg.connect("state-changed", self.button_changed)
        self.hwg.Adjust_Window_Dimensions(self.x, self.y)

    # ---------- menu button events ----------
    def button_press(self, _widget, event):
        if event.button == 1:
            if not self._menu_visible():
                if self.hwg:
                    self.hwg.Adjust_Window_Dimensions(self.x, self.y)
                self.ShowMenu()
                self.Button_state = 2
            else:
                if self.Button_state == 2:
                    self.HideMenu()
                    self.Button_state = 1
                else:
                    if self.hwg:
                        self.hwg.Adjust_Window_Dimensions(self.x, self.y)
                    self.ShowMenu()
                    self.Button_state = 2
            self._redraw_graphics()
        elif event.button == 3:
            pass  # reserved for future menu

    def select_box(self, *_args):
        if self.Button_state == 0:
            self.Button_state = 1
        self._redraw_graphics()

    def deselect_box(self, *_args):
        if self.Button_state == 1:
            self.Button_state = 0
        self._redraw_graphics()

    def button_changed(self, _event, button, _button1):
        self.Button_state = button
        self._redraw_graphics()

    # ---------- show/hide ----------
    def ShowMenu(self):
        if not self.hwg:
            return
        try:
            origin = self.applet.get_window().get_origin()
            self.hwg.Adjust_Window_Dimensions(origin[0], origin[1])
        except Exception:
            self.hwg.Adjust_Window_Dimensions(self.x, self.y)
        self.hwg.show_window()

    def HideMenu(self):
        if self.hwg and self._menu_visible():
            self.hwg.hide_window()
        self.Button_state = 0
        self._redraw_graphics()

    def _menu_visible(self) -> bool:
        try:
            return self.hwg.window.get_visible()
        except Exception:
            return False

    # ---------- drawing ----------
    def _fallback_icon(self, size: int):
        try:
            theme = Gtk.IconTheme.get_default()
            for name in ("applications-system", "start-here", "application-menu", "system-run"):
                if theme.has_icon(name):
                    return theme.load_icon(name, size, 0)
        except Exception:
            pass
        # last resort, visible square
        pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, size, size)
        pb.fill(0xffffffff)  # opaque white
        return pb

    def _redraw_graphics(self):
        btn_h = max(16, int(self.size))
        pixbuf = None
        use_logo = Globals.Settings.get("Distributor_Logo", 0) == 1 and hasattr(Globals, "distro_logo")

        try:
            if use_logo and os.path.isfile(Globals.distro_logo):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(Globals.distro_logo, btn_h, btn_h)
            else:
                path = None
                if getattr(Globals, "StartButton", None):
                    try:
                        path = Globals.StartButton[self.Button_state]
                    except Exception:
                        path = None

                if path and os.path.isfile(path):
                    im = GdkPixbuf.Pixbuf.new_from_file(path)
                    w = max(1, im.get_width())
                    h = max(1, im.get_height())
                    scale = float(btn_h) / float(h)
                    pixbuf = im.scale_simple(int(w * scale), btn_h, GdkPixbuf.InterpType.BILINEAR)
                    if Globals.flip is False and Globals.ButtonHasTop == 1:
                        try:
                            pixbuf = pixbuf.flip(True)
                        except Exception:
                            pass
        except Exception:
            pixbuf = None

        if pixbuf is None:
            pixbuf = self._fallback_icon(btn_h)

        btn_w = max(24, int(pixbuf.get_width()))
        try:
            self.applet.set_size_hints(btn_w, btn_w, btn_h, btn_h)
        except Exception:
            pass

        self.Fixed.set_size_request(btn_w, btn_h)
        self.EBox.set_size_request(btn_w, btn_h)
        self.Image.set_from_pixbuf(pixbuf)
        self.Image.set_size_request(btn_w, btn_h)
        self.applet.show_all()

    # ---------- cleanup ----------
    def cleanup(self, *_args):
        if self.hwg:
            try:
                self.hwg.destroy()
            except Exception:
                pass
        del self.applet


# ---------- factory callback ----------
try:
    GObject.type_register(Tilo)
except Exception:
    pass

def Tilo_factory(applet, iid, data=None):
    Tilo(applet, iid)
    return True


# ============================================================
# Entry points
# ============================================================
if __name__ == "__main__":
    # Spawned by mate-panel via the D-Bus service
    if "--factory" in sys.argv or os.environ.get("MATE_PANEL_APPLET_ID"):
        print("Tilo factory starting. IID=OAFIID:MATE_TiloMenu; argv=", sys.argv)
        MatePanelApplet.Applet.factory_main(
            "OAFIID:MATE_TiloMenu",        # must match MateComponentId
            True,
            MatePanelApplet.Applet.__gtype__,
            Tilo_factory,
            None
        )
        sys.exit(0)

    # 2) Dev helpers
    if "--show" in sys.argv:
        def _hide(): Gtk.main_quit()
        m = Main_Menu(_hide)
        m.show_window()
        Gtk.main()
        sys.exit(0)

    if "--run-in-window" in sys.argv or "--run-in-console" in sys.argv:
        class FakeApplet(Gtk.EventBox):
            def __init__(self):
                super().__init__()
                self._size = 36
                self._orient = 1
            def set_background_widget(self, widget): pass
            def get_orient(self): return self._orient
            def get_size(self): return self._size

        win = Gtk.Window(title="Tilo (standalone)")
        win.connect("destroy", Gtk.main_quit)
        fake = FakeApplet()
        win.add(fake)
        Tilo(fake, "")
        win.show_all()
        Gtk.main()

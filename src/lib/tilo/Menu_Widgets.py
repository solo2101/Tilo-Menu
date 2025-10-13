#!/usr/bin/env python3

import os
import subprocess
from typing import Optional, List

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gtk, Gdk, GObject, GLib, GdkPixbuf, Pango

from Menu_Items import XDMateMenu
import Globals
import IconFactory

try:
    INSTALL_PREFIX = open("/etc/tilo/prefix").read().strip()
except Exception:
    INSTALL_PREFIX = "/usr"

import gettext
gettext.textdomain('tilo')
gettext.install('tilo', INSTALL_PREFIX + '/share/locale')
gettext.bindtextdomain('tilo', INSTALL_PREFIX + '/share/locale')
_ = gettext.gettext


# ------------------------- helpers -------------------------

def sh(cmd: str) -> str:
    """Run a shell command and return decoded stdout (best effort)."""
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return out.decode('utf-8', errors='replace').strip()
    except Exception:
        return ""


def _draw_pixbuf(cr, pixbuf: GdkPixbuf.Pixbuf, x=0, y=0):
    if not pixbuf:
        return
    Gdk.cairo_set_source_pixbuf(cr, pixbuf, x, y)
    cr.paint()


def _pixbuf_from_file(path: str) -> Optional[GdkPixbuf.Pixbuf]:
    try:
        return GdkPixbuf.Pixbuf.new_from_file(path)
    except Exception:
        return None


def _pixbuf_from_file_at_size(path: str, w: int, h: int) -> Optional[GdkPixbuf.Pixbuf]:
    try:
        return GdkPixbuf.Pixbuf.new_from_file_at_size(path, max(1, int(w)), max(1, int(h)))
    except Exception:
        return None


def _invert_hex(color_hex: str) -> str:
    # Accepts "#rrggbb" or "#rgb"
    try:
        s = color_hex.lstrip('#')
        if len(s) == 3:
            s = ''.join(ch * 2 for ch in s)
        r = 255 - int(s[0:2], 16)
        g = 255 - int(s[2:4], 16)
        b = 255 - int(s[4:6], 16)
        return '#%02x%02x%02x' % (r, g, b)
    except Exception:
        return "#000000"


# ------------------------- widgets -------------------------

class MenuButton:
    def __init__(self, i: int, base: Gtk.Fixed, backimage: GdkPixbuf.Pixbuf):
        self.i = i
        self.Button = Gtk.EventBox()
        self.Frame = Gtk.Fixed()
        self.Button.add(self.Frame)
        self.Frame.connect("draw", self._on_draw_background)

        # foreground image (button skin)
        self.Image = Gtk.Image()
        self.Pic = _pixbuf_from_file(Globals.ImageDirectory + Globals.MenuButtonImage[i])
        if self.Pic is None:
            self.Pic = _pixbuf_from_file(Globals.BrokenImage)
        self.Image.set_from_pixbuf(self.Pic)

        self.w = self.Pic.get_width()
        self.h = self.Pic.get_height()

        # sub-surface of the menu background behind this button
        if Globals.flip is False:
            sub = backimage.new_subpixbuf(Globals.MenuButtonX[i],
                                          Globals.MenuHeight - Globals.MenuButtonY[i] - self.h,
                                          self.w, self.h)
            self.backimagearea = sub.flip(True)
        else:
            self.backimagearea = backimage.new_subpixbuf(Globals.MenuButtonX[i],
                                                         Globals.MenuButtonY[i],
                                                         self.w, self.h)

        # optional background image for button (ImageBack)
        self.BackgroundImage = Gtk.Image()
        if Globals.MenuButtonImageBack[i]:
            pb = _pixbuf_from_file(Globals.ImageDirectory + Globals.MenuButtonImageBack[i])
            self.BackgroundImage.set_from_pixbuf(pb)
        else:
            self.BackgroundImage.clear()

        self.Image.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)

        self.Frame.put(self.BackgroundImage, 0, 0)
        self.Frame.put(self.Image, 0, 0)

        # optional icon overlay
        self.Icon: Optional[Gtk.Image] = None
        if Globals.MenuButtonIcon[i]:
            self.Icon = Gtk.Image()
            self.SetIcon(Globals.ImageDirectory + Globals.MenuButtonIcon[i])
            self.Frame.put(self.Icon, Globals.MenuButtonIconX[i], Globals.MenuButtonIconY[i])

        # label
        self.Label = Gtk.Label()
        txt = Globals.MenuButtonMarkup[i]
        try:
            txt = txt.replace(Globals.MenuButtonNames[i], _(Globals.MenuButtonNames[i]))
        except Exception:
            pass
        self.Label.set_markup(txt)
        ellipsize = Pango.EllipsizeMode.END
        self.Label.set_ellipsize(ellipsize)
        self.Label.set_size_request(int(self.w - Globals.MenuButtonNameOffsetX[i] * 2) - 2, -1)
        # alignment: 0-left / 1-center / 2-right
        align = Globals.MenuButtonNameAlignment[i]
        if align == 0:
            self.Label.set_xalign(0.0)
        elif align == 1:
            self.Label.set_xalign(0.5)
        else:
            self.Label.set_xalign(1.0)
        self.Frame.put(self.Label, Globals.MenuButtonNameOffsetX[i], Globals.MenuButtonNameOffsetY[i])

        if self.Label.get_text() == '' or Globals.Settings.get('Show_Tips'):
            self.Frame.set_tooltip_text(_(Globals.MenuButtonNames[i]))

        base.put(self.Button, Globals.MenuButtonX[i], Globals.MenuButtonY[i])

    def _on_draw_background(self, widget, cr):
        # Paint the captured background under this widget then the button image is on top via Gtk.Image
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        _draw_pixbuf(cr, self.backimagearea)
        return False

    def SetIcon(self, filename: str):
        if self.Icon is None:
            return
        try:
            size = Globals.MenuButtonIconSize[self.i]
            if size:
                ww = hh = size
                pb = _pixbuf_from_file_at_size(filename, ww, hh)
            else:
                pb = _pixbuf_from_file(filename)
                if pb:
                    ww = pb.get_width()
                    hh = pb.get_height()
            if Globals.Settings.get('System_Icons'):
                if not Globals.MenuButtonIconSel[self.i]:
                    ico = IconFactory.GetSystemIcon(Globals.MenuButtonIcon[self.i]) or filename
                    pb = _pixbuf_from_file_at_size(ico, ww, hh)
            if pb:
                self.Icon.set_from_pixbuf(pb)
        except Exception:
            print('MenuButton: error SetIcon', filename)

    def Setimage(self, imagefile: str):
        pb = _pixbuf_from_file(imagefile)
        if pb:
            self.Image.set_from_pixbuf(pb)

    def SetBackground(self):
        self.Image.clear()


class MenuImage:
    def __init__(self, i: int, base: Gtk.Fixed, backimage: GdkPixbuf.Pixbuf):
        self.Frame = Gtk.Fixed()
        self.Frame.connect("draw", self._on_draw)
        self.Image = Gtk.Image()

        pb = _pixbuf_from_file(Globals.ImageDirectory + Globals.MenuImage[i])
        if pb is None:
            pb = _pixbuf_from_file(Globals.BrokenImage)
        w = pb.get_width()
        h = pb.get_height()

        if Globals.Settings.get('System_Icons'):
            ico = IconFactory.GetSystemIcon(Globals.MenuImage[i]) or (Globals.ImageDirectory + Globals.MenuImage[i])
            pb = _pixbuf_from_file_at_size(ico, w, h)

        if Globals.flip is False:
            sub = backimage.new_subpixbuf(Globals.MenuImageX[i],
                                          Globals.MenuHeight - Globals.MenuImageY[i] - h,
                                          w, h)
            self.backimagearea = sub.flip(True)
        else:
            self.backimagearea = backimage.new_subpixbuf(Globals.MenuImageX[i],
                                                         Globals.MenuImageY[i],
                                                         w, h)
        # compose over background
        pb.composite(self.backimagearea, 0, 0, w, h, 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, 255)
        self.Image.set_from_pixbuf(self.backimagearea)
        self.Image.set_size_request(w, h)
        self.Frame.set_size_request(w, h)
        self.Frame.put(self.Image, 0, 0)
        base.put(self.Frame, Globals.MenuImageX[i], Globals.MenuImageY[i])

    def _on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        return False


class MenuTab:
    def __init__(self, i: int, base: Gtk.Fixed, backimage: GdkPixbuf.Pixbuf):
        self.i = i
        self.Tab = Gtk.EventBox()
        self.Frame = Gtk.Fixed()
        self.Tab.add(self.Frame)
        self.Frame.connect("draw", self._on_draw_background)

        fmt, w, h = GdkPixbuf.Pixbuf.get_file_info(Globals.ImageDirectory + Globals.MenuTabImageSel[self.i])
        self.w = w or 1
        self.h = h or 1

        self.Image = Gtk.Image()
        self.Setimage(Globals.ImageDirectory + Globals.MenuTabImage[i])

        if Globals.flip is False:
            sub = backimage.new_subpixbuf(Globals.MenuTabX[i],
                                          Globals.MenuHeight - Globals.MenuTabY[i] - self.h,
                                          self.w, self.h)
            self.backimagearea = sub.flip(True)
        else:
            self.backimagearea = backimage.new_subpixbuf(Globals.MenuTabX[i],
                                                         Globals.MenuTabY[i],
                                                         self.w, self.h)

        self.Image.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)
        self.Frame.put(self.Image, 0, 0)

        # optional tab icon
        if Globals.MenuTabIcon[i]:
            self.Icon = Gtk.Image()
            self.SetIcon(Globals.ImageDirectory + Globals.MenuTabIcon[i])
            self.Frame.put(self.Icon, Globals.MenuCairoIcontabX[i], Globals.MenuCairoIcontabY[i])
        else:
            self.Icon = None

        # label
        self.Label = Gtk.Label()
        txt = Globals.MenuTabMarkup[i]
        try:
            txt = txt.replace(Globals.MenuTabNames[i], _(Globals.MenuTabNames[i]))
        except Exception:
            pass

        # extract prime color from markup (best-effort)
        self.txt = txt
        self.prime_color = "#ffffff"
        try:
            p = txt.split("span foreground='", 1)[1]
            self.prime_color = "#" + p.split("'", 1)[0].lstrip('#')
        except Exception:
            pass
        self.second_color = _invert_hex(self.prime_color)

        # alignment
        align = Globals.MenuTabNameAlignment[i]
        if align == 0:
            self.Label.set_xalign(0.0)
        elif align == 1:
            self.Label.set_xalign(0.5)
        else:
            self.Label.set_xalign(1.0)
        self.Label.set_size_request(int(self.w - Globals.MenuTabNameOffsetX[i] * 2) - 2, -1)
        self.Label.set_ellipsize(Pango.EllipsizeMode.END)
        self.Frame.put(self.Label, Globals.MenuTabNameOffsetX[i], Globals.MenuTabNameOffsetY[i])

        self.Tab.connect("enter-notify-event", self._enter)
        self.Tab.connect("leave-notify-event", self._leave)

        self.Tab.set_tooltip_text(_(Globals.MenuTabNames[i]))
        base.put(self.Tab, Globals.MenuTabX[i], Globals.MenuTabY[i])

        self.selected_tab = False
        self.SetSelectedTab(False)

    def _on_draw_background(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        _draw_pixbuf(cr, self.backimagearea)
        return False

    def _enter(self, *args):
        # hover effect for icon (subset of original)
        if self.Icon and Globals.MenuTabIcon[self.i]:
            ico = IconFactory.GetSystemIcon(Globals.MenuTabIcon[self.i]) if Globals.Settings.get('System_Icons') else None
            path = ico or (Globals.ImageDirectory + Globals.MenuTabIcon[self.i])
            w = Globals.MenuCairoIcontabSize[self.i] or 0
            if w <= 0:
                fmt, iw, ih = GdkPixbuf.Pixbuf.get_file_info(path)
                w = iw or 16
            pb = _pixbuf_from_file_at_size(path, w, w)
            if pb:
                # simple saturate/brighten on hover
                pb2 = pb.copy()
                pb2.saturate_and_pixelate(pb2, 1.5, False)
                self.Icon.set_from_pixbuf(pb2)

    def _leave(self, *args):
        if self.Icon:
            self.SetIcon(Globals.ImageDirectory + Globals.MenuTabIcon[self.i])

    def SetIcon(self, filename: str):
        ico = None
        if Globals.Settings.get('System_Icons'):
            ico = IconFactory.GetSystemIcon(Globals.MenuTabIcon[self.i])
        path = ico or (Globals.ImageDirectory + Globals.MenuTabIcon[self.i])
        size = Globals.MenuCairoIcontabSize[self.i] or 0
        if size <= 0:
            fmt, iw, ih = GdkPixbuf.Pixbuf.get_file_info(path)
            size = iw or 16
        pb = _pixbuf_from_file_at_size(path, size, size)
        if pb:
            self.Icon.set_from_pixbuf(pb)

    def Setimage(self, imagefile: str):
        pb = _pixbuf_from_file(imagefile)
        if pb:
            if Globals.Settings.get('GtkColors') == 1 and Globals.Has_Numpy:
                # legacy colorize path kept as-is if numpy is available
                colorpb = pb.copy()
                pb.composite(colorpb, 0, 0, self.w, self.h, 0, 0, 1, 1, GdkPixbuf.InterpType.BILINEAR, 70)
                pb = colorpb
            if Globals.flip is False:
                self.Image.set_from_pixbuf(pb.flip(True))
            else:
                self.Image.set_from_pixbuf(pb)

    def SetBackground(self):
        self.Image.clear()

    def SetSelectedTab(self, tab: bool):
        if not tab:
            if Globals.MenuTabInvertTextColorSel[self.i]:
                txt1 = self.txt.replace(self.prime_color, self.second_color)
                self.Label.set_markup(txt1)
            else:
                self.Label.set_markup(self.txt)
            self.selected_tab = False
            self.SetBackground()
            self.Setimage(Globals.ImageDirectory + Globals.MenuTabImage[self.i])
        else:
            self.Label.set_markup(self.txt)
            self.selected_tab = True
            self.Setimage(Globals.ImageDirectory + Globals.MenuTabImageSel[self.i])

    def GetSelectedTab(self) -> bool:
        return self.selected_tab


class Separator:
    def __init__(self, i: int, base: Gtk.Fixed):
        self.Image = Gtk.Image()
        pb = _pixbuf_from_file(Globals.ImageDirectory + Globals.MenuButtonImage[i])
        self.Image.set_from_pixbuf(pb)
        base.put(self.Image, Globals.MenuButtonX[i], Globals.MenuButtonY[i])


class MenuLabel:
    def __init__(self, i: int, base: Gtk.Fixed):
        self.i = i
        self.Label = Gtk.Label()
        txt = Globals.MenuLabelMarkup[i]
        txt = txt.replace(Globals.MenuLabelNames[i], _(Globals.MenuLabelNames[i]))
        if Globals.MenuLabelCommands[i]:
            a = sh(Globals.MenuLabelCommands[i])
            txt = txt.replace('[TEXT]', a)
        self.Label.set_markup(txt)
        # alignment
        align = Globals.MenuLabelNameAlignment[i]
        # obtain natural width to offset when centered/right
        w_req = self.Label.get_preferred_width()[0]
        if align == 0:
            xoff = 0
        elif align == 1:
            xoff = int(w_req / 2)
        else:
            xoff = int(w_req)
        if Globals.flip is False:
            base.put(self.Label, Globals.MenuLabelX[i] - xoff, Globals.MenuLabelY[i] - self.Label.get_preferred_height()[0])
        else:
            base.put(self.Label, Globals.MenuLabelX[i] - xoff, Globals.MenuLabelY[i])


from typing import List, Optional
import os
import cairo
from gi.repository import Gtk, GdkPixbuf, GLib

class ImageFrame:
    """User image frame with simple cross-fade between up to 2 overlay icons."""

    def __init__(self, w, h, inset_x, inset_y, inset_w, inset_h,
                 base: Gtk.Fixed, backimage: GdkPixbuf.Pixbuf):
        # overall frame size
        self.w, self.h = int(w), int(h)
        # where the face image sits *inside* the frame
        self.face_x, self.face_y = int(inset_x), int(inset_y)
        self.face_w, self.face_h = int(inset_w), int(inset_h)

        # container and widgets
        self.fixed = base
        self.frame_window = Gtk.EventBox()
        self.Frame = Gtk.Fixed()
        self.Image = Gtk.Image()
        self.frame_window.add(self.Frame)
        self.Frame.connect("draw", self._on_draw_background)
        self.frame_window.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)
        self.Frame.put(self.Image, 0, 0)

        # place the eventbox into the Fixed (we’ll move it later)
        self.fixed.put(self.frame_window,
                       int(Globals.UserIconFrameOffsetX),
                       int(Globals.UserIconFrameOffsetY))

        # snapshot the theme background under the frame
        if not Globals.flip:
            sub = backimage.new_subpixbuf(
                int(Globals.UserIconFrameOffsetX),
                int(Globals.MenuHeight - Globals.UserIconFrameOffsetY - self.h),
                self.w, self.h
            )
            self.backimagearea = sub.flip(True)
        else:
            self.backimagearea = backimage.new_subpixbuf(
                int(Globals.UserIconFrameOffsetX),
                int(Globals.UserIconFrameOffsetY),
                self.w, self.h
            )

        # layers & animation state
        self.icons: List[Optional[GdkPixbuf.Pixbuf]] = [None, None, None, None]
        self.iconopacity = [0.0, 0.0, 0.0, 0.0]
        self._steps = [0, 0, 0, 0]
        self._timer = None

        # click opens "About Me"
        self.frame_window.set_tooltip_text(_('About Me'))
        self.frame_window.connect("button-press-event", self._clicked)

    # ---- drawing ----
    def _on_draw_background(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        _draw_pixbuf(cr, self.backimagearea)
        return False

    def _compose(self) -> GdkPixbuf.Pixbuf:
        """Composite background + visible layers into a pixbuf."""
        basepb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, self.w, self.h)
        basepb.fill(0x00000000)

        def blit(src: GdkPixbuf.Pixbuf, dst: GdkPixbuf.Pixbuf, dx: int, dy: int, alpha: int):
            if alpha <= 0:
                return
            # copy with alpha via composite
            src.composite(dst, dx, dy, src.get_width(), src.get_height(),
                          dx, dy, 1.0, 1.0, GdkPixbuf.InterpType.BILINEAR, alpha)

        # 0: frame (full size)
        if self.icons[0]:
            blit(self.icons[0], basepb, 0, 0, int(self.iconopacity[0] * 255))
        # 1: face (draw inset)
        if self.icons[1]:
            blit(self.icons[1], basepb, self.face_x, self.face_y, int(self.iconopacity[1] * 255))
        # 2 & 3: overlays (full size)
        for i in (2, 3):
            if self.icons[i]:
                blit(self.icons[i], basepb, 0, 0, int(self.iconopacity[i] * 255))

        return basepb

    def _redraw(self):
        self.Image.set_from_pixbuf(self._compose())

    # ---- public API expected by Main_Menu ----
    def move(self, x, y):
        self.fixed.move(self.frame_window, int(x), int(y))

    def SetBackground(self):
        self.Image.clear()

    def updateimage(self, layer: int, path_or_pixbuf):
        """Load/assign an image to a layer (0=frame, 1=face, 2/3=overlay)."""
        if isinstance(path_or_pixbuf, str):
            if not os.path.isfile(path_or_pixbuf):
                self.icons[layer] = None
            else:
                pb = GdkPixbuf.Pixbuf.new_from_file(path_or_pixbuf)
                self.icons[layer] = self._scale_for_layer(layer, pb)
        elif isinstance(path_or_pixbuf, GdkPixbuf.Pixbuf):
            self.icons[layer] = self._scale_for_layer(layer, path_or_pixbuf)
        else:
            self.icons[layer] = None
        self._redraw()

    def _scale_for_layer(self, layer: int, pb: GdkPixbuf.Pixbuf) -> GdkPixbuf.Pixbuf:
        if layer == 1:
            # face fits in its inset box
            return pb.scale_simple(self.face_w, self.face_h, GdkPixbuf.InterpType.BILINEAR)
        else:
            # full frame
            return pb.scale_simple(self.w, self.h, GdkPixbuf.InterpType.BILINEAR)

    def transition(self, steps, duration_ms, _easing=None, on_done=None):
        """Fade layers according to steps list: 1=in, -1=out, 0=hold."""
        self._steps = [int(s or 0) for s in steps] + [0, 0, 0, 0]
        self._steps = self._steps[:4]
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = None

        interval = 25  # ms
        total = max(1, int(duration_ms // interval))
        delta = 1.0 / float(total)

        # set targets: in -> towards 1, out -> towards 0
        def tick():
            done = True
            for i, s in enumerate(self._steps):
                if s == 0:
                    continue
                done = False
                if s > 0:
                    self.iconopacity[i] = min(1.0, self.iconopacity[i] + delta)
                    if self.iconopacity[i] >= 1.0:
                        self._steps[i] = 0
                else:
                    self.iconopacity[i] = max(0.0, self.iconopacity[i] - delta)
                    if self.iconopacity[i] <= 0.0:
                        self._steps[i] = 0
            self._redraw()
            if done:
                self._timer = None
                if callable(on_done):
                    try:
                        on_done()
                    except Exception:
                        pass
                return False
            return True

        # start animation
        self._timer = GLib.timeout_add(interval, tick)

    def _clicked(self, *_a):
        os.system(Globals.Settings['User'] + ' &')



# ------------------------- search bars -------------------------

class GtkSearchBar(Gtk.Entry):
    def __init__(self):
        super().__init__()
        # Keep API parity with old code
        self.connect("draw", self._on_draw)

    # no-op to keep compatibility with old `.set_inner_border(None)` calls
    def set_inner_border(self, _b=None):  # noqa: N802 (keep legacy name)
        return

    def _on_draw(self, *_a):
        # Let theme handle drawing; we only keep a hook so the class exists.
        return False


class CairoSearchBar(Gtk.Entry):
    """Simple custom-drawn entry with colored border/background."""
    def __init__(self, BackColor="#FFFFFF", BorderColor="#000000", TextColor="#000000"):
        super().__init__()
        self._rgba_back = Gdk.RGBA()
        self._rgba_border = Gdk.RGBA()
        self._rgba_text = Gdk.RGBA()
        self._rgba_back.parse(BackColor)
        self._rgba_border.parse(BorderColor)
        self._rgba_text.parse(TextColor)
        self.connect("draw", self._on_draw)
        self.override_color(Gtk.StateFlags.NORMAL, self._rgba_text)

    def set_inner_border(self, _b=None):  # compatibility
        return

    def _on_draw(self, widget, cr):
        alloc = self.get_allocation()
        # background
        cr.set_source_rgba(self._rgba_back.red, self._rgba_back.green, self._rgba_back.blue, self._rgba_back.alpha or 1.0)
        cr.rectangle(0, 0, alloc.width, alloc.height)
        cr.fill()
        # border
        cr.set_source_rgba(self._rgba_border.red, self._rgba_border.green, self._rgba_border.blue, self._rgba_border.alpha or 1.0)
        cr.rectangle(0.5, 0.5, alloc.width - 1, alloc.height - 1)
        cr.set_line_width(1.0)
        cr.stroke()
        # let Gtk render the text/caret
        return False


# ------------------------- program lists -------------------------

class TreeProgramList(GObject.GObject):
    __gsignals__ = {
		'activate':      (GObject.SignalFlags.RUN_LAST, None, ()),
		'menu':          (GObject.SignalFlags.RUN_LAST, None, ()),
		'clicked':       (GObject.SignalFlags.RUN_LAST, None, ()),
		'right-clicked': (GObject.SignalFlags.RUN_LAST, None, ()),
	}

    def __init__(self):
        super().__init__()
        self.XDG = XDMateMenu()
        self.XDG.connect('changed', self.menu_callback)

    def menu_callback(self, _event):
        self.Restart('previous')

    def ProgramListPopulate(self, Frame: Gtk.Fixed, Destroyer):
        self.BanFocusSteal = False
        self.Destroyer = Destroyer
        self.Frame = Frame
        self._construct(Frame)
        self.PopulateButtons()

    def _construct(self, Frame):
        self.ScrollFrame = Gtk.ScrolledWindow()
        self.ScrollFrame.set_shadow_type(Gtk.ShadowType.NONE)
        self.ScrollFrame.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.VBoxOut = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.EBox = Gtk.EventBox()
        self.tree = Gtk.TreeView()

        self.render = Gtk.CellRendererPixbuf()
        self.cell1 = Gtk.CellRendererText()
        self.cell1.set_property('ellipsize', Pango.EllipsizeMode.END)
        col1 = Gtk.TreeViewColumn("", self.render, pixbuf=0)
        col2 = Gtk.TreeViewColumn("", self.cell1, text=1)
        self.tree.append_column(col1)
        self.tree.append_column(col2)

        self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.tree.set_model(self.model)
        self.tree.set_headers_visible(False)
        self.tree.connect("key-press-event", self._key)
        self.tree.connect("button-release-event", self._clicked)

        # DnD
        self.tree.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                                           [Gtk.TargetEntry.new('text/uri-list', 0, 0)],
                                           Gdk.DragAction.COPY)
        self.tree.connect("drag-data-get", self._drag_data_get)

        self.ScrollFrame.add(self.tree)
        self.VBoxOut.pack_start(self.ScrollFrame, True, True, 0)
        self.EBox.add(self.VBoxOut)
        Frame.put(self.EBox, Globals.PG_buttonframe[0], Globals.PG_buttonframe[1])
        self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0], Globals.PG_buttonframedimensions[1])

    def _drag_data_get(self, widget, drag_context, selection_data, info, timestamp):
        uri = self._uri_for_index(self._current_index())
        if uri:
            selection_data.set_uris([uri])

    def _current_index(self) -> Optional[int]:
        sel = self.tree.get_selection()
        model, it = sel.get_selected()
        if it:
            return int(model.get_path(it).to_string())
        return None

    def _uri_for_index(self, idx: Optional[int]) -> Optional[str]:
        if idx is None:
            return None
        if self.XDG.allgio is not None:
            for z in self.XDG.allgio:
                if z.get_name() == self.XDG.L_Names[idx]:
                    return f'file:///usr/share/applications/{z.get_id()}'
        name = str(self.XDG.L_Execs[idx]).replace('%F', '').replace('%f', '').replace('%u', '').replace('%U', '')
        if name.startswith('file:/'):
            return name
        if name.startswith('/'):
            return f'file://{name}'
        return f'file:///usr/bin/{name}'

    def _key(self, widget, event):
        key = event.hardware_keycode
        # Enter/Space/Right
        if key in (36, 65, 114):
            self._activate(event)
        # Left
        elif key == 113:
            self.Restart('previous')
        return False

    def _clicked(self, widget, event):
        if event.button == 1:
            self._activate(event)
        elif event.button == 3:
            self.emit('menu')

    def _activate(self, event):
        idx = self._current_index()
        if idx is None:
            return
        a = self.XDG.ButtonClick(idx, event)
        if a == 1:
            self.Destroyer()
        self.PopulateButtons()
        self.emit('clicked')

    def RemoveButtons(self):
        self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.tree.set_model(self.model)

    def PopulateButtons(self):
        self.RemoveButtons()
        for i, name in enumerate(self.XDG.L_Names):
            typ = self.XDG.L_Types[i]
            if typ in (8, 9):  # separators/labels ignored in tree view
                continue
            pb = self.XDG.L_Icons[i] or _pixbuf_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize)
            self.model.insert(i, [pb, name])
        adj = self.ScrollFrame.get_vadjustment()
        adj.set_value(0)

    def CallSpecialMenu(self, command, data=None):
        self.XDG.CallSpecialMenu(command, data)
        self.PopulateButtons()

    def destroy(self):
        self.XDG.destroy()


class IconProgramList(GObject.GObject):
    __gsignals__ = {
        'activate':       (GObject.SignalFlags.RUN_LAST, None, ()),
        'menu':           (GObject.SignalFlags.RUN_LAST, None, ()),
        'clicked':        (GObject.SignalFlags.RUN_LAST, None, ()),
        'right-clicked':  (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.XDG = XDMateMenu()
        self.XDG.connect('changed', self.menu_callback)

    def menu_callback(self, _event):
        self.Restart('previous')

    def ProgramListPopulate(self, Frame: Gtk.Fixed, Destroyer):
        self.BanFocusSteal = False
        self.Destroyer = Destroyer
        self.Frame = Frame
        self._construct(Frame)
        self.PopulateButtons()

    def _construct(self, Frame):
        self.ScrollFrame = Gtk.ScrolledWindow()
        self.ScrollFrame.set_shadow_type(Gtk.ShadowType.NONE)
        self.ScrollFrame.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.VBoxOut = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.EBox = Gtk.EventBox()
        self.view = Gtk.IconView()
        self.view.set_text_column(1)
        self.view.set_pixbuf_column(0)
        self.view.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.view.connect("item-activated", self._item_activated)
        self.view.connect("button-release-event", self._button_release)

        # nicer packing
        self.view.set_margin(0)
        self.view.set_spacing(0)
        try:
            self.view.set_item_padding(0)
        except Exception:
            pass

        # DnD
        self.view.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                                           [Gtk.TargetEntry.new('text/uri-list', 0, 0)],
                                           Gdk.DragAction.COPY)
        self.view.connect("drag-data-get", self._drag_data_get)

        self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.view.set_model(self.model)

        self.ScrollFrame.add(self.view)
        self.VBoxOut.pack_start(self.ScrollFrame, True, True, 0)
        self.EBox.add(self.VBoxOut)
        Frame.put(self.EBox, Globals.PG_buttonframe[0], Globals.PG_buttonframe[1])
        self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0], Globals.PG_buttonframedimensions[1])

    def _drag_data_get(self, widget, drag_context, selection_data, info, timestamp):
        idx = self._current_index()
        if idx is None:
            return
        uri = self._uri_for_index(idx)
        if uri:
            selection_data.set_uris([uri])

    def _uri_for_index(self, idx: int) -> Optional[str]:
        if self.XDG.allgio is not None:
            for z in self.XDG.allgio:
                if z.get_name() == self.XDG.L_Names[idx]:
                    return f'file:///usr/share/applications/{z.get_id()}'
        name = str(self.XDG.L_Execs[idx]).replace('%F', '').replace('%f', '').replace('%u', '').replace('%U', '')
        if name.startswith('file:/'):
            return name
        if name.startswith('/'):
            return f'file://{name}'
        return f'file:///usr/bin/{name}'

    def _current_index(self) -> Optional[int]:
        paths = self.view.get_selected_items()
        if not paths:
            return None
        return int(paths[0].to_string())

    def _button_release(self, widget, event):
        if event.button == 3:
            self.emit('menu')
        return False

    def _item_activated(self, widget, path):
        idx = int(path.to_string())
        a = self.XDG.ButtonClick(idx, None)
        if a == 1:
            self.Destroyer()
        self.PopulateButtons()
        self.emit('clicked')

    def RemoveButtons(self):
        self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.view.set_model(self.model)

    def PopulateButtons(self):
        self.RemoveButtons()
        for i, name in enumerate(self.XDG.L_Names):
            typ = self.XDG.L_Types[i]
            if typ in (8, 9):
                continue
            pb = self.XDG.L_Icons[i] or _pixbuf_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize)
            self.model.insert(i, [pb, name])
        vadj = self.ScrollFrame.get_vadjustment()
        vadj.set_value(0)

    def CallSpecialMenu(self, command, data=None):
        self.XDG.CallSpecialMenu(command, data)
        self.PopulateButtons()

    def destroy(self):
        self.XDG.destroy()


class ProgramList(GObject.GObject):
    __gsignals__ = {
        'activate':       (GObject.SignalFlags.RUN_LAST, None, ()),
        'menu':           (GObject.SignalFlags.RUN_LAST, None, ()),
        'clicked':        (GObject.SignalFlags.RUN_LAST, None, ()),
        'right-clicked':  (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.XDG = XDMateMenu()
        self.XDG.connect('changed', self.menu_callback)
        self.Buttonlist: List[Gtk.Widget] = []

    def menu_callback(self, _event):
        self.Restart('previous')

    def ProgramListPopulate(self, Frame: Gtk.Fixed, Destroyer):
        self.BanFocusSteal = False
        self.Destroyer = Destroyer
        self.Frame = Frame
        self._construct(Frame)
        self.PopulateButtons()

    def _construct(self, Frame):
        self.PrevSelButton = -1
        self.ScrollFrame = Gtk.ScrolledWindow()
        self.ScrollFrame.set_shadow_type(Gtk.ShadowType.NONE)
        self.ScrollFrame.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.VBoxIn = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.VBoxOut = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.VBoxOut.pack_start(self.ScrollFrame, True, True, 0)
        self.ScrollFrame.add(self.VBoxIn)
        self.ScrollFrame.get_children()[0].set_shadow_type(Gtk.ShadowType.NONE)

        Frame.put(self.VBoxOut, Globals.PG_buttonframe[0], Globals.PG_buttonframe[1])
        self.ScrollFrame.set_size_request(Globals.PG_buttonframedimensions[0], Globals.PG_buttonframedimensions[1])

    def update_icons(self, *_a):
        self.XDG.Icon_change()
        self.Restart('previous')

    def Restart(self, data='all'):
        if self.XDG.Restart(data):
            self.PopulateButtons()

    def PopulateButtons(self):
        self.RemoveButtons()
        self.Buttonlist = []
        for i, name in enumerate(self.XDG.L_Names):
            typ = self.XDG.L_Types[i]
            if typ == 8:
                self.AddSeparator()
            elif typ == 9:
                self.AddLabel(name)
            else:
                self.AddButton(name, self.XDG.L_Icons[i], i)
        # focus first child if available
        try:
            self.VBoxIn.get_children()[0].grab_focus()
        except Exception:
            pass
        self.ScrollFrame.get_vadjustment().set_value(0)

    def AddButton(self, name, icon_pb, i):
        btn = Gtk.Button.new_with_label(name)
        img = Gtk.Image.new_from_pixbuf(icon_pb or _pixbuf_from_file_at_size(Globals.BrokenImage, Globals.PG_iconsize, Globals.PG_iconsize))
        btn.set_image(img)
        btn.set_always_show_image(True)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_halign(Gtk.Align.FILL)
        btn.set_valign(Gtk.Align.CENTER)
        btn.set_size_request(Globals.PG_buttonframedimensions[0] - 12, Globals.PG_iconsize + 10)

        # DnD
        btn.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                            [Gtk.TargetEntry.new('text/uri-list', 0, 0)],
                            Gdk.DragAction.COPY)
        btn.connect("drag-data-get", self._drag_data_get, i)
        btn.connect("button-release-event", self._button_released, i)
        btn.connect("key-press-event", self._key, i)

        self.VBoxIn.pack_start(btn, True if Globals.Settings['Prog_List'] == 1 else False,
                               True if Globals.Settings['Prog_List'] == 1 else False, 0)
        btn.show()
        # label tweaks
        try:
            image, label = btn.get_children()[0].get_children()[0].get_children()
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_xalign(0.0)
            label.set_margin_start(5)
        except Exception:
            pass
        self.Buttonlist.append(btn)
        return btn

    def _button_released(self, widget, event, i):
        if event.button == 3:
            self.emit('menu')
            return False
        self._activate(event, i)
        return False

    def _drag_data_get(self, widget, drag_context, selection_data, info, timestamp, i):
        idx = i
        uri = None
        if self.XDG.allgio is not None:
            for z in self.XDG.allgio:
                if z.get_name() == self.XDG.L_Names[idx]:
                    uri = f'file:///usr/share/applications/{z.get_id()}'
                    break
        if uri is None:
            name = str(self.XDG.L_Execs[idx]).replace('%F', '').replace('%f', '').replace('%u', '').replace('%U', '')
            if name.startswith('file:/'):
                uri = name
            elif name.startswith('/'):
                uri = f'file://{name}'
            else:
                uri = f'file:///usr/bin/{name}'
        selection_data.set_uris([uri])

    def AddLabel(self, name):
        lab = Gtk.Label(label=name)
        lab.set_line_wrap(True)
        lab.set_ellipsize(Pango.EllipsizeMode.END)
        self.VBoxOut.pack_start(lab, False, False, 0)
        lab.show()
        self.Buttonlist.append(lab)

    def AddSeparator(self):
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.VBoxIn.pack_start(sep, False, False, 0)
        sep.show()
        self.Buttonlist.append(sep)

    def RemoveButtons(self):
        for child in list(self.VBoxIn.get_children()):
            self.VBoxIn.remove(child)
            child.destroy()
        for child in list(self.VBoxOut.get_children()):
            if child is not self.ScrollFrame:
                self.VBoxOut.remove(child)
                child.destroy()

    def _key(self, widget, event, i):
        key = event.hardware_keycode
        if key in (36, 65):  # Enter/Space
            self._activate(event, i)
        elif key == 113:     # Left
            self.XDG.CallSpecialMenu(0)
            self.PopulateButtons()
        return False

    def _activate(self, event, i):
        self.index = i
        a = self.XDG.ButtonClick(i, event)
        if a == 1:
            self.Destroyer()
        self.PopulateButtons()
        self.emit('clicked')

    def CallSpecialMenu(self, command, data=None):
        self.XDG.CallSpecialMenu(command, data)
        self.PopulateButtons()

    def destroy(self):
        self.XDG.destroy()


# keep cairo available for draw handlers
import cairo  # noqa: E402

"""Archived GTK3 Cairo application-list renderer connected to original XDGMenu.

Adapted from archive/gtk3-revival-2026-11-14 tilomenu/themes/app_list.py.
The original Menu_Items.XDGMenu still owns program discovery, launches,
navigation, search, Favorites and context menus. Gtk.IconView is not used.
"""
import cairo
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GObject, Pango, PangoCairo

import Globals
from Menu_Items import XDGMenu


class ArchivedCairoProgramList(GObject.GObject):
    __gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_LAST, None, ()),
        'menu': (GObject.SignalFlags.RUN_LAST, None, ()),
        'clicked': (GObject.SignalFlags.RUN_LAST, None, ()),
        'right-clicked': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.XDG = XDGMenu()
        self.XDG.connect('changed', self.menu_callback)
        self.BanFocusSteal = False
        self.index = -1
        self.hover = -1
        self.offset = 0
        self.width, self.height = Globals.PG_buttonframedimensions
        self.icon_size = max(16, min(48, int(Globals.PG_iconsize)))
        self.row_height = max(30, self.icon_size + 8)
        self.view = Gtk.DrawingArea()
        self.view.set_size_request(self.width, self.height)
        self.view.set_can_focus(True)
        self.view.set_app_paintable(True)
        self.view.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK |
            Gdk.EventMask.SCROLL_MASK |
            Gdk.EventMask.KEY_PRESS_MASK
        )
        self.view.connect('draw', self._draw)
        self.view.connect('button-press-event', self._button)
        self.view.connect('motion-notify-event', self._motion)
        self.view.connect('leave-notify-event', self._leave)
        self.view.connect('scroll-event', self._scroll)
        self.view.connect('key-press-event', self._key)

    def ProgramListPopulate(self, frame, destroyer):
        self.Destroyer = destroyer
        self.Frame = frame
        frame.put(self.view, *Globals.PG_buttonframe)
        self.view.show()
        self.PopulateButtons()

    def PopulateButtons(self):
        self.offset = 0
        self.hover = -1
        self.index = -1
        self.view.queue_draw()

    def menu_callback(self, event):
        self.Restart('previous')

    def Restart(self, data='all'):
        if self.XDG.Restart(data):
            self.PopulateButtons()

    def CallSpecialMenu(self, command, data=None):
        self.XDG.CallSpecialMenu(command, data)
        self.PopulateButtons()

    def destroy(self):
        self.XDG.destroy()

    def SetFirstButton(self, event):
        if not self.BanFocusSteal:
            self.view.grab_focus()

    def SetLastButton(self, event):
        self.SetFirstButton(event)

    def SetInputFocus(self):
        self.SetFirstButton(None)

    def _visible_count(self):
        return max(1, self.height // self.row_height)

    def _max_offset(self):
        return max(0, len(self.XDG.L_Names) - self._visible_count())

    def _index_at(self, y):
        index = self.offset + int(y // self.row_height)
        return index if 0 <= index < len(self.XDG.L_Names) else None

    def _label(self, cr, value, x, y, width, bright):
        layout = PangoCairo.create_layout(cr)
        layout.set_text(str(value), -1)
        layout.set_font_description(Pango.FontDescription('Sans 9'))
        layout.set_width(max(1, int(width)) * Pango.SCALE)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        cr.move_to(x, y)
        if bright:
            cr.set_source_rgb(0.97, 0.97, 0.97)
        else:
            cr.set_source_rgb(0.09, 0.09, 0.09)
        PangoCairo.show_layout(cr, layout)

    def _draw(self, widget, cr):
        # Direct port of archive ThemeAppList's clipped Cairo painter.
        width = self.width
        height = self.height
        rgba = Gdk.RGBA()
        if not rgba.parse(Globals.ThemeColorHtml):
            rgba.parse('#ffffff')
        bright = (0.2126 * rgba.red + 0.7152 * rgba.green + 0.0722 * rgba.blue) < 0.55
        cr.save()
        cr.rectangle(0, 0, width, height)
        cr.clip()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgb(rgba.red, rgba.green, rgba.blue)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        count = self._visible_count()
        names = self.XDG.L_Names
        for index in range(self.offset, min(len(names), self.offset + count + 1)):
            y = (index - self.offset) * self.row_height
            if index == self.hover:
                cr.set_source_rgba(0.25, 0.47, 0.72, 0.24)
                cr.rectangle(0, y, width - 7, self.row_height)
                cr.fill()
            icon = self.XDG.L_Icons[index]
            text_x = 8
            if icon is not None:
                try:
                    pix = icon
                    if pix.get_width() > self.icon_size or pix.get_height() > self.icon_size:
                        from gi.repository import GdkPixbuf
                        pix = pix.scale_simple(
                            self.icon_size, self.icon_size, GdkPixbuf.InterpType.BILINEAR)
                    Gdk.cairo_set_source_pixbuf(
                        cr, pix, 7, y + (self.row_height - pix.get_height()) / 2)
                    cr.paint()
                    text_x = 14 + self.icon_size
                except Exception:
                    pass
            if self.XDG.L_Types[index] == 9 and '\n' in names[index]:
                # Restore the original three-line Favorites instruction text.
                layout = PangoCairo.create_layout(cr)
                layout.set_text(names[index], -1)
                layout.set_font_description(Pango.FontDescription('Sans 9'))
                layout.set_width(max(1, width - text_x - 14) * Pango.SCALE)
                layout.set_wrap(Pango.WrapMode.WORD_CHAR)
                if bright:
                    cr.set_source_rgb(0.97, 0.97, 0.97)
                else:
                    cr.set_source_rgb(0.09, 0.09, 0.09)
                cr.move_to(text_x, y + 6)
                PangoCairo.show_layout(cr, layout)
            else:
                self._label(
                    cr, names[index].replace('\n', ' '),
                    text_x, y + max(5, (self.row_height - 17) / 2),
                    width - text_x - 14, bright)
        if len(names) > count:
            track = max(1, height - 8)
            bar_h = max(16, track * count / len(names))
            bar_y = 4 + (track - bar_h) * self.offset / max(1, self._max_offset())
            cr.set_source_rgba(0.4, 0.4, 0.4, 0.55)
            cr.rectangle(width - 6, bar_y, 4, bar_h)
            cr.fill()
        cr.restore()
        return False

    def _motion(self, widget, event):
        index = self._index_at(event.y)
        new_hover = index if index is not None else -1
        if new_hover != self.hover:
            self.hover = new_hover
            self.view.queue_draw()
        return False

    def _leave(self, widget, event):
        self.hover = -1
        self.view.queue_draw()
        return False

    def _activate(self, index, event):
        self.index = index
        action = self.XDG.ButtonClick(index, event)
        if event.button == 1:
            if action == 1:
                self.Destroyer()
            self.PopulateButtons()
            self.emit('clicked')
        elif event.button == 3:
            self.emit('right-clicked')

    def _button(self, widget, event):
        if event.button not in (1, 3):
            return False
        index = self._index_at(event.y)
        if index is None:
            return False
        self._activate(index, event)
        return True

    def _key(self, widget, event):
        if event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down):
            step = -1 if event.keyval == Gdk.KEY_Up else 1
            count = len(self.XDG.L_Names)
            if count:
                self.index = max(0, min(count - 1, self.index + step))
                self.hover = self.index
                if self.index < self.offset:
                    self.offset = self.index
                if self.index >= self.offset + self._visible_count():
                    self.offset = self.index - self._visible_count() + 1
                self.view.queue_draw()
            return True
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space):
            if self.index >= 0:
                class Click:
                    button = 1
                    type = Gdk.EventType.KEY_PRESS
                self._activate(self.index, Click())
            return True
        if event.keyval == Gdk.KEY_Left:
            self.Restart('previous')
            return True
        return False

    def _scroll(self, widget, event):
        # Archive behavior: only vertical movement, never a horizontal pane.
        step = 0
        if event.direction == Gdk.ScrollDirection.DOWN:
            step = 3
        elif event.direction == Gdk.ScrollDirection.UP:
            step = -3
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            valid, dx, dy = event.get_scroll_deltas()
            if valid and dy:
                step = 3 if dy > 0 else -3
        if step:
            self.offset = max(0, min(self._max_offset(), self.offset + step))
            self.view.queue_draw()
        return bool(step)

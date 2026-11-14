#!/usr/bin/env python3
#
# This application is released under the GNU General Public License
# v3 (or, at your option, any later version).
#
# (c) QB89Dragon 2007/8 <hughescih@hotmail.com>
# (c) Whise 2008,2009,2010 <helderfraga@gmail.com>
#
# Direct Python 3/GTK 3 port of GnoMenu 2.9.1 src/lib/gnomenu/GnoMenu.py.
# Preserve original methods and events while migrating GNOME 2 Bonobo
# applet registration to MatePanelApplet 4.0. Original menu and settings
# modules have not been ported at this stage.

import subprocess
import sys
import xml.dom.minidom
from pathlib import Path

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('MatePanelApplet', '4.0')
from gi.repository import Gdk, GdkPixbuf, Gtk, MatePanelApplet


name = 'TiloMenu'
APPLET_IID = 'TiloMenuApplet'
FACTORY_IID = 'TiloMenuFactory'
# Source: src/lib/tilomenu -> src/share/tilomenu
# Installed: /usr/lib/tilomenu -> /usr/share/tilomenu
INSTALL_PREFIX = Path(__file__).resolve().parents[2]
ThemeDirectory = INSTALL_PREFIX / 'share' / 'tilomenu' / 'Themes'
ProgramDirectory = Path(__file__).resolve().parent


def start_button_images():
    """Port of Globals.ReloadSettings() Button Background XML loading.

    GnoBlue is the original default until Globals.py is ported.
    Artwork remains byte-for-byte identical to GnoMenu 2.9.1.
    """
    directory = ThemeDirectory / 'Button' / 'GnoBlue'
    document = xml.dom.minidom.parse(str(directory / 'themedata.xml'))
    background = document.getElementsByTagName('Background')[0]
    return tuple(str(directory / background.getAttribute(attribute)) for attribute in (
        'Image', 'ImageHover', 'ImagePressed'
    ))


class TiloMenu:
    # Original: class GnoMenu(gnomeapplet.Applet)
    # As in the original __init__, MATE's factory-provided applet is
    # stored in self.applet rather than creating our own replacement.

    def __init__(self, applet, iid):
        self.panel_size = 24
        self.Button_state = 0  # 0 Normal, 1 Mouse over, 2 Depressed
        self.applet = applet
        self.applet.set_name(name)
        self.remove_applet_border()
        self.panel_id = None
        self.hwg = None  # Original Main_Menu has not yet been ported.
        self.orientation = None
        self.change_orientation()
        self.size = self.get_panel_size()
        self.StartButton = start_button_images()
        self.scale = 1.0

        self.Fixed = Gtk.Fixed()
        self.EBox = Gtk.EventBox()
        self.EBox.set_tooltip_text(name)
        self.Fixed.put(self.EBox, 0, 0)
        self.applet.add(self.Fixed)
        self.EBox.set_border_width(0)
        self.EBox.set_visible_window(False)
        self.Fixed.set_border_width(0)
        self.Image = Gtk.Image()
        self.EBox.add(self.Image)

        self.applet.connect('destroy', self.cleanup)
        self.applet.connect('change-orient', self.change_orientation)
        self.applet.connect('size-allocate', self.size_allocate_event)
        self.applet.connect('map-event', self.map_event)
        self.EBox.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.EBox.connect('button-press-event', self.button_press)
        self.EBox.connect('enter-notify-event', self.select_box)
        self.EBox.connect('leave-notify-event', self.deselect_box)
        self.old_origin = None
        self.oldsize = 0
        self.x, self.y = 0, 0
        self.oldx, self.oldy = 0, 0
        self.aux = None
        self.create_menu()
        self.Redraw_graphics()
        self.applet.show_all()
        self.EBox.set_size_request(-1, self.size)
        self.Fixed.set_size_request(-1, self.size)
        self.Image.set_size_request(-1, self.size)

    def remove_applet_border(self):
        # gtk.rc_parse_string was removed in GTK3.
        css = Gtk.CssProvider()
        css.load_from_data(b'eventbox { padding: 0; border: 0; }')
        self.applet.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self._css = css

    def get_panel_size(self):
        # GNOME 2 GConf panel-size lookup replaced with MATE applet API.
        try:
            return max(16, int(self.applet.get_size()))
        except (AttributeError, ValueError, TypeError):
            return 30

    def change_orientation(self, *args):
        try:
            orient = self.applet.get_orient()
            self.orientation = 'top' if int(orient) == 1 else 'bottom'
        except (AttributeError, TypeError, ValueError):
            self.orientation = 'bottom'
        return True

    def map_event(self, widget, event):
        self.Redraw_graphics()
        # Original: self.hwg = Main_Menu(self.HideMenu)
        # Deferred until src/lib/tilomenu/Menu_Main.py is ported.
        return False

    def size_allocate_event(self, widget, allocation):
        size = self.get_panel_size()
        if size != self.size:
            self.size = size
            self.Redraw_graphics()
        window = widget.get_window()
        if window is not None:
            self.x, self.y = window.get_origin()
        else:
            self.x, self.y = 0, 0
        return False

    def button_press(self, widget, event):
        if event.button == 1:
            # Do not fabricate a popup; restore original ShowMenu/HideMenu
            # logic when porting Menu_Main.py.
            if self.hwg is None:
                return True
            if self.Button_state == 2:
                self.HideMenu()
                self.Button_state = 1
            else:
                self.ShowMenu()
                self.Button_state = 2
            self.Redraw_graphics()
            return True
        if event.button == 3:
            # MATE handles the registered applet context menu.
            return False
        return False

    def create_menu(self):
        # Original: applet.setup_menu(propxml, verbs, None).
        # Modern: applet.setup_menu(xml, Gtk.ActionGroup).
        self.propxml = '''
        <menuitem name="Preferences" action="Props"/>
        <menuitem name="About Item" action="About"/>
        <menuitem name="Edit Menus" action="Edit"/>
        '''
        self.verbs = Gtk.ActionGroup('TiloMenuActions')
        actions = (
            ('Props', 'document-properties', 'Preferences', self.properties),
            ('About', 'help-about', 'About Item', self.about_info),
            ('Edit', 'document-edit', 'Edit Menus', self.edit_menus),
        )
        for key, icon, label, callback in actions:
            action = Gtk.Action(key, label, None, icon)
            action.connect('activate', callback)
            # No fake settings; enable after porting original settings.
            action.set_sensitive(False)
            self.verbs.add_action(action)
        self.applet.setup_menu(self.propxml, self.verbs)

    def properties(self, event, data=None):
        target = ProgramDirectory / 'TiloMenu-Settings.py'
        if target.is_file():
            subprocess.Popen([sys.executable, str(target)], start_new_session=True)

    def about_info(self, event, data=None):
        target = ProgramDirectory / 'TiloMenu-Settings.py'
        if target.is_file():
            subprocess.Popen([sys.executable, str(target), '--about'], start_new_session=True)

    def edit_menus(self, event, data=None):
        # Original invokes MenuEditor configured in Globals.py.
        return None

    def select_box(self, widget, event):
        if self.Button_state == 0:
            self.Button_state = 1
        self.Redraw_graphics()
        return False

    def deselect_box(self, widget, event):
        if self.Button_state == 1:
            self.Button_state = 0
        self.Redraw_graphics()
        return False

    def ShowMenu(self):
        if self.hwg:
            self.hwg.show_window()

    def HideMenu(self):
        if self.hwg:
            self.hwg.hide_window()
        self.Button_state = 0
        self.Redraw_graphics()

    def Redraw_graphics(self):
        self.Fixed.set_size_request(-1, self.size)
        self.EBox.set_size_request(-1, self.size)
        self.Image.set_size_request(-1, self.size)
        im = GdkPixbuf.Pixbuf.new_from_file(self.StartButton[self.Button_state])
        w = im.get_width()
        h = im.get_height()
        self.scale = float(self.size) / float(h)
        pixmap = im.scale_simple(
            max(1, int(w * self.scale)), self.size,
            GdkPixbuf.InterpType.HYPER
        )
        self.Image.set_from_pixbuf(pixmap)

    def cleanup(self, event):
        if self.hwg is not None:
            self.hwg.destroy()
        self.hwg = None


def TiloMenu_factory(applet, iid, data=None):
    if iid != APPLET_IID:
        return False
    TiloMenu(applet, iid)
    return True


def main():
    return MatePanelApplet.Applet.factory_main(
        FACTORY_IID, True, MatePanelApplet.Applet.__gtype__,
        TiloMenu_factory, None
    )


if __name__ == '__main__':
    sys.exit(main())

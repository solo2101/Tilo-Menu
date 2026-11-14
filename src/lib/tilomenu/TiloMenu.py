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

import Globals
from Menu_Main import Main_Menu


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
        self.hwg = None
        self.orientation = None
        self.change_orientation()
        self.size = self.get_panel_size()
        self.StartButton = Globals.StartButton
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
        # The original run-in-window sandbox uses a plain GTK widget.
        if isinstance(self.applet, MatePanelApplet.Applet):
            self.applet.connect('change-orient', self.change_orientation)
        self.applet.connect('size-allocate', self.size_allocate_event)
        self.applet.connect('map-event', self.map_event)
        # Gtk3 maps child widgets synchronously; keep original map-event too.
        self.applet.connect('map', lambda widget: self.map_event(widget, None))
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
        Globals.flip = False if self.orientation == 'top' else None
        return True

    def map_event(self, widget, event):
        # The original GnoMenu constructs the menu when the panel maps.
        self.Redraw_graphics()
        if self.hwg is None:
            self.hwg = Main_Menu(self.HideMenu)
            self.hwg.connect('state-changed', self.button_changed)
        self.hwg.Adjust_Window_Dimensions(self.x, self.y)
        Globals.SavedOriginState = self.x, self.y
        return False

    def size_allocate_event(self, widget, allocation):
        size = self.get_panel_size()
        if size != self.size:
            self.size = size
            self.Redraw_graphics()
        window = widget.get_window()
        if window is not None:
            self.x, self.y = window.get_origin()
            self.update_panel_position()
        else:
            self.x, self.y = 0, 0
        return False

    def update_panel_position(self):
        # Preserve original panel-to-popup repositioning on resize/move.
        if self.x != self.oldx and self.hwg is not None:
            self.hwg.Adjust_Window_Dimensions(self.x, self.y)
            Globals.SavedOriginState = self.x, self.y
            self.oldx = self.x

    def button_press(self, widget, event):
        if event.button == 1:
            if self.hwg is None:
                self.map_event(widget, event)
            self.hwg.Adjust_Window_Dimensions(self.x, self.y)
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
            # Settings uses the original TiloMenu-Settings.py window.
            # The original external MenuEditor remains deferred.
            action.set_sensitive(key in ('Props', 'About'))
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
            window = self.applet.get_window()
            if window is not None:
                origin = window.get_origin()
                if origin != getattr(Globals, 'SavedOriginState', None):
                    self.hwg.Adjust_Window_Dimensions(*origin)
                    Globals.SavedOriginState = origin
            self.hwg.show_window()

    def HideMenu(self):
        if self.hwg:
            self.hwg.hide_window()
        self.Button_state = 0
        self.Redraw_graphics()

    def button_changed(self, event, button, button1):
        # Original Main_Menu's "state-changed" signal resets the orb.
        self.Button_state = button
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


def run_in_window():
    """Port of original GnoMenu.py run-in-window testing sandpit."""
    class StandaloneApplet(Gtk.EventBox):
        def get_orient(self):
            return 1

        def get_size(self):
            return 32

        def setup_menu(self, xml, action_group):
            # Bonobo's GTK2 testing applet had no registered panel context.
            pass

    main_window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    main_window.set_decorated(True)
    main_window.set_title('TiloMenu Testing Sandpit')
    main_window.connect('destroy', Gtk.main_quit)
    applet = StandaloneApplet()
    TiloMenu(applet, '')
    main_window.add(applet)
    main_window.show_all()
    Gtk.main()
    return 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'run-in-window':
        return run_in_window()
    return MatePanelApplet.Applet.factory_main(
        FACTORY_IID, True, MatePanelApplet.Applet.__gtype__,
        TiloMenu_factory, None
    )


if __name__ == '__main__':
    sys.exit(main())

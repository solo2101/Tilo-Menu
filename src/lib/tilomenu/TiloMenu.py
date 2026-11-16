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

import shlex
import shutil
import subprocess
import sys
import xml.dom.minidom
from pathlib import Path

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('MatePanelApplet', '4.0')
from gi.repository import Gdk, GdkPixbuf, Gtk, MatePanelApplet, GLib

import Globals
import backend
from Menu_Main import Main_Menu
from Launcher import resolve_legacy_action


name = 'TiloMenu'
APPLET_IID = 'TiloMenuApplet'
FACTORY_IID = 'TiloMenuFactory'
# Source: src/lib/tilomenu -> src/share/tilomenu
# Installed: /usr/lib/tilomenu -> /usr/share/tilomenu
INSTALL_PREFIX = Path(__file__).resolve().parents[2]
ThemeDirectory = INSTALL_PREFIX / 'share' / 'tilomenu' / 'Themes'
ProgramDirectory = Path(__file__).resolve().parent


def start_button_top_images(theme_name=None):
    """Original GnoMenu Button/Top assets are independent of Background.

    When Top=1 the protruding artwork must be drawn outside the MATE
    panel's allocation. Otherwise GTK clips the upper part of the icon.
    """
    directory = ThemeDirectory / 'Button' / (theme_name or 'GnoBlue')
    xml_path = directory / 'themedata.xml'
    if not xml_path.is_file():
        return None
    document = xml.dom.minidom.parse(str(xml_path))
    theme = document.getElementsByTagName('theme')[0]
    if theme.getAttribute('Top') != '1':
        return None
    top = document.getElementsByTagName('Top')
    if not top:
        return None
    paths = tuple(str(directory / top[0].getAttribute(attribute))
                  for attribute in ('Image', 'ImageHover', 'ImagePressed'))
    return paths if all(Path(path).is_file() for path in paths) else None


def start_button_images(theme_name=None):
    """Port of Globals.ReloadSettings() Button Background XML loading.

    GnoBlue is the original default until Globals.py is ported.
    Artwork remains byte-for-byte identical to GnoMenu 2.9.1.
    """
    directory = ThemeDirectory / 'Button' / (theme_name or 'GnoBlue')
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
        self._button_theme = str(Globals.Settings['Button_Name'])
        self._top_images = start_button_top_images(self._button_theme)
        self._top_window = None
        self._menu_signature = self._current_menu_signature()
        self._settings_refresh_id = None
        self._settings_signal_id = None
        # GSettings writes are emitted by the separate Preferences process.
        # Follow them in the live MATE applet without restarting mate-panel.
        if backend.settings is not None:
            self._settings_signal_id = backend.settings.connect(
                'changed::values', self._settings_changed)
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

    def _settings_changed(self, settings, key):
        # Apply writes many keys in sequence. Debounce and redraw once.
        if self._settings_refresh_id is not None:
            GLib.source_remove(self._settings_refresh_id)
        self._settings_refresh_id = GLib.timeout_add(
            200, self._refresh_applied_settings)

    def _current_menu_signature(self):
        # Orientation changes the original theme geometry and artwork too.
        keys = ('Menu_Name', 'Icon_Name', 'Prog_List', 'IconSize',
                'GtkColors', 'System_Icons', 'TabHover')
        return tuple(backend.load_setting(key) for key in keys) + (self.orientation,)

    def _refresh_applied_settings(self):
        self._settings_refresh_id = None
        self._refresh_button_theme()
        self._refresh_menu_theme()
        return False

    def _refresh_menu_theme(self):
        signature = self._current_menu_signature()
        if signature == self._menu_signature:
            return False

        # Preflight the selected original menu XML before replacing the
        # functioning popup. Never kill or restart the MATE panel.
        selected = signature[0] or 'Menu'
        theme_file = ThemeDirectory / 'Menu' / selected / 'themedata.xml'
        if not theme_file.is_file():
            print('TiloMenu menu theme not applied: missing', theme_file)
            return False
        try:
            xml.dom.minidom.parse(str(theme_file))
            Globals.ReloadSettings(orientation_override=self.orientation)
            replacement = Main_Menu(self.HideMenu)
            replacement.connect('state-changed', self.button_changed)
        except Exception as error:
            print('TiloMenu menu theme refresh failed:', error)
            return False

        previous = self.hwg
        self.hwg = replacement
        self._menu_signature = signature
        if previous is not None:
            previous.window.hide()
            try:
                previous.PGL.destroy()
            except (AttributeError, RuntimeError):
                pass
            previous.window.destroy()
        # A fresh popup stays hidden until its panel button is clicked.
        # Preferences keeps keyboard focus and the panel button stays alive.
        return False

    def _refresh_button_theme(self):
        self._settings_refresh_id = None
        selected = backend.load_setting('Button_Name') or 'GnoBlue'
        if selected == self._button_theme:
            return False
        try:
            images = start_button_images(selected)
            # Verify all states first; leave the working button unchanged
            # when a selected theme is incomplete.
            for image in images:
                if not GdkPixbuf.Pixbuf.get_file_info(image):
                    raise OSError('Invalid button image: ' + image)
        except (OSError, ValueError, IndexError, KeyError) as error:
            print('TiloMenu button theme not applied:', error)
            return False
        self.StartButton = images
        self._button_theme = selected
        self._top_images = start_button_top_images(selected)
        self.Redraw_graphics()
        return False

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
        old_orientation = self.orientation
        try:
            orient = self.applet.get_orient()
            # MatePanelApplet DOWN=1, meaning the panel is at the top.
            self.orientation = 'top' if int(orient) == 1 else 'bottom'
        except (AttributeError, TypeError, ValueError):
            self.orientation = 'bottom'
        if old_orientation != self.orientation:
            Globals.ReloadSettings(orientation_override=self.orientation)
            if self.hwg is not None:
                self._refresh_menu_theme()
        return True

    def map_event(self, widget, event):
        # The original GnoMenu constructs the menu when the panel maps.
        self.Redraw_graphics()
        if self.hwg is None:
            self.hwg = Main_Menu(self.HideMenu)
            self.hwg.connect('state-changed', self.button_changed)
        self.hwg.Adjust_Window_Dimensions(self.x, self.y, self.size)
        self._redraw_button_top()
        Globals.SavedOriginState = self.x, self.y
        return False

    def size_allocate_event(self, widget, allocation):
        size = self.get_panel_size()
        if size != self.size:
            self.size = size
            self.Redraw_graphics()
        window = widget.get_window()
        if window is not None:
            self.x, self.y = window.get_origin()[-2:]
            self.update_panel_position()
            self._position_button_top()
        else:
            self.x, self.y = 0, 0
        return False

    def update_panel_position(self):
        # Preserve original panel-to-popup repositioning on resize/move.
        if self.x != self.oldx and self.hwg is not None:
            self.hwg.Adjust_Window_Dimensions(self.x, self.y, self.size)
            Globals.SavedOriginState = self.x, self.y
            self.oldx = self.x

    def button_press(self, widget, event):
        if event.button == 1:
            if self.hwg is None:
                self.map_event(widget, event)
            self.hwg.Adjust_Window_Dimensions(self.x, self.y, self.size)
            if self.Button_state == 2:
                self.HideMenu()
                self.Button_state = 1
            else:
                self.ShowMenu()
                self.Button_state = 2
            self.Redraw_graphics()
            return True
        if event.button == 3:
            # MATE handles the real panel context menu. The standalone test
            # window offers the same original Preferences/About actions.
            if not isinstance(self.applet, MatePanelApplet.Applet):
                preview = getattr(self.applet, 'preview_menu', None)
                if preview:
                    preview.popup_at_pointer(event)
                    return True
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
            # The original Edit Menus action uses the configured editor.
            # MATE supplies Mozo instead of GNOME 2's Alacarte.
            action.set_sensitive(
                key != 'Edit' or self._menu_editor_command() is not None)
            self.verbs.add_action(action)
        self.applet.setup_menu(self.propxml, self.verbs)

    def properties(self, event, data=None):
        self.launch_settings([])

    def about_info(self, event, data=None):
        self.launch_settings(['--about'])

    def launch_settings(self, arguments):
        # Keep the original separate settings process. The MATE panel starts
        # the applet over D-Bus, where child stderr is otherwise invisible.
        # Retain its output to diagnose GTK3 compatibility failures.
        target = ProgramDirectory / 'TiloMenu-Settings.py'
        logpath = Path.home() / '.cache' / 'tilomenu' / 'settings.log'
        logpath.parent.mkdir(parents=True, exist_ok=True)
        with logpath.open('a', encoding='utf-8') as output:
            output.write('Launching original TiloMenu settings: %s\n' % target)
            output.flush()
            if not target.is_file():
                output.write('ERROR: settings script not installed\n')
                return
            try:
                subprocess.Popen(
                    [sys.executable, str(target)] + arguments,
                    stdout=output, stderr=subprocess.STDOUT,
                    start_new_session=True)
            except OSError as error:
                output.write('ERROR: %s\n' % error)

    def _menu_editor_command(self):
        command = resolve_legacy_action(
            'MenuEditor', Globals.Settings.get('MenuEditor', 'alacarte'))
        try:
            arguments = shlex.split(command)
        except (TypeError, ValueError):
            return None
        return arguments if arguments and shutil.which(arguments[0]) else None

    def edit_menus(self, event, data=None):
        # Preserve the original configured menu editor, with a compatibility
        # lookup for its GNOME 2 default. Only launch when installed.
        arguments = self._menu_editor_command()
        if arguments:
            try:
                subprocess.Popen(arguments, start_new_session=True)
            except OSError as error:
                print('TiloMenu menu editor launch failed:', error)

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
        # Also support the original XML settings fallback when GSettings
        # change notifications are unavailable.
        self._refresh_button_theme()
        self._refresh_menu_theme()
        if self.hwg:
            window = self.applet.get_window()
            if window is not None:
                origin = window.get_origin()[-2:]
                if origin != getattr(Globals, 'SavedOriginState', None):
                    self.hwg.Adjust_Window_Dimensions(*origin, self.size)
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

    def _destroy_button_top(self):
        if self._top_window is not None:
            self._top_window.destroy()
            self._top_window = None

    def _position_button_top(self):
        if self._top_window is None or self._top_images is None:
            return
        pix = self._top_pixbuf
        panel_width = self.Image.get_pixbuf().get_width() if self.Image.get_pixbuf() else pix.get_width()
        # The original GnoMenu renders the extra Top PNG beyond the panel.
        # Align it with the middle of the main button in either orientation.
        x = int(self.x + (panel_width - pix.get_width()) / 2)
        if self.orientation == 'top':
            y = int(self.y + self.size)
        else:
            y = int(self.y - pix.get_height())
        self._top_window.move(x, y)

    def _redraw_button_top(self):
        if self._top_images is None or not isinstance(self.applet, MatePanelApplet.Applet):
            self._destroy_button_top()
            return
        pix = GdkPixbuf.Pixbuf.new_from_file(self._top_images[self.Button_state])
        self._top_pixbuf = pix
        if self._top_window is None:
            top = Gtk.Window(type=Gtk.WindowType.POPUP)
            top.set_decorated(False)
            top.set_accept_focus(False)
            top.set_focus_on_map(False)
            top.set_skip_taskbar_hint(True)
            top.set_skip_pager_hint(True)
            top.set_app_paintable(True)
            screen = top.get_screen()
            visual = screen.get_rgba_visual()
            if visual is not None:
                top.set_visual(visual)
            top.connect('draw', self._draw_button_top)
            self._top_window = top
        self._top_window.set_size_request(pix.get_width(), pix.get_height())
        self._top_window.resize(pix.get_width(), pix.get_height())
        self._position_button_top()
        self._top_window.show_all()
        surface = self._top_window.get_window()
        if surface is not None:
            # The main panel button remains the only clickable surface.
            surface.set_pass_through(True)
        self._top_window.queue_draw()

    def _draw_button_top(self, widget, cr):
        import cairo
        cr.set_operator(cairo.OPERATOR_SOURCE)
        Gdk.cairo_set_source_pixbuf(cr, self._top_pixbuf, 0, 0)
        cr.paint()
        return True

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
        self._redraw_button_top()

    def cleanup(self, event):
        self._destroy_button_top()
        if self._settings_refresh_id is not None:
            GLib.source_remove(self._settings_refresh_id)
            self._settings_refresh_id = None
        if self._settings_signal_id is not None and backend.settings is not None:
            backend.settings.disconnect(self._settings_signal_id)
            self._settings_signal_id = None
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
            # Expose the same action callbacks as the actual MATE panel.
            self.preview_menu = Gtk.Menu()
            for label, name in (('Preferences', 'Props'), ('About', 'About')):
                item = Gtk.MenuItem(label=label)
                item.connect('activate', lambda _item, action=name:
                             action_group.get_action(action).activate())
                self.preview_menu.append(item)
            self.preview_menu.show_all()

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
    if len(sys.argv) == 2 and sys.argv[1] == 'preferences':
        return subprocess.call([sys.executable, str(ProgramDirectory / 'TiloMenu-Settings.py')])
    return MatePanelApplet.Applet.factory_main(
        FACTORY_IID, True, MatePanelApplet.Applet.__gtype__,
        TiloMenu_factory, None
    )


if __name__ == '__main__':
    sys.exit(main())

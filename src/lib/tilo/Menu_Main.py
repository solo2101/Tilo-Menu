#!/usr/bin/env python3
# Menu window (Tilo-Menu, MATE)

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib

import sys
import os
import time
import subprocess

from Menu_Widgets import (
    MenuButton, Separator, ImageFrame, ProgramList, IconProgramList,
    MenuTab, MenuLabel, MenuImage, TreeProgramList
)
import Globals
import utils
import Launcher
import IconFactory

# Optional sound via GStreamer 1.0
has_gst = False
try:
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst
    Gst.init(None)
    has_gst = True
except Exception:
    has_gst = False

try:
    with open("/etc/tilo/prefix", "r") as f:
        INSTALL_PREFIX = f.read().strip() or "/usr"
except Exception:
    INSTALL_PREFIX = "/usr"

import gettext
gettext.textdomain('tilo')
gettext.install('tilo', os.path.join(INSTALL_PREFIX, 'share', 'locale'))
gettext.bindtextdomain('tilo', os.path.join(INSTALL_PREFIX, 'share', 'locale'))

def _(s):
    return gettext.gettext(s)

class Main_Menu(GObject.GObject):
    __gsignals__ = {
        'state-changed': (GObject.SignalFlags.RUN_LAST, None, (int, int)),
    }

    first_time = True

    def __init__(self, hide_method):
        GObject.GObject.__init__(self)
        print('start')
        self.searchitem = ''
        self.hide_method = hide_method

        os.chdir(Globals.HomeDirectory)

        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title('Tilo')
        self.window.set_focus_on_map(True)
        self.window.set_app_paintable(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_decorated(False)
        self.window.set_keep_above(False)
        self.window.stick()
        self.window.set_default_size(Globals.MenuWidth, Globals.MenuHeight)
        try:
            self.window.set_property('has-resize-grip', False)
        except Exception:
            pass

        self.colorpb = None
        self.supports_alpha = True

        self.window.connect("draw", self.on_draw)
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("focus-out-event", self.lose_focus)
        self.window.connect("key-press-event", self.key_down)

        self.gtk_screen = self.window.get_screen()
        self.Launcher = Launcher.Launcher()
        self.Launcher.connect('special-command', self.special_command)

        self.w, self.h = self.window.get_size()
        self.leave_focus = True
        self.callback_search = None
        self.MateMenu = None
        self.visible = False

        self.setup()

    # ===== Special commands =====
    def special_command(self, event):
        self.leave_focus = False
        # Placeholder for MATE menu integration
        self.callback = GLib.timeout_add(1500, self.timeout_callback)

    def MateMenu_unmap(self, event):
        if not self.window.is_active():
            self.emit('state-changed', 0, 0)
            self.hide_window()

    def auxdestroyed(self):
        pass

    def destroy(self):
        self.PGL.destroy()

    def internal_destroy(self, widget, event):
        self.PGL.destroy()

    def ToggleMenu(self):
        print(self.visible)
        if not self.window.get_visible():
            self.emit('state-changed', 2, 2)
            self.show_window()
            self.visible = True
        else:
            if not self.visible:
                self.emit('state-changed', 2, 2)
                self.show_window()
                self.visible = True
            else:
                self.emit('state-changed', 0, 0)
                self.hide_window()
                self.visible = False

    # ===== Window paint =====
    def on_draw(self, widget, cr):
        # Clear with transparent or white
        cr.set_source_rgba(1, 1, 1, 0 if self.supports_alpha else 1)
        # Using Cairo operator requires pycairo; the constant import is implicit
        cr.set_operator(gi.repository.cairo.OPERATOR_SOURCE)
        cr.paint()
        # Background image handled by Gtk.Image placed in setup()
        return False

    # ===== Setup =====
    def setup(self):
        self.menuframe = Gtk.Fixed()
        self.window.add(self.menuframe)

        # Background image buffer
        try:
            self.bgpb = GdkPixbuf.Pixbuf.new_from_file(
                os.path.join(Globals.ImageDirectory, Globals.StartMenuTemplate)
            )
        except Exception:
            self.bgpb = None

        # Place a Gtk.Image as background
        self.background = Gtk.Image()
        if self.bgpb:
            self.background.set_from_pixbuf(self.bgpb)
        self.menuframe.put(self.background, 0, 0)

        w, h = self.window.get_size()
        if w == 0:
            w = 100
        if h == 0:
            h = 100
        self.w = w
        self.h = h

        self.window.set_opacity(0.99)

        # User icon
        if Globals.MenuHasIcon == 1 and self.bgpb:
            self.usericon = ImageFrame(
                Globals.IconW, Globals.IconH,
                Globals.IconInX, Globals.IconInY,
                Globals.IconInW, Globals.IconInH,
                self.menuframe, self.bgpb
            )
            self.usericonstate = 0
            self.LastUserPicName = ""

        # Menu Buttons
        self.MenuButtons = []
        for i in range(0, Globals.MenuButtonCount):
            if Globals.MenuButtonNames[i] == ":SEPARATOR:":
                self.MenuButtons.append(Separator(i, self.menuframe))
            else:
                self.MenuButtons.append(MenuButton(i, self.menuframe, self.bgpb))
                self.MenuButtons[i].Button.connect("enter-notify-event", self.Button_enter, i)
                self.MenuButtons[i].Button.connect("leave-notify-event", self.Button_leave, i)
                self.MenuButtons[i].Button.connect("button-release-event", self.Button_click, i)

        # Menu Labels
        self.MenuLabels = []
        for i in range(0, Globals.MenuLabelCount):
            self.MenuLabels.append(MenuLabel(i, self.menuframe))

        # Program list (CairoProgramList removed; map legacy value to IconProgramList)
        prog_style = Globals.Settings.get('Prog_List', 2)
        if prog_style == 0:
            self.PGL = TreeProgramList()
        elif prog_style in (1, 2):
            self.PGL = ProgramList()
        else:
            # Legacy 3 (Cairo) or any unknown -> icons
            self.PGL = IconProgramList()

        self.PGL.connect('menu', self.menu_callback)
        self.PGL.connect('clicked', self.menu_clicked)
        self.PGL.connect('right-clicked', self.menu_right_clicked)
        self.PGL.ProgramListPopulate(self.menuframe, self.hide_method)

        # Search bar
        if Globals.MenuHasSearch:
            self.prevsearchitem = ""
            widget_type = (Globals.SearchWidget or "").upper()
            if widget_type == "CUSTOM":
                from Menu_Widgets import CustomSearchBar
                try:
                    GObject.type_register(CustomSearchBar)
                except Exception:
                    pass
                self.SearchBar = CustomSearchBar(
                    Globals.ImageDirectory + Globals.SearchBackground if Globals.SearchBackground else None,
                    Globals.SearchInitialText,
                    Globals.SearchTextColor,
                    Globals.SearchX, Globals.SearchY, Globals.SearchW, Globals.SearchH,
                    Globals.SearchIX, Globals.SearchIY,
                    self.bgpb
                )
            elif widget_type == "GTK":
                from Menu_Widgets import GtkSearchBar
                try:
                    GObject.type_register(GtkSearchBar)
                except Exception:
                    pass
                self.SearchBar = GtkSearchBar()
                self.SearchBar.set_text('')
            elif widget_type == "CAIRO":
                # If present, keep using the Cairo-drawn search bar (independent of the old program list)
                from Menu_Widgets import CairoSearchBar
                try:
                    GObject.type_register(CairoSearchBar)
                except Exception:
                    pass
                self.SearchBar = CairoSearchBar(
                    Globals.CairoSearchBackColor,
                    Globals.CairoSearchBorderColor,
                    Globals.CairoSearchTextColor
                )
                self.SearchBar.set_text('')
            else:
                self.SearchBar = None

            if self.SearchBar:
                try:
                    self.SearchBar.set_size_request(Globals.SearchW, Globals.SearchH)
                    self.menuframe.put(self.SearchBar, Globals.SearchX, Globals.SearchY)
                    self.SearchBar.connect_after("key-release-event", self.SearchBarActivate)
                except Exception:
                    print('search init wait')

        # Tabs
        self.MenuTabs = []
        for i in range(0, Globals.MenuTabCount):
            self.MenuTabs.append(MenuTab(i, self.menuframe, self.bgpb))
            if Globals.Settings['TabHover']:
                self.MenuTabs[i].Tab.connect("enter-notify-event", self.Tab_hover, i)
            else:
                self.MenuTabs[i].Tab.connect("enter-notify-event", self.Tab_enter, i)
                self.MenuTabs[i].Tab.connect("leave-notify-event", self.Tab_leave, i)
                self.MenuTabs[i].Tab.connect("button-release-event", self.Tab_click, i)

            if i == 0:
                self.PGL.CallSpecialMenu(Globals.MenuTabCommands[i])
                self.MenuTabs[i].SetSelectedTab(True)
            else:
                self.MenuTabs[i].SetSelectedTab(False)

        # Standalone images
        self.MenuImages = []
        for i in range(0, Globals.MenuImageCount):
            self.MenuImages.append(MenuImage(i, self.menuframe, self.bgpb))

        if has_gst:
            self.StartEngine()

    # ===== Menu list callbacks =====
    def menu_callback(self, event):
        self.leave_focus = False
        if self.leave_focus is False:
            self.callback = GLib.timeout_add(500, self.timeout_callback)

    def menu_clicked(self, event):
        self.PlaySound(2)

    def menu_right_clicked(self, event):
        self.leave_focus = False
        self.callback = GLib.timeout_add(500, self.timeout_callback)

    def Adjust_Window_Dimensions(self, win_x, win_y):
        self.window.move(win_x, win_y)

    def composite_changed(self, widget):
        self.hide_method()
        self.show_window()
        self.shape()

    # ===== Show / hide =====
    def show_window(self):
        print('show')
        self.window.set_keep_above(True)
        if not self.window.get_visible():
            self.window.show_all()
        else:
            try:
                self.window.present_with_time(int(time.time()))
            except Exception:
                self.window.present()
        self.window.set_urgency_hint(True)
        self.window.activate_focus()
        self.ChangeUserPic_Normalise()
        self.PlaySound(0)
        
        focus_first = getattr(self.PGL, "SetFirstButton", None)
        if callable(focus_first):
            focus_first(0)
        else:
            focus_input = getattr(self.PGL, "SetInputFocus", None)
        if callable(focus_input):
            focus_input()
        

    def lose_focus(self, widget, event):
        print('focus lost')
        if self.leave_focus is True:
            self.hide_method()

    def hide_window(self):
        print('hide')
        self.window.hide()
        if Globals.MenuTabCount == 0:
            self.PGL.Restart()
        if Globals.MenuHasSearch and self.SearchBar:
            if self.searchitem != '':
                self.SearchBar.set_text('')
                self.PGL.Restart('previous')
        self.PlaySound(1)

    def key_down(self, widget, event):
        key = event.hardware_keycode
        if key == 9:
            self.hide_method()
        elif key in (98, 104, 102, 100, 36, 116, 111, 113, 114, 23):
            if Globals.MenuHasSearch and self.SearchBar:
                if self.SearchBar.is_focus():
                    if key == 36 and getattr(self.PGL, "XDG", None) and self.PGL.XDG.searchresults != 0:
                        self.PGL.CallSpecialMenu(6)
                        self.hide_method()
                    self.PGL.BanFocusSteal = False
                    self.PGL.SetInputFocus()
            if key == 23:
                for i in range(0, Globals.MenuTabCount):
                    if self.MenuTabs[i].GetSelectedTab():
                        c = i + 1
                        if c > Globals.MenuTabCount - 1:
                            c = 0
                for i in range(0, Globals.MenuTabCount):
                    if i == c:
                        self.MenuTabs[i].SetSelectedTab(True)
                        if Globals.MenuTabSub[i] == 0:
                            self.Launcher.Launch(Globals.MenuTabCommands[i])
                        else:
                            self.PGL.CallSpecialMenu(int(Globals.MenuTabCommands[i]))
                        if Globals.MenuTabClose[i] == 1 and self.leave_focus is True:
                            self.hide_method()
                        if self.leave_focus is False:
                            self.callback = GLib.timeout_add(3000, self.timeout_callback)
                    else:
                        self.MenuTabs[i].SetSelectedTab(False)
                self.PlaySound(3)
            if key == 36:
                self.PlaySound(2)
        else:
            if Globals.MenuHasSearch and self.SearchBar:
                if not self.SearchBar.is_focus():
                    self.SearchBar.grab_focus()
                self.SearchBarActivate()

    # ===== Buttons =====
    def Button_enter(self, widget, event, i):
        self.MenuButtons[i].Setimage(Globals.ImageDirectory + Globals.MenuButtonImage[i])
        if Globals.MenuButtonIconSel[i]:
            self.MenuButtons[i].SetIcon(Globals.ImageDirectory + Globals.MenuButtonIconSel[i])
        try:
            GLib.source_remove(self.timeout_button)
        except Exception:
            pass
        self.timeout_button = GLib.timeout_add(300, self.button_has_entered, widget, event, i)

    def button_has_entered(self, widget, event, i):
        if Globals.MenuButtonExecOnHover[i]:
            self.Button_click(widget, event, i)
        self.UpdateUserImage(i, Globals.MenuCairoIconButton[i])

    def button_has_leave(self, widget, event, i):
        if Globals.MenuHasFade == 1:
            self.LeaveCustomState()

    def Button_leave(self, widget, event, i):
        self.MenuButtons[i].SetBackground()
        if Globals.MenuButtonIcon[i]:
            self.MenuButtons[i].SetIcon(Globals.ImageDirectory + Globals.MenuButtonIcon[i])
        try:
            GLib.source_remove(self.timeout_button)
        except Exception:
            pass
        self.timeout_button = GLib.timeout_add(300, self.button_has_leave, widget, event, i)

    def Button_click(self, widget, event, i):
        if Globals.MenuButtonSub[i] == 0:
            self.Launcher.Launch(Globals.MenuButtonCommands[i])
        else:
            self.PGL.CallSpecialMenu(int(Globals.MenuButtonCommands[i]))
        if Globals.MenuButtonClose[i] == 1 and self.leave_focus is True:
            self.hide_method()
        if self.leave_focus is False:
            self.callback = GLib.timeout_add(3000, self.timeout_callback)
        self.PlaySound(2)

    # ===== Tabs =====
    def Tab_enter(self, widget, event, i):
        try:
            GLib.source_remove(self.timeout_tab)
        except Exception:
            pass
        self.timeout_tab = GLib.timeout_add(300, self.tab_has_entered, widget, event, i)

    def tab_has_entered(self, widget, event, i):
        self.UpdateUserImage(i, Globals.MenuCairoIconTab[i])

    def Tab_leave(self, widget, event, i):
        self.timeout_tab = GLib.timeout_add(300, self.tab_has_leave, widget, event, i)

    def tab_has_leave(self, widget, event, i):
        if Globals.MenuHasFade == 1:
            self.LeaveCustomState()

    def Tab_hover(self, widget, event, i):
        for ii in range(0, Globals.MenuTabCount):
            if i != ii:
                self.MenuTabs[ii].SetSelectedTab(False)
        self.MenuTabs[i].SetSelectedTab(True)
        if Globals.MenuTabSub[i] == 0:
            self.Launcher.Launch(Globals.MenuTabCommands[i])
        else:
            self.PGL.CallSpecialMenu(int(Globals.MenuTabCommands[i]))
        if Globals.MenuTabClose[i] == 1 and self.leave_focus is True:
            self.hide_method()
        if self.leave_focus is False:
            self.callback = GLib.timeout_add(3000, self.timeout_callback)

    def Tab_click(self, widget, event, i):
        for ii in range(0, Globals.MenuTabCount):
            if i != ii:
                self.MenuTabs[ii].SetSelectedTab(False)
        self.MenuTabs[i].SetSelectedTab(True)
        if Globals.MenuTabSub[i] == 0:
            self.Launcher.Launch(Globals.MenuTabCommands[i])
        else:
            self.PGL.CallSpecialMenu(int(Globals.MenuTabCommands[i]))
        if Globals.MenuTabClose[i] == 1 and self.leave_focus is True:
            self.hide_method()
        if self.leave_focus is False:
            self.callback = GLib.timeout_add(3000, self.timeout_callback)
        self.PlaySound(3)

    def timeout_callback(self):
        self.leave_focus = True
        return False

    # ===== User icon =====
    def UpdateUserImage(self, i, image=None):
        if image and Globals.MenuHasIcon == 1 and Globals.MenuHasFade == 1:
            if Globals.Settings['System_Icons']:
                ico = IconFactory.GetSystemIcon(image) or (Globals.IconDirectory + image)
            else:
                ico = Globals.IconDirectory + image

            self.UserPicName = ico
            if self.LastUserPicName != self.UserPicName:
                self.LastUserPicName = self.UserPicName
                if self.usericonstate == 0:
                    self.usericon.updateimage(2, self.UserPicName)
                    self.usericon.transition([-1, -1, 1, -1], Globals.TransitionS, Globals.TransitionQ, None)
                elif self.usericonstate == 1:
                    self.usericon.updateimage(3, self.UserPicName)
                    self.usericon.transition([-1, -1, -1, 1], Globals.TransitionS, Globals.TransitionQ, None)
                elif self.usericonstate == 2:
                    self.usericon.updateimage(2, self.UserPicName)
                    self.usericon.transition([-1, -1, 1, -1], Globals.TransitionS, Globals.TransitionQ, None)
                if self.usericonstate == 1:
                    self.usericonstate = 2
                else:
                    self.usericonstate = 1

    def LeaveCustomState(self):
        if getattr(self, "LastUserPicName", "") != "":
            self.ChangeUserPic_Normalise()

    def ChangeUserPic_Normalise(self):
        if Globals.MenuHasIcon == 1:
            self.usericon.move(Globals.UserIconFrameOffsetX, Globals.UserIconFrameOffsetY)
            self.usericon.updateimage(0, Globals.UserImageFrame)
            self.usericon.updateimage(1, Globals.UserImage)
            self.usericon.transition([1, 1, -1, -1], Globals.TransitionS, Globals.TransitionQ, None)
            self.usericonstate == 0
            self.LastUserPicName = ""

    # ===== Sound =====
    def StartEngine(self):
        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "my-fakesink")
        self.player.set_property("video-sink", fakesink)
        self.player_bus = self.player.get_bus()
        self.player_bus.add_signal_watch()
        self.player_bus.connect('message', self.on_message)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)

    def PlaySound(self, sound):
        if Globals.Settings['Sound_Theme'] == 'None':
            return
        if sound == 0:
            uri = f'file://{INSTALL_PREFIX}/share/tilo/Themes/Sound/{Globals.Settings["Sound_Theme"]}/show-menu.ogg'
        elif sound == 1:
            uri = f'file://{INSTALL_PREFIX}/share/tilo/Themes/Sound/{Globals.Settings["Sound_Theme"]}/hide-menu.ogg'
        elif sound == 2:
            uri = f'file://{INSTALL_PREFIX}/share/tilo/Themes/Sound/{Globals.Settings["Sound_Theme"]}/button-pressed.ogg'
        elif sound == 3:
            uri = f'file://{INSTALL_PREFIX}/share/tilo/Themes/Sound/{Globals.Settings["Sound_Theme"]}/tab-pressed.ogg'
        else:
            return

        if has_gst:
            self.player.set_state(Gst.State.NULL)
            self.player.set_property('uri', uri)
            self.player.set_state(Gst.State.PLAYING)
        else:
            subprocess.Popen(["sh", "-c", f"paplay {uri} || aplay {uri} || true"])

    # ===== Search =====
    def SearchBarActivate(self, widget=None, event=None):
        if not self.SearchBar:
            return
        self.searchitem = self.SearchBar.get_text()
        if getattr(self, "prevsearchitem", "") != self.searchitem:
            self.PGL.BanFocusSteal = True
            self.prevsearchitem = self.searchitem
            if self.callback_search:
                GLib.source_remove(self.callback_search)
            self.callback_search = GLib.timeout_add(500, self.timeout_callback_search)

    def timeout_callback_search(self):
        self.PGL.CallSpecialMenu(5, self.searchitem)
        print('search')
        return False

# Standalone test
def destroy():
    hwg.destroy()
    sys.exit(0)

if __name__ == "__main__":
    hwg = Main_Menu(destroy)
    #hwg.setup()
    hwg.show_window()
    Gtk.main()

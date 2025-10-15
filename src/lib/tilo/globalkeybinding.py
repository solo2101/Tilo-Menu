#!/usr/bin/env python3
# globalkeybinding.py  (safe if Xlib is missing)

import threading
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GObject, GLib

try:
    from Xlib.display import Display
    from Xlib import X
    HAVE_XLIB = True
except Exception:
    HAVE_XLIB = False
    Display = None
    X = None


class GlobalKeyBinding(GObject.GObject, threading.Thread):
    __gsignals__ = {"activate": (GObject.SignalFlags.RUN_LAST, None, ())}

    def __init__(self, key: str):
        GObject.GObject.__init__(self)
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.key = key
        self.keycode = None
        self.modifiers = None
        self.running = False
        self._toggle = True

        self.keymap = Gdk.Keymap.get_default()

        if HAVE_XLIB:
            self.display = Display()
            self.screen = self.display.screen()
            self.root = self.screen.root
            self._map_modifiers()
            self.grab()
        else:
            print("GlobalKeyBinding disabled. python-xlib not installed.")

    def _map_modifiers(self):
        gdk_mods = (
            Gdk.ModifierType.CONTROL_MASK, Gdk.ModifierType.SHIFT_MASK,
            Gdk.ModifierType.MOD1_MASK,  Gdk.ModifierType.MOD2_MASK,
            Gdk.ModifierType.MOD3_MASK,  Gdk.ModifierType.Mod4Mask,
            Gdk.ModifierType.MOD5_MASK,  Gdk.ModifierType.SUPER_MASK,
            Gdk.ModifierType.HYPER_MASK, Gdk.ModifierType.LOCK_MASK,
        )
        self.known_modifiers_mask = 0
        for m in gdk_mods:
            name = Gtk.accelerator_name(0, m)
            if "Mod" not in name:
                self.known_modifiers_mask |= int(m)

    def on_key_changed(self, *args):
        if HAVE_XLIB:
            self.regrab()

    def regrab(self):
        if HAVE_XLIB:
            self.ungrab()
            self.grab()

    def grab(self):
        if not HAVE_XLIB:
            return
        keyval, modifiers = Gtk.accelerator_parse(self.key)
        if not self.key or (not keyval and not modifiers):
            self.keycode = None
            self.modifiers = None
            return
        self.keycode = self.display.keysym_to_keycode(keyval)
        self.modifiers = int(modifiers)
        try:
            self.root.grab_key(self.keycode, X.AnyModifier, True, X.GrabModeAsync, X.GrabModeSync)
            self.display.flush()
        except Exception:
            self.keycode = None

    def ungrab(self):
        if HAVE_XLIB and self.keycode:
            try:
                self.root.ungrab_key(self.keycode, X.AnyModifier, self.root)
                self.display.flush()
            except Exception:
                pass

    def _emit_activate(self):
        if self._toggle:
            self.emit("activate")
            self._toggle = False
        else:
            self._toggle = True
        return False

    def run(self):
        if not HAVE_XLIB:
            return
        self.running = True
        wait_for_release = False
        while self.running:
            event = self.display.next_event()
            if (
                self.keycode
                and event.type == X.KeyPress
                and event.detail == self.keycode
                and not wait_for_release
            ):
                mods = event.state & self.known_modifiers_mask
                if mods == self.modifiers:
                    wait_for_release = True
                    self.display.allow_events(X.AsyncKeyboard, event.time)
                else:
                    self.display.allow_events(X.ReplayKeyboard, event.time)
            elif self.keycode and wait_for_release and event.detail == self.keycode:
                if event.type == X.KeyRelease:
                    wait_for_release = False
                    GLib.idle_add(self._emit_activate)
                self.display.allow_events(X.AsyncKeyboard, event.time)
            else:
                self.display.allow_events(X.ReplayKeyboard, event.time)

    def stop(self):
        self.running = False
        self.ungrab()
        if HAVE_XLIB:
            try:
                self.display.close()
            except Exception:
                pass

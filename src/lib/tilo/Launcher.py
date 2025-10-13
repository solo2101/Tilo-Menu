#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0") 
from gi.repository import GObject

import os
import shlex
import subprocess
from urllib.parse import unquote

import utils
import Globals


_FIELD_CODES = ["%f","%F","%u","%U","%d","%D","%n","%N","%k","%v","%m","%i","%c"]

def _strip_field_codes(cmd: str) -> str:
    for tok in _FIELD_CODES:
        cmd = cmd.replace(tok, "")
    return cmd.strip()

def _spawn(cmd: str):
    try:
        if any(ch in cmd for ch in "|;&><$`*"):
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(shlex.split(cmd))
    except Exception as e:
        print(f"Launcher: failed to run {cmd!r}: {e}")

class Launcher(GObject.GObject):
    __gsignals__ = {
        'special-command': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.MateMenu = None

    def Launch(self, command, tag=0):
        if tag == 0:
            c = self.LookUpCommand(command)
            if c:
                _spawn(c)
        elif tag == 1:
            # Application Exec= line from .desktop
            cmd = _strip_field_codes(command)
            if cmd:
                _spawn(cmd)
        elif tag == 3 or tag == 4:
            # Open files/URIs with default handler
            _spawn(f"xdg-open {shlex.quote(command)}")
        elif tag in (5, 6, 7):
            # Settings/system helpers
            _spawn(command)

    def LookUpCommand(self, command):
        c = command.lower()
        if c == 'home':
            return f"xdg-open {os.path.expanduser('~')}"
        if c == 'network':
            return "xdg-open network:///"
        if c == 'computer':
            return "xdg-open computer:///"
        if c == 'trash':
            return "xdg-open trash:///"

        xdg = utils.xdg_dir(f"XDG_{str(command).upper()}_DIR")
        if xdg is not False:
            return f"xdg-open {unquote(xdg)}"

        for i, action in enumerate(Globals.MenuActions):
            if action == command:
                return Globals.SecurityCheck(f"{Globals.MenuCommands[i]}")

        if ':ALLAPPS:' in command:
            self.emit('special-command')
            return ""

        print(f"{command} - Running custom command")
        return Globals.SecurityCheck(command)

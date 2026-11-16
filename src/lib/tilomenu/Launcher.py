#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) QB89Dragon 2007/8 <hughescih@hotmail.com>
#(c) Whise 2008,2009 <helderfraga@gmail.com>
#
# Menu window
# Part of the GnoMenu

import utils
import Globals
import os
import shlex
import shutil
import subprocess
import urllib.parse as urllib
from gi.repository import GObject as gobject


# Keep the GnoMenu action names and user settings unchanged. Only translate
# the exact legacy defaults when launching them from a modern MATE session.
# First available command wins; custom commands always retain precedence.
_MATE_ACTIONS = {
        'Search': ('mate-search-tool', 'catfish', 'gnome-search-tool'),
        'Control Panel': ('mate-control-center', 'gnome-control-center'),
        'Network Config': ('nm-connection-editor', 'mate-control-center'),
        # Fedora 43 supports Software, PackageKit, and dnfdragora.
        # Prefer graphical tools for ordinary sessions. Some dnfdragora
        # releases exist on Fedora but fail to launch on certain systems.
        'Package Manager': ('gnome-software', 'gpk-application',
                            'dnfdragora', 'synaptic'),
        'Power': ('mate-session-save --shutdown-dialog',),
        'Shutdown': ('mate-session-save --shutdown-dialog',),
        'Lock': ('mate-screensaver-command --lock', 'loginctl lock-session'),
        'Suspend': ('systemctl suspend',),
        'Hibernate': ('systemctl hibernate',),
        'Run': ('mate-panel --run-dialog',),
        'Logout': ('mate-session-save --logout-dialog',),
        'LogoutNow': ('mate-session-save --logout',),
        # MATE's shutdown chooser includes a restart option. Avoid issuing
        # an immediate reboot from a legacy theme command.
        'Restart': ('mate-session-save --shutdown-dialog',),
        'User': ('mate-about-me', 'mate-control-center'),
        'MenuEditor': ('mozo', 'alacarte'),
}

# A few original themes hard-code GNOME 2 binary names in their XML,
# rather than referring to a named action in Globals.MenuActions.
_THEME_COMMANDS = {
        'gnome-terminal': ('mate-terminal', 'gnome-terminal'),
        'gnome-app-install': ('gnome-software', 'gpk-application',
                              'dnfdragora', 'gnome-app-install'),
        # These are literal Exec values in the original Auxiliary page.
        'gnome-about-me': ('mate-about-me', 'mate-control-center'),
        'gnome-appearance-properties': (
                'mate-appearance-properties', 'mate-control-center'),
        'alacarte': ('mozo', 'alacarte'),
        'gnome-screensaver-preferences': (
                'mate-screensaver-preferences', 'mate-control-center'),
        'gnome-system-monitor': ('mate-system-monitor', 'gnome-system-monitor'),
}


def _first_installed(candidates):
        for candidate in candidates:
                try:
                        program = shlex.split(candidate)[0]
                except (ValueError, IndexError):
                        continue
                if shutil.which(program):
                        return candidate
        return None


def resolve_legacy_action(action, configured):
        """Port original commands without overriding user preferences."""
        # XML action labels use spaces, but original preference keys use
        # underscores. Look up the setting key before checking for defaults.
        setting_key = {
                'Control Panel': 'Control_Panel',
                'Package Manager': 'Package_Manager',
                'Network Config': 'Network_Config',
        }.get(action, action)
        original = Globals.DefaultSettings.get(setting_key)
        if original is None or configured != original:
                return configured
        return _first_installed(_MATE_ACTIONS.get(action, ())) or configured


def resolve_theme_command(command):
        """Translate only known retired GNOME 2 theme commands."""
        return _first_installed(_THEME_COMMANDS.get(command, ())) or command


def resolve_legacy_exec(command):
        """Resolve original stored defaults even for application-list rows.

        The old GnoMenu Shutdown page submits values directly as Exec
        commands (tag=1), bypassing LookUpCommand entirely.
        """
        for action in _MATE_ACTIONS:
                setting_key = {
                        'Control Panel': 'Control_Panel',
                        'Package Manager': 'Package_Manager',
                        'Network Config': 'Network_Config',
                }.get(action, action)
                if command == Globals.DefaultSettings.get(setting_key):
                        return resolve_legacy_action(action, command)
        return resolve_theme_command(command)


class Launcher(gobject.GObject):
        __gsignals__ = {
        'special-command': (gobject.SignalFlags.RUN_LAST, None, ()),
        }

        def __init__(self):
                gobject.GObject.__init__(self)
                self.GnomeMenu = None


        def Launch(self,command,tag=0):
                if tag == 0:
                        c = self.LookUpCommand(command)
                        if c != '':
                                os.system(c)
                elif tag == 1:
                        # Shutdown-page entries and Favorites launch through
                        # tag=1 instead of the normal named-action handler.
                        command = resolve_legacy_exec(command)
                        # Original .desktop Exec syntax includes quoted
                        # arguments and placeholders such as %f, %u and %F.
                        # Splitting on spaces breaks both. Preserve shell
                        # quoting, and drop placeholders without a file/URL.
                        try:
                                args = shlex.split(command)
                                args = [value.replace('%%', '%') for value in args
                                        if value not in ('%f', '%F', '%u', '%U',
                                                         '%i', '%c', '%k')]
                                if args:
                                        subprocess.Popen(args, start_new_session=True)
                        except (OSError, ValueError) as error:
                                print('TiloMenu application launch failed:', error)

                elif tag == 3 or tag == 4:
                        try:
                                subprocess.Popen(['xdg-open', command],
                                                 start_new_session=True)
                        except OSError as error:
                                print('TiloMenu open failed:', error)
                elif tag == 5 or tag == 6 or tag == 7:
                        # Original Auxiliary page passes literal GNOME 2
                        # commands directly, bypassing LookUpCommand.
                        command = resolve_legacy_exec(command)
                        try:
                                subprocess.Popen(['/bin/sh', '-c', command],
                                                 start_new_session=True)
                        except OSError as error:
                                print('TiloMenu command failed:', error)


        def LookUpCommand(self,command):
                print(command)
                if command.lower() == 'home':
                        command= os.path.expanduser("~")
                        return 'xdg-open %s &' % shlex.quote(command)
                if command.lower() == 'network':
                        command = "network:///"
                        return 'xdg-open %s &' % command
                elif command.lower() == 'computer':
                        command = "computer:///"
                        return 'xdg-open %s &' % command
                elif command.lower() == 'trash':
                        command = "trash:///"
                        return 'xdg-open %s &' % command
                
                # Respect original XDG user-directory names, including
                # localized folders and paths containing spaces.
                folder = utils.xdg_dir("XDG_%s_DIR" % str(command).upper())
                if folder is not False and folder:
                        return 'xdg-open %s &' % shlex.quote(urllib.unquote(folder))
                if str(command).upper() in (
                        'DESKTOP', 'DOCUMENTS', 'DOWNLOAD', 'MUSIC',
                        'PICTURES', 'PUBLICSHARE', 'TEMPLATES', 'VIDEOS'):
                        if shutil.which('xdg-user-dir'):
                                try:
                                        result = subprocess.run(
                                                ['xdg-user-dir', str(command).upper()],
                                                capture_output=True, text=True,
                                                timeout=2, check=False)
                                        folder = result.stdout.strip()
                                        if result.returncode == 0 and folder and os.path.isdir(folder):
                                                return 'xdg-open %s &' % shlex.quote(folder)
                                except (OSError, subprocess.TimeoutExpired):
                                        pass
                        # Without xdg-user-dirs configuration, open Home
                        # instead of silently invoking an unknown command.
                        return 'xdg-open %s &' % shlex.quote(os.path.expanduser('~'))
                
                for i in range(0,len(Globals.MenuActions)):
                        if Globals.MenuActions[i]==command:
                                return '%s &' % resolve_legacy_action(
                                        command, Globals.MenuCommands[i])
                if command.find(':ALLAPPS:') != -1:

                        self.emit('special-command')
                        return ""
                        
                print("%s - Running custom command" % str(command))
                return Globals.SecurityCheck(
                        '%s &' % resolve_theme_command(command))



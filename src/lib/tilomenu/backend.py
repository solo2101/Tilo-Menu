#!/usr/bin/env python3
#
# This application is released under the GNU General Public License
# v3 (or, at your option, any later version).
#
# (c) Whise 2009 <helderfraga@gmail.com>
#
# backend for saving and loading settings
# Part of the TiloMenu, ported from GnoMenu 2.9.1.
#
# GConf -> GSettings (normally backed by dconf), with original XML fallback.
# Keep save_setting, load_setting, and the mail/browser APIs unchanged.

import os
import xml.dom.minidom

try:
    from gi.repository import Gio, GLib
except ImportError:
    Gio = None
    GLib = None

HomeDirectory = os.path.expanduser("~")
ConfigDirectory = HomeDirectory + '/.tilomenu'
gconf_app_key = '/apps/tilomenu'  # Legacy API variable, no longer used by Gio.
_SCHEMA = 'org.tilomenu'
_VALUES = 'values'


def _gsettings():
    if Gio is None:
        return None
    source = Gio.SettingsSchemaSource.get_default()
    schema = source.lookup(_SCHEMA, True) if source else None
    if schema is None:
        return None
    return Gio.Settings.new_full(schema, None, None)


settings = _gsettings()
BACKEND = 'gsettings' if settings is not None else 'xml'


def _variant(value):
    if isinstance(value, bool):
        return GLib.Variant('i', int(value))
    if isinstance(value, int):
        return GLib.Variant('i', value)
    if isinstance(value, float):
        return GLib.Variant('d', value)
    if isinstance(value, (list, tuple)):
        return GLib.Variant('as', [str(entry) for entry in value])
    return GLib.Variant('s', str(value))


def _xml_file():
    return os.path.join(ConfigDirectory, '.TiloMenu-Settings.xml')


def _xml_load():
    filenames = (
        _xml_file(),
        os.path.join(HomeDirectory, '.gnomenu', '.GnoMenu-Settings.xml'),
    )
    for filename in filenames:
        if not os.path.isfile(filename):
            continue
        try:
            document = xml.dom.minidom.parse(filename)
            nodes = document.getElementsByTagName('settings')
            if nodes:
                return {key: nodes[0].getAttribute(key)
                        for key in nodes[0].attributes.keys()}
        except (OSError, ValueError, xml.dom.DOMException):
            continue
    return {}


def _from_xml(name, value):
    if name == 'favorites':
        if not value or value == '[]':
            return []
        # Original GnoMenu wrote favorites as a Python repr; preserve the
        # representation without running arbitrary data as executable code.
        import ast
        try:
            result = ast.literal_eval(value)
            if isinstance(result, list):
                return result
        except (ValueError, SyntaxError):
            pass
        return [item.strip(" '\"") for item in value.strip('[]').split(',')
                if item.strip(" '\"")]
    try:
        return int(value)
    except (ValueError, TypeError):
        return value


def save_setting(name, value):
    """Original save_setting(name,value) contract, using GSettings/dconf."""
    if not name:
        return
    if BACKEND == 'gsettings':
        # GSettings uses a declared key. A{sv} preserves the original dynamic
        # setting names and int/string/list values without renaming the API.
        old = settings.get_value(_VALUES).unpack()
        values = {key: item if isinstance(item, GLib.Variant) else _variant(item)
                  for key, item in old.items()}
        values[name] = _variant(value)
        settings.set_value(_VALUES, GLib.Variant('a{sv}', values))
    else:
        os.makedirs(ConfigDirectory, exist_ok=True)
        document = xml.dom.minidom.Document()
        root = document.createElement('TiloMenu')
        node = document.createElement('settings')
        old = _xml_load()
        old[name] = str(value)
        for key, item in old.items():
            node.setAttribute(key, item)
        root.appendChild(node)
        document.appendChild(root)
        with open(_xml_file(), 'w', encoding='utf-8') as output:
            document.writexml(output, '', '', '', 'UTF-8')
        document.unlink()


def load_setting(name):
    """Original load_setting(name) contract, including [] for favorites."""
    if BACKEND == 'gsettings':
        stored = settings.get_value(_VALUES).lookup_value(name, None)
        if stored is not None:
            return stored.unpack()
        # Import existing XML settings the first time a setting is requested.
        xml_values = _xml_load()
        if name in xml_values:
            value = _from_xml(name, xml_values[name])
            save_setting(name, value)
            return value
    else:
        values = _xml_load()
        if name in values:
            return _from_xml(name, values[name])
    return [] if name == 'favorites' else None


def get_default_mail_client():
    if Gio is not None:
        app = Gio.AppInfo.get_default_for_uri_scheme('mailto')
        if app:
            return app.get_commandline() or 'xdg-open mailto:'
    return 'xdg-open mailto:'


def get_default_internet_browser():
    if Gio is not None:
        app = Gio.AppInfo.get_default_for_uri_scheme('http')
        if app:
            return app.get_commandline() or 'xdg-open http:'
    return 'xdg-open http:'

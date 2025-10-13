#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License v3 (or later)
# http://www.gnu.org/licenses/gpl.txt
# Backend for saving and loading settings (Tilo)
# Prefers dconf; falls back to XML in ~/.tilo/.Tilo-Settings.xml

import os
import shlex
import subprocess
import ast
from typing import Any, List

HomeDirectory = os.path.expanduser("~")
ConfigDirectory = os.path.join(HomeDirectory, ".tilo")
os.makedirs(ConfigDirectory, exist_ok=True)

# Base path we’ll use in dconf (no schema required)
DCONF_BASE = "/org/tilo/"

def _which(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None

def _run(cmd: str) -> str:
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace").strip()
    except Exception:
        return ""

def _to_gvariant(value: Any) -> str:
    """Serialize a Python value into a GVariant text for dconf write."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # GVariant accepts bare doubles; textual round-trip is fine
        return repr(value)
    if isinstance(value, str):
        # single-quote and escape single quotes/backslashes
        s = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{s}'"
    if isinstance(value, list):
        if all(isinstance(x, (int, float, bool)) for x in value):
            return "[" + ", ".join(_to_gvariant(x) for x in value) + "]"
        # default to array of strings
        return "[" + ", ".join(_to_gvariant(str(x)) for x in value) + "]"
    # fallback to string
    return _to_gvariant(str(value))

def _from_gvariant(text: str) -> Any:
    """Best-effort parse of dconf read output."""
    if text == "" or text is None:
        return None
    t = text.strip()
    if t in ("true", "false"):
        return t == "true"
    if t.startswith("'") and t.endswith("'"):
        # unescape \' and \\  (keep it simple)
        s = t[1:-1]
        s = s.replace("\\'", "'").replace("\\\\", "\\")
        return s
    if t.startswith("[") and t.endswith("]"):
        # Try safe Python literal eval (GVariant text lists are compatible enough)
        try:
            val = ast.literal_eval(t)
            return val
        except Exception:
            # Loose splitter fallback: split by comma and strip quotes/spaces
            inner = t[1:-1].strip()
            if not inner:
                return []
            parts = [p.strip() for p in inner.split(",")]
            parts = [p[1:-1] if len(p) >= 2 and p[0] in ("'", '"') and p[-1] == p[0] else p for p in parts]
            return parts
    # number?
    try:
        if "." in t:
            return float(t)
        return int(t)
    except Exception:
        return t

# Decide backend
if _which("dconf"):
    BACKEND = "dconf"
    print("backend.py: using dconf backend")
else:
    BACKEND = "xml"
    print("backend.py: using xml backend")

# ---------------------- dconf backend ----------------------

def _dconf_write(key: str, value: Any) -> None:
    path = DCONF_BASE + key
    gvar = _to_gvariant(value)
    _run(f"dconf write {shlex.quote(path)} {shlex.quote(gvar)}")

def _dconf_read(key: str) -> Any:
    path = DCONF_BASE + key
    out = _run(f"dconf read {shlex.quote(path)}")
    return _from_gvariant(out)

# ---------------------- xml backend ----------------------

_XML_FILE = os.path.join(ConfigDirectory, ".Tilo-Settings.xml")

def _xml_load_dom():
    import xml.dom.minidom as minidom
    if os.path.isfile(_XML_FILE):
        try:
            return minidom.parse(_XML_FILE)
        except Exception:
            # corrupt file: start fresh
            pass
    doc = minidom.Document()
    base = doc.createElement("Tilo")
    doc.appendChild(base)
    return doc

def _xml_save_dom(doc) -> None:
    with open(_XML_FILE, "w", encoding="utf-8") as f:
        doc.writexml(f, "    ", "", "", "UTF-8")

def _xml_save(name: str, value: Any) -> None:
    if not name:
        return
    doc = _xml_load_dom()
    base = doc.getElementsByTagName("Tilo")[0]
    nodes = base.getElementsByTagName("settings")
    node = nodes[0] if nodes else doc.createElement("settings")
    # Store as string; keep lists as Python-like text for compatibility
    node.setAttribute(name, repr(value) if isinstance(value, list) else str(value))
    if not nodes:
        base.appendChild(node)
    _xml_save_dom(doc)

def _xml_load(name: str) -> Any:
    if not os.path.isfile(_XML_FILE):
        return None
    import xml.dom.minidom as minidom
    try:
        doc = minidom.parse(_XML_FILE)
        base = doc.getElementsByTagName("Tilo")[0]
        node = base.getElementsByTagName("settings")[0]
        if node.hasAttribute(name):
            raw = node.getAttribute(name)
            # Favorites historically stored as list-ish text. Try to parse.
            if raw == "" and name == "favorites":
                return []
            # Try int -> float -> literal list -> string
            try:
                return int(raw)
            except Exception:
                try:
                    return float(raw)
                except Exception:
                    if raw.startswith("[") and raw.endswith("]"):
                        try:
                            return ast.literal_eval(raw)
                        except Exception:
                            # very old format: try manual
                            inner = raw.strip()[1:-1].strip()
                            return [] if not inner else [p.strip().strip("'\"") for p in inner.split(",")]
                    return raw
    except Exception:
        pass
    return [] if name == "favorites" else None

# ---------------------- public api ----------------------

def save_setting(name: str, value: Any) -> None:
    if BACKEND == "dconf":
        _dconf_write(name, value)
    else:
        _xml_save(name, value)

def load_setting(name: str) -> Any:
    if BACKEND == "dconf":
        val = _dconf_read(name)
        if val is None and name == "favorites":
            return []
        return val
    else:
        val = _xml_load(name)
        if val is None and name == "favorites":
            return []
        return val

# ---------------------- helpers for system handlers ----------------------

def get_default_mail_client() -> str:
    """
    Return a command to open mailto links.
    Prefer desktop tools; fall back to xdg-open.
    """
    # xdg-email is purpose-built for mailto:
    if _which("xdg-email"):
        return "xdg-email"
    # Fallback — xdg-open understands mailto: too
    return "xdg-open mailto:"

def get_default_internet_browser() -> str:
    """
    Return a command to open http links.
    Prefer xdg-open (lets the desktop choose).
    """
    return "xdg-open http:"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) Whise 2008–2009; modernized for Python 3 / GTK3
#
# Bookmarks helper for Tilo/GnoMenu:
#  - Chromium/Chrome JSON
#  - Firefox JSON (new) + sqlite (fallback)
#  - Opera legacy .adr
#  - Epiphany RDF, XBEL (Konqueror/Galeon/Midori)
#
# Returns rows like: [title, url, description, icon_or_path]

import os
import stat
import re
import base64
import json
import sqlite3 as sqlite
import configparser
from functools import reduce

# GI is optional here—only used if we ever build pixbufs locally
try:
    import gi
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf  # noqa: F401
except Exception:
    GdkPixbuf = None  # graceful fallback

# Optional XML bits (Epiphany, XBEL)
try:
    import xml.sax
    XML_SAX_ENABLED = True
except Exception:
    XML_SAX_ENABLED = False

# Optional HTML parser (very old Firefox)
try:
    from html.parser import HTMLParser
    HTMLPARSER_ENABLED = True
except Exception:
    HTMLPARSER_ENABLED = False

import backend  # project-local


# ------------------------ Data Model ------------------------

class Node:
    def __init__(self, parent, data):
        self.data = data
        self.parent = parent
        self.children = []

    def append(self, data):
        return self.append_node(Node(self, data))

    def append_node(self, node):
        self.children.append(node)
        return node

    def up(self):
        return self.parent

    def down(self):
        return self.children[0] if self.children else None

    def next(self):
        if self.parent is None:
            return None
        siblings = self.parent.children
        i = siblings.index(self) + 1
        return siblings[i] if i < len(siblings) else None

    # callback(node, user_data) -> next_user_data
    def traverse(self, callback, user_data):
        for n in self.children:
            d = callback(n, user_data)
            n.traverse(callback, d)


class Root(Node):
    def __init__(self):
        super().__init__(None, None)


def old_tree_format_to_new(old_tree, old_favicons, parent=None):
    new_tree = parent if parent is not None else Root()
    for (name, href_or_folder) in old_tree:
        node = Node(new_tree, None)
        if name is None:
            bookmark = None
        else:
            favicon = None
            if isinstance(href_or_folder, list):
                old_tree_format_to_new(href_or_folder, old_favicons, node)
                href = None
            else:
                href = href_or_folder
                if old_favicons is not None and href in old_favicons:
                    favicon = old_favicons[href]
            bookmark = Bookmark(href, name, None, favicon)
        node.data = bookmark
        new_tree.append_node(node)
    return new_tree


class Bookmark:
    def __init__(self, url, title, description, favicon):
        self.url = url
        self.title = title
        self.description = description
        self.favicon = favicon  # path or themed icon name (string)


class BrowserSupport:
    def isBrowser(self, browser):  # str -> bool
        raise NotImplementedError
    def icon(self): return None
    def isFunctional(self): return True
    def requiredModule(self): return None
    def bookmarksFilename(self, browser):  # str -> path or None
        raise NotImplementedError
    def editorCmd(self): return None
    def editorLabel(self): return None
    def editorIcon(self): return None
    def createTree(self, filename):  # path -> Root
        raise NotImplementedError


browsers_supported = []

# ------------------------ Opera (ADR) ------------------------

BOOKMARKS_FILE = "bookmarks.adr"

def _opera_bookmarks():
    home = os.path.expanduser("~/.opera/")
    path = os.path.join(home, BOOKMARKS_FILE)
    if not os.path.exists(path):
        return []
    import codecs
    out = []
    with codecs.open(path, "r", "utf-8", errors="ignore") as f:
        name = url = None
        for raw in f:
            line = raw.strip()
            if line.startswith("NAME="):
                name = line[5:]
            elif line.startswith("URL="):
                url = line[4:]
            elif line.startswith("#"):
                if name and url:
                    out.append([name, url])
                name = url = None
        if name and url:
            out.append([name, url])
    return out


class OperaBookmarksParser(BrowserSupport):
    def __init__(self):
        self._adr = os.path.join(os.path.expanduser("~/.opera/"), BOOKMARKS_FILE)

    def isBrowser(self, browser):
        return ("opera" in browser) and os.path.exists(self._adr)

    def icon(self): return "opera"
    def requiredModule(self): return "codecs"

    def bookmarksFilename(self, _browser):
        return self._adr

    def editorLabel(self): return "Organize Bookmarks..."

    def createTree(self, _filename):
        root = Root()
        for title, url in _opera_bookmarks():
            root.append(Bookmark(url, title, None, None))
        return root

browsers_supported.append(OperaBookmarksParser())

# ------------------------ Chromium / Chrome ------------------------

def _chromium_profile_file(name):
    base = os.path.expanduser("~/.config/chromium/Default/")
    if os.path.exists(base):
        return os.path.join(base, name)
    # Google Chrome (stable) fallback
    base = os.path.expanduser("~/.config/google-chrome/Default/")
    if os.path.exists(base):
        return os.path.join(base, name)
    return None


def _chromium_bookmarks(bookmarks_file):
    if not bookmarks_file or not os.path.exists(bookmarks_file):
        return []

    with open(bookmarks_file, "r", encoding="utf-8", errors="ignore") as f:
        root = json.load(f)

    def is_container(ch): return ch.get("type") == "folder"
    def is_bookmark(ch):  return "url" in ch
    def is_good(ch):
        scheme = ch["url"].split(":", 1)[0].lower()
        return scheme not in ("data", "place", "javascript")

    items = []
    for key in ("bookmark_bar", "other", "synced"):
        node = root.get("roots", {}).get(key, {})
        if node:
            items.extend(node.get("children", []))

    out = {}
    stack = list(items)
    while stack:
        it = stack.pop()
        if is_bookmark(it) and is_good(it):
            out[it["id"]] = it
        if is_container(it):
            stack.extend(it.get("children", []))

    # return list of dicts with 'name' and 'url'
    return list(out.values())


class ChromiumBookmarksParser(BrowserSupport):
    def isBrowser(self, browser):
        return (("chromium" in browser) or ("google-chrome" in browser)) and \
               os.path.exists(_chromium_profile_file("Bookmarks") or "")

    def icon(self): return "chromium-browser"
    def requiredModule(self): return "json"

    def bookmarksFilename(self, _browser):
        return _chromium_profile_file("Bookmarks")

    def editorLabel(self): return "Organize Bookmarks..."

    def createTree(self, _filename):
        root = Root()
        for x in _chromium_bookmarks(_chromium_profile_file("Bookmarks")):
            root.append(Bookmark(x["url"], x.get("name") or x["url"], None, None))
        return root

browsers_supported.append(ChromiumBookmarksParser())

# ------------------------ Firefox (JSON + sqlite fallback) ------------------------

def _firefox_profile_file(needed_file):
    # Try multiple base dirs (legacy naming first, then modern)
    candidates = [
        "~/.mozilla/firefox-3/",
        "~/.mozilla/firefox-3.9/",
        "~/.mozilla/firefox-3.8/",
        "~/.mozilla/firefox-3.7/",
        "~/.mozilla/firefox-3.6/",
        "~/.mozilla/firefox-3.5/",
        "~/.mozilla/firefox/",
    ]
    firefox_dir = None
    for base in (os.path.expanduser(p) for p in candidates):
        if os.path.exists(base):
            firefox_dir = base
            break
    if not firefox_dir:
        return None

    cfg = configparser.RawConfigParser({"Default": "0"})
    cfg.read(os.path.join(firefox_dir, "profiles.ini"))

    path = None
    for sec in cfg.sections():
        if cfg.has_option(sec, "Default") and cfg.get(sec, "Default") == "1":
            path = cfg.get(sec, "Path")
            break
        elif path is None and cfg.has_option(sec, "Path"):
            path = cfg.get(sec, "Path")

    if path is None:
        return None

    if path.startswith("/"):
        return os.path.join(path, needed_file)
    return os.path.join(firefox_dir, path, needed_file)


def _firefox_bookmarks_json(json_file):
    if not json_file or not os.path.exists(json_file):
        return []

    with open(json_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Some historic dumps had a trailing comma; be forgiving.
    try:
        root = json.loads(content)
    except Exception:
        content = content.replace(",]}", "]}")
        root = json.loads(content)

    # Helpers
    MOZ_CONTAINER = "text/x-moz-place-container"
    MOZ_PLACE = "text/x-moz-place"
    BAD = ("data", "place", "javascript")

    def is_container(ch): return ch.get("type") == MOZ_CONTAINER
    def is_bookmark(ch):  return ch.get("type") == MOZ_PLACE and ch.get("uri")
    def is_good(ch):      return ch.get("uri", "").split(":", 1)[0].lower() not in BAD

    # Collect top-level and tags
    catalogs, tagcatalogs = [], []
    for child in root.get("children", []):
        if child.get("root") == "tagsFolder":
            tagcatalogs.extend(child.get("children", []))
        elif child.get("root"):
            catalogs.append(child)

    out = {}
    visited = set()
    while catalogs:
        nxt = catalogs.pop()
        _id = nxt.get("id")
        if _id in visited:
            continue
        for ch in nxt.get("children", []):
            if is_container(ch):
                catalogs.append(ch)
                tagcatalogs.append(ch)
            elif is_bookmark(ch) and is_good(ch):
                out[ch["id"]] = ch
        visited.add(_id)

    # tag folders
    for tag in tagcatalogs:
        for bmark in tag.get("children", []):
            if is_bookmark(bmark) and is_good(bmark):
                out[bmark["id"]] = bmark

    # Return simplified dicts: title, uri
    return [{"title": b.get("title") or b.get("uri"), "uri": b["uri"]} for b in out.values()]


def _firefox_profile_dir():
    firefox_dir = os.path.expanduser("~/.mozilla/firefox/")
    profiles = os.path.join(firefox_dir, "profiles.ini")
    if not os.path.exists(profiles):
        return None
    cfg = configparser.RawConfigParser()
    cfg.read(profiles)
    for sec in cfg.sections():
        if cfg.has_option(sec, "Path"):
            p = cfg.get(sec, "Path")
            return p if p.startswith("/") else os.path.join(firefox_dir, p)
    return None


class FirefoxJsonBookmarks(BrowserSupport):
    def isBrowser(self, browser):
        return "firefox" in browser and os.path.exists(self.bookmarksFilename(browser) or "")

    def icon(self): return "firefox"
    def requiredModule(self): return "json"

    def bookmarksFilename(self, _browser):
        backups = _firefox_profile_file("bookmarkbackups")
        if not backups or not os.path.isdir(backups):
            return None
        files = sorted(os.listdir(backups))
        if not files:
            return None
        return os.path.join(backups, files[-1])

    def editorCmd(self):
        return "firefox -chrome chrome://browser/content/places/places.xul"

    def editorLabel(self):
        return "Organize Bookmarks..."

    def createTree(self, filename):
        root = Root()
        for x in _firefox_bookmarks_json(filename):
            root.append(Bookmark(x["uri"], x["title"], None, None))
        return root


class FirefoxSqliteBookmarks(BrowserSupport):
    """Fallback when JSON isn’t available; requires Firefox not running."""
    def isBrowser(self, browser):
        return "firefox" in browser and os.path.exists(self.bookmarksFilename(browser) or "")

    def icon(self): return "firefox"
    def requiredModule(self): return "sqlite3"

    def bookmarksFilename(self, _browser):
        d = _firefox_profile_dir()
        return os.path.join(d, "places.sqlite") if d else None

    def editorCmd(self):
        return "firefox -chrome chrome://browser/content/places/places.xul"

    def editorLabel(self):
        return "Organize Bookmarks..."

    def createTree(self, filename):
        root = Root()

        def create_children(conn, parent_node, parent_id):
            cur = conn.cursor()
            cur.execute("SELECT title, id, fk, parent FROM moz_bookmarks WHERE parent = ? ORDER BY position", (parent_id,))
            for title, _id, fk, _parent in cur.fetchall():
                url = None
                if fk is not None:
                    c2 = conn.cursor()
                    c2.execute("SELECT url FROM moz_places WHERE id = ?", (fk,))
                    row = c2.fetchone()
                    if row:
                        url = row[0]
                if title is None:
                    title = "<>"
                node = Node(parent_node, Bookmark(url, title, None, None))
                parent_node.append_node(node)
                if fk is None:
                    create_children(conn, node, _id)

        try:
            conn = sqlite.connect(filename, timeout=0.5)
            create_children(conn, root, 2)
            conn.close()
        except sqlite.OperationalError as error:
            # If locked (Firefox running), keep old tree if any, else show a stub
            root.append(Bookmark("", f"Error: firefox running, bookmarks locked\nDetails: {error}", None, None))
        return root


# pick JSON if we can, else sqlite
_ff_json = FirefoxJsonBookmarks()
if _ff_json.bookmarksFilename("firefox"):
    browsers_supported.append(_ff_json)
else:
    browsers_supported.append(FirefoxSqliteBookmarks())

# ------------------------ Epiphany (RDF) ------------------------

class EpiphanyFormatBookmarksParser(BrowserSupport):
    def isBrowser(self, browser):
        return ("epiphany" in browser)

    def icon(self): return "epiphany"
    def isFunctional(self): return XML_SAX_ENABLED
    def requiredModule(self): return "python-xml"

    def bookmarksFilename(self, _browser):
        return os.path.expanduser("~/.mate2/epiphany/bookmarks.rdf")

    def editorCmd(self): return "epiphany --bookmarks-editor"
    def editorLabel(self): return "Edit Bookmarks..."
    def editorIcon(self): return "/usr/share/epiphany/icons/hicolor/16x16/actions/bookmark-view.png"

    def createTree(self, filename):
        if not XML_SAX_ENABLED:
            return Root()

        class Parser(xml.sax.ContentHandler):
            def __init__(self, bookmarks_file_name):
                super().__init__()
                self.subjects = {}
                self.bookmarks_with_no_subjects = []
                self.chars = ""
                self.title = None
                self.href = None
                self.root_menu = []
                parser = xml.sax.make_parser()
                parser.setContentHandler(self)
                if bookmarks_file_name and os.path.exists(bookmarks_file_name):
                    parser.parse(bookmarks_file_name)

            def startElement(self, name, attrs):
                self.chars = ""
                if name == "item":
                    self.title = None
                    self.href = None
                    self.no_subject = True

            def endElement(self, name):
                if name == "title":
                    self.title = self.chars
                elif name == "link":
                    if self.href is None:
                        self.href = self.chars
                elif name == "ephy:smartlink":
                    self.href = self.chars
                elif name == "dc:subject":
                    self.no_subject = False
                    s = self.chars
                    self.subjects.setdefault(s, []).append((self.title, self.href))
                elif name == "item":
                    if self.no_subject:
                        self.bookmarks_with_no_subjects.append((self.title, self.href))

            def characters(self, chars):
                self.chars += chars

            def endDocument(self):
                self.root_menu = []
                create_menu(self.root_menu, True, list(self.subjects.items()), self.bookmarks_with_no_subjects)

        def create_menu(menu, toplevel, topics, uncategorized):
            remaining = set(uncategorized)
            for _topic, bms in topics:
                remaining |= set(bms)
            unused = [(len(bookmarks), topic, bookmarks) for topic, bookmarks in topics]
            menu_divs = [[]]
            menu_divs_named = []

            while True:
                unused = [(l, t, b) for (l, t, b) in unused if l != 0]
                unused.sort()
                if not unused:
                    break
                l, topic, bookmarks = unused.pop()
                if toplevel or (len(bookmarks) > 6 and len(remaining) > 20):
                    submenu = []
                    menu_divs[0].append((topic, submenu))
                    subtopics = []
                    subuncat = set(bookmarks)
                    for topic2, bookmarks2 in topics:
                        if topic2 is topic:
                            continue
                        inter = set(bookmarks).intersection(bookmarks2)
                        if not inter:
                            continue
                        subuncat -= inter
                        subtopics.append((topic2, list(inter)))
                    create_menu(submenu, False, subtopics, list(subuncat))
                else:
                    menu_divs_named.append((topic, bookmarks))
                remaining -= set(bookmarks)
                unused = [(len(remaining.intersection(bookmarks)), t, bookmarks) for (_l, t, bookmarks) in unused]

            if menu_divs_named:
                menu_divs_named.sort(key=lambda x: x[0].lower())
                menu_divs.extend([b for (_t, b) in menu_divs_named])
            menu_divs.append(uncategorized)

            for division in menu_divs:
                if division:
                    if menu and menu[-1] and not toplevel:
                        menu.append(None)
                    division.sort(key=lambda x: (x[0] or "").lower())
                    menu.extend(division)

        p = Parser(self.bookmarksFilename(None))
        old_tree = p.root_menu
        # No reliable favicon map here
        return old_tree_format_to_new(old_tree, None)

browsers_supported.append(EpiphanyFormatBookmarksParser())

# ------------------------ XBEL (Konqueror / Galeon / Midori) ------------------------

class XbelFormatBookmarksParser(BrowserSupport):
    def isBrowser(self, browser):
        if "konqueror" in browser:
            self.bookmarks_file = os.path.expanduser("~/.kde/share/apps/konqueror/bookmarks.xml")
            return True
        elif "midori" in browser:
            self.bookmarks_file = os.path.expanduser("~/.config/midori/bookmarks.xbel")
            return True
        elif "galeon" in browser:
            self.bookmarks_file = os.path.expanduser("~/.galeon/bookmarks.xbel")
            return True
        return False

    def icon(self): return "konqueror"
    def isFunctional(self): return XML_SAX_ENABLED
    def requiredModule(self): return "python-xml"
    def bookmarksFilename(self, _browser): return getattr(self, "bookmarks_file", None)
    def editorCmd(self): return "keditbookmarks"
    def editorLabel(self): return "Edit Bookmarks"

    def createTree(self, filename):
        if not XML_SAX_ENABLED:
            return Root()

        class Parser(xml.sax.ContentHandler):
            def __init__(self, bookmarks_file_name):
                super().__init__()
                self.root_menu = []
                self.currently_in_bookmark = False
                self.currently_in_folder = False
                self.currently_in_smarturl = False
                self.currently_in_title = False
                self.title = ""
                self.current_bookmark_name = None
                self.current_bookmark_href = None
                self.current_folder = self.root_menu
                self.folder_stack = [self.root_menu]
                parser = xml.sax.make_parser()
                parser.setContentHandler(self)
                if bookmarks_file_name and os.path.exists(bookmarks_file_name):
                    parser.parse(bookmarks_file_name)

            def startElement(self, name, attrs):
                if name == "folder":
                    self.currently_in_folder = True
                elif name == "bookmark":
                    self.currently_in_bookmark = True
                    self.current_bookmark_href = attrs["href"] if "href" in attrs else ""
                elif name == "smarturl":
                    self.currently_in_smarturl = True
                    self.current_bookmark_href = ""
                elif name == "title":
                    self.currently_in_title = True
                    self.title = ""

            def endElement(self, name):
                if name == "folder":
                    self.folder_stack.pop()
                    self.currently_in_folder = False
                if name == "separator":
                    self.folder_stack[-1].append((None, None))
                elif name == "bookmark":
                    self.folder_stack[-1].append((self.current_bookmark_name, self.current_bookmark_href))
                    self.currently_in_bookmark = False
                    self.current_bookmark_name = None
                    self.current_bookmark_href = None
                elif name == "smarturl":
                    self.currently_in_smarturl = False
                elif name == "title":
                    if self.currently_in_bookmark:
                        self.current_bookmark_name = self.title
                    elif self.currently_in_folder:
                        f = []
                        self.folder_stack[-1].append((self.title, f))
                        self.folder_stack.append(f)
                    self.currently_in_title = False

            def characters(self, chars):
                if self.currently_in_title:
                    self.title += chars
                elif self.currently_in_smarturl:
                    self.current_bookmark_href += chars

        old_tree = Parser(filename).root_menu
        return old_tree_format_to_new(old_tree, None)

browsers_supported.append(XbelFormatBookmarksParser())


# ------------------------ Wrapper API ------------------------

browser_cmd = backend.get_default_internet_browser()

class BookmarksMenu:
    def __init__(self):
        self.format = None
        self.file = None
        for impl in browsers_supported:
            try:
                if impl.isBrowser(browser_cmd):
                    self.format = impl
                    self.file = impl.bookmarksFilename(browser_cmd)
                    break
            except Exception:
                continue
        self.mtime = self.get_mtime()
        self.tree = None

    def is_dirty(self):
        return self.mtime != self.get_mtime()

    def get_mtime(self):
        if not self.file or not os.path.exists(self.file):
            return 0
        return os.stat(self.file)[stat.ST_MTIME]

    def broken(self):
        return self.format is None or not self.format.isFunctional()

    def error(self):
        if self.format is None:
            if not browser_cmd:
                return "No Web Browser set as favorite.\nUse mate-control-center."
            return f"Web Browser not supported:\n{browser_cmd}"
        return f"Python module not installed:\n{self.format.requiredModule()}"

    def icon(self):
        return None if self.broken() else self.format.icon()

    def hasEditor(self):
        return (self.format.editorCmd() is not None) if self.format else False
    def editorLabel(self):
        return self.format.editorLabel() if self.format else None
    def editorIcon(self):
        return self.format.editorIcon() if self.format else None
    def editorCmd(self):
        return self.format.editorCmd() if self.format else None

    def getTree(self):
        if not self.broken() and (self.tree is None or self.is_dirty()):
            try:
                self.tree = self.format.createTree(self.file)
            except Exception:
                # keep it graceful—return empty tree on failures
                self.tree = Root()
            self.mtime = self.get_mtime()
        return self.tree

    def getBookmarks(self):
        self.bookmarker = []
        self.getTree().traverse(self._sendBookmark, 0)
        return self.bookmarker

    def _sendBookmark(self, node, level):
        bookmark = node.data
        if bookmark and bookmark.url and not str(bookmark.url).startswith("place:"):
            icon = bookmark.favicon if bookmark.favicon else "applications-internet"
            self.bookmarker.append([bookmark.title, bookmark.url, bookmark.description, icon])
        return level + 1


bookmarks = BookmarksMenu()

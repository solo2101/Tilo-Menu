"""GnoMenu 2.9.1 BookmarksMenu interface for modern Python 3 browsers.

Ported from the original bookmarks.py contract: getBookmarks() returns rows
[title, URL, description, icon]. The old source supported Firefox Places
and Chromium's Bookmarks JSON, but its Python 2/old-profile reader could
not load current profiles. Keep that same data model and read-only behavior.
"""
import configparser
import json
import os
from pathlib import Path
import sqlite3

import backend


_ICON = "applications-internet"
_LIMIT = 500


def _allowed(url):
    if not isinstance(url, str) or not url.strip():
        return False
    # Original GnoMenu excluded internal browser/database commands.
    return url.split(":", 1)[0].lower() not in ("data", "place", "javascript")


def _append(rows, name, url, seen):
    if not _allowed(url) or url in seen:
        return
    seen.add(url)
    rows.append([str(name or url), url, None, _ICON])


def _chromium_files():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    directories = (
        base / "chromium",
        base / "google-chrome",
        base / "BraveSoftware" / "Brave-Browser",
        base / "microsoft-edge",
        base / "opera",
        Path.home() / ".var/app/org.chromium.Chromium/config/chromium",
    )
    for directory in directories:
        if directory.is_dir():
            for filename in sorted(directory.glob("*/Bookmarks")):
                yield filename


def _chromium_bookmarks():
    rows, seen = [], set()
    for filename in _chromium_files():
        try:
            if filename.stat().st_size > 32 * 1024 * 1024:
                continue
            with filename.open(encoding="utf-8") as handle:
                data = json.load(handle)
            roots = data.get("roots", {})
            pending = []
            for branch in roots.values():
                if isinstance(branch, dict):
                    pending.extend(branch.get("children", []))
            while pending and len(rows) < _LIMIT:
                entry = pending.pop()
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") == "folder":
                    pending.extend(entry.get("children", []))
                elif entry.get("type") == "url":
                    _append(rows, entry.get("name"), entry.get("url"), seen)
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return rows


def _firefox_files():
    directories = (
        Path.home() / ".mozilla/firefox",
        Path.home() / ".var/app/org.mozilla.firefox/.mozilla/firefox",
    )
    for base in directories:
        if not base.is_dir():
            continue
        profiles = []
        config = configparser.ConfigParser()
        try:
            config.read(base / "profiles.ini", encoding="utf-8")
            for section in config.sections():
                if config.has_option(section, "Path"):
                    entry = Path(config.get(section, "Path"))
                    if not config.getboolean(section, "IsRelative", fallback=True):
                        profiles.append(entry)
                    else:
                        profiles.append(base / entry)
        except (OSError, ValueError, configparser.Error):
            pass
        profiles.extend(base.glob("*.default*"))
        seen = set()
        for profile in profiles:
            db = profile / "places.sqlite"
            if db in seen or not db.is_file():
                continue
            seen.add(db)
            yield db


def _firefox_bookmarks():
    rows, seen = [], set()
    for filename in _firefox_files():
        try:
            # Firefox uses SQLite WAL. Read-only access avoids writing to,
            # locking or copying a user's active browser profile.
            conn = sqlite3.connect(filename.as_uri() + "?mode=ro",
                                   uri=True, timeout=0.5)
            try:
                cursor = conn.execute(
                    "SELECT b.title, p.url FROM moz_bookmarks b "
                    "JOIN moz_places p ON p.id = b.fk "
                    "WHERE b.type = 1 AND p.url IS NOT NULL "
                    "ORDER BY b.id DESC LIMIT 500"
                )
                for name, url in cursor:
                    _append(rows, name, url, seen)
                    if len(rows) >= _LIMIT:
                        return rows
            finally:
                conn.close()
        except (OSError, sqlite3.Error, ValueError):
            continue
    return rows


class BookmarksMenu:
    """Maintain the original getBookmarks() API used by Menu_Items.XDGMenu."""

    def getBookmarks(self):
        selected = (backend.get_default_internet_browser() or "").lower()
        readers = (_firefox_bookmarks, _chromium_bookmarks)
        if any(browser in selected for browser in
               ("chromium", "chrome", "brave", "edge", "opera")):
            readers = (_chromium_bookmarks, _firefox_bookmarks)
        for reader in readers:
            rows = reader()
            if rows:
                return rows
        return []

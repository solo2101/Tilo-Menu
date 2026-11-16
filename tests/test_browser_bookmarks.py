"""Preserve the original GnoMenu BookmarksMenu API with current browser files."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import sqlite3
import sys

import gi
gi.require_version("Gtk", "3.0")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/lib/tilomenu"))
import bookmarks
from Menu_Items import XDGMenu

with TemporaryDirectory() as tmp:
    home = Path(tmp)
    chrome = home / ".config/chromium/Default/Bookmarks"
    chrome.parent.mkdir(parents=True)
    chrome.write_text(json.dumps({
        "roots": {"bookmark_bar": {"children": [
            {"type": "url", "name": "Home", "url": "https://example.com"},
            {"type": "folder", "name": "Folder", "children": [
                {"type": "url", "name": "Project", "url": "https://example.org"},
                {"type": "url", "name": "Bad", "url": "javascript:alert(1)"},
            ]}
        ]}}
    }), encoding="utf-8")

    firefox = home / ".mozilla/firefox/abc.default-release"
    firefox.mkdir(parents=True)
    (firefox.parent / "profiles.ini").write_text(
        "[Profile0]\nName=default-release\nIsRelative=1\n"
        "Path=abc.default-release\nDefault=1\n", encoding="utf-8")
    with sqlite3.connect(firefox / "places.sqlite") as db:
        db.executescript(
            "CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT);"
            "CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, "
            "title TEXT, fk INTEGER, type INTEGER);"
            "INSERT INTO moz_places VALUES (1,'https://mozilla.org');"
            "INSERT INTO moz_bookmarks VALUES (1,'Firefox',1,1);"
        )

    with patch.object(bookmarks.Path, "home", return_value=home), \
         patch.dict("os.environ", {"XDG_CONFIG_HOME": str(home / ".config")}):
        with patch.object(bookmarks.backend, "get_default_internet_browser",
                          return_value="chromium %u"):
            chrome_rows = bookmarks.BookmarksMenu().getBookmarks()
            assert {row[0] for row in chrome_rows} == {"Home", "Project"}, chrome_rows
            assert all(len(row) == 4 and row[3] == "applications-internet"
                       for row in chrome_rows)
        with patch.object(bookmarks.backend, "get_default_internet_browser",
                          return_value="firefox %u"):
            firefox_rows = bookmarks.BookmarksMenu().getBookmarks()
            assert firefox_rows == [
                ["Firefox", "https://mozilla.org", None, "applications-internet"]
            ], firefox_rows

# Original XDGMenu uses this exact four-column output for the Web Bookmarks
# tab and its original type-3 URI launcher.
with patch.object(bookmarks.BookmarksMenu, "getBookmarks", return_value=[
    ["Example", "https://example.com", None, "applications-internet"]
]):
    xdg = XDGMenu()
    xdg.Restart("webbookmarks")
    index = xdg.L_Names.index("Example")
    assert xdg.L_Types[index] == 3
    assert xdg.L_Execs[index] == "https://example.com"

print("PASS: Chromium and Firefox bookmarks feed original four-column Web Bookmarks XDG list")

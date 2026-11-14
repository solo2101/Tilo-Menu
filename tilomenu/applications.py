"""Application discovery, desktop categories, and safe GIO launching."""

import configparser
from pathlib import Path

from gi.repository import Gio


CATEGORY_NAMES = {
    "AudioVideo": "Sound & Video",
    "Development": "Programming",
    "Education": "Education",
    "Game": "Games",
    "Graphics": "Graphics",
    "Network": "Internet",
    "Office": "Office",
    "Settings": "Preferences",
    "System": "System Tools",
    "Utility": "Accessories",
}


def installed_applications():
    apps = [
        app for app in Gio.AppInfo.get_all()
        if app.should_show() and app.get_name()
    ]
    return sorted(apps, key=lambda app: (app.get_display_name() or app.get_name()).casefold())


def application_categories(app):
    """Read freedesktop Categories from the application's desktop file."""
    filename = getattr(app, "get_filename", lambda: None)()
    if not filename or not Path(filename).is_file():
        return ("Other",)
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(filename, encoding="utf-8")
        values = parser.get("Desktop Entry", "Categories", fallback="")
    except (configparser.Error, OSError, UnicodeError):
        return ("Other",)
    matches = tuple(dict.fromkeys(
        CATEGORY_NAMES[key] for key in values.split(";") if key in CATEGORY_NAMES
    ))
    return matches or ("Other",)


def search_applications(query):
    query = query.strip().casefold()
    return [
        app for app in installed_applications()
        if not query or query in (app.get_display_name() or app.get_name()).casefold()
        or query in (app.get_description() or "").casefold()
    ]


def launch_application(app):
    return app.launch([], None)

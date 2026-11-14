"""MATE-only application discovery and launching via GIO (GTK 3 stack)."""

from gi.repository import Gio


def installed_applications():
    """Return visible desktop applications, sorted by display name."""
    apps = [
        app for app in Gio.AppInfo.get_all()
        if app.should_show() and app.get_name()
    ]
    return sorted(apps, key=lambda app: app.get_display_name().casefold())


def search_applications(query):
    """Search visible apps by name or description."""
    query = query.strip().casefold()
    if not query:
        return installed_applications()
    return [
        app for app in installed_applications()
        if query in app.get_display_name().casefold()
        or query in (app.get_description() or "").casefold()
    ]


def launch_application(app):
    """Launch through GIO so desktop-file Exec fields are handled correctly."""
    return app.launch([], None)

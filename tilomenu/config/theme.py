"""Theme selection and resource paths (XML rendering comes later)."""

from pathlib import Path
from .paths import USER_THEMES_DIR


def theme_directory(name):
    """Return a user theme directory, rejecting path traversal."""
    if not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("Invalid theme name")
    return USER_THEMES_DIR / name

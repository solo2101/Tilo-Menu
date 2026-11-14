"""XDG paths. Importing this module never creates directories."""

from pathlib import Path
import os

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
CONFIG_DIR = CONFIG_HOME / "tilo-menu"
DATA_DIR = DATA_HOME / "tilo-menu"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
USER_THEMES_DIR = DATA_DIR / "themes"

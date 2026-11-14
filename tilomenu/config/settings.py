"""Load and save menu preferences without side effects on import."""

import json
from .defaults import DEFAULTS
from .paths import CONFIG_DIR, SETTINGS_FILE


def load_settings():
    settings = DEFAULTS.copy()
    if SETTINGS_FILE.exists():
        saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if not isinstance(saved, dict):
            raise ValueError("Settings must contain a JSON object")
        settings.update({key: value for key, value in saved.items() if key in DEFAULTS})
    return settings


def save_settings(settings):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {key: settings[key] for key in DEFAULTS if key in settings}
    SETTINGS_FILE.write_text(json.dumps(allowed, indent=2) + "\n", encoding="utf-8")

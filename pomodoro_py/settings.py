import json
import os
from pathlib import Path

SETTINGS_FILE_PATH = Path.home() / ".pomodoro_cli_settings.json"
DEFAULT_SETTINGS = {"focus_minutes": 25, "focus_minutes_divisor": 5, "daily_goal_minutes": 450}

def save_settings(settings: dict):
    """Saves settings to the settings file."""
    try:
        with open(SETTINGS_FILE_PATH, "w") as f:
            json.dump(settings, f)
    except IOError:
        print(f"Error: Could not write to settings file at {SETTINGS_FILE_PATH}")

def load_settings() -> dict:
    """Loads settings from the settings file.

    Returns default settings if the file doesn't exist or is invalid.
    """
    if not SETTINGS_FILE_PATH.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE_PATH, "r") as f:
            settings = json.load(f)
            # Ensure default keys are present
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            return settings
    except (IOError, json.JSONDecodeError):
        print(f"Error: Could not read or decode settings file at {SETTINGS_FILE_PATH}. Using default settings.")
        return DEFAULT_SETTINGS.copy()

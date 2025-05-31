import unittest
import json
import os
from pathlib import Path
# Adjust import path assuming tests are run from the root directory or using `python -m unittest discover`
from python_cli.settings import save_settings, load_settings, DEFAULT_SETTINGS, SETTINGS_FILE_PATH as APP_SETTINGS_FILE_PATH

# Use a temporary settings file for tests to avoid interfering with user's actual settings
TEST_SETTINGS_FILE_PATH = Path.home() / ".pomodoro_cli_settings_test.json"

class TestSettings(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test."""
        # Store the original settings path from the app
        self.original_app_settings_path = APP_SETTINGS_FILE_PATH

        # Override the settings module's global SETTINGS_FILE_PATH
        # This requires settings.py to use its global SETTINGS_FILE_PATH directly
        import python_cli.settings
        self.settings_module_ref = python_cli.settings
        self.original_module_path_val = self.settings_module_ref.SETTINGS_FILE_PATH
        self.settings_module_ref.SETTINGS_FILE_PATH = TEST_SETTINGS_FILE_PATH

        self.addCleanup(self.restore_settings_path_and_cleanup_file)

    def restore_settings_path_and_cleanup_file(self):
        """Restore original settings path in the module and remove the test settings file."""
        self.settings_module_ref.SETTINGS_FILE_PATH = self.original_module_path_val
        if TEST_SETTINGS_FILE_PATH.exists():
            try:
                os.remove(TEST_SETTINGS_FILE_PATH)
            except OSError as e:
                print(f"Warning: Could not remove test settings file {TEST_SETTINGS_FILE_PATH}: {e}")


    def test_01_save_and_load_settings(self):
        """Test saving and then loading settings."""
        test_data = {"focus_minutes": 30, "rest_minutes": 10}
        save_settings(test_data) # Uses the mocked TEST_SETTINGS_FILE_PATH
        loaded_settings = load_settings()
        self.assertEqual(loaded_settings, test_data)

    def test_02_load_default_settings_no_file(self):
        """Test loading default settings when no file exists."""
        self.assertFalse(TEST_SETTINGS_FILE_PATH.exists()) # Pre-condition
        loaded_settings = load_settings()
        self.assertEqual(loaded_settings, DEFAULT_SETTINGS)

    def test_03_load_default_settings_invalid_json(self):
        """Test loading default settings when the file contains invalid JSON."""
        with open(TEST_SETTINGS_FILE_PATH, "w") as f:
            f.write("this is not json { invalid")

        # Capture print output for error messages if possible (optional enhancement)
        # For now, just check functionality
        loaded_settings = load_settings()
        self.assertEqual(loaded_settings, DEFAULT_SETTINGS)

    def test_04_load_settings_missing_keys(self):
        """Test that missing keys in the settings file are filled with defaults."""
        test_data_missing_key = {"focus_minutes": 50} # Missing "rest_minutes"
        save_settings(test_data_missing_key)

        loaded_settings = load_settings()

        expected_settings = DEFAULT_SETTINGS.copy()
        expected_settings["focus_minutes"] = 50

        self.assertEqual(loaded_settings["focus_minutes"], 50)
        self.assertEqual(loaded_settings["rest_minutes"], DEFAULT_SETTINGS["rest_minutes"])
        self.assertEqual(loaded_settings, expected_settings)

    def test_05_save_settings_empty_dict(self):
        """Test saving an empty dictionary."""
        # This should still save an empty JSON object '{}'
        # When loaded, it should be augmented by default settings.
        save_settings({})
        loaded_settings = load_settings()
        self.assertEqual(loaded_settings, DEFAULT_SETTINGS)

    def test_06_load_settings_keeps_extra_keys(self):
        """Test that loading settings preserves extra keys not in defaults."""
        test_data_extra_key = {"focus_minutes": 20, "rest_minutes": 7, "extra_key": "extra_value"}
        save_settings(test_data_extra_key)
        loaded_settings = load_settings()
        self.assertEqual(loaded_settings, test_data_extra_key)


if __name__ == '__main__':
    # This allows running the test file directly
    # Ensure the python_cli package is in PYTHONPATH or run as module
    # e.g. python -m python_cli.tests.test_settings
    unittest.main()

import unittest
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from python_cli.stats import (
    load_stats,
    save_daily_focus_time,
    get_today_stats_display,
    format_seconds_to_hms,
    STATS_FILE_PATH as APP_STATS_FILE_PATH,
    get_today_date_str
)

# Use a temporary stats file for tests
TEST_STATS_FILE_PATH = Path.home() / ".pomodoro_cli_stats_test.json"

class TestStats(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test and mock the stats file path."""
        self.original_app_stats_path = APP_STATS_FILE_PATH

        import python_cli.stats # Import the module to modify its global
        self.stats_module_ref = python_cli.stats
        self.original_module_path_val = self.stats_module_ref.STATS_FILE_PATH
        self.stats_module_ref.STATS_FILE_PATH = TEST_STATS_FILE_PATH

        self.addCleanup(self.restore_stats_path_and_cleanup_file)

    def restore_stats_path_and_cleanup_file(self):
        """Restore original stats path and remove the test stats file."""
        self.stats_module_ref.STATS_FILE_PATH = self.original_module_path_val
        if TEST_STATS_FILE_PATH.exists():
            try:
                os.remove(TEST_STATS_FILE_PATH)
            except OSError as e:
                print(f"Warning: Could not remove test stats file {TEST_STATS_FILE_PATH}: {e}")

    def test_01_load_initial_stats_no_file(self):
        """Test loading initial (default) stats when no file exists."""
        self.assertFalse(TEST_STATS_FILE_PATH.exists()) # Pre-condition
        stats = load_stats()
        today_str = get_today_date_str()
        self.assertEqual(stats["date"], today_str)
        self.assertEqual(stats["time_spent_focus_seconds"], 0)

    def test_02_save_and_load_focus_time(self):
        """Test saving focus time and that it accumulates correctly on the same day."""
        save_daily_focus_time(30 * 60)  # 30 minutes
        stats = load_stats()
        self.assertEqual(stats["time_spent_focus_seconds"], 30 * 60)

        save_daily_focus_time(15 * 60)  # Another 15 minutes
        stats = load_stats()
        self.assertEqual(stats["time_spent_focus_seconds"], (30 + 15) * 60)

    def test_03_get_today_stats_display(self):
        """Test the display string for today's stats."""
        save_daily_focus_time( (1 * 3600) + (25 * 60) + 5 ) # 1h 25m 5s
        display_str = get_today_stats_display()
        expected_str = "Total focus time today: 01:25:05"
        self.assertEqual(display_str, expected_str)

    def test_04_stats_reset_on_date_change(self):
        """Test that stats reset when the date changes."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_stats_data = {"date": yesterday, "time_spent_focus_seconds": 5000}

        with open(TEST_STATS_FILE_PATH, "w") as f:
            json.dump(yesterday_stats_data, f)

        # load_stats should see the date is old and return fresh stats for today
        stats_on_new_day = load_stats()
        today_str = get_today_date_str()
        self.assertEqual(stats_on_new_day["date"], today_str)
        self.assertEqual(stats_on_new_day["time_spent_focus_seconds"], 0)

    def test_05_load_stats_corrupt_json(self):
        """Test loading stats from a corrupt JSON file."""
        with open(TEST_STATS_FILE_PATH, "w") as f:
            f.write("this is not valid json {")

        stats = load_stats()
        today_str = get_today_date_str()
        self.assertEqual(stats["date"], today_str)
        self.assertEqual(stats["time_spent_focus_seconds"], 0)

    def test_06_load_stats_missing_time_key(self):
        """Test loading stats from a file where today's date is present but time_spent_focus_seconds is missing."""
        today_str = get_today_date_str()
        stats_missing_key = {"date": today_str} # Missing 'time_spent_focus_seconds'

        with open(TEST_STATS_FILE_PATH, "w") as f:
            json.dump(stats_missing_key, f)

        stats = load_stats()
        self.assertEqual(stats["date"], today_str)
        self.assertEqual(stats["time_spent_focus_seconds"], 0) # Should default to 0

    def test_07_format_seconds_to_hms(self):
        """Test the helper function for formatting seconds."""
        self.assertEqual(format_seconds_to_hms(0), "00:00:00")
        self.assertEqual(format_seconds_to_hms(59), "00:00:59")
        self.assertEqual(format_seconds_to_hms(60), "00:01:00")
        self.assertEqual(format_seconds_to_hms(3600), "01:00:00")
        self.assertEqual(format_seconds_to_hms(3661), "01:01:01") # 1h 1m 1s
        self.assertEqual(format_seconds_to_hms(86399), "23:59:59") # Max seconds in a day - 1
        self.assertEqual(format_seconds_to_hms(-100), "00:00:00") # Invalid input
        # self.assertEqual(format_seconds_to_hms("abc"), "00:00:00") # Invalid type, if type checking is strict

    def test_08_save_daily_focus_time_invalid_input(self):
        """Test save_daily_focus_time with invalid (negative) input."""
        initial_stats = load_stats()
        initial_focus_seconds = initial_stats.get("time_spent_focus_seconds", 0)

        save_daily_focus_time(-100) # Should not change the stats

        stats_after_invalid_save = load_stats()
        self.assertEqual(stats_after_invalid_save.get("time_spent_focus_seconds", 0), initial_focus_seconds)
        # This test assumes save_daily_focus_time prints an error but doesn't raise one or alter stats for negative time.

if __name__ == '__main__':
    unittest.main()

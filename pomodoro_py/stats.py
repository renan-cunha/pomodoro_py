import json
from datetime import datetime, timedelta
from pathlib import Path
import os
from settings import load_settings

STATS_FILE_PATH = Path.home() / ".pomodoro_cli_stats.json"

def get_today_date_str() -> str:
    """Returns today's date as a YYYY-MM-DD string."""
    return datetime.now().strftime("%Y-%m-%d")

def load_stats() -> dict:
    """
    Loads stats for today.
    If no stats file exists, it's an old date, or the file is corrupt,
    returns a new stats dictionary for today.
    """
    today_str = get_today_date_str()
    default_stats = {"date": today_str, "time_spent_focus_seconds": 0}

    if not STATS_FILE_PATH.exists():
        return default_stats

    try:
        with open(STATS_FILE_PATH, "r") as f:
            stats = json.load(f)
            if not isinstance(stats, dict) or stats.get("date") != today_str:
                # Either not a dict, or date is not today, so reset
                return default_stats
            # Ensure essential keys are present
            if "time_spent_focus_seconds" not in stats:
                stats["time_spent_focus_seconds"] = 0
            stats["date"] = today_str # Ensure date is current, though it should be by the check above
            return stats
    except (IOError, json.JSONDecodeError):
        # Error reading or parsing, so reset
        return default_stats

def save_daily_focus_time(seconds_spent_in_focus: float):
    """
    Adds focus time to today's stats and saves it.
    """
    seconds_spent_in_focus = int(seconds_spent_in_focus)
    if seconds_spent_in_focus < 0:
        print("Error: Invalid time provided to save_daily_focus_time.")
        return

    stats = load_stats() # This ensures we're working with today's data or fresh data

    # This check is slightly redundant due to load_stats behavior but good for safety
    if stats.get("date") != get_today_date_str():
        # This case should ideally be handled by load_stats returning default for new day
        stats = {"date": get_today_date_str(), "time_spent_focus_seconds": 0}

    stats["time_spent_focus_seconds"] = stats.get("time_spent_focus_seconds", 0) + seconds_spent_in_focus

    try:
        with open(STATS_FILE_PATH, "w") as f:
            json.dump(stats, f, indent=4)
    except IOError:
        print(f"Error: Could not write to stats file at {STATS_FILE_PATH}")

def format_seconds_to_hms(total_seconds: int) -> str:
    """Formats total seconds into HH:MM:SS string."""
    if not isinstance(total_seconds, int) or total_seconds < 0:
        return "00:00:00"
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_today_stats_display() -> str:
    """Returns two lines:
    
    (1) the goal (focus+rest) for today in HH:MM:SS format,
    (2) the time remaining in total time today (focus+rest) in HH:MM:SS format.
    """
    settings = load_settings()
    focus_minutes = settings.get("focus_minutes", 25)
    focus_minutes_divisor = settings.get("focus_minutes_divisor", 5)
    daily_goal_minutes = settings.get("daily_goal_minutes", 450)

    total_focus_seconds = focus_minutes * 60
    total_rest_seconds = (focus_minutes // focus_minutes_divisor) * 60
    total_daily_seconds = (daily_goal_minutes * 60)

    goal_time_str = format_seconds_to_hms(total_daily_seconds)
    
    stats = load_stats()
    time_spent_focus_seconds = stats.get("time_spent_focus_seconds", 0)
    total_time_spent_in_seconds = time_spent_focus_seconds + (time_spent_focus_seconds // focus_minutes_divisor)
    
    time_remaining_seconds = total_daily_seconds - total_time_spent_in_seconds
    time_remaining_str = format_seconds_to_hms(time_remaining_seconds)

    return f"Goal for today: {goal_time_str}\n\tTime Remaining: {time_remaining_str}"

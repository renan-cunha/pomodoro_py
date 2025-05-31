# Python Pomodoro CLI

## Overview

A simple but effective command-line Pomodoro timer to help you stay focused and manage your work/rest cycles directly from your terminal.

## Features

*   **Focus & Rest Sessions**: Standard Pomodoro technique with dedicated focus and rest periods.
*   **Configurable Durations**: Set custom default durations for focus and rest periods. Override defaults per session.
*   **"Continue Focus" Mode**: Option to continue focusing after a focus session ends, with the extra time logged.
*   **Daily Statistics**: Tracks total time spent in focus mode each day.
*   **Terminal Notifications**: Simple audio (terminal bell) and text notifications for session completion.

## Requirements

*   Python 3.7+
*   `click` library (for the command-line interface)

## Installation

1.  Ensure you have Python 3.7 or newer installed.
2.  Install the `click` library using pip:
    ```bash
    pip install click
    ```
3.  Currently, the application is run directly from its source files. No further package installation is required beyond `click`.

## Usage

To run the CLI, navigate to the root directory of this project (the one containing the `python_cli` directory) and use the following pattern:

```bash
python -m python_cli.main [COMMAND] [OPTIONS]
```

### Main Commands

#### `start`

Initiates a Pomodoro session.

*   Start with default or saved settings:
    ```bash
    python -m python_cli.main start
    ```
*   Override durations for the current session:
    ```bash
    python -m python_cli.main start --focus 20 --rest 4
    ```

#### `settings`

Manage default session durations.

*   View current settings:
    ```bash
    python -m python_cli.main settings view
    ```
*   Set a new default focus duration:
    ```bash
    python -m python_cli.main settings set --focus-minutes 30
    ```
*   Set a new default rest duration:
    ```bash
    python -m python_cli.main settings set --rest-minutes 7
    ```
*   Set both default durations:
    ```bash
    python -m python_cli.main settings set --focus-minutes 25 --rest-minutes 5
    ```

#### `stats`

View your focus statistics.

*   View total focus time for today:
    ```bash
    python -m python_cli.main stats view
    ```

### Interacting with the Timer

*   **Ctrl+C**:
    *   During a running focus or rest session (but not "Continued Focus"): Pauses the timer. You'll be prompted to resume or exit.
    *   During "Continued Focus" mode: Stops the continued focus, logs the additional time, and prompts to start a dynamically calculated rest session or exit.
    *   If pressed when paused or between sessions: Offers to exit.

## Configuration Files

The application stores its data in your user home directory:

*   **Settings**: `~/.pomodoro_cli_settings.json`
    *   Stores your default focus and rest minute preferences.
*   **Statistics**: `~/.pomodoro_cli_stats.json`
    *   Stores daily statistics, specifically `time_spent_focus_seconds` for each day.

You can view these files to see your raw data, but it's recommended to manage settings via the `settings set` command.

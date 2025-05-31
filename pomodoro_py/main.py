import click
import time
import sys

from pomodoro_py.cli_timer import Timer
from pomodoro_py.settings import load_settings, save_settings, DEFAULT_SETTINGS
from pomodoro_py.stats import save_daily_focus_time, get_today_stats_display
from pomodoro_py.notifications import send_notification

# Global variable to help manage timer state across KeyboardInterrupts
_timer_instance = None



def menu_action_loop():
    """Main loop to display menu and handle user actions."""
    while True:
        displays_menu()
        perform_user_action()

def displays_menu(commands=['Start Pomodoro Session', 'Change Focus Time', 'Change Goal for Today']):
    """
    Displays:
    (1) the main menu options for the Pomodoro CLI.
    (2) the statistics for today's focus time.
    (3) the current settings for focus durations.
    (4) the timer's current state.
    """
    click.clear()
    click.echo("\nPomodoro CLI Timer 🍅\n")
    if len(commands) > 0:
        click.echo("="*40)
        click.echo("Commands 🤖")
        for index, cmd in enumerate(commands):
            click.echo(f"\t{index+1}. {cmd}")

    settings = load_settings()
    focus_minutes = settings.get("focus_minutes", DEFAULT_SETTINGS["focus_minutes"])
    click.echo("="*40)
    click.echo("Settings 🛠️")
    click.echo(f" \tFocus Duration: {focus_minutes} minutes")
    click.echo("="*40)

    stats_display = get_today_stats_display()
    click.echo("Statistics 📊")
    click.echo(f"\t{stats_display}\n")


def perform_user_action():
    """Gets user input and calls the respective function.
    The printing of the command is erased after the user input is received.
    """
    click.echo("\nEnter a command (1-3) or 'q' to quit:")
    user_input = click.prompt("Command", type=str).strip().lower()

    if user_input == '1':
        displays_menu(commands=['Press Ctrl+C to pause'])
        start()
    elif user_input == '2':
        focus_minutes_override = click.prompt("Enter new focus duration in minutes", type=float, default=DEFAULT_SETTINGS["focus_minutes"])
        settings = load_settings()
        settings["focus_minutes"] = focus_minutes_override
        save_settings(settings)
        start(focus_minutes_override=focus_minutes_override)
    elif user_input == '3':
        daily_goal_minutes = click.prompt("Enter new daily goal in HH:MM format", type=str, default="07:30")
        try:
            hours, minutes = map(int, daily_goal_minutes.split(':'))
            total_minutes = hours * 60 + minutes
            settings = load_settings()
            settings["daily_goal_minutes"] = total_minutes
            save_settings(settings)
            click.echo(f"Daily goal set to {total_minutes} minutes.")
        except ValueError:
            click.echo("Invalid format. Please use HH:MM format.", err=True)
        
    elif user_input == 'q':
        click.echo("Exiting Pomodoro CLI.")
        sys.exit(0)
    else:
        click.echo("Invalid command. Please try again.")
        perform_user_action()


def cli():
    """A simple Pomodoro CLI timer."""
    menu_action_loop()
    pass

@click.option('--focus', 'focus_minutes_override', type=int, help='Focus duration in minutes.')
def start(focus_minutes_override=None):
    """Starts a Pomodoro session with an HH:MM:SS timer and a burning wick visualization."""
    global _timer_instance
    settings = load_settings()

    focus_minutes = (
        focus_minutes_override
        if focus_minutes_override is not None
        else settings.get("focus_minutes", DEFAULT_SETTINGS["focus_minutes"])
    )
    rest_minutes = focus_minutes / DEFAULT_SETTINGS["focus_minutes_divisor"]

    if focus_minutes <= 0 or rest_minutes <= 0:
        click.echo("Error: Focus and rest durations must be positive.", err=True)
        sys.exit(1)

    try:
        _timer_instance = Timer(focus_minutes=focus_minutes, rest_minutes=rest_minutes)
    except ValueError as e:  # Should be caught by above check, but good practice
        click.echo(f"Error initializing timer: {e}", err=True)
        sys.exit(1)

    # Store initial values for calculating dynamic rest later
    _timer_instance.initial_focus_minutes = focus_minutes
    _timer_instance.initial_rest_minutes = rest_minutes

    _timer_instance.start()
    click.echo(f"Starting {focus_minutes} min focus.")

    while True:  # Main loop for focus/rest cycles
        try:
            current_mode_on_entry = _timer_instance.current_mode
            continued_focus_active_on_entry = is_continued_focus_active()

            while _timer_instance.is_running and not _timer_instance.is_paused:
                time_is_up = _timer_instance.tick()

                # === Build HH:MM:SS display ===
                total_left = int(_timer_instance.time_left_seconds)
                hours = total_left // 3600
                minutes = (total_left % 3600) // 60
                seconds = total_left % 60
                display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                # === Determine total seconds for the current period ===
                if _timer_instance.current_mode == "focus":
                    period_seconds = _timer_instance.initial_focus_minutes * 60
                else:
                    period_seconds = _timer_instance.initial_rest_minutes * 60

                # Avoid division by zero (just in case)
                if period_seconds <= 0:
                    segments_remaining = 0
                else:
                    segments_remaining = max(0, min(period_seconds, total_left))

                # === Compute flame position along a 10‐segment wick ===
                # We’ll split the period into 10 equal segments.
                total_segments = 10
                elapsed = period_seconds - total_left
                # If elapsed >= period_seconds, flame should be at the very end.
                if elapsed >= period_seconds:
                    flame_index = total_segments - 1
                elif elapsed <= 0:
                    flame_index = 0
                else:
                    # Map elapsed [0..period_seconds] → [0..(total_segments-1)]
                    frac = elapsed / period_seconds
                    flame_index = int(frac * (total_segments - 1))

                # Build a 10-character string:
                #   ‘.’ for burnt segments (i < flame_index)
                #   ‘🔥’ at i == flame_index
                #   ‘-’ for unburnt segments (i > flame_index)
                wick_chars = []
                for i in range(total_segments):
                    if i <= flame_index:
                        wick_chars.append("🔥")
                    else:
                        wick_chars.append("-")
                wick = "".join(wick_chars)

                prefix = "Continued Focus" if is_continued_focus_active() else _timer_instance.current_mode.capitalize()
                click.echo(f"\r{prefix} Mode | {display} | {wick}  ", nl=False)
                time.sleep(1)

                if time_is_up:
                    click.echo()
                    displays_menu(commands=[])
                    send_notification(f"{_timer_instance.current_mode.capitalize()} session ended!")
                    click.echo()  # Newline after timer display

                    if _timer_instance.current_mode == "focus":
                        # Save time for the completed focus segment (initial focus, not continued)
                        save_daily_focus_time(_timer_instance.focus_minutes * 60)

                        if click.confirm("\nStart rest session?", default=True):
                            displays_menu(commands=[])
                            _timer_instance.switch_mode()  # To rest
                            # Rest duration is fixed based on initial settings or override
                            _timer_instance.time_left_seconds = _timer_instance.rest_minutes * 60
                            _timer_instance.start()
                        else:
                            displays_menu(commands=[])
                            _timer_instance.start_continue_focus()
                            click.echo("Continuing focus. Press Ctrl+C to stop and log.")

                    else:  # Current mode is rest

                        menu_action_loop()  # Return to main menu after rest
                    break  # Break from inner while loop to re-evaluate outer loop condition (e.g. mode switch)

            if not _timer_instance.is_running and not _timer_instance.is_paused:
                # This means timer was stopped (e.g. by user choice "Exiting Pomodoro")
                break  # Exit main Pomodoro session loop

            # If paused, this outer loop will spin; Ctrl+C handles resume/exit
            # Or if continued focus was started, inner loop continues
            # If time_is_up and a new session started, inner loop continues
            time.sleep(0.1)  # prevent busy loop if paused

        except KeyboardInterrupt:
            # Handle Ctrl+C for pausing or resuming if needed
            if is_continued_focus_active():
                # If in continued focus mode, stop it
                handle_keyboard_interrupt()
            else: # If not interrupted, continue the loop
                displays_menu()
                _timer_instance.pause()
                click.echo("\nTimer paused.")
                input("Press Enter to resume")
                _timer_instance.resume()

def is_continued_focus_active():
    return _timer_instance._continued_focus_elapsed_seconds > 0


def handle_keyboard_interrupt():
    """Handles Ctrl+C interruption."""
    displays_menu(commands=[])
    global _timer_instance
    if not _timer_instance:
        click.echo("\nExiting.")
        sys.exit(0)

    click.echo() # Newline after the ^C

    if _timer_instance._continued_focus_elapsed_seconds > 0:
        # Currently in "continued focus" mode
        _timer_instance.pause() # Effectively stops the count-up for logging
        continued_seconds = int(_timer_instance.time_left_seconds) # This is the elapsed continued time

        if continued_seconds > 0:
            save_daily_focus_time(continued_seconds)
            send_notification("Continued focus stopped.")
            click.echo(f"Logged {continued_seconds // 60}m {continued_seconds % 60}s of continued focus.")

        _timer_instance.stop() # Fully stop and reset continued focus markers
        _timer_instance.current_mode = "focus" # Prepare for switch_mode to correctly go to "rest"

        # Calculate rest based on initial focus + continued focus
        total_focus_seconds = (_timer_instance.initial_focus_minutes * 60) + continued_seconds

        # Dynamic rest: ratio from initial settings. e.g. if 25/5, ratio is 1/5
        # Or a simpler fixed ratio like 1/5 of total focus.
        # Let's use the ratio from initial settings.
        if _timer_instance.initial_focus_minutes > 0: # Avoid division by zero
            rest_ratio = _timer_instance.initial_rest_minutes / _timer_instance.initial_focus_minutes
        else: # Should not happen with validation, but as a fallback
            rest_ratio = 1/5

        new_rest_seconds = int(total_focus_seconds * rest_ratio)
        new_rest_minutes = new_rest_seconds / 60 # Ensure at least 1 min rest if some focus was done

        _timer_instance.rest_minutes = new_rest_minutes # Update timer's rest duration for this cycle
        _timer_instance.switch_mode() # To rest mode
        _timer_instance.time_left_seconds = int(_timer_instance.rest_minutes * 60)
        _timer_instance.start()
        click.echo(f"Starting {new_rest_minutes} min rest.")




    elif _timer_instance.is_running and not _timer_instance.is_paused:
        _timer_instance.pause()
        click.echo(f"\nTimer paused at {_timer_instance.get_display_time()}.")
        if click.confirm("Resume?", default=True):
            _timer_instance.resume()
            # The main loop in `start` will continue
        else:
            click.echo("Exiting.")
            sys.exit(0)
    elif _timer_instance.is_paused:
        click.echo(f"\nTimer is already paused at {_timer_instance.get_display_time()}.")
        if click.confirm("Resume?", default=True):
            _timer_instance.resume()
        elif click.confirm("Exit Pomodoro?", default=False):
             click.echo("Exiting.")
             sys.exit(0)
        # If neither, stays paused, user can Ctrl+C again or main loop continues if structured for it.
    else: # Not running, not paused (e.g. between sessions, or after a stop)
        click.echo("\nNo active timer session to pause/resume. Exiting.")
        sys.exit(0)


@click.group(name="settings")
def settings_group():
    """Manage Pomodoro settings."""
    pass

@settings_group.command(name='view')
def view_settings():
    """View current settings."""
    settings = load_settings()
    click.echo("Current settings:")
    focus_minutes = settings.get('focus_minutes', DEFAULT_SETTINGS['focus_minutes'])
    click.echo(f"  Focus duration: {focus_minutes} minutes")
    rest_minutes = settings.get('rest_minutes', DEFAULT_SETTINGS['focus_minutes'] // DEFAULT_SETTINGS['focus_minutes_divisor'])
    click.echo(f"  Rest duration: {rest_minutes} minutes")
    click.echo(f"Settings file: {Path.home() / '.pomodoro_cli_settings.json'}")


@settings_group.command(name='set')
@click.option('--focus-minutes', type=int, help="Set focus duration in minutes.")
@click.option('--rest-minutes', type=int, help="Set rest duration in minutes.")
def set_settings(focus_minutes):
    """Set new default focus and/or rest durations."""
    if focus_minutes is None:
        click.echo("No settings provided. Use --focus-minutes or --rest-minutes.")
        return

    settings = load_settings()
    updated = False

    if focus_minutes is not None:
        if focus_minutes > 0:
            settings['focus_minutes'] = focus_minutes
            updated = True
            click.echo(f"Default focus duration set to {focus_minutes} minutes.")
        else:
            click.echo("Error: Focus minutes must be positive.", err=True)

    if updated:
        save_settings(settings)
    else:
        click.echo("No valid settings were updated.")


@click.group(name="stats")
def stats_group():
    """View Pomodoro statistics."""
    pass

@stats_group.command(name='view')
def view_stats():
    """View today's focus statistics."""
    click.echo(get_today_stats_display())


if __name__ == '__main__':
    cli()

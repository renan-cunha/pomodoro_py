import time

class Timer:
    def __init__(self, focus_minutes: int, rest_minutes: int):
        if focus_minutes <= 0 or rest_minutes <= 0:
            raise ValueError("Focus and rest minutes must be positive.")

        self.focus_minutes = focus_minutes
        self.rest_minutes = rest_minutes

        self.current_mode = "focus"  # "focus" or "rest"
        self.time_left_seconds = self.focus_minutes * 60
        self.is_running = False
        self.is_paused = False

        self._start_time = 0.0
        self._paused_time = 0.0
        self._continued_focus_elapsed_seconds = 0 # Tracks time in "continue focus"

    @property
    def initial_duration_for_mode(self) -> int:
        """Returns the initial duration in seconds for the current mode."""
        if self.current_mode == "focus":
            return self.focus_minutes * 60
        else: # rest
            return self.rest_minutes * 60

    def start(self):
        """Starts the timer for the current mode."""
        self.is_running = True
        self.is_paused = False
        self._start_time = time.monotonic()
        self._continued_focus_elapsed_seconds = 0 # Reset continued focus
        self.time_left_seconds = self.initial_duration_for_mode

    def pause(self):
        """Pauses the timer if it's running and not already paused."""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self._paused_time = time.monotonic()
            # Save the accurately calculated remaining time
            elapsed_time_before_pause = self._paused_time - self._start_time
            if self._continued_focus_elapsed_seconds > 0: # Pausing during continued focus
                 self.time_left_seconds = elapsed_time_before_pause # time_left_seconds counts up
            else:
                self.time_left_seconds = max(0, self.initial_duration_for_mode - elapsed_time_before_pause)


    def resume(self):
        """Resumes the timer if it's running and paused."""
        if self.is_running and self.is_paused:
            pause_duration = time.monotonic() - self._paused_time
            self._start_time += pause_duration # Adjust start time to account for pause
            self.is_paused = False

    def stop(self):
        """Stops the timer and resets its state for the current mode."""
        self.is_running = False
        self.is_paused = False
        self._continued_focus_elapsed_seconds = 0
        self.time_left_seconds = self.initial_duration_for_mode

    def tick(self) -> bool:
        """
        Updates the timer's state. Called every second.
        Returns True if the current segment (focus/rest) is over, False otherwise.
        """
        if not self.is_running or self.is_paused:
            return False

        elapsed_time = time.monotonic() - self._start_time

        if self._continued_focus_elapsed_seconds > 0: # In "continue focus" mode
            self.time_left_seconds = elapsed_time # Time counts up
            return False # "Continue focus" doesn't end on its own
        else:
            current_time_left = self.initial_duration_for_mode - elapsed_time
            self.time_left_seconds = max(0, int(current_time_left))

            if self.time_left_seconds == 0:
                return True
        return False

    def switch_mode(self):
        """Switches between focus and rest modes and resets the timer."""
        if self.current_mode == "focus":
            self.current_mode = "rest"
            self.time_left_seconds = self.rest_minutes * 60
        else: # current_mode == "rest"
            self.current_mode = "focus"
            self.time_left_seconds = self.focus_minutes * 60

        self.is_running = False
        self.is_paused = False
        self._continued_focus_elapsed_seconds = 0

    def start_continue_focus(self):
        """Starts or continues the 'continue focus' mode after focus time is up."""
        if self.current_mode == "focus" and self.time_left_seconds == 0 and self._continued_focus_elapsed_seconds == 0:
            self.is_running = True
            self.is_paused = False
            self._start_time = time.monotonic() # Reset start time for continued focus
            self._continued_focus_elapsed_seconds = 1 # Mark as active
            self.time_left_seconds = 0 # Visually starts from 00:00 and counts up
        else:
            # This case should ideally not be reached if UI logic is correct
            print("Warning: start_continue_focus called inappropriately.")


    def get_display_time(self) -> str:
        """Returns the time left (or elapsed in continued focus) formatted as MM:SS."""
        # In continued focus mode, time_left_seconds is the elapsed time.
        display_seconds = self.time_left_seconds

        minutes = int(display_seconds // 60)
        seconds = int(display_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

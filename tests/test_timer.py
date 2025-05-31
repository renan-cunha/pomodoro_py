import unittest
import time
from python_cli.cli_timer import Timer

class TestTimer(unittest.TestCase):

    def test_01_timer_creation(self):
        """Test basic timer creation and initial state."""
        timer = Timer(focus_minutes=25, rest_minutes=5)
        self.assertEqual(timer.focus_minutes, 25)
        self.assertEqual(timer.rest_minutes, 5)
        self.assertEqual(timer.current_mode, "focus")
        self.assertEqual(timer.time_left_seconds, 25 * 60)
        self.assertFalse(timer.is_running)
        self.assertFalse(timer.is_paused)
        self.assertEqual(timer._continued_focus_elapsed_seconds, 0)

    def test_02_timer_creation_invalid_input(self):
        """Test timer creation with invalid (zero or negative) durations."""
        with self.assertRaises(ValueError):
            Timer(focus_minutes=0, rest_minutes=5)
        with self.assertRaises(ValueError):
            Timer(focus_minutes=25, rest_minutes=0)
        with self.assertRaises(ValueError):
            Timer(focus_minutes=-5, rest_minutes=5)

    def test_03_start_stop(self):
        """Test starting and stopping the timer."""
        timer = Timer(1, 1) # Short duration for testing
        timer.start()
        self.assertTrue(timer.is_running)
        self.assertFalse(timer.is_paused)
        self.assertEqual(timer.time_left_seconds, 1 * 60)

        timer.stop()
        self.assertFalse(timer.is_running)
        self.assertFalse(timer.is_paused)
        self.assertEqual(timer.time_left_seconds, 1 * 60) # Resets to initial for current mode

    def test_04_pause_resume(self):
        """Test pausing and resuming the timer."""
        timer = Timer(1, 1)
        timer.start()
        time.sleep(0.1) # Let some time pass

        timer.pause()
        self.assertTrue(timer.is_running) # Still considered running conceptually
        self.assertTrue(timer.is_paused)
        time_at_pause = timer.time_left_seconds
        self.assertLess(time_at_pause, 1 * 60) # Time should have decreased

        time.sleep(0.1) # This time should not count
        self.assertEqual(timer.time_left_seconds, time_at_pause) # Time should not change while paused

        timer.resume()
        self.assertTrue(timer.is_running)
        self.assertFalse(timer.is_paused)
        time.sleep(0.1) # Let some time pass
        self.assertLess(timer.time_left_seconds, time_at_pause) # Time should have decreased further

    def test_05_tick_and_time_up(self):
        """Test the tick method and time up condition."""
        timer = Timer(focus_minutes=0.02, rest_minutes=1) # Approx 1.2 seconds for focus
        timer.start()
        self.assertTrue(timer.is_running)

        time_up = False
        # Loop for a bit longer than the timer duration to ensure it triggers
        for _ in range(int(0.02 * 60) + 2):
            time.sleep(0.1) # Simulate 0.1 second passing
            time_up = timer.tick()
            if time_up:
                break

        self.assertTrue(time_up, "Timer should have indicated time is up.")
        self.assertEqual(timer.time_left_seconds, 0)

    def test_06_switch_mode(self):
        """Test switching modes between focus and rest."""
        timer = Timer(25, 5)

        # Switch from focus to rest
        timer.switch_mode()
        self.assertEqual(timer.current_mode, "rest")
        self.assertEqual(timer.time_left_seconds, 5 * 60)
        self.assertFalse(timer.is_running) # Should reset running state

        # Switch from rest to focus
        timer.switch_mode()
        self.assertEqual(timer.current_mode, "focus")
        self.assertEqual(timer.time_left_seconds, 25 * 60)
        self.assertFalse(timer.is_running)

    def test_07_get_display_time(self):
        """Test the time formatting for display."""
        timer = Timer(25, 5)
        timer.time_left_seconds = 25 * 60 # 25:00
        self.assertEqual(timer.get_display_time(), "25:00")

        timer.time_left_seconds = 5 * 60 + 30 # 05:30
        self.assertEqual(timer.get_display_time(), "05:30")

        timer.time_left_seconds = 59 # 00:59
        self.assertEqual(timer.get_display_time(), "00:59")

        timer.time_left_seconds = 0 # 00:00
        self.assertEqual(timer.get_display_time(), "00:00")

        # Test display during continued focus (time counts up)
        timer.current_mode = "focus"
        timer.time_left_seconds = 0 # Simulate focus end
        timer.start_continue_focus() # This will set _continued_focus_elapsed_seconds > 0
                                     # and time_left_seconds to 0 initially

        # Simulate 90 seconds (1m 30s) passing in continued focus
        # In the actual tick, time_left_seconds gets updated to elapsed_time
        timer.time_left_seconds = 90
        self.assertEqual(timer.get_display_time(), "01:30")


    def test_08_start_continue_focus(self):
        """Test starting the 'continue focus' mode."""
        timer = Timer(0.02, 1) # Short focus for quick time up
        timer.start()
        time.sleep(0.02 * 60 + 0.2) # Ensure time is up
        is_up = timer.tick()
        self.assertTrue(is_up)
        self.assertEqual(timer.time_left_seconds, 0)

        timer.start_continue_focus()
        self.assertTrue(timer.is_running)
        self.assertFalse(timer.is_paused)
        self.assertGreater(timer._continued_focus_elapsed_seconds, 0)
        self.assertEqual(timer.time_left_seconds, 0) # Visually starts at 00:00

        time.sleep(0.1)
        timer.tick() # Update time_left_seconds which is elapsed time in this mode
        self.assertGreater(timer.time_left_seconds, 0) # Time should be counting up
        self.assertTrue(timer.get_display_time().startswith("00:00") or timer.get_display_time().startswith("00:01"))


    def test_09_stop_from_continued_focus(self):
        """Test stopping the timer while in 'continue focus' mode."""
        timer = Timer(1, 1)
        timer.time_left_seconds = 0 # Simulate focus time up
        timer.start_continue_focus()
        self.assertTrue(timer.is_running)
        self.assertGreater(timer._continued_focus_elapsed_seconds, 0)

        timer.stop()
        self.assertFalse(timer.is_running)
        self.assertEqual(timer._continued_focus_elapsed_seconds, 0) # Reset this marker
        self.assertEqual(timer.time_left_seconds, timer.initial_duration_for_mode) # Reset to initial focus duration

    def test_10_pause_resume_in_continued_focus(self):
        """Test pause and resume during continued focus mode."""
        timer = Timer(0.02, 1) # Short focus
        timer.start()
        time.sleep(0.02 * 60 + 0.2) # Let focus time pass
        self.assertTrue(timer.tick()) # Focus is up

        timer.start_continue_focus()
        time.sleep(0.1) # Let continued focus run a bit
        timer.tick()
        time_at_continue_tick1 = timer.time_left_seconds
        self.assertGreater(time_at_continue_tick1, 0)

        timer.pause()
        self.assertTrue(timer.is_paused)
        time_at_pause = timer.time_left_seconds # This should be the elapsed time so far
        self.assertEqual(time_at_pause, time_at_continue_tick1)

        time.sleep(0.1) # This time should not count
        timer.tick() # Tick while paused should not change time
        self.assertEqual(timer.time_left_seconds, time_at_pause)

        timer.resume()
        self.assertFalse(timer.is_paused)
        time.sleep(0.1) # Let it run a bit more
        timer.tick()
        self.assertGreater(timer.time_left_seconds, time_at_pause)

if __name__ == '__main__':
    unittest.main()

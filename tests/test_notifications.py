import unittest
import io
from unittest.mock import patch
from python_cli.notifications import send_notification

class TestNotifications(unittest.TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_send_notification_output(self, mock_stdout):
        """Test that send_notification prints the message and bell character."""
        message = "Test notification message!"
        send_notification(message)

        output = mock_stdout.getvalue()

        # Check for the message part
        self.assertIn(message, output)
        # Check for the bell icon prefix
        self.assertIn("🔔", output)
        # Check for the alert character (bell sound)
        self.assertIn("\a", output)
        # Check for the newline at the beginning
        self.assertTrue(output.startswith("\n"))

    def test_send_notification_runs_without_error(self):
        """Test that send_notification executes without raising an exception."""
        try:
            send_notification("Simple test")
        except Exception as e:
            self.fail(f"send_notification raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()

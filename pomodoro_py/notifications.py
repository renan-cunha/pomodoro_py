def send_notification(message: str):
    """
    Sends a notification by printing it to the console and attempting to play the terminal bell.
    """
    # \a is the ASCII bell character. Its behavior depends on the terminal.
    print(f"\n🔔 {message}\a")
    # On some systems, flushing stdout might be necessary for the bell to be immediate.
    import sys
    sys.stdout.flush()

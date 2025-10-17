"""
Spinner utility for showing progress during long-running operations.

This module provides a simple spinner that can be used by all doc-utils tools
to indicate that processing is in progress.
"""

import sys
import time
import threading
from typing import Optional


class Spinner:
    """A simple spinner to show progress during long operations."""

    FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, message: str = "Processing"):
        """
        Initialize the spinner with a message.

        Args:
            message: The message to display alongside the spinner
        """
        self.message = message
        self.spinning = False
        self.thread: Optional[threading.Thread] = None
        self.frame_index = 0

    def _spin(self):
        """Internal method that runs in a separate thread to animate the spinner."""
        while self.spinning:
            frame = self.FRAMES[self.frame_index % len(self.FRAMES)]
            sys.stdout.write(f'\r{frame} {self.message}...')
            sys.stdout.flush()
            self.frame_index += 1
            time.sleep(0.1)

    def start(self):
        """Start the spinner animation."""
        if not self.spinning:
            self.spinning = True
            self.thread = threading.Thread(target=self._spin)
            self.thread.daemon = True
            self.thread.start()

    def stop(self, final_message: Optional[str] = None, success: bool = True):
        """
        Stop the spinner animation.

        Args:
            final_message: Optional message to display after stopping
            success: Whether the operation was successful (affects the symbol shown)
        """
        if self.spinning:
            self.spinning = False
            if self.thread:
                self.thread.join()

            # Clear the spinner line completely
            sys.stdout.write('\r' + ' ' * 80 + '\r')

            # Write final message if provided
            if final_message:
                symbol = '✓' if success else '✗'
                sys.stdout.write(f'{symbol} {final_message}\n')

            sys.stdout.flush()

    def __enter__(self):
        """Context manager entry - start the spinner."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop the spinner."""
        success = exc_type is None
        self.stop(success=success)
        return False


def with_spinner(message: str = "Processing"):
    """
    Decorator to add a spinner to a function.

    Usage:
        @with_spinner("Loading data")
        def load_data():
            # ... long running operation
            return data
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            spinner = Spinner(message)
            spinner.start()
            try:
                result = func(*args, **kwargs)
                spinner.stop(success=True)
                return result
            except Exception as e:
                spinner.stop(success=False)
                raise e
        return wrapper
    return decorator


# Convenience functions for common operations
def show_progress(message: str = "Processing", total: Optional[int] = None):
    """
    Show progress with optional item count.

    Args:
        message: The base message to display
        total: Optional total number of items being processed
    """
    if total:
        return Spinner(f"{message} ({total} items)")
    return Spinner(message)
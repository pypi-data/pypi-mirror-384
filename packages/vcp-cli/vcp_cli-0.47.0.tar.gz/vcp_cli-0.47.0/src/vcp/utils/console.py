"""
Utility functions to normalize rich text outptut to the console.
"""

from shutil import get_terminal_size


# get terminal width for formatting
def get_term_width(default: int = 100) -> int:
    """Return current terminal width (columns) or a sensible fallback."""
    try:
        return max(40, get_terminal_size(fallback=(default, 24)).columns)
    except Exception:
        return default

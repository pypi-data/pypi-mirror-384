"""
WikiTree API Python Client
exceptions.py

Custom exception classes for the WikiTree API client.
Copyright (c) 2025 Steven Harris
License: GPL-3.0-only
"""

class WikiTreeAPIError(Exception):
    """Raised when the WikiTree API returns an error or unexpected data."""

    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload

    def __str__(self):
        base = super().__str__()
        if self.status not in (None, 0, "0"):
            base += f" (status: {self.status})"
        return base

"""
WikiTree API Python Client
utils.py

Helper functions for request and response handling within the WikiTree API client.
Includes safe JSON parsing and simple status extraction logic.
Copyright (c) 2025 Steven Harris
License: GPL-3.0-only
"""

from typing import Any


def ensure_json(payload: Any) -> Any:
    """
    Verify that a response payload is a JSON-compatible structure
    (dict or list). Raise ValueError if not.

    :param payload: Parsed response object
    :return: The same payload if valid
    """
    if isinstance(payload, (dict, list)):
        return payload
    raise ValueError("Expected JSON object or array from API response")


def extract_status(payload: Any):
    """
    Attempt to extract a 'status' value from a WikiTree API response.

    Many actions return a list with one object that contains a
    'status' field; others return a single object. This helper
    normalizes that behavior for easier inspection.

    :param payload: API response (list or dict)
    :return: Status value (int, str, or None)
    """
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict) and "status" in first:
            return first.get("status")

    if isinstance(payload, dict) and "status" in payload:
        return payload.get("status")

    return None

"""
WikiTree API Python Client
__init__.py

Package initializer for the WikiTree API client.
Provides public access to core classes and constants.
Copyright (c) 2025 Steven Harris
License: GPL-3.0-only
"""

from .session import WikiTreeSession
from .exceptions import WikiTreeAPIError

__all__ = ["WikiTreeSession", "WikiTreeAPIError"]

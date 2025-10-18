"""
Antonnia Events SDK

This package provides event types and utilities for working with Antonnia webhook events.
"""

from .types import (
    App,
    AppUpdateFields,
    AppConnection,
)

__version__ = "1.0.2"

__all__ = [
    # Event types
    "App",
    "AppUpdateFields",
    "AppConnection",
] 
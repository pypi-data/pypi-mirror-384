"""Temporal-specific error definitions.

This module defines custom exception classes for Temporal worker operations,
extending the base ArchiPy error handling patterns.
"""

from typing import Any

from archipy.models.errors.base_error import BaseError


class TemporalError(BaseError):
    """Base exception for all Temporal-related errors.

    This is the root exception class for all Temporal workflow engine errors
    within the ArchiPy system.
    """

    pass


class WorkerConnectionError(TemporalError):
    """Exception raised when a worker fails to connect to Temporal server."""

    def __init__(
        self,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the worker connection error."""
        super().__init__(additional_data=additional_data)


class WorkerShutdownError(TemporalError):
    """Exception raised when a worker fails to shutdown gracefully."""

    def __init__(
        self,
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the worker shutdown error."""
        super().__init__(additional_data=additional_data)

"""
Signal handling utilities for graceful cancellation.

Provides support for handling SIGTERM and other signals for graceful shutdown
in GitHub Actions workflows.
"""

from __future__ import annotations

import signal
from collections.abc import Callable
from typing import Any

from .exceptions import CancellationRequested
from .print_messages import warning


class CancellationHandler:
    """
    Unified handler for managing cancellation signals in GitHub Actions workflows.

    Provides methods to enable/disable signal handling, register cleanup handlers,
    and check cancellation status.
    """

    def __init__(self) -> None:
        self._handlers: list[Callable[[], None]] = []
        self._original_handlers: dict[signal.Signals, Any] = {}
        self._enabled: bool = False

    def register(self, handler: Callable[[], None]) -> None:
        """
        Register a handler to be called on cancellation.

        The handler will be called when SIGTERM or SIGINT is received, before
        raising CancellationRequested. Handlers should perform cleanup operations.

        Example:
            def cleanup():
                print("Cleaning up resources...")

            cancellation.register(cleanup)

        :param handler: Function to call on cancellation (takes no arguments)
        """
        self._handlers.append(handler)

    def enable(self) -> None:
        """
        Enable automatic handling of cancellation signals.

        Sets up signal handlers for SIGTERM and SIGINT that will:
        1. Call all registered cancellation handlers
        2. Raise CancellationRequested exception

        This allows code to gracefully handle cancellation in GitHub Actions workflows.

        Example:
            cancellation = CancellationHandler()
            cancellation.enable()
            try:
                # Your long-running operation
                pass
            except CancellationRequested:
                print("Operation was cancelled")
        """
        if self._enabled:
            return

        self._original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, self._handle_signal)
        self._original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, self._handle_signal)

        self._enabled = True

    def disable(self) -> None:
        """
        Disable automatic handling of cancellation signals.

        Restores original signal handlers. Useful for testing or when you need
        to temporarily disable cancellation handling.
        """
        if not self._enabled:
            return

        for sig, original_handler in self._original_handlers.items():
            if original_handler is not None:
                signal.signal(sig, original_handler)

        self._original_handlers.clear()
        self._enabled = False

    def is_enabled(self) -> bool:
        """
        Check if cancellation support is currently enabled.

        :returns: True if cancellation handlers are registered, False otherwise
        """
        return self._enabled

    def _handle_signal(self, signum: int, frame: Any) -> None:  # pyright: ignore[reportUnusedParameter]
        """Handle cancellation signals by calling registered handlers and raising exception."""
        signal_name = signal.Signals(signum).name
        warning(f"Received {signal_name} signal. Initiating graceful shutdown...")

        for handler in self._handlers:
            try:
                handler()
            except Exception as e:  # noqa: BLE001
                warning(f"Error in cancellation handler: {e}")

        raise CancellationRequested(f"Operation cancelled by {signal_name} signal")

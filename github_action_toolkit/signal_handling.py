"""
Signal handling utilities for graceful cancellation.

Provides support for handling SIGTERM and other signals for graceful shutdown
in GitHub Actions workflows.
"""

from __future__ import annotations

import signal
from collections.abc import Callable
from typing import Any

from .print_messages import warning


class CancellationRequested(Exception):
    """
    Raised when a cancellation signal (SIGTERM, SIGINT) is received.

    This allows code to handle cancellation gracefully by catching this exception.
    """


_cancellation_handlers: list[Callable[[], None]] = []
_original_handlers: dict[signal.Signals, Any] = {}
_cancellation_registered = False


def _handle_cancellation_signal(signum: int, frame: Any) -> None:  # pyright: ignore[reportUnusedParameter]
    """Handle cancellation signals by calling registered handlers and raising exception."""
    signal_name = signal.Signals(signum).name
    warning(f"Received {signal_name} signal. Initiating graceful shutdown...")

    for handler in _cancellation_handlers:
        try:
            handler()
        except Exception as e:  # noqa: BLE001
            warning(f"Error in cancellation handler: {e}")

    raise CancellationRequested(f"Operation cancelled by {signal_name} signal")


def register_cancellation_handler(handler: Callable[[], None]) -> None:
    """
    Register a handler to be called on cancellation.

    The handler will be called when SIGTERM or SIGINT is received, before
    raising CancellationRequested. Handlers should perform cleanup operations.

    Example:
        def cleanup():
            print("Cleaning up resources...")

        register_cancellation_handler(cleanup)

    :param handler: Function to call on cancellation (takes no arguments)
    """
    _cancellation_handlers.append(handler)


def enable_cancellation_support() -> None:
    """
    Enable automatic handling of cancellation signals.

    Sets up signal handlers for SIGTERM and SIGINT that will:
    1. Call all registered cancellation handlers
    2. Raise CancellationRequested exception

    This allows code to gracefully handle cancellation in GitHub Actions workflows.

    Example:
        enable_cancellation_support()
        try:
            # Your long-running operation
            pass
        except CancellationRequested:
            print("Operation was cancelled")
    """
    global _cancellation_registered  # noqa: PLW0603

    if _cancellation_registered:
        return

    _original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, _handle_cancellation_signal)
    _original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, _handle_cancellation_signal)

    _cancellation_registered = True


def disable_cancellation_support() -> None:
    """
    Disable automatic handling of cancellation signals.

    Restores original signal handlers. Useful for testing or when you need
    to temporarily disable cancellation handling.
    """
    global _cancellation_registered  # noqa: PLW0603

    if not _cancellation_registered:
        return

    for sig, original_handler in _original_handlers.items():
        if original_handler is not None:
            signal.signal(sig, original_handler)

    _original_handlers.clear()
    _cancellation_registered = False


def is_cancellation_enabled() -> bool:
    """
    Check if cancellation support is currently enabled.

    :returns: True if cancellation handlers are registered, False otherwise
    """
    return _cancellation_registered

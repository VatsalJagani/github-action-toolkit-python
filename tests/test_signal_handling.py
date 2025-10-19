# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false

import signal
import time

import pytest

import github_action_toolkit as gat


def test_enable_disable_cancellation_support():
    """Test enabling and disabling cancellation support."""
    assert not gat.is_cancellation_enabled()

    gat.enable_cancellation_support()
    assert gat.is_cancellation_enabled()

    gat.disable_cancellation_support()
    assert not gat.is_cancellation_enabled()


def test_enable_cancellation_support_idempotent():
    """Test that enabling cancellation support multiple times is safe."""
    gat.enable_cancellation_support()
    gat.enable_cancellation_support()
    assert gat.is_cancellation_enabled()

    gat.disable_cancellation_support()


def test_disable_cancellation_support_idempotent():
    """Test that disabling cancellation support multiple times is safe."""
    gat.disable_cancellation_support()
    gat.disable_cancellation_support()
    assert not gat.is_cancellation_enabled()


def test_register_cancellation_handler():
    """Test registering cancellation handlers."""
    handler_called = []

    def handler():
        handler_called.append(True)

    gat.register_cancellation_handler(handler)
    gat.enable_cancellation_support()

    try:
        with pytest.raises(gat.CancellationRequested):
            signal.raise_signal(signal.SIGTERM)

        assert len(handler_called) == 1
    finally:
        gat.disable_cancellation_support()


def test_multiple_cancellation_handlers():
    """Test that multiple handlers are called in order."""
    call_order = []

    def handler1():
        call_order.append(1)

    def handler2():
        call_order.append(2)

    gat.register_cancellation_handler(handler1)
    gat.register_cancellation_handler(handler2)
    gat.enable_cancellation_support()

    try:
        with pytest.raises(gat.CancellationRequested):
            signal.raise_signal(signal.SIGTERM)

        assert call_order == [1, 2]
    finally:
        gat.disable_cancellation_support()


def test_cancellation_handler_exceptions_are_caught():
    """Test that exceptions in handlers don't prevent other handlers from running."""
    call_order = []

    def failing_handler():
        call_order.append(1)
        raise RuntimeError("Handler failed")

    def successful_handler():
        call_order.append(2)

    gat.register_cancellation_handler(failing_handler)
    gat.register_cancellation_handler(successful_handler)
    gat.enable_cancellation_support()

    try:
        with pytest.raises(gat.CancellationRequested):
            signal.raise_signal(signal.SIGTERM)

        assert call_order == [1, 2]
    finally:
        gat.disable_cancellation_support()

# pyright: reportPrivateUsage=false
# pyright: reportUnusedVariable=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

import signal

import pytest

import github_action_toolkit as gat
from github_action_toolkit.exceptions import CancellationRequested


def test_enable_disable_cancellation_support():
    """Test enabling and disabling cancellation support."""
    handler = gat.CancellationHandler()
    assert not handler.is_enabled()

    handler.enable()
    assert handler.is_enabled()

    handler.disable()
    assert not handler.is_enabled()


def test_enable_cancellation_support_idempotent():
    """Test that enabling cancellation support multiple times is safe."""
    handler = gat.CancellationHandler()
    handler.enable()
    handler.enable()
    assert handler.is_enabled()

    handler.disable()


def test_disable_cancellation_support_idempotent():
    """Test that disabling cancellation support multiple times is safe."""
    handler = gat.CancellationHandler()
    handler.disable()
    handler.disable()
    assert not handler.is_enabled()


def test_register_cancellation_handler():
    """Test registering cancellation handlers."""
    handler_called = []

    def handler():
        handler_called.append(True)

    cancellation = gat.CancellationHandler()
    cancellation.register(handler)
    cancellation.enable()

    try:
        with pytest.raises(CancellationRequested):
            signal.raise_signal(signal.SIGTERM)

        assert len(handler_called) == 1
    finally:
        cancellation.disable()


def test_multiple_cancellation_handlers():
    """Test that multiple handlers are called in order."""
    call_order = []

    def handler1():
        call_order.append(1)

    def handler2():
        call_order.append(2)

    cancellation = gat.CancellationHandler()
    cancellation.register(handler1)
    cancellation.register(handler2)
    cancellation.enable()

    try:
        with pytest.raises(CancellationRequested):
            signal.raise_signal(signal.SIGTERM)

        assert call_order == [1, 2]
    finally:
        cancellation.disable()


def test_cancellation_handler_exceptions_are_caught():
    """Test that exceptions in handlers don't prevent other handlers from running."""
    call_order = []

    def failing_handler():
        call_order.append(1)
        raise RuntimeError("Handler failed")

    def successful_handler():
        call_order.append(2)

    cancellation = gat.CancellationHandler()
    cancellation.register(failing_handler)
    cancellation.register(successful_handler)
    cancellation.enable()

    try:
        with pytest.raises(CancellationRequested):
            signal.raise_signal(signal.SIGTERM)

        assert call_order == [1, 2]
    finally:
        cancellation.disable()

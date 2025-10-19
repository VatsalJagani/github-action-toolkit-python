#!/usr/bin/env python3
"""
Example demonstrating the developer experience improvements in github-action-toolkit.

This example shows:
1. Custom exception handling with specific exception types
2. Scoped environment variable management
3. Graceful cancellation support
4. Actionable error messages
"""

import time

import github_action_toolkit as gat


def demo_exception_handling():
    """Demonstrate exception handling with specific exception types."""
    gat.info("=== Exception Handling Demo ===")

    # Example 1: Catching specific exceptions
    try:
        # This will raise InputError if value cannot be converted
        timeout = gat.get_user_input_as("timeout", int, default_value=30)
        gat.info(f"Timeout set to: {timeout} seconds")
    except gat.InputError as e:
        gat.warning(f"Invalid input: {e}")
        # Error message is actionable and explains how to fix
        timeout = 30
        gat.info(f"Using default timeout: {timeout} seconds")

    # Example 2: Catching base exception for all toolkit errors
    try:
        # Simulate an operation that might fail
        pass
    except gat.GitHubActionError as e:
        gat.error(f"Toolkit error occurred: {e}")
        # All toolkit exceptions inherit from GitHubActionError


def demo_scoped_environment():
    """Demonstrate scoped environment variable management."""
    gat.info("=== Scoped Environment Demo ===")

    import os

    # Example 1: Temporary environment variables
    original_value = os.environ.get("MY_TEMP_VAR", "not set")
    gat.info(f"Before context: MY_TEMP_VAR = {original_value}")

    with gat.with_env(MY_TEMP_VAR="temporary", ANOTHER_VAR="test"):
        gat.info(f"Inside context: MY_TEMP_VAR = {os.environ['MY_TEMP_VAR']}")
        gat.info(f"Inside context: ANOTHER_VAR = {os.environ['ANOTHER_VAR']}")

    restored_value = os.environ.get("MY_TEMP_VAR", "not set")
    gat.info(f"After context: MY_TEMP_VAR = {restored_value}")


def demo_cancellation_support():
    """Demonstrate graceful cancellation support."""
    gat.info("=== Cancellation Support Demo ===")

    # Track cleanup state
    cleanup_called = False

    def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
        gat.warning("Cleanup handler called - closing connections...")
        # Perform cleanup operations
        time.sleep(0.1)

    # Register cleanup handler
    gat.register_cancellation_handler(cleanup_handler)

    # Enable cancellation support
    gat.enable_cancellation_support()
    gat.info("Cancellation support enabled")

    # Simulate long-running operation
    try:
        gat.info("Starting long-running operation...")
        gat.info("Press Ctrl+C to test cancellation (or let it complete)")

        for i in range(5):
            gat.info(f"Processing item {i+1}/5...")
            time.sleep(0.5)

        gat.info("Operation completed successfully")

    except gat.CancellationRequested as e:
        gat.warning(f"Operation cancelled: {e}")
        # Cleanup handler was already called
        gat.info(f"Cleanup executed: {cleanup_called}")

    finally:
        # Disable cancellation support (cleanup)
        gat.disable_cancellation_support()


def demo_actionable_errors():
    """Demonstrate actionable error messages."""
    gat.info("=== Actionable Error Messages Demo ===")

    # Example 1: Configuration error with clear guidance
    try:
        # This will fail because no url or path is provided
        repo = gat.Repo()
    except gat.ConfigurationError as e:
        gat.warning("Got expected configuration error:")
        gat.info(f"  {e}")
        # Error message explains what's wrong and how to fix it

    # Example 2: Environment error with context
    import os

    # Temporarily clear GITHUB_OUTPUT to demonstrate error
    original_output = os.environ.pop("GITHUB_OUTPUT", None)

    try:
        gat.set_output("test", "value")
    except gat.EnvironmentVariableError as e:
        gat.warning("Got expected environment error:")
        gat.info(f"  {e}")
        # Error message explains the requirement and solution

    # Restore original value
    if original_output:
        os.environ["GITHUB_OUTPUT"] = original_output


def main():
    """Run all demos."""
    gat.info("Developer Experience Improvements Demo")
    gat.info("=" * 50)

    with gat.group("Exception Handling"):
        demo_exception_handling()

    with gat.group("Scoped Environment Variables"):
        demo_scoped_environment()

    with gat.group("Actionable Error Messages"):
        demo_actionable_errors()

    with gat.group("Cancellation Support"):
        demo_cancellation_support()

    gat.info("=" * 50)
    gat.info("Demo completed! ✓")


if __name__ == "__main__":
    main()

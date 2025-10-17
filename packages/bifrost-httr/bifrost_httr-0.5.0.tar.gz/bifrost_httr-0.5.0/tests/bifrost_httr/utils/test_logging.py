"""Tests for logging utilities."""

import logging

import pytest

from bifrost_httr.utils.logging import (
    configure_logging,
    get_logger,
    is_logging_configured,
)


def test_configure_logging() -> None:
    """Test logging configuration."""
    # Initial configuration
    configure_logging()
    logger = logging.getLogger("bifrost")
    assert len(logger.handlers) == 1
    assert logger.level == logging.INFO
    assert not logger.propagate

    # Check handler configuration
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.level == logging.INFO
    assert isinstance(handler.formatter, logging.Formatter)

    # Test that calling configure_logging again doesn't add duplicate handlers
    configure_logging()
    assert len(logger.handlers) == 1

    # Test force reconfigure
    configure_logging(force_reconfigure=True)
    assert len(logger.handlers) == 1  # Should still be 1 after reconfigure


def test_get_logger() -> None:
    """Test logger retrieval."""
    # Test with module name
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "bifrost.test_module"

    # Test with already prefixed name
    logger = get_logger("bifrost.test_module")
    assert logger.name == "bifrost.test_module"

    # Verify parent logger is configured
    bifrost_logger = logging.getLogger("bifrost")
    assert len(bifrost_logger.handlers) > 0
    assert not bifrost_logger.propagate


def test_is_logging_configured() -> None:
    """Test logging configuration state check."""
    # This test relies on the fact that configure_logging was called in previous tests
    # or by get_logger
    assert is_logging_configured()

    # Force reconfigure and check
    configure_logging(force_reconfigure=True)
    assert is_logging_configured()


def test_logger_output(caplog: pytest.LogCaptureFixture) -> None:
    """Test actual logger output.

    Args:
        caplog: Pytest fixture for capturing log output
    """
    # Ensure logging is configured
    configure_logging()

    logger = get_logger("test_output")
    test_message = "Test log message"

    # The bifrost logger has propagate=False and uses its own handler
    # So we need to temporarily enable propagation to capture with caplog
    bifrost_logger = logging.getLogger("bifrost")
    original_propagate = bifrost_logger.propagate
    bifrost_logger.propagate = True

    try:
        with caplog.at_level(logging.INFO):
            logger.info(test_message)

        # Check that the message was captured
        assert len(caplog.records) > 0
        assert test_message in caplog.text
        assert "bifrost.test_output" in caplog.records[-1].name
    finally:
        # Restore original propagate setting
        bifrost_logger.propagate = original_propagate

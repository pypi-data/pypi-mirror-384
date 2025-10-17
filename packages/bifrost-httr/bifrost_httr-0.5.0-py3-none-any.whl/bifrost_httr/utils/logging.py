# Bifrost-HTTr- transcriptomics based dose response analysis
# Copyright (C) 2025 as Unilever Global IP Limited
# Bifrost-HTTr is free software: you can redistribute it and/or modify it under the terms
# of the GNU Lesser General Public License as published by the Free Software Foundation,
# either version 3 of the License. Bifrost-HTTr is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with Bifrost-HTTr.
# If not, see https://www.gnu.org/licenses/ . It is the responsibility of Bifrost-HTTr users to
# familiarise themselves with all dependencies and their associated licenses.

"""Logging configuration for BIFROST package.

This module provides centralized logging configuration to ensure consistent
logging behavior across the package.
"""

import logging

# Global flag to track if logging has been configured
_logging_configured = False


def configure_logging(*, force_reconfigure: bool = False) -> None:
    """Configure logging for the BIFROST package.

    This function uses a singleton pattern to ensure logging is configured only once,
    preventing duplicate handlers and configuration conflicts.

    Args:
        force_reconfigure: If True, forces reconfiguration even if already configured

    This function:
    1. Sets up a consistent format for log messages
    2. Ensures no duplicate handlers are added
    3. Sets appropriate log levels
    4. Only configures once unless force_reconfigure=True

    """
    global _logging_configured

    # Skip if already configured unless forced
    if _logging_configured and not force_reconfigure:
        return

    # Get the root logger for bifrost
    logger = logging.getLogger("bifrost")

    # Remove any existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create our handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Prevent the log messages from being propagated to the root logger
    logger.propagate = False

    # Mark as configured
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    This is the preferred way to get a logger in the BIFROST package.
    It ensures the logger is properly named and will use the centralized configuration.

    Args:
        name: Usually __name__ of the calling module

    Returns:
        A configured logger instance

    """
    # Ensure logging is configured before returning any logger
    configure_logging()

    # If name doesn't start with bifrost, add it as a prefix
    if not name.startswith("bifrost"):
        name = f"bifrost.{name}"
    return logging.getLogger(name)


def is_logging_configured() -> bool:
    """Check if logging has been configured.

    Returns:
        True if logging has been configured, False otherwise

    """
    return _logging_configured

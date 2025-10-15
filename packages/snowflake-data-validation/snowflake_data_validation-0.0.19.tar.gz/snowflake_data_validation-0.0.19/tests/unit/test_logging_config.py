#!/usr/bin/env python3
"""Test script for logging configuration functionality."""

import logging
import sys
from pathlib import Path

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent / "snowflake-data-validation" / "src"))

from snowflake.snowflake_data_validation.configuration.model.logging_configuration import (
    LoggingConfiguration,
)
from snowflake.snowflake_data_validation.utils.logging_config import setup_logging


def test_logging_configuration():
    """Test the logging configuration functionality."""
    print("Testing logging configuration...")

    # Test 1: Basic logging configuration
    print("\n1. Testing basic logging configuration...")
    setup_logging(log_level="DEBUG")

    logger = logging.getLogger("test")
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    # Test 2: Different console and file levels
    print("\n2. Testing different console and file levels...")
    setup_logging(log_level="INFO", console_level="WARNING", file_level="DEBUG")

    logger.debug("This DEBUG message should only appear in file")
    logger.info("This INFO message should only appear in file")
    logger.warning("This WARNING message should appear in both console and file")
    logger.error("This ERROR message should appear in both console and file")

    # Test 3: LoggingConfiguration model
    print("\n3. Testing LoggingConfiguration model...")
    config = LoggingConfiguration(
        level="INFO", console_level="ERROR", file_level="DEBUG"
    )

    print(f"Console level: {config.get_console_level()}")
    print(f"File level: {config.get_file_level()}")
    print(f"Console level int: {config.get_console_level_int()}")
    print(f"File level int: {config.get_file_level_int()}")

    # Test 4: Validation
    print("\n4. Testing validation...")
    try:
        invalid_config = LoggingConfiguration(level="INVALID")
        print("ERROR: Should have failed validation")
    except ValueError as e:
        print(f"✓ Validation correctly caught invalid level: {e}")

    print("\n✓ All logging configuration tests completed!")


if __name__ == "__main__":
    test_logging_configuration()

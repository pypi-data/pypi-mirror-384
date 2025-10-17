
#!/usr/bin/env python3
"""
This module provides file-related utility functions for the EPUB reader.
"""

import logging
import os
import tempfile
from typing import List

# Set up logging
logger = logging.getLogger(__name__)

_temp_files: List[str] = []


def ensure_directory(path: str) -> None:
    """
    Ensures that a directory exists. If it doesn't, it creates it.

    Args:
        path (str): The path to the directory.
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            logger.debug(f"Created directory: {path}")
        except OSError as e:
            logger.error(f"Error creating directory {path}: {e}")
            raise


def get_temp_dir() -> str:
    """
    Gets the path to a temporary directory for the application.

    Returns:
        str: The path to the temporary directory.
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "speakub")
    ensure_directory(temp_dir)
    return temp_dir


def cleanup_temp_files() -> None:
    """
    Removes all temporary files created during the session.
    """
    global _temp_files
    for temp_file in _temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"Removed temporary file: {temp_file}")
        except OSError as e:
            logger.error(f"Error removing temporary file {temp_file}: {e}")
    _temp_files = []


# Example usage (for testing)
if __name__ == "__main__":
    # Test ensure_directory
    test_dir = os.path.join(get_temp_dir(), "test_dir")
    print(f"Ensuring directory exists: {test_dir}")
    ensure_directory(test_dir)
    print(f"Directory exists: {os.path.exists(test_dir)}")

    # Test get_temp_dir
    app_temp_dir = get_temp_dir()
    print(f"Application temporary directory: {app_temp_dir}")
    print(f"Temp dir exists: {os.path.exists(app_temp_dir)}")

    # Clean up test directory
    if os.path.exists(test_dir):
        os.rmdir(test_dir)
        print(f"Cleaned up test directory: {test_dir}")

    print("File utils test complete.")

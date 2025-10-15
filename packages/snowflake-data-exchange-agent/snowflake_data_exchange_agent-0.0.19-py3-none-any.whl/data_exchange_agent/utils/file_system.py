"""
File system utility functions.

This module provides utility functions for file and directory operations
including deletion, cleanup, and file system management tasks used
throughout the data exchange agent.
"""

import os
import shutil

from data_exchange_agent.utils.decorators import log_error


@log_error
def delete_folder_file(folder_path: str) -> None:
    """
    Delete a file or folder and all its contents recursively.

    Args:
        folder_path (str): Path to the file or folder to delete

    Returns:
        None

    """
    if os.path.exists(folder_path):
        if os.path.isfile(folder_path):
            os.remove(folder_path)
        else:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    delete_folder_file(file_path)  # Recursively handle subdirectories

            shutil.rmtree(folder_path)


@log_error
def delete_file(file_path: str) -> None:
    """
    Delete a single file if it exists.

    Args:
        file_path (str): Path to the file to delete

    Returns:
        None

    """
    if os.path.exists(file_path):
        os.remove(file_path)


@log_error
def file_exists(file_path: str) -> bool:
    """
    Check if a file exists at the given path.

    Args:
        file_path (str): Path to check for file existence

    Returns:
        bool: True if file exists, False otherwise

    """
    return os.path.exists(file_path)

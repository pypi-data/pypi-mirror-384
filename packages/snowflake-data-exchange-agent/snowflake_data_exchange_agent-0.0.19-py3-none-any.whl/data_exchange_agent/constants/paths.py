"""
Path constants and utilities for the data exchange agent.

This module defines standard file and directory paths used throughout the
data exchange agent, including database paths, configuration paths, and
result storage locations.
"""

import os

from datetime import datetime


def _get_home_dir() -> str:
    """
    Get the user's home directory path.

    Returns:
        str: The absolute path to the user's home directory.

    """
    return os.path.expanduser("~")


APP_FOLDER_PATH = os.path.join(_get_home_dir(), ".data_exchange_agent")
ROOT_DBS_FOLDER_PATH = os.path.join(APP_FOLDER_PATH, "dbs")
ROOT_JARS_FOLDER_PATH = os.path.join(APP_FOLDER_PATH, "jars")
ROOT_LOGS_FOLDER_PATH = os.path.join(APP_FOLDER_PATH, "logs")
ROOT_RESULTS_FOLDER_PATH = os.path.join(APP_FOLDER_PATH, "result_data")
DB_TASKS_FILE_PATH = os.path.join(ROOT_DBS_FOLDER_PATH, "data_exchange_tasks.db")
CONFIGURATION_FILE_PATH = "src/data_exchange_agent/configuration.toml"


def build_actual_results_folder_path(task_id: str = None) -> str:
    """
    Build the actual results folder path.

    Args:
        task_id (str): The task ID (optional)

    Returns:
        str: The actual results folder path

    """
    task_id_folder_name = _get_task_id_folder_name(task_id)
    timestamp_string = _get_timestamp_string()

    results_folder_path = os.path.join(
        ROOT_RESULTS_FOLDER_PATH,
        task_id_folder_name,
        timestamp_string,
    )
    return results_folder_path


def _get_task_id_folder_name(task_id: str | None) -> str:
    """
    Get the task ID folder name.

    Args:
        task_id (str): The task ID

    """
    return f"task_{task_id}" if task_id else "unknown_task_id"


def _get_timestamp_string() -> str:
    """Get the timestamp string."""
    now = datetime.now()
    milliseconds = now.microsecond // 1000
    timestamp_string = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{milliseconds:03d}"
    return timestamp_string

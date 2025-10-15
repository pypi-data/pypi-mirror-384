"""
API management module for handling external API interactions.

This module provides the APIManager class for managing communication with
external APIs, including authentication, task retrieval, and status updates.
"""

import os

import requests
import toml

from data_exchange_agent.constants.paths import CONFIGURATION_FILE_PATH
from data_exchange_agent.constants.snow_api import BASE_URL
from data_exchange_agent.utils.decorators import log_error


class APIManager:
    """
    Manages API interactions for the Data Exchange Agent.

    This class handles communication with the external API service, including:
    - Loading API authentication credentials
    - Retrieving tasks from the API
    - Updating task status and details

    The API key is loaded from a TOML configuration file and used to authenticate requests.
    """

    def __init__(self) -> None:
        """
        Initialize the APIManager.

        Sets up the API key attribute and loads the key from configuration.
        """
        self.api_key = None
        self.load_api_key()

    @log_error
    def load_api_key(self) -> None:
        """
        Load the API key from the TOML configuration file.

        Reads the API key from the configuration file if it exists and contains
        the required api_configuration section with a key field.
        """
        if os.path.exists(CONFIGURATION_FILE_PATH):
            toml_config = toml.load(CONFIGURATION_FILE_PATH)
            if (
                "api_configuration" in toml_config
                and "key" in toml_config["api_configuration"]
            ):
                self.api_key = toml_config["api_configuration"]["key"]

    @log_error
    def get_tasks(self) -> list[dict]:
        """
        Retrieve tasks from the API.

        Makes an authenticated GET request to fetch tasks for the specified agent and group.

        Returns:
            list[dict]: List of task dictionaries from the API response

        Raises:
            Exception: If the API request fails

        """
        response = requests.get(
            f"{BASE_URL}/tasks?agent_id=1&group_id=1",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get tasks: {response.status_code}")

    @log_error
    def update_task(self, update_data: dict) -> dict:
        """
        Update the status and details of a task.

        Makes a PUT request to update a task's status and details in the API.

        Args:
            update_data: Dictionary containing task_id, status and details to update

        Returns:
            dict: API response data on success, or error message on failure

        """
        response = requests.put(
            f"{BASE_URL}/tasks/{update_data['task_id']}",
            json={
                "status": update_data["status"],
                "details": update_data["details"],
            },
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"message": f"Failed to update task: {response.status_code}"}

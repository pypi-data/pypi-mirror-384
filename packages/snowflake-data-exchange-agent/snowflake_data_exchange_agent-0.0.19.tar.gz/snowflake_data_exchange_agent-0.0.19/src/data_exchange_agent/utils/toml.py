"""TOML configuration file utilities for the data exchange agent."""

import os

import toml

from data_exchange_agent import custom_exceptions
from data_exchange_agent.utils.decorators import log_error


@log_error
def load_toml_file(file_path: str) -> dict | None:
    """
    Load a TOML file and return the contents as a dictionary.

    Args:
        file_path (str): The path to the TOML file to load

    Returns:
        dict | None: The contents of the TOML file as a dictionary or None if the file does not exist

    """
    if not os.path.exists(file_path):
        return None
    return toml.load(file_path)


@log_error
def get_snowflake_connection_name(configuration_file_path: str) -> str | None:
    """
    Get the Snowflake connection name from the TOML file.

    Args:
        configuration_file_path (str): The path to the configuration TOML file

    Returns:
        str | None: The Snowflake connection name or None if the connection name is not found

    """
    configuration_toml = load_toml_file(configuration_file_path)
    if (
        configuration_toml
        and "connection" in configuration_toml
        and "snowflake" in configuration_toml["connection"]
        and "connection_name" in configuration_toml["connection"]["snowflake"]
    ):
        return configuration_toml["connection"]["snowflake"]["connection_name"]
    return None


@log_error
def get_connection_and_cloud_storage_toml(
    configuration_file_path: str,
) -> tuple[dict, dict]:
    """
    Get the connection and cloud storage configurations from the TOML file.

    Loads the configuration file and extracts both the connection settings
    for databases and cloud storage settings.

    Args:
        configuration_file_path (str): The path to the configuration TOML file

    Raises:
        custom_exceptions.ConfigurationError: If the configuration file cannot be loaded
            or if the connection or cloud storage configuration is not found

    Returns:
        tuple[dict, dict]: A tuple containing (connection_config, cloud_storage_config)

    """
    configuration_toml = load_toml_file(configuration_file_path)
    if not configuration_toml:
        raise custom_exceptions.ConfigurationError(
            f"Failed to load configuration file '{configuration_file_path}'. "
            "Please check if the file exists and is a valid TOML file."
        )
    if "connection" not in configuration_toml:
        raise custom_exceptions.ConfigurationError(
            "Connection configuration not found in the configuration TOML file. "
            f"Please check the connection section in the '{configuration_file_path}' file."
        )
    if "cloud_storage" not in configuration_toml:
        raise custom_exceptions.ConfigurationError(
            "Cloud storage configuration not found in the configuration TOML file. "
            f"Please check the cloud storage section in the '{configuration_file_path}' file."
        )
    return configuration_toml["connection"], configuration_toml["cloud_storage"]


# Alias for backwards compatibility - tests expect this function name
load = load_toml_file

"""
Uploader interface for data exchange agent.

This module defines the abstract interface for uploading files to different
storage systems (e.g., S3, Snowflake stages). It provides a standard contract
that all uploader implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any


class UploaderInterface(ABC):
    """
    Interface for uploading files to a destination.

    This abstract base class defines the interface that uploader implementations
    must follow to provide file upload functionality.
    """

    def __init__(self, cloud_storage_toml: dict | None = None) -> None:
        """
        Initialize the uploader with cloud storage configuration.

        Args:
            cloud_storage_toml (dict | None): Configuration dictionary containing cloud storage
                                            settings from the TOML file. Used to configure
                                            the specific uploader implementation. If None,
                                            an empty dict will be used.

        Attributes:
            cloud_storage_toml (dict): The cloud storage configuration dictionary that will
                                     be used by implementing classes. Contains settings like
                                     bucket names, connection strings, credentials etc.

        """
        if cloud_storage_toml:
            self.cloud_storage_toml = cloud_storage_toml
        else:
            self.cloud_storage_toml = {}
        self.configure()

    @abstractmethod
    def configure(self) -> None:
        """Configure the uploader with cloud storage settings."""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Connect to the uploader."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the uploader."""
        pass

    @abstractmethod
    def upload_file(self, source_path: str, destination_path: str) -> None:
        """
        Upload a file from the given path to the destination.

        Args:
            source_path: The file path to upload from.
            destination_path: The file path to upload to.

        Returns:
            None

        """
        pass

    def __enter__(self) -> "UploaderInterface":
        """
        Enter the runtime context for the uploader.

        Automatically connects to the uploader service when entering the context.

        Returns:
            UploaderInterface: The uploader instance.

        """
        self.connect()
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any
    ) -> None:
        """
        Exit the runtime context for the uploader.

        Automatically disconnects from the uploader service when exiting the context,
        ensuring proper cleanup of resources regardless of whether an exception occurred.

        Args:
            exc_type: The exception type if an exception was raised, None otherwise.
            exc_val: The exception value if an exception was raised, None otherwise.
            exc_tb: The exception traceback if an exception was raised, None otherwise.

        """
        self.disconnect()

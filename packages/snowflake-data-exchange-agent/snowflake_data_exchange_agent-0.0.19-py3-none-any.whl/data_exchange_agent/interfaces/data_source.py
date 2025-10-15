"""
Data source interface definition.

This module defines the abstract base class interface that all data source
implementations must follow for connecting to and extracting data from
various data stores.
"""

from abc import ABC, abstractmethod


class DataSourceInterface(ABC):
    """
    Abstract base class defining the interface for data sources.

    This interface defines the required methods that all data source implementations
    must provide. Data sources are responsible for:
    - Creating connections to the underlying data store
    - Executing statements/queries against the data store
    - Properly closing connections when finished

    Implementations of this interface could include database connections,
    file system access, API clients, etc.
    """

    @abstractmethod
    def create_connection(self):
        """
        Create and return a connection to the data source.

        This method should establish a connection to the underlying data source,
        such as a database, file system, or API. The connection details and
        authentication should be handled based on the specific data source type.

        Returns:
            Connection object specific to the data source implementation

        Raises:
            ConnectionError: If unable to establish connection to the data source
            AuthenticationError: If authentication fails
            custom_exceptions.ConfigurationError: If connection configuration is invalid

        """
        pass

    @abstractmethod
    def execute_statement(self, statement: str, results_folder_path: str = None) -> str:
        """
        Execute a statement against the data source and return results.

        This method executes the provided statement or query against the underlying
        data source and returns the results. The exact format of the statement and
        return value will depend on the specific data source implementation.

        Args:
            statement: The statement or query to execute against the data source.
                      Format depends on the data source type (e.g. SQL, API params)
            results_folder_path (str): The path to the results folder (optional)

        Returns:
            str: The path to the results folder

        Raises:
            ExecutionError: If statement execution fails
            ConnectionError: If connection to data source is lost
            ValidationError: If statement format is invalid

        """
        pass

    @abstractmethod
    def close_connection(self):
        """
        Close the connection to the data source.

        This method should properly close and clean up the connection to the underlying
        data source. This includes releasing any resources, committing/rolling back
        transactions if applicable, and ensuring the connection is fully terminated.

        The default implementation does nothing since some data sources may not require
        explicit connection closing.

        Returns:
            None

        Raises:
            ConnectionError: If error occurs while closing the connection

        """
        pass

"""
Snowflake database connection implementation.

This module provides the SnowflakeDataSource class for connecting to and
executing queries against Snowflake databases using the snowflake-connector-python
library.
"""

from collections.abc import Generator

from data_exchange_agent.constants.paths import CONFIGURATION_FILE_PATH
from data_exchange_agent.interfaces.data_source import DataSourceInterface
from data_exchange_agent.utils.toml import get_snowflake_connection_name


class SnowflakeDataSource(DataSourceInterface):
    """
    A Snowflake implementation of the DataSourceInterface.

    This class provides functionality to connect to and execute queries against a Snowflake database.
    It manages connections using configuration from a Snowflake config file.

    Attributes:
        connection_name (str | None): Name of connection configuration to use from config file
        connection (snowflake.connector.SnowflakeConnection | None): The active Snowflake connection

    """

    def __init__(self, connection_name: str = None) -> None:
        """
        Initialize a new SnowflakeDataSource.

        Args:
            connection_name (str, optional): Name of connection configuration to use.
                If None, uses default connection from config file.

        """
        self.connection_name: str = (
            connection_name
            if connection_name
            else get_snowflake_connection_name(CONFIGURATION_FILE_PATH)
        )
        self.connection = None

    def create_connection(self) -> None:
        """
        Create a new connection to Snowflake if one doesn't exist.

        Uses connection details from ~/.snowflake/config.toml file.
        If connection_name is specified, uses that named connection config,
        otherwise uses the default connection config.
        """
        import snowflake.connector

        if self.connection is not None:
            return
        if self.connection_name is None:
            # Use default connection from snowflake config file (~/.snowflake/config.toml)
            self.connection = snowflake.connector.connect()
        else:
            # Use specified named connection from config file
            self.connection = snowflake.connector.connect(
                connection_name=self.connection_name
            )

    def execute_statement(self, statement: str) -> Generator[any, None, None]:
        """
        Execute a SQL statement against Snowflake.

        Creates a connection if one doesn't exist, then executes the statement
        and yields the results.

        Args:
            statement (str): The SQL statement to execute

        Yields:
            Results from executing the SQL statement

        """
        if self.connection is None:
            self.create_connection()
        with self.connection.cursor() as cursor:
            yield from cursor.execute(statement)

    def is_closed(self) -> bool:
        """
        Check if the Snowflake connection is closed.

        Returns:
            bool: True if connection is closed or doesn't exist, False otherwise

        """
        if self.connection is None:
            return True
        return self.connection.is_closed()

    def close_connection(self) -> None:
        """
        Close the Snowflake connection if one exists.

        Closes the connection and sets it to None.
        """
        if self.connection is not None:
            self.connection.close()
            self.connection = None

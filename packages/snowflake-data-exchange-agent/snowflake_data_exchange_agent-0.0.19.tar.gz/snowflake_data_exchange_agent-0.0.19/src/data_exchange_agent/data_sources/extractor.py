"""
Data extraction utilities for executing statements against data sources.

This module provides the DataSourceExtractor class for executing statements
against various data sources and retrieving results in a standardized format.
"""

from data_exchange_agent.constants.paths import build_actual_results_folder_path
from data_exchange_agent.interfaces.data_source import DataSourceInterface
from data_exchange_agent.utils.decorators import log_error


class DataSourceExtractor:
    """
    A class that extracts data from a data source using a provided statement.

    This class acts as a wrapper around a DataSourceInterface implementation to execute
    statements and retrieve data in a standardized way.

    Attributes:
        statement (str): The statement to execute against the data source
        connection (DataSourceInterface): The data source connection to use for execution

    """

    def __init__(self, statement: str, connection: DataSourceInterface) -> None:
        """
        Initialize a new DataSourceExtractor.

        Args:
            statement (str): The statement to execute against the data source
            connection (DataSourceInterface): The data source connection to use for execution

        """
        self.statement = statement
        self.connection = connection

    @log_error
    def extract_data(self, results_folder_path: str = None) -> str:
        """
        Execute the statement and return the results as a generator.

        Args:
            results_folder_path (str): The path to the results folder

        Returns:
            str: The path to the results folder

        """
        if results_folder_path is None:
            results_folder_path = build_actual_results_folder_path()
        return self.connection.execute_statement(self.statement, results_folder_path)

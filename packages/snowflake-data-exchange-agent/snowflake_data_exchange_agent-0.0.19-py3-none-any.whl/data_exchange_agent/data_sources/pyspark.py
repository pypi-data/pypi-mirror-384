"""
PySpark-based data source implementation.

This module provides the PySparkDataSource class for connecting to and
extracting data from various database engines using Apache Spark. It handles
JDBC connections, query execution, and data export to Parquet format with
dynamic partitioning and resource management.
"""

import logging
import threading
import uuid

import psutil

from pyspark.sql import SparkSession

from data_exchange_agent.constants.paths import build_actual_results_folder_path
from data_exchange_agent.data_sources.database_engines import (
    get_database_engine_from_string,
)
from data_exchange_agent.data_sources.dataset_result_sizes import DatasetResultSize
from data_exchange_agent.data_sources.export_data import (
    export_data_to_parquet_with_jdbc,
)
from data_exchange_agent.data_sources.jdbc_jar_dict import JDBCJarDict
from data_exchange_agent.data_sources.sql_command_type import SQLCommandType
from data_exchange_agent.data_sources.sql_parser import get_read_only_sql_command_type
from data_exchange_agent.interfaces.data_source import DataSourceInterface


class PySparkDataSource(DataSourceInterface):
    """
    A PySpark-based implementation of the DataSourceInterface.

    This class provides a way to execute SQL statements against various databases using PySpark's
    JDBC capabilities. It manages Spark sessions and JDBC driver JAR files for different database types.

    Attributes:
        driver_name (str): The name of the JDBC driver to use (e.g., 'postgresql', 'sqlserver')
        source_authentification_info (dict): Authentication details including url, username, and password
        connection (SparkSession | None): The active Spark session, if one exists
        _lock (threading.Lock): Thread lock for synchronizing Spark session creation
        jdbc_jar_dict (JDBCJarDict): Manager for JDBC driver JAR files

    """

    def __init__(
        self,
        driver_name: str,
        **source_authentification_info: dict,
    ) -> None:
        """
        Initialize a new PySparkDataSource.

        Args:
            driver_name (str): The name of the JDBC driver to use
            **source_authentification_info (dict): Authentication details including:
                - url: JDBC connection URL
                - username: Database username
                - password: Database password

        """
        self.driver_name: str = driver_name
        self.source_authentification_info: dict = source_authentification_info
        self.connection: SparkSession | None = None
        self._lock: threading.Lock = threading.Lock()
        self.jdbc_jar_dict: JDBCJarDict = JDBCJarDict()

    def create_connection(self) -> None:
        """
        Create a new Spark session with JDBC capabilities.

        Downloads required JDBC driver JARs and creates a new Spark session configured
        for stable JDBC connections. Uses thread locking to ensure thread safety.

        Raises:
            Exception: If there is an error creating the Spark connection

        """
        try:
            print("Downloading jars if necessary...")
            self.jdbc_jar_dict.download_all_jars()
            if self.driver_name in self.jdbc_jar_dict.jars:
                with self._lock:
                    # Configure Spark to run in local mode to avoid network issues
                    self.connection = SparkSession.getActiveSession()
                    if SparkSession.getActiveSession() is None:
                        jdbc_jar_paths = self.jdbc_jar_dict.get_all_jar_paths()
                        session_builder: SparkSession.Builder = SparkSession.builder.appName(
                            f"DataExchangeAgent-{self.driver_name}-{uuid.uuid4().hex[:8]}"
                        ).config(
                            "spark.jars", jdbc_jar_paths
                        )
                        session_builder = self._add_spark_session_config(
                            session_builder
                        )
                        print(
                            f"Creating Spark session for {self.driver_name} connection..."
                        )
                        self.connection = session_builder.getOrCreate()
                        print("Spark session created successfully")

        except Exception as e:
            print(f"Error creating Spark connection. Driver name: {self.driver_name}")
            raise e

    def _add_spark_session_config(
        self,
        session_builder: SparkSession.Builder,
        session_config: dict[str, str] = None,
    ) -> SparkSession.Builder:
        if session_config is None:
            mem = psutil.virtual_memory()
            available_mb = mem.available / (1024**2)

            driver_memory_mb = int(available_mb * 0.75)
            logging.info(f"Driver memory: {driver_memory_mb} MB")

            driver_maxresultsize_mb = int(driver_memory_mb * 0.15)
            logging.info(f"Driver max result size: {driver_maxresultsize_mb} MB")

            session_config = {
                "spark.driver.host": "localhost",
                "spark.driver.bindAddress": "0.0.0.0",
                "spark.driver.memory": f"{driver_memory_mb}m",
                "spark.driver.maxResultSize": f"{driver_maxresultsize_mb}m",
                #  # JVM options for direct memory (critical for Snowflake JDBC)
                #  "spark.driver.extraJavaOptions":
                #         f"-XX:MaxDirectMemorySize={driver_maxresultsize_mb}m "
                #         "-XX:+UseG1GC "
                #         "-XX:G1HeapRegionSize=16m "
                #         "-XX:+UnlockExperimentalVMOptions "
                #         "-XX:+UseCGroupMemoryLimitForHeap",
                #  # Executor configuration
                #  "spark.executor.memory": f"{driver_memory_mb}m",
                #  "spark.executor.extraJavaOptions":
                #         f"-XX:MaxDirectMemorySize={driver_maxresultsize_mb}m "
                #         "-XX:+UseG1GC",
                # Serialization and network settings
                "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
                # Adaptive query execution
                "spark.sql.adaptive.enabled": "false",
                "spark.sql.adaptive.coalescePartitions.enabled": "false",
                # Snowflake-specific optimizations
                "spark.sql.execution.arrow.pyspark.enabled": "true",
                # Other options settings
                "spark.network.timeout": "600s",
                "spark.executor.heartbeatInterval": "60s",
                "spark.dynamicAllocation.enabled": "false",
                "spark.shuffle.service.enabled": "false",
            }

        for key, value in session_config.items():
            session_builder = session_builder.config(key, value)

        return session_builder

    def execute_statement(self, statement: str, results_folder_path: str = None) -> str:
        """
        Execute a SQL statement using Spark's JDBC capabilities.

        Executes the given SQL statement against the configured database and returns
        the path to the results folder.

        Args:
            statement (str): The SQL statement to execute
            results_folder_path (str): The path to the results folder (optional)

        Returns:
           str: The path to the results folder

        Raises:
            Exception: If there is no active connection or an error occurs during execution

        """
        if results_folder_path is None:
            results_folder_path = build_actual_results_folder_path()

        try:
            print("*" * 100)
            print(statement)
            print("*" * 100)
            if self.connection is None:
                raise Exception(
                    "No active Spark connection. Call create_connection() first."
                )

            truncated_statement = (
                statement[:100] + "..." if len(statement) > 100 else statement
            )
            print(
                f"""Executing SQL statement: {truncated_statement}
                with driver name: {self.driver_name}"""
            )

            # Use the URL from configuration
            jdbc_url: str = self.source_authentification_info["url"]

            # set the database engine
            database_engine = get_database_engine_from_string(self.driver_name)

            # Check if the SQL statement is a read-only operation
            sql_command_type = get_read_only_sql_command_type(statement)
            dataset_result_size = DatasetResultSize.SMALL
            match sql_command_type:
                case SQLCommandType.DESCRIBE | SQLCommandType.DESC | SQLCommandType.SHOW | SQLCommandType.EXPLAIN:
                    dataset_result_size = DatasetResultSize.SMALL
                case SQLCommandType.SELECT | SQLCommandType.WITH:
                    dataset_result_size = DatasetResultSize.LARGE
                case _:
                    raise Exception("The SQL statement is not a read-only operation.")

            export_data_to_parquet_with_jdbc(
                self.connection,
                self.jdbc_jar_dict.jars[self.driver_name].class_name,
                jdbc_url,
                self.get_connection_properties(),
                database_engine,
                statement,
                dataset_result_size,
                results_folder_path,
            )

            return results_folder_path

        except Exception as e:
            print(
                f"error in execute_statement: {str(e)} with driver name: {self.driver_name}"
            )
            raise e

    def get_connection_properties(self) -> dict:
        """
        Get database connection properties for JDBC connections.

        Extracts username and password from the authentication information
        to create a connection properties dictionary for database access.

        Returns:
            dict: Dictionary containing connection properties with user and password

        """
        connection_options = {
            "user": self.source_authentification_info["username"],
            "password": self.source_authentification_info["password"],
        }

        return connection_options

    def close_connection(self) -> None:
        """
        Close the Spark session to free up resources.

        Stops the active Spark session if one exists, cleaning up resources.

        Raises:
            Exception: If an error occurs while closing the connection

        """
        try:
            if self.connection:
                print("Closing Spark session...")
                self.connection.stop()
                self.connection = None
                print("Spark session closed successfully")
        except Exception:
            print(f"Error closing Spark connection. Driver name: {self.driver_name}")

"""
JDBC JAR dictionary management for database engines.

This module provides the JDBCJarDict singleton class that manages JDBC
driver JAR files for different database types, providing a centralized
registry for database-specific JDBC drivers.
"""

import os

from data_exchange_agent.constants.paths import ROOT_JARS_FOLDER_PATH
from data_exchange_agent.data_sources.jdbc_jar import JDBCJar


class JDBCJarDict:
    """
    A singleton class that manages JDBC driver JAR files for different database types.

    This class maintains a dictionary of JDBCJar objects and handles their initialization,
    storage, and retrieval. It implements the singleton pattern to ensure only one instance
    exists throughout the application lifecycle.

    The class supports downloading and managing JDBC drivers for:
    - PostgreSQL
    - Microsoft SQL Server
    - Teradata

    Each driver is represented by a JDBCJar object containing metadata like:
    - Driver class name
    - JAR file name and download URL
    - Local storage path

    The class provides methods to:
    - Initialize supported JDBC drivers
    - Add new drivers to the dictionary
    - Download all driver JARs
    - Get paths to downloaded JARs
    """

    def __init__(self) -> None:
        """
        Initialize the JDBCJarDict singleton instance.

        Creates an empty jars dictionary and initializes it with supported
        JDBC drivers for various database engines. This method is only
        called once due to the singleton pattern implementation.

        """
        self.jars: dict[str, JDBCJar] = {}
        self.initialize_jars()

    def initialize_jars(self) -> None:
        """
        Initialize the dictionary with supported JDBC drivers.

        Creates JDBCJar objects for PostgreSQL, SQL Server, and Teradata
        and adds them to the internal jars dictionary.

        The following drivers are initialized:
        - PostgreSQL: postgresql-42.7.7.jar
        - SQL Server: mssql-jdbc-12.10.1.jre11.jar
        - Teradata: terajdbc-20.00.00.49.jar

        Each driver is configured with its appropriate class name and download URL.
        """
        postgresql_jar: JDBCJar = JDBCJar(
            name="postgresql",
            jar_name="postgresql-42.7.7.jar",
            class_name="org.postgresql.Driver",
            url="https://jdbc.postgresql.org/download/postgresql-42.7.7.jar",
            download_type="jar",
        )
        self.add_jar(postgresql_jar)
        sqlserver_jar: JDBCJar = JDBCJar(
            name="sqlserver",
            jar_name="mssql-jdbc-12.10.1.jre11.jar",
            class_name="com.microsoft.sqlserver.jdbc.SQLServerDriver",
            url="https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.10.1.jre11/mssql-jdbc-12.10.1.jre11.jar",
            download_type="jar",
        )
        self.add_jar(sqlserver_jar)
        teradata_jar: JDBCJar = JDBCJar(
            name="teradata",
            jar_name="terajdbc-20.00.00.49.jar",
            class_name="com.teradata.jdbc.TeraDriver",
            url="https://repo1.maven.org/maven2/com/teradata/jdbc/terajdbc/20.00.00.49/terajdbc-20.00.00.49.jar",
            download_type="jar",
        )
        self.add_jar(teradata_jar)

    def add_jar(self, jar: JDBCJar) -> None:
        """
        Add a JDBCJar object to the internal dictionary.

        Stores the provided JDBCJar object in the internal dictionary,
        using the jar's name as the key.

        Args:
            jar (JDBCJar): The JDBCJar object to add to the dictionary

        """
        self.jars[jar.name] = jar

    def get_jars(self) -> dict[str, JDBCJar]:
        """
        Get the dictionary of all registered JDBC jars.

        Returns:
            dict[str, JDBCJar]: Dictionary mapping jar names to JDBCJar objects.
                               Keys are the jar names (e.g. "postgresql")
                               Values are the corresponding JDBCJar instances.

        """
        return self.jars

    def download_all_jars(self) -> None:
        """
        Download all registered JDBC driver JARs if they don't exist locally.

        Iterates through all registered JDBCJar objects and downloads their
        associated JAR files if they are not already present in the local
        storage directory.
        """
        for jar in self.jars.values():
            jar.download_jars()

    def get_all_jar_paths(self) -> str:
        """
        Get a comma-separated string of paths to all downloaded JAR files.

        Builds a comma-separated string containing the absolute paths to all
        downloaded JDBC driver JAR files in the local storage directory.

        Returns:
            str: Comma-separated list of absolute paths to JAR files.
                 Example: "/home/user/.data_exchange_agent/jars/postgresql.jar,
                          /home/user/.data_exchange_agent/jars/sqlserver.jar"

        """
        all_jar_paths: list[str] = []
        for _, jdbc_jar in self.jars.items():
            jdbc_jar: JDBCJar
            dialect_jar_path: str = os.path.join(
                ROOT_JARS_FOLDER_PATH, jdbc_jar.jar_name
            )
            all_jar_paths.append(dialect_jar_path)

        return ",".join(all_jar_paths)

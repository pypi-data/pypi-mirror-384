"""Database engines."""

from enum import Enum


class DatabaseEngine(Enum):
    """
    Enumeration of supported database engine types.

    This enum defines all the database engines that the data exchange agent
    can connect to and extract data from.

    Attributes:
        ORACLE: Oracle Database
        SQLSERVER: Microsoft SQL Server
        TERADATA: Teradata Database
        REDSHIFT: Amazon Redshift
        BIGQUERY: Google BigQuery
        GREENPLUM: Greenplum Database
        SYBASE: Sybase Database
        NETEZZA: IBM Netezza
        POSTGRESQL: PostgreSQL Database
        DATABRICKS: Databricks Platform
        MYSQL: MySQL Database
        SQLITE: SQLite Database
        SNOWFLAKE: Snowflake Data Cloud

    """

    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    TERADATA = "teradata"
    REDSHIFT = "redshift"
    BIGQUERY = "bigquery"
    GREENPLUM = "greenplum"
    SYBASE = "sybase"
    NETEZZA = "netezza"
    POSTGRESQL = "postgresql"
    DATABRICKS = "databricks"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SNOWFLAKE = "snowflake"


def is_database_engine_supported(database_engine: DatabaseEngine) -> bool:
    """
    Check if the given database engine is supported.

    Args:
        database_engine: The database engine to check.

    Returns:
        bool: True if the database engine is supported, False otherwise.

    """
    return database_engine in DatabaseEngine


def get_database_engine_from_string(database_engine_string: str) -> DatabaseEngine:
    """
    Get the database engine from a string.

    Args:
        database_engine_string: The string representation of the database engine.

    Returns:
        DatabaseEngine: The database engine.

    Raises:
        ValueError: If the database engine string is not supported.

    """
    database_engine_string = database_engine_string.lower()
    try:
        return DatabaseEngine(database_engine_string)
    except ValueError:
        raise ValueError(
            f"Unsupported database engine: {database_engine_string}"
        ) from None

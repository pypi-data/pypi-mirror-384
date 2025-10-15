"""Get the number of partitions for a PySpark DataFrame."""

import logging
import math
import multiprocessing

from pyspark.sql import DataFrame, DataFrameReader
from pyspark.sql.functions import avg, col, length, regexp_replace, to_json
from pyspark.sql.types import (
    ArrayType,
    BinaryType,
    BooleanType,
    ByteType,
    DateType,
    DecimalType,
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    MapType,
    NullType,
    ShortType,
    StringType,
    StructType,
    TimestampType,
)

from data_exchange_agent.data_sources import database_engines
from data_exchange_agent.data_sources.database_engines import DatabaseEngine
from data_exchange_agent.data_sources.dataset_result_sizes import DatasetResultSize


MIN_NUM_PARTITIONS = 1
MIN_TOTAL_ROWS_COUNT = 500000
UNCOMPRESSED_PARTITION_ESTIMATED_TARGET_MB = 1500


def get_num_partitions(
    dataset_result_size: DatasetResultSize,
    df_reader: DataFrameReader,
    database_engine: DatabaseEngine,
    sql_query: str,
) -> int:
    """
    Get the optimal number of partitions for a PySpark DataFrame based on dataset size.

    Determines the number of partitions to use when loading data from a database
    based on the expected dataset size. For small datasets, uses a minimum number
    of partitions. For medium datasets, uses a default based on CPU cores. For
    large datasets, calculates an optimal number based on data characteristics.

    Args:
        dataset_result_size (DatasetResultSize): The expected size category of the dataset
        df_reader (DataFrameReader): PySpark DataFrameReader configured for the data source
        database_engine (DatabaseEngine): The type of database engine being used
        sql_query (str): The SQL query to be executed

    Returns:
        int: The optimal number of partitions to use for the DataFrame

    Raises:
        ValueError: If the database engine is not supported (for large datasets)

    """
    match dataset_result_size:
        case DatasetResultSize.SMALL:
            return MIN_NUM_PARTITIONS
        case DatasetResultSize.MEDIUM:
            return _get_default_num_partitions()
        case DatasetResultSize.LARGE:
            try:
                return _get_better_num_partitions(df_reader, database_engine, sql_query)
            except Exception as e:
                default_num_partitions = _get_default_num_partitions()
                logging.error(
                    f"Error getting better number of partitions: {e}. "
                    f"Using default {default_num_partitions} partitions as fallback"
                )
                return default_num_partitions
        case _:
            logging.error(
                f"Unsupported dataset result size: {dataset_result_size}. "
                f"Using default {MIN_NUM_PARTITIONS} partition as fallback"
            )
            return MIN_NUM_PARTITIONS


def _get_default_num_partitions() -> int:
    num_cores = multiprocessing.cpu_count()
    num_partitions = num_cores * 3  # A good number is 2-4x your number of CPU cores
    return num_partitions


def _get_better_num_partitions(
    df_reader: DataFrameReader,
    database_engine: DatabaseEngine,
    sql_query: str,
) -> int:
    if not database_engines.is_database_engine_supported(database_engine):
        raise ValueError(f"Unsupported database engine: {database_engine}")

    # Get the total number of rows
    total_rows_count_sql_query = _get_total_rows_count_sql_query(
        database_engine, sql_query
    )
    total_rows_count = int(
        df_reader.option("query", total_rows_count_sql_query).load().collect()[0][0]
    )
    logging.info(f"Total rows count: {total_rows_count}")

    # Check if there is enough data to estimate chunk size
    if total_rows_count <= MIN_TOTAL_ROWS_COUNT:
        logging.warning(
            f"Dataset with {total_rows_count} rows is too small for partitioning. "
            f"Using minimum {MIN_NUM_PARTITIONS} partition for optimal performance."
        )
        return MIN_NUM_PARTITIONS

    # Calculate the sample size
    sample_size = _calculate_finite_sample_size(total_rows_count)
    logging.info(f"Sample size: {sample_size}")

    # Get a small sample to estimate row size
    sample_sql_query = _get_sample_sql_query(database_engine, sql_query, sample_size)
    sample_df = df_reader.option("query", sample_sql_query).load()
    sample_rows = sample_df.collect()
    logging.info(f"Total columns count: {len(sample_rows[0])}")

    # Estimate average row size
    estimated_row_size = _get_estimated_row_size(sample_df)
    logging.info(f"Estimated row size: {estimated_row_size} bytes")

    # Calculate total estimated size
    total_estimated_bytes = total_rows_count * estimated_row_size
    logging.info(f"Total estimated size: {total_estimated_bytes / 1024 / 1024} MB")

    # Calculate the number of partitions
    target_bytes = UNCOMPRESSED_PARTITION_ESTIMATED_TARGET_MB * 1024 * 1024
    num_partitions = int(total_estimated_bytes / target_bytes)

    # Ensure at least one partition if there's data
    result = max(num_partitions, MIN_NUM_PARTITIONS)
    logging.info(f"Number of partitions estimated at {result}.")
    return result


def _get_total_rows_count_sql_query(
    database_engine: DatabaseEngine, sql_query: str
) -> str:
    match database_engine:
        case (
            DatabaseEngine.BIGQUERY
            | DatabaseEngine.GREENPLUM
            | DatabaseEngine.MYSQL
            | DatabaseEngine.ORACLE
            | DatabaseEngine.POSTGRESQL
            | DatabaseEngine.REDSHIFT
            | DatabaseEngine.SNOWFLAKE
            | DatabaseEngine.SQLITE
            | DatabaseEngine.SQLSERVER
            | DatabaseEngine.SYBASE
            | DatabaseEngine.TERADATA
        ):
            return (
                f"SELECT count(1) AS data_exchange_agent_query_count "
                f"FROM ({sql_query}) AS data_exchange_agent_query_wrapper"
            )
        case _:
            raise ValueError(f"Unsupported engine type: {database_engine}")


def _get_sample_sql_query(
    database_engine: DatabaseEngine, sql_query: str, sample_size: int
) -> str:
    match database_engine:
        case (
            DatabaseEngine.BIGQUERY
            | DatabaseEngine.GREENPLUM
            | DatabaseEngine.MYSQL
            | DatabaseEngine.POSTGRESQL
            | DatabaseEngine.REDSHIFT
            | DatabaseEngine.SNOWFLAKE
            | DatabaseEngine.SQLITE
        ):
            return (
                f"SELECT * "
                f"FROM ({sql_query}) AS data_exchange_agent_query_wrapper "
                f"LIMIT {sample_size}"
            )
        case DatabaseEngine.SQLSERVER | DatabaseEngine.SYBASE | DatabaseEngine.TERADATA:
            return (
                f"SELECT TOP {sample_size} * "
                f"FROM ({sql_query}) AS data_exchange_agent_query_wrapper"
            )
        case DatabaseEngine.ORACLE:
            return (
                f"SELECT * "
                f"FROM ({sql_query}) AS data_exchange_agent_query_wrapper "
                f"WHERE ROWNUM <= {sample_size}"
            )
        case _:
            raise ValueError(f"Unsupported engine type: {database_engine}")


def _calculate_finite_sample_size(
    total_rows: int,
    confidence_level: float = 0.99,
    margin_of_error: float = 0.02,
    population_proportion: float = 0.5,
) -> int:
    """
    Calculate the minimum acceptable sample size for a finite population.

    Args:
        total_rows (int): The total number of rows in the table (population size).
        confidence_level (float): The desired confidence level (e.g., 0.99 for 99%).
            The expected values are 0.90, 0.95, and 0.99.
        margin_of_error (float): The desired margin of error (e.g., 0.02 for 2%).
        population_proportion (float): The population proportion, assumed to be 0.5 (worst-case scenario).

    Returns:
        int: The minimum acceptable sample size.

    """
    logging.info(
        f"Start: Calculating sample size for total rows: {total_rows}, "
        f"confidence level: {confidence_level}, "
        f"margin of error: {margin_of_error}, "
        f"population proportion: {population_proportion}..."
    )
    # Mapping confidence levels to Z-scores
    if confidence_level == 0.90:
        z_score = 1.645
    elif confidence_level == 0.95:
        z_score = 1.96
    elif confidence_level == 0.99:
        z_score = 2.576
    else:
        raise ValueError(
            "Unsupported confidence level. Please use 0.90, 0.95, or 0.99."
        )

    # Calculate the infinite population sample size (n0) first
    n0 = (pow(z_score, 2) * population_proportion * (1 - population_proportion)) / pow(
        margin_of_error, 2
    )

    # Apply the finite population correction formula
    finite_n = (n0 * total_rows) / (n0 + (total_rows - 1))

    result = math.ceil(finite_n)
    logging.info(
        f"End: Calculating sample size for total rows: {total_rows}, "
        f"confidence level: {confidence_level}, "
        f"margin of error: {margin_of_error}, "
        f"population proportion: {population_proportion}. "
        f"Sample size: {result}"
    )
    return result


def _get_estimated_row_size(df: DataFrame) -> int:
    size = 0
    for field in df.schema.fields:
        if isinstance(field.dataType, NullType):
            size += 0
        elif isinstance(field.dataType, BooleanType | ByteType):
            size += 1
        elif isinstance(field.dataType, ShortType):
            size += 2
        elif isinstance(field.dataType, IntegerType | FloatType | DateType):
            size += 4
        elif isinstance(field.dataType, LongType | DoubleType | TimestampType):
            size += 8
        elif isinstance(field.dataType, DecimalType):
            if field.dataType.precision <= 9:
                size += 4
            elif field.dataType.precision <= 18:
                size += 8
            elif field.dataType.precision <= 38:
                size += 16
            else:
                size += 32
        elif isinstance(field.dataType, StringType | BinaryType):
            average_length = df.agg(avg(length(col(field.name)))).collect()[0][0]
            size += round(average_length) if average_length else 0
        elif isinstance(field.dataType, MapType | ArrayType | StructType):
            json_content = regexp_replace(
                to_json(col(field.name)), r'[\{\}\[\]:\,"]', ""
            )
            average_length = df.agg(avg(length(json_content))).collect()[0][0]
            size += round(average_length) if average_length else 0
        else:
            size += 1
    return size

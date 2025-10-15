"""Export data using PySpark."""

import logging

from pyspark.sql import DataFrame, SparkSession

from data_exchange_agent.data_sources.database_engines import DatabaseEngine
from data_exchange_agent.data_sources.dataset_result_sizes import DatasetResultSize
from data_exchange_agent.data_sources.num_partitions import get_num_partitions


def export_data_to_parquet_with_jdbc(
    spark: SparkSession,
    driver_class_name: str,
    jar_url: str,
    connection_properties: dict,
    database_engine: DatabaseEngine,
    sql_query: str,
    dataset_result_size: DatasetResultSize = (DatasetResultSize.MEDIUM),
    parquet_folder_path: str = "data_chunks",
) -> None:
    """
    Export data from a database to Parquet files using JDBC connection.

    Executes a SQL query against a database via JDBC, optimizes the DataFrame partitioning
    based on the dataset size, and writes the results to Parquet format.

    Args:
        spark (SparkSession): The Spark session to use for data processing
        driver_class_name (str): The JDBC driver class name (e.g., 'com.mysql.cj.jdbc.Driver')
        jar_url (str): The JDBC connection URL
        connection_properties (dict): Additional connection properties like username, password
        database_engine (DatabaseEngine): The type of database engine being connected to
        sql_query (str): The SQL query to execute for data extraction
        dataset_result_size (DatasetResultSize, optional): Expected size of the result set.
            Defaults to DatasetResultSize.MEDIUM
        parquet_folder_path (str, optional): Output directory path for Parquet files.
            Defaults to "data_chunks"

    Returns:
        None

    Example:
        >>> export_data_to_parquet_with_jdbc(
        ...     spark=spark_session,
        ...     driver_class_name="com.mysql.cj.jdbc.Driver",
        ...     jar_url="jdbc:mysql://localhost:3306/mydb",
        ...     connection_properties={"user": "username", "password": "password"},
        ...     database_engine=DatabaseEngine.MYSQL,
        ...     sql_query="SELECT * FROM my_table",
        ...     dataset_result_size=DatasetResultSize.LARGE,
        ...     parquet_folder_path="/output/data"
        ... )

    """
    df_reader = (
        spark.read.format("jdbc")
        .option("driver", driver_class_name)
        .option("url", jar_url)
        .options(**connection_properties)
    )

    logging.info(f"Start: Execution of query: {sql_query}...")
    df: DataFrame = df_reader.option("query", sql_query).load()
    logging.info(f"End: Execution of query: {sql_query}.")

    logging.info(
        f"Start: Repartition the data based on the provided size: "
        f"{dataset_result_size}..."
    )
    num_partitions = get_num_partitions(
        dataset_result_size, df_reader, database_engine, sql_query
    )
    if num_partitions > df.rdd.getNumPartitions():
        df = df.repartition(num_partitions)
    else:
        df = df.coalesce(num_partitions)
    logging.info(f"End: Repartition the data. {num_partitions} partitions.")

    logging.info(f"Start: Writing parquet chunks with {num_partitions} partitions...")
    df.write.mode("overwrite").parquet(parquet_folder_path)
    logging.info(f"End: Writing parquet chunks with {num_partitions} partitions.")

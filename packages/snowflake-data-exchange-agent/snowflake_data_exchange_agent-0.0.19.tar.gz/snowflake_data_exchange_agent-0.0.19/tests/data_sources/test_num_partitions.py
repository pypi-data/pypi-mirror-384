"""Unit tests for the num_partitions module."""

import math
import multiprocessing
from unittest.mock import Mock, patch

import pytest
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
    StructField,
    StructType,
    TimestampType,
)

from data_exchange_agent.data_sources.database_engines import DatabaseEngine
from data_exchange_agent.data_sources.dataset_result_sizes import DatasetResultSize
from data_exchange_agent.data_sources.num_partitions import (
    MIN_NUM_PARTITIONS,
    MIN_TOTAL_ROWS_COUNT,
    UNCOMPRESSED_PARTITION_ESTIMATED_TARGET_MB,
    _calculate_finite_sample_size,
    _get_better_num_partitions,
    _get_default_num_partitions,
    _get_estimated_row_size,
    _get_sample_sql_query,
    _get_total_rows_count_sql_query,
    get_num_partitions,
)


class TestGetNumPartitions:
    """Test class for get_num_partitions function."""

    def test_small_dataset_returns_min_partitions(self):
        """Test that small datasets return minimum partitions."""
        mock_df_reader = Mock()

        result = get_num_partitions(
            DatasetResultSize.SMALL,
            mock_df_reader,
            DatabaseEngine.POSTGRESQL,
            "SELECT * FROM test",
        )

        assert result == MIN_NUM_PARTITIONS

    @patch(
        "data_exchange_agent.data_sources.num_partitions._get_default_num_partitions"
    )
    def test_medium_dataset_returns_default_partitions(self, mock_get_default):
        """Test that medium datasets return default partitions."""
        mock_get_default.return_value = 12
        mock_df_reader = Mock()

        result = get_num_partitions(
            DatasetResultSize.MEDIUM,
            mock_df_reader,
            DatabaseEngine.POSTGRESQL,
            "SELECT * FROM test",
        )

        assert result == 12
        mock_get_default.assert_called_once()

    @patch("data_exchange_agent.data_sources.num_partitions._get_better_num_partitions")
    def test_large_dataset_returns_calculated_partitions(self, mock_get_better):
        """Test that large datasets return calculated partitions."""
        mock_get_better.return_value = 25
        mock_df_reader = Mock()

        result = get_num_partitions(
            DatasetResultSize.LARGE,
            mock_df_reader,
            DatabaseEngine.POSTGRESQL,
            "SELECT * FROM test",
        )

        assert result == 25
        mock_get_better.assert_called_once_with(
            mock_df_reader, DatabaseEngine.POSTGRESQL, "SELECT * FROM test"
        )

    @patch("data_exchange_agent.data_sources.num_partitions._get_better_num_partitions")
    @patch(
        "data_exchange_agent.data_sources.num_partitions._get_default_num_partitions"
    )
    @patch("data_exchange_agent.data_sources.num_partitions.logging")
    def test_large_dataset_fallback_on_exception(
        self, mock_logging, mock_get_default, mock_get_better
    ):
        """Test that large datasets fallback to default on exception."""
        mock_get_better.side_effect = Exception("Database error")
        mock_get_default.return_value = 12
        mock_df_reader = Mock()

        result = get_num_partitions(
            DatasetResultSize.LARGE,
            mock_df_reader,
            DatabaseEngine.POSTGRESQL,
            "SELECT * FROM test",
        )

        assert result == 12
        mock_logging.error.assert_called_once()

    @patch("data_exchange_agent.data_sources.num_partitions.logging")
    def test_unsupported_dataset_size_returns_min_partitions(self, mock_logging):
        """Test that unsupported dataset sizes return minimum partitions."""
        mock_df_reader = Mock()
        # Create a mock enum value that's not in the expected cases
        unsupported_size = Mock()
        unsupported_size.name = "UNSUPPORTED"

        result = get_num_partitions(
            unsupported_size,
            mock_df_reader,
            DatabaseEngine.POSTGRESQL,
            "SELECT * FROM test",
        )

        assert result == MIN_NUM_PARTITIONS
        mock_logging.error.assert_called_once()


class TestGetDefaultNumPartitions:
    """Test class for _get_default_num_partitions function."""

    @patch("data_exchange_agent.data_sources.num_partitions.multiprocessing.cpu_count")
    def test_returns_cpu_count_times_three(self, mock_cpu_count):
        """Test that default partitions are CPU count * 3."""
        mock_cpu_count.return_value = 8

        result = _get_default_num_partitions()

        assert result == 24
        mock_cpu_count.assert_called_once()


class TestGetBetterNumPartitions:
    """Test class for _get_better_num_partitions function."""

    @patch(
        "data_exchange_agent.data_sources.num_partitions.database_engines.is_database_engine_supported"
    )
    def test_unsupported_database_engine_raises_error(self, mock_is_supported):
        """Test that unsupported database engines raise ValueError."""
        mock_is_supported.return_value = False
        mock_df_reader = Mock()

        with pytest.raises(ValueError, match="Unsupported database engine"):
            _get_better_num_partitions(
                mock_df_reader, DatabaseEngine.POSTGRESQL, "SELECT * FROM test"
            )

    @patch(
        "data_exchange_agent.data_sources.num_partitions.database_engines.is_database_engine_supported"
    )
    @patch(
        "data_exchange_agent.data_sources.num_partitions._get_total_rows_count_sql_query"
    )
    @patch("data_exchange_agent.data_sources.num_partitions.logging")
    def test_small_row_count_returns_min_partitions(
        self, mock_logging, mock_get_count_query, mock_is_supported
    ):
        """Test that small row counts return minimum partitions."""
        mock_is_supported.return_value = True
        mock_get_count_query.return_value = "SELECT COUNT(1) FROM (SELECT * FROM test)"

        # Mock DataFrame with small row count
        mock_df = Mock()
        mock_df.collect.return_value = [[100]]  # Less than MIN_TOTAL_ROWS_COUNT

        mock_df_reader = Mock()
        mock_df_reader.option.return_value.load.return_value = mock_df

        result = _get_better_num_partitions(
            mock_df_reader, DatabaseEngine.POSTGRESQL, "SELECT * FROM test"
        )

        assert result == MIN_NUM_PARTITIONS
        mock_logging.warning.assert_called_once()

    @patch(
        "data_exchange_agent.data_sources.num_partitions.database_engines.is_database_engine_supported"
    )
    @patch(
        "data_exchange_agent.data_sources.num_partitions._get_total_rows_count_sql_query"
    )
    @patch(
        "data_exchange_agent.data_sources.num_partitions._calculate_finite_sample_size"
    )
    @patch("data_exchange_agent.data_sources.num_partitions._get_sample_sql_query")
    @patch("data_exchange_agent.data_sources.num_partitions._get_estimated_row_size")
    @patch("data_exchange_agent.data_sources.num_partitions.logging")
    def test_large_dataset_calculates_partitions(
        self,
        mock_logging,
        mock_get_row_size,
        mock_get_sample_query,
        mock_calc_sample,
        mock_get_count_query,
        mock_is_supported,
    ):
        """Test that large datasets calculate partitions based on data size."""
        mock_is_supported.return_value = True
        mock_get_count_query.return_value = "SELECT COUNT(1) FROM (SELECT * FROM test)"
        mock_calc_sample.return_value = 1000
        mock_get_sample_query.return_value = (
            "SELECT * FROM (SELECT * FROM test) LIMIT 1000"
        )
        mock_get_row_size.return_value = 500  # 500 bytes per row

        # Mock large row count (1M rows)
        mock_count_df = Mock()
        mock_count_df.collect.return_value = [[1000000]]

        # Mock sample DataFrame
        mock_sample_df = Mock()
        # Create mock rows with 5 columns each
        mock_sample_rows = [[f"col{i}_row{j}" for i in range(5)] for j in range(1000)]
        mock_sample_df.collect.return_value = mock_sample_rows

        mock_df_reader = Mock()
        mock_df_reader.option.return_value.load.side_effect = [
            mock_count_df,
            mock_sample_df,
        ]

        result = _get_better_num_partitions(
            mock_df_reader, DatabaseEngine.POSTGRESQL, "SELECT * FROM test"
        )

        # Expected calculation:
        # total_estimated_bytes = 1000000 * 500 = 500MB
        # target_bytes = 1500MB
        # num_partitions = 500MB / 1500MB = 0.33, max with MIN_NUM_PARTITIONS = 1
        expected_partitions = 1
        assert result == expected_partitions


class TestGetTotalRowsCountSqlQuery:
    """Test class for _get_total_rows_count_sql_query function."""

    def test_supported_database_engines(self):
        """Test SQL query generation for all supported database engines."""
        sql_query = "SELECT * FROM users WHERE active = 1"

        supported_engines = [
            DatabaseEngine.BIGQUERY,
            DatabaseEngine.GREENPLUM,
            DatabaseEngine.MYSQL,
            DatabaseEngine.ORACLE,
            DatabaseEngine.POSTGRESQL,
            DatabaseEngine.REDSHIFT,
            DatabaseEngine.SNOWFLAKE,
            DatabaseEngine.SQLITE,
            DatabaseEngine.SQLSERVER,
            DatabaseEngine.SYBASE,
            DatabaseEngine.TERADATA,
        ]

        for engine in supported_engines:
            result = _get_total_rows_count_sql_query(engine, sql_query)
            expected = (
                "SELECT count(1) AS data_exchange_agent_query_count "
                "FROM (SELECT * FROM users WHERE active = 1) AS data_exchange_agent_query_wrapper"
            )
            assert result == expected

    def test_unsupported_database_engine_raises_error(self):
        """Test that unsupported database engines raise ValueError."""
        unsupported_engine = Mock()
        unsupported_engine.name = "UNSUPPORTED_DB"

        with pytest.raises(ValueError, match="Unsupported engine type"):
            _get_total_rows_count_sql_query(unsupported_engine, "SELECT * FROM test")


class TestGetSampleSqlQuery:
    """Test class for _get_sample_sql_query function."""

    def test_limit_based_engines(self):
        """Test SQL query generation for LIMIT-based database engines."""
        sql_query = "SELECT * FROM users"
        sample_size = 1000

        limit_engines = [
            DatabaseEngine.BIGQUERY,
            DatabaseEngine.GREENPLUM,
            DatabaseEngine.MYSQL,
            DatabaseEngine.POSTGRESQL,
            DatabaseEngine.REDSHIFT,
            DatabaseEngine.SNOWFLAKE,
            DatabaseEngine.SQLITE,
        ]

        for engine in limit_engines:
            result = _get_sample_sql_query(engine, sql_query, sample_size)
            expected = (
                "SELECT * "
                "FROM (SELECT * FROM users) AS data_exchange_agent_query_wrapper "
                "LIMIT 1000"
            )
            assert result == expected

    def test_top_based_engines(self):
        """Test SQL query generation for TOP-based database engines."""
        sql_query = "SELECT * FROM users"
        sample_size = 500

        top_engines = [
            DatabaseEngine.SQLSERVER,
            DatabaseEngine.SYBASE,
            DatabaseEngine.TERADATA,
        ]

        for engine in top_engines:
            result = _get_sample_sql_query(engine, sql_query, sample_size)
            expected = (
                "SELECT TOP 500 * "
                "FROM (SELECT * FROM users) AS data_exchange_agent_query_wrapper"
            )
            assert result == expected

    def test_oracle_rownum_engine(self):
        """Test SQL query generation for Oracle using ROWNUM."""
        sql_query = "SELECT * FROM orders"
        sample_size = 750

        result = _get_sample_sql_query(DatabaseEngine.ORACLE, sql_query, sample_size)
        expected = (
            "SELECT * "
            "FROM (SELECT * FROM orders) AS data_exchange_agent_query_wrapper "
            "WHERE ROWNUM <= 750"
        )
        assert result == expected

    def test_unsupported_database_engine_raises_error(self):
        """Test that unsupported database engines raise ValueError."""
        unsupported_engine = Mock()
        unsupported_engine.name = "UNSUPPORTED_DB"

        with pytest.raises(ValueError, match="Unsupported engine type"):
            _get_sample_sql_query(unsupported_engine, "SELECT * FROM test", 100)


class TestCalculateFiniteSampleSize:
    """Test class for _calculate_finite_sample_size function."""

    @patch("data_exchange_agent.data_sources.num_partitions.logging")
    def test_default_parameters(self, mock_logging):
        """Test sample size calculation with default parameters."""
        total_rows = 1000000

        result = _calculate_finite_sample_size(total_rows)

        # With default params (99% confidence, 2% margin, 0.5 proportion)
        # Expected result should be around 4144 for large populations
        assert isinstance(result, int)
        assert result > 0
        assert result < total_rows
        mock_logging.info.assert_called()

    @patch("data_exchange_agent.data_sources.num_partitions.logging")
    def test_different_confidence_levels(self, mock_logging):
        """Test sample size calculation with different confidence levels."""
        total_rows = 500000

        # Test 90% confidence
        result_90 = _calculate_finite_sample_size(total_rows, confidence_level=0.90)

        # Test 95% confidence
        result_95 = _calculate_finite_sample_size(total_rows, confidence_level=0.95)

        # Test 99% confidence
        result_99 = _calculate_finite_sample_size(total_rows, confidence_level=0.99)

        # Higher confidence should require larger sample size
        assert result_90 < result_95 < result_99

    def test_unsupported_confidence_level_raises_error(self):
        """Test that unsupported confidence levels raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported confidence level"):
            _calculate_finite_sample_size(1000000, confidence_level=0.85)

    @patch("data_exchange_agent.data_sources.num_partitions.logging")
    def test_small_population_returns_reasonable_sample(self, mock_logging):
        """Test that small populations return reasonable sample sizes."""
        total_rows = 1000

        result = _calculate_finite_sample_size(total_rows)

        # For small populations, sample size should be reasonable
        assert result <= total_rows
        assert result > 0


class TestGetEstimatedRowSize:
    """Test class for _get_estimated_row_size function."""

    def test_null_type_size(self):
        """Test row size estimation for NullType."""
        schema = StructType([StructField("null_col", NullType(), True)])
        mock_df = Mock()
        mock_df.schema.fields = schema.fields

        result = _get_estimated_row_size(mock_df)
        assert result == 0

    def test_boolean_and_byte_types_size(self):
        """Test row size estimation for Boolean and Byte types."""
        schema = StructType(
            [
                StructField("bool_col", BooleanType(), True),
                StructField("byte_col", ByteType(), True),
            ]
        )
        mock_df = Mock()
        mock_df.schema.fields = schema.fields

        result = _get_estimated_row_size(mock_df)
        assert result == 2  # 1 + 1

    def test_short_type_size(self):
        """Test row size estimation for ShortType."""
        schema = StructType([StructField("short_col", ShortType(), True)])
        mock_df = Mock()
        mock_df.schema.fields = schema.fields

        result = _get_estimated_row_size(mock_df)
        assert result == 2

    def test_integer_float_date_types_size(self):
        """Test row size estimation for 4-byte types."""
        schema = StructType(
            [
                StructField("int_col", IntegerType(), True),
                StructField("float_col", FloatType(), True),
                StructField("date_col", DateType(), True),
            ]
        )
        mock_df = Mock()
        mock_df.schema.fields = schema.fields

        result = _get_estimated_row_size(mock_df)
        assert result == 12  # 4 + 4 + 4

    def test_long_double_timestamp_types_size(self):
        """Test row size estimation for 8-byte types."""
        schema = StructType(
            [
                StructField("long_col", LongType(), True),
                StructField("double_col", DoubleType(), True),
                StructField("timestamp_col", TimestampType(), True),
            ]
        )
        mock_df = Mock()
        mock_df.schema.fields = schema.fields

        result = _get_estimated_row_size(mock_df)
        assert result == 24  # 8 + 8 + 8

    def test_decimal_type_different_precisions(self):
        """Test row size estimation for DecimalType with different precisions."""
        schema = StructType(
            [
                StructField("decimal_small", DecimalType(precision=5, scale=2), True),
                StructField("decimal_medium", DecimalType(precision=15, scale=4), True),
                StructField("decimal_large", DecimalType(precision=30, scale=6), True),
                StructField("decimal_xlarge", DecimalType(precision=50, scale=8), True),
            ]
        )
        mock_df = Mock()
        mock_df.schema.fields = schema.fields

        result = _get_estimated_row_size(mock_df)
        assert result == 60  # 4 + 8 + 16 + 32

    @patch("data_exchange_agent.data_sources.num_partitions.avg")
    @patch("data_exchange_agent.data_sources.num_partitions.length")
    @patch("data_exchange_agent.data_sources.num_partitions.col")
    def test_string_and_binary_types_size(self, mock_col, mock_length, mock_avg):
        """Test row size estimation for String and Binary types."""
        schema = StructType(
            [
                StructField("string_col", StringType(), True),
                StructField("binary_col", BinaryType(), True),
            ]
        )

        # Mock DataFrame aggregation - each field calls agg separately
        mock_df = Mock()
        mock_df.schema.fields = schema.fields
        # First call returns 25.5, second call returns 10.2
        mock_df.agg.return_value.collect.side_effect = [[[25.5]], [[10.2]]]

        result = _get_estimated_row_size(mock_df)
        assert result == 36  # round(25.5) + round(10.2) = 26 + 10

    @patch("data_exchange_agent.data_sources.num_partitions.regexp_replace")
    @patch("data_exchange_agent.data_sources.num_partitions.to_json")
    @patch("data_exchange_agent.data_sources.num_partitions.avg")
    @patch("data_exchange_agent.data_sources.num_partitions.length")
    @patch("data_exchange_agent.data_sources.num_partitions.col")
    def test_complex_types_size(
        self, mock_col, mock_length, mock_avg, mock_to_json, mock_regexp_replace
    ):
        """Test row size estimation for complex types (Map, Array, Struct)."""
        schema = StructType(
            [
                StructField("map_col", MapType(StringType(), IntegerType()), True),
                StructField("array_col", ArrayType(StringType()), True),
                StructField(
                    "struct_col",
                    StructType([StructField("nested", StringType())]),
                    True,
                ),
            ]
        )

        # Mock DataFrame aggregation for complex types - each field calls agg separately
        mock_df = Mock()
        mock_df.schema.fields = schema.fields
        # Each call returns different values: 15.0, 20.0, 12.0
        mock_df.agg.return_value.collect.side_effect = [[[15.0]], [[20.0]], [[12.0]]]

        result = _get_estimated_row_size(mock_df)
        assert result == 47  # 15 + 20 + 12

    def test_unknown_type_defaults_to_one_byte(self):
        """Test that unknown types default to 1 byte."""
        # Create a mock field with unknown type
        mock_field = Mock()
        mock_field.dataType = Mock()
        mock_field.dataType.__class__ = type("UnknownType", (), {})

        mock_df = Mock()
        mock_df.schema.fields = [mock_field]

        result = _get_estimated_row_size(mock_df)
        assert result == 1

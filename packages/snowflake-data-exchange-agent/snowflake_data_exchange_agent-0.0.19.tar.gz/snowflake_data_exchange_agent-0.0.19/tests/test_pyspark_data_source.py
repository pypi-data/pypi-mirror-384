import unittest
from unittest.mock import Mock, patch

from data_exchange_agent.data_sources.database_engines import (
    get_database_engine_from_string,
)
from data_exchange_agent.data_sources.pyspark import PySparkDataSource
from data_exchange_agent.interfaces.data_source import DataSourceInterface


class TestPySparkDataSource(unittest.TestCase):
    """Comprehensive test suite for the PySparkDataSource class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.auth_info = {
            "url": "jdbc:postgresql://localhost:5432/testdb",
            "username": "testuser",
            "password": "testpass",
        }

        with patch("data_exchange_agent.data_sources.pyspark.JDBCJarDict"):
            self.data_source = PySparkDataSource("postgresql", **self.auth_info)

    def test_pyspark_data_source_is_data_source_interface(self):
        """Test that PySparkDataSource implements DataSourceInterface."""
        self.assertIsInstance(self.data_source, DataSourceInterface)

    def test_initialization(self):
        """Test PySparkDataSource initialization."""
        self.assertEqual(self.data_source.driver_name, "postgresql")
        self.assertEqual(self.data_source.source_authentification_info, self.auth_info)
        self.assertIsNone(self.data_source.connection)
        self.assertIsNotNone(self.data_source._lock)
        self.assertTrue(hasattr(self.data_source._lock, "acquire"))
        self.assertTrue(hasattr(self.data_source._lock, "release"))

    @patch("data_exchange_agent.data_sources.pyspark.JDBCJarDict")
    def test_initialization_with_jdbc_jar_dict(self, mock_jdbc_jar_dict_class):
        """Test initialization creates JDBCJarDict instance."""
        mock_jdbc_jar_dict = Mock()
        mock_jdbc_jar_dict_class.return_value = mock_jdbc_jar_dict

        data_source = PySparkDataSource("sqlserver", **self.auth_info)

        mock_jdbc_jar_dict_class.assert_called_once()
        self.assertEqual(data_source.jdbc_jar_dict, mock_jdbc_jar_dict)

    @patch("data_exchange_agent.data_sources.pyspark.SparkSession")
    def test_create_connection_success(self, mock_spark_session_class):
        """Test successful connection creation."""
        mock_spark_session = Mock()
        mock_builder = Mock()
        mock_spark_session_class.builder = mock_builder
        mock_spark_session_class.getActiveSession.return_value = None

        mock_builder.appName.return_value = mock_builder
        mock_builder.config.return_value = mock_builder
        mock_builder.getOrCreate.return_value = mock_spark_session

        mock_jar_dict = Mock()
        mock_jar_dict.jars = {"postgresql": Mock()}
        mock_jar_dict.get_all_jar_paths.return_value = "/path/to/jars"
        self.data_source.jdbc_jar_dict = mock_jar_dict

        self.data_source.create_connection()

        mock_jar_dict.download_all_jars.assert_called_once()

        mock_builder.appName.assert_called_once()
        mock_builder.getOrCreate.assert_called_once()

        self.assertEqual(self.data_source.connection, mock_spark_session)

    @patch("data_exchange_agent.data_sources.pyspark.SparkSession")
    def test_create_connection_with_active_session(self, mock_spark_session_class):
        """Test connection creation when active session exists."""
        mock_active_session = Mock()
        mock_spark_session_class.getActiveSession.return_value = mock_active_session

        mock_jar_dict = Mock()
        mock_jar_dict.jars = {"postgresql": Mock()}
        self.data_source.jdbc_jar_dict = mock_jar_dict

        self.data_source.create_connection()

        self.assertEqual(self.data_source.connection, mock_active_session)

    def test_create_connection_driver_not_in_jars(self):
        """Test connection creation when driver not in jars."""
        mock_jar_dict = Mock()
        mock_jar_dict.jars = {}  # Empty jars dict
        self.data_source.jdbc_jar_dict = mock_jar_dict

        self.data_source.create_connection()
        self.assertIsNone(self.data_source.connection)

    def test_create_connection_exception_handling(self):
        """Test connection creation exception handling."""
        mock_jar_dict = Mock()
        mock_jar_dict.download_all_jars.side_effect = Exception("Download failed")
        self.data_source.jdbc_jar_dict = mock_jar_dict

        with self.assertRaises(Exception) as context:
            self.data_source.create_connection()

        self.assertEqual(str(context.exception), "Download failed")

    @patch("data_exchange_agent.data_sources.pyspark.export_data_to_parquet_with_jdbc")
    def test_execute_statement_success(self, mock_export_data):
        """Test successful statement execution."""
        results_folder = "/path/to/results"
        mock_export_data.return_value = None

        mock_spark_session = Mock()

        self.data_source.connection = mock_spark_session

        mock_jar = Mock()
        mock_jar.class_name = "org.postgresql.Driver"
        mock_jar_dict = Mock()
        mock_jar_dict.jars = {"postgresql": mock_jar}
        self.data_source.jdbc_jar_dict = mock_jar_dict

        statement = "SELECT * FROM users"

        with patch(
            "data_exchange_agent.data_sources.pyspark.build_actual_results_folder_path",
            return_value=results_folder,
        ):
            result = self.data_source.execute_statement(statement)

        mock_export_data.assert_called_once()
        call_args = mock_export_data.call_args[0]
        self.assertEqual(call_args[0], mock_spark_session)  # spark
        self.assertEqual(call_args[1], mock_jar.class_name)  # driver_class_name
        self.assertEqual(call_args[2], self.auth_info["url"])  # jar_url
        self.assertEqual(
            call_args[4], get_database_engine_from_string(self.data_source.driver_name)
        )  # database_engine
        self.assertEqual(call_args[5], statement)  # sql_query

        self.assertEqual(result, results_folder)

    def test_execute_statement_no_connection(self):
        """Test statement execution without connection."""
        statement = "SELECT * FROM users"

        with self.assertRaises(Exception) as context:
            list(self.data_source.execute_statement(statement))

        self.assertIn("No active Spark connection", str(context.exception))

    def test_execute_statement_exception_handling(self):
        """Test statement execution exception handling."""
        mock_spark_session = Mock()
        mock_read = Mock()
        mock_spark_session.read = mock_read
        mock_read.format.side_effect = Exception("JDBC error")

        self.data_source.connection = mock_spark_session

        mock_jar = Mock()
        mock_jar.class_name = "org.postgresql.Driver"
        mock_jar_dict = Mock()
        mock_jar_dict.jars = {"postgresql": mock_jar}
        self.data_source.jdbc_jar_dict = mock_jar_dict

        statement = "SELECT * FROM users"

        with self.assertRaises(Exception) as context:
            list(self.data_source.execute_statement(statement))

        self.assertEqual(str(context.exception), "JDBC error")

    def test_close_connection_success(self):
        """Test successful connection closing."""
        mock_spark_session = Mock()
        self.data_source.connection = mock_spark_session

        self.data_source.close_connection()

        mock_spark_session.stop.assert_called_once()

        self.assertIsNone(self.data_source.connection)

    def test_close_connection_no_connection(self):
        """Test closing connection when no connection exists."""
        self.data_source.connection = None

        self.data_source.close_connection()

        self.assertIsNone(self.data_source.connection)

    def test_close_connection_exception_handling(self):
        """Test connection closing exception handling."""
        mock_spark_session = Mock()
        mock_spark_session.stop.side_effect = Exception("Stop failed")
        self.data_source.connection = mock_spark_session

        with patch("builtins.print") as mock_print:
            self.data_source.close_connection()

            mock_print.assert_called()
            self.assertIn("Error closing Spark connection", mock_print.call_args[0][0])

    def test_thread_safety_lock_usage(self):
        """Test that thread lock is used in create_connection."""
        with patch.object(self.data_source, "_lock") as mock_lock:
            mock_jar_dict = Mock()
            mock_jar_dict.jars = {"postgresql": Mock()}
            self.data_source.jdbc_jar_dict = mock_jar_dict

            with patch(
                "data_exchange_agent.data_sources.pyspark.SparkSession"
            ) as mock_spark_session_class:
                mock_spark_session_class.getActiveSession.return_value = None
                mock_builder = Mock()
                mock_spark_session_class.builder = mock_builder
                mock_builder.appName.return_value = mock_builder
                mock_builder.config.return_value = mock_builder
                mock_builder.getOrCreate.return_value = Mock()

                self.data_source.create_connection()

                mock_lock.__enter__.assert_called_once()
                mock_lock.__exit__.assert_called_once()

    def test_spark_configuration_options(self):
        """Test that Spark is configured with correct options."""
        with patch(
            "data_exchange_agent.data_sources.pyspark.SparkSession"
        ) as mock_spark_session_class:
            mock_builder = Mock()
            mock_spark_session_class.builder = mock_builder
            mock_spark_session_class.getActiveSession.return_value = None

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = Mock()

            mock_jar_dict = Mock()
            mock_jar_dict.jars = {"postgresql": Mock()}
            mock_jar_dict.get_all_jar_paths.return_value = "/path/to/jars"
            self.data_source.jdbc_jar_dict = mock_jar_dict

            self.data_source.create_connection()

            app_name_call = mock_builder.appName.call_args[0][0]
            self.assertIn("postgresql", app_name_call)
            self.assertIn("DataExchangeAgent", app_name_call)

            config_calls = mock_builder.config.call_args_list
            config_dict = {call[0][0]: call[0][1] for call in config_calls}

            expected_configs = [
                "spark.jars",
                "spark.sql.adaptive.enabled",
                "spark.sql.adaptive.coalescePartitions.enabled",
                "spark.serializer",
                "spark.driver.host",
                "spark.driver.bindAddress",
                "spark.network.timeout",
                "spark.executor.heartbeatInterval",
                "spark.dynamicAllocation.enabled",
                "spark.shuffle.service.enabled",
                "spark.sql.execution.arrow.pyspark.enabled",
            ]

            for config_key in expected_configs:
                self.assertIn(config_key, config_dict)


if __name__ == "__main__":
    unittest.main()

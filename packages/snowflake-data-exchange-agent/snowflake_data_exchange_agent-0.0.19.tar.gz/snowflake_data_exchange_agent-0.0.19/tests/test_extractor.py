import unittest
from collections.abc import Generator
from unittest.mock import Mock

from data_exchange_agent.data_sources.extractor import DataSourceExtractor
from data_exchange_agent.interfaces.data_source import DataSourceInterface


class TestDataSourceExtractor(unittest.TestCase):
    """
    Comprehensive test suite for the DataSourceExtractor class.

    This test class validates the DataSourceExtractor functionality, including:
    - Proper initialization with SQL statements and database connections
    - Data extraction through connection.execute_statement calls
    - Generator-based data iteration for memory-efficient processing
    - Error handling for invalid parameters and connection failures
    - Integration with various DataSourceInterface implementations
    - Proper resource management and cleanup

    Tests use mocking to isolate the extractor from actual database connections
    and ensure reliable, fast test execution without external dependencies.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.

        Creates mock database connection and test SQL statement for use
        in all test methods. This ensures consistent test data and
        isolates tests from actual database dependencies.
        """
        self.mock_connection = Mock(spec=DataSourceInterface)
        self.test_statement = "SELECT * FROM test_table"
        self.extractor = DataSourceExtractor(
            statement=self.test_statement, connection=self.mock_connection
        )

    def test_init_with_valid_parameters(self):
        """Test that DataSourceExtractor initializes correctly with valid parameters."""
        extractor = DataSourceExtractor("SELECT 1", self.mock_connection)

        self.assertEqual(extractor.statement, "SELECT 1")
        self.assertEqual(extractor.connection, self.mock_connection)

    def test_init_with_empty_statement(self):
        """Test that DataSourceExtractor can be initialized with empty statement."""
        extractor = DataSourceExtractor("", self.mock_connection)

        self.assertEqual(extractor.statement, "")
        self.assertEqual(extractor.connection, self.mock_connection)

    def test_extract_data_calls_connection_execute_statement(self):
        """Test that extract_data calls execute_statement on the connection with correct statement."""
        expected_data = [{"id": 1, "name": "test"}]
        expected_path = "/path/to/results"
        self.mock_connection.execute_statement.return_value = expected_path

        result = self.extractor.extract_data()

        self.mock_connection.execute_statement.assert_called()
        call_args = self.mock_connection.execute_statement.call_args
        self.assertEqual(
            call_args[0][0], self.test_statement
        )  # First argument should be the statement
        self.assertEqual(
            result, expected_path
        )  # Should return the path, not a generator

    def test_extract_data_returns_result_path(self):
        """Test that extract_data returns the result path."""
        expected_path = "/path/to/results"
        self.mock_connection.execute_statement.return_value = expected_path

        result = self.extractor.extract_data()

        self.assertEqual(result, expected_path)

    def test_extract_data_with_empty_result(self):
        """Test extract_data behavior when connection returns empty path."""
        expected_path = "/path/to/empty/results"
        self.mock_connection.execute_statement.return_value = expected_path

        result = self.extractor.extract_data()

        self.assertEqual(result, expected_path)

    def test_extract_data_with_single_row(self):
        """Test extract_data with single row result."""
        expected_path = "/path/to/single/row/results"
        self.mock_connection.execute_statement.return_value = expected_path

        result = self.extractor.extract_data()

        self.assertEqual(result, expected_path)

    def test_extract_data_preserves_generator_behavior(self):
        """Test that extract_data preserves lazy evaluation through generator."""

        def mock_generator():
            yield {"id": 1}
            yield {"id": 2}
            yield {"id": 3}

        self.mock_connection.execute_statement.return_value = mock_generator()

        result = self.extractor.extract_data()

        self.assertIsInstance(result, Generator)
        first_item = next(result)
        self.assertEqual(first_item, {"id": 1})

        remaining_items = list(result)
        self.assertEqual(remaining_items, [{"id": 2}, {"id": 3}])

    def test_multiple_extract_data_calls(self):
        """Test that multiple calls to extract_data work correctly."""
        path1 = "/path/to/results/1"
        path2 = "/path/to/results/2"
        self.mock_connection.execute_statement.side_effect = [path1, path2]

        result1 = self.extractor.extract_data()
        result2 = self.extractor.extract_data()

        self.assertEqual(self.mock_connection.execute_statement.call_count, 2)
        self.assertEqual(result1, path1)
        self.assertEqual(result2, path2)

    def test_extractor_with_different_statements(self):
        """Test extractor behavior with different SQL statements."""
        select_extractor = DataSourceExtractor(
            "SELECT * FROM users", self.mock_connection
        )
        self.assertEqual(select_extractor.statement, "SELECT * FROM users")

        insert_extractor = DataSourceExtractor(
            "INSERT INTO users VALUES (1, 'test')", self.mock_connection
        )
        self.assertEqual(
            insert_extractor.statement, "INSERT INTO users VALUES (1, 'test')"
        )

        complex_statement = """
        SELECT u.id, u.name, p.title
        FROM users u
        JOIN posts p ON u.id = p.user_id
        WHERE u.active = 1
        """
        complex_extractor = DataSourceExtractor(complex_statement, self.mock_connection)
        self.assertEqual(complex_extractor.statement, complex_statement)

    def test_connection_exception_handling(self):
        """Test that exceptions from connection are propagated."""
        self.mock_connection.execute_statement.side_effect = Exception(
            "Database connection error"
        )

        with self.assertRaises(Exception) as context:
            result = self.extractor.extract_data()
            next(result)  # Force generator execution

        self.assertEqual(str(context.exception), "Database connection error")


class MockDataSource(DataSourceInterface):
    """Mock implementation of DataSourceInterface for testing."""

    def __init__(self, test_data=None):
        self.test_data = test_data or []
        self.connection_created = False

    def create_connection(self):
        self.connection_created = True
        return "mock_connection"

    def execute_statement(self, statement: str, output_path: str = None):
        return iter(self.test_data)

    def close_connection(self):
        """Mock close_connection method."""
        pass


class TestDataSourceExtractorIntegration(unittest.TestCase):
    """Integration tests using MockDataSource."""

    def test_integration_with_mock_data_source(self):
        """Test DataSourceExtractor with a mock data source implementation."""
        test_data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]
        mock_data_source = MockDataSource(test_data)
        extractor = DataSourceExtractor("SELECT * FROM users", mock_data_source)

        result = extractor.extract_data()
        result_list = list(result)

        self.assertEqual(len(result_list), 3)
        self.assertEqual(result_list, test_data)

    def test_integration_with_empty_data_source(self):
        """Test DataSourceExtractor with empty data source."""
        mock_data_source = MockDataSource([])
        extractor = DataSourceExtractor("SELECT * FROM empty_table", mock_data_source)

        result = extractor.extract_data()
        result_list = list(result)

        self.assertEqual(len(result_list), 0)
        self.assertEqual(result_list, [])


if __name__ == "__main__":
    unittest.main()

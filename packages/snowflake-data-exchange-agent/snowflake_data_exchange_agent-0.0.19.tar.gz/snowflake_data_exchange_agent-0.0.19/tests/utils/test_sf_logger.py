import logging
import os
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from data_exchange_agent.utils.sf_logger import SFLogger


class TestSFLogger(unittest.TestCase):
    """Comprehensive test suite for the SFLogger class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after each test method."""
        logging.getLogger("test_logger").handlers.clear()
        logging.getLogger("data_exchange_agent").handlers.clear()

    @patch("data_exchange_agent.constants.paths._get_home_dir")
    @patch("os.makedirs")
    def test_sf_logger_initialization_default(self, mock_makedirs, mock_get_home_dir):
        """Test SFLogger initialization with default parameters."""
        mock_get_home_dir.return_value = tempfile.gettempdir()

        logger = SFLogger()

        self.assertEqual(logger.name, "data_exchange_agent")
        self.assertEqual(logger.logger.level, logging.INFO)

        mock_makedirs.assert_called_once()
        call_args = mock_makedirs.call_args[0][0]  # Get first positional argument
        self.assertTrue(
            call_args.endswith(os.path.join(".data_exchange_agent", "logs"))
        )

    @patch("data_exchange_agent.constants.paths._get_home_dir")
    @patch("os.makedirs")
    def test_sf_logger_initialization_custom(self, mock_makedirs, mock_get_home_dir):
        """Test SFLogger initialization with custom parameters."""
        mock_get_home_dir.return_value = tempfile.gettempdir()

        logger = SFLogger(
            name="custom_logger",
            log_level="DEBUG",
            console_output=False,
            file_output=True,
            max_file_size=5 * 1024 * 1024,
            backup_count=3,
        )

        self.assertEqual(logger.name, "custom_logger")
        self.assertEqual(logger.logger.level, logging.DEBUG)

    def test_sf_logger_prevents_duplicate_handlers(self):
        """Test that SFLogger prevents duplicate handlers."""
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()

            logger1 = SFLogger(name="test_logger")
            initial_handler_count = len(logger1.logger.handlers)

            logger2 = SFLogger(name="test_logger")

            self.assertEqual(len(logger2.logger.handlers), initial_handler_count)

    @patch("data_exchange_agent.constants.paths._get_home_dir")
    @patch("os.makedirs")
    def test_sf_logger_file_handler_creation(self, mock_makedirs, mock_get_home_dir):
        """Test that file handler is created correctly."""
        mock_get_home_dir.return_value = tempfile.gettempdir()

        with patch("logging.handlers.RotatingFileHandler") as mock_rotating_handler:
            mock_handler = Mock()
            mock_rotating_handler.return_value = mock_handler

            SFLogger(name="test_logger", file_output=True)

            mock_rotating_handler.assert_called_once()
            call_args = mock_rotating_handler.call_args[0][
                0
            ]  # Get first positional argument (path)
            self.assertTrue(
                call_args.endswith(
                    os.path.join(".data_exchange_agent", "logs", "test_logger.log")
                )
            )

            mock_handler.setFormatter.assert_called_once()

    @patch("data_exchange_agent.constants.paths._get_home_dir")
    @patch("os.makedirs")
    def test_sf_logger_console_handler_creation(self, mock_makedirs, mock_get_home_dir):
        """Test that console handler is created correctly."""
        mock_get_home_dir.return_value = tempfile.gettempdir()

        logger = SFLogger(name="test_logger", console_output=True)

        self.assertTrue(len(logger.logger.handlers) > 0)

        for handler in logger.logger.handlers:
            logger.logger.removeHandler(handler)

    @patch("data_exchange_agent.constants.paths._get_home_dir")
    @patch("os.makedirs")
    def test_sf_logger_no_handlers(self, mock_makedirs, mock_get_home_dir):
        """Test SFLogger with no handlers enabled."""
        mock_get_home_dir.return_value = tempfile.gettempdir()

        logger = SFLogger(name="test_logger", console_output=False, file_output=False)

        self.assertEqual(logger.name, "test_logger")

    def test_debug_method(self):
        """Test debug method.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with patch.object(logger.logger, "debug") as mock_debug:
                logger.debug("Debug message", extra_param="value")
                mock_debug.assert_called_once_with("Debug message", extra_param="value")

    def test_info_method(self):
        """Test info method.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with patch.object(logger.logger, "info") as mock_info:
                logger.info("Info message", extra_param="value")
                mock_info.assert_called_once_with("Info message", extra_param="value")

    def test_warning_method(self):
        """Test warning method.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with patch.object(logger.logger, "warning") as mock_warning:
                logger.warning("Warning message", extra_param="value")
                mock_warning.assert_called_once_with(
                    "Warning message", extra_param="value"
                )

    def test_error_method_without_exception(self):
        """Test error logging method without exception."""
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with (
                patch.object(logger.logger, "error") as mock_error,
                patch.object(logger.logger, "exception") as mock_exception,
            ):
                logger.error("Error message", extra_param="value")

                mock_error.assert_called_once_with("Error message", extra_param="value")
                mock_exception.assert_not_called()

    def test_error_method_with_exception(self):
        """Test error logging method with exception."""
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            test_exception = ValueError("Test exception")

            with (
                patch.object(logger.logger, "error") as mock_error,
                patch.object(logger.logger, "exception") as mock_exception,
            ):
                logger.error(
                    "Error message", exception=test_exception, extra_param="value"
                )

                mock_error.assert_called_once_with("Error message", extra_param="value")
                mock_exception.assert_called_once_with(
                    "Exception details:", exc_info=test_exception
                )

    def test_critical_method(self):
        """Test critical method.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with patch.object(logger.logger, "critical") as mock_critical:
                logger.critical("Critical message", extra_param="value")
                mock_critical.assert_called_once_with(
                    "Critical message", extra_param="value"
                )

    def test_log_task_start(self):
        """Test log task start.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with patch.object(logger, "info") as mock_info:
                logger.log_task_start("task_123", "data_extraction")
                mock_info.assert_called_once_with(
                    "TASK_START | ID: task_123 | Type: data_extraction"
                )

    def test_log_task_complete(self):
        """Test log_task_complete method."""
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with patch.object(logger, "info") as mock_info:
                logger.log_task_complete("task_123", 45.67, 1000)
                mock_info.assert_called_once_with(
                    "TASK_COMPLETE | ID: task_123 | Duration: 45.67s | Records: 1000"
                )

    def test_log_task_error(self):
        """Test log task error.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            test_error = ValueError("Test error")
            context = {"database": "test_db", "table": "test_table"}

            with patch.object(logger, "error") as mock_error:
                logger.log_task_error("task_123", test_error, context)

                expected_message = (
                    "TASK_ERROR | ID: task_123 | Error: Test error | "
                    "Context: {'database': 'test_db', 'table': 'test_table'}"
                )
                mock_error.assert_called_once_with(
                    expected_message, exception=test_error
                )

    def test_log_task_error_without_context(self):
        """Test log_task_error method without context."""
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            test_error = ValueError("Test error")

            with patch.object(logger, "error") as mock_error:
                logger.log_task_error("task_123", test_error)

                expected_message = "TASK_ERROR | ID: task_123 | Error: Test error"
                mock_error.assert_called_once_with(
                    expected_message, exception=test_error
                )

    def test_log_data_operation(self):
        """Test log_data_operation method."""
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger")

            with patch.object(logger, "info") as mock_info:
                logger.log_data_operation("extract", "postgresql_db", 5000, 12.34)

                expected_message = (
                    "DATA_OP | Operation: extract | Source: postgresql_db | "
                    "Records: 5000 | Duration: 12.34s"
                )
                mock_info.assert_called_once_with(expected_message)

    def test_set_level(self):
        """Test set level.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()
            logger = SFLogger(name="test_logger", log_level="INFO")

            mock_handler1 = Mock()
            mock_handler2 = Mock()
            logger.logger.handlers = [mock_handler1, mock_handler2]

            with patch.object(logger.logger, "setLevel") as mock_set_level:
                logger.set_level("DEBUG")

                mock_set_level.assert_called_once_with(logging.DEBUG)

                mock_handler1.setLevel.assert_called_once_with(logging.DEBUG)
                mock_handler2.setLevel.assert_called_once_with(logging.DEBUG)

    def test_formatters_are_configured(self):
        """Test that formatters are properly configured."""
        with (
            patch(
                "data_exchange_agent.constants.paths._get_home_dir"
            ) as mock_get_home_dir,
            patch("os.makedirs"),
        ):
            mock_get_home_dir.return_value = tempfile.gettempdir()

            with patch("logging.Formatter") as mock_formatter_class:
                mock_formatter = Mock()
                mock_formatter_class.return_value = mock_formatter

                SFLogger(name="test_logger", console_output=True, file_output=False)

                self.assertGreaterEqual(mock_formatter_class.call_count, 1)

                call_args = mock_formatter_class.call_args_list
                format_strings = [
                    call[1]["fmt"] for call in call_args if "fmt" in call[1]
                ]

                console_format_found = any(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s" in fmt
                    for fmt in format_strings
                )
                self.assertTrue(console_format_found)


if __name__ == "__main__":
    unittest.main()

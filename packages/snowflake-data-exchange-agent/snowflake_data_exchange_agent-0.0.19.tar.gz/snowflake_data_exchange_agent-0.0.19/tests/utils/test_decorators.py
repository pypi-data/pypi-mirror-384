import unittest
from unittest.mock import Mock, patch, call

from data_exchange_agent import custom_exceptions

from data_exchange_agent import custom_exceptions
from data_exchange_agent.utils.decorators import (
    api_endpoint_error,
    log_error,
    print_error_with_message,
)
from data_exchange_agent.utils.sf_logger import SFLogger


class TestDecorators(unittest.TestCase):
    """Comprehensive test suite for the Decorators class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_logger = Mock(spec=SFLogger)
        patcher = patch(
            "data_exchange_agent.utils.decorators._logger", self.mock_logger
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_log_error_decorator_success(self):
        """Test log_error decorator with successful function execution."""

        @log_error
        def test_function(x, y):
            return x + y

        result = test_function(2, 3)

        self.assertEqual(result, 5)
        self.mock_logger.error.assert_not_called()

    def test_log_error_decorator_with_exception(self):
        """Test log_error decorator with function that raises exception."""

        @log_error
        def test_function():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            test_function()

        self.mock_logger.error.assert_called_once()
        call_args = self.mock_logger.error.call_args
        self.assertIn("Error in test_function", call_args[0][0])
        self.assertIn("Test error", call_args[0][0])

    def test_log_error_decorator_with_logger_exception(self):
        """Test log_error decorator when logger itself raises exception."""
        self.mock_logger.error.side_effect = Exception("Logger error")

        @log_error
        def test_function():
            raise ValueError("Test error")

        with patch("builtins.print") as mock_print:

            with self.assertRaises(ValueError):
                test_function()

            mock_print.assert_called_once()
            self.assertIn(
                "Error logging error in test_function", mock_print.call_args[0][0]
            )

    def test_log_error_decorator_without_arguments(self):
        """Test log_error decorator used without parentheses."""

        @log_error
        def test_function():
            return "success"

        result = test_function()
        self.assertEqual(result, "success")

    def test_log_error_decorator_with_arguments(self):
        """Test log_error decorator used with parentheses."""

        @log_error()
        def test_function():
            return "success"

        result = test_function()
        self.assertEqual(result, "success")

    def test_print_error_with_message_decorator_success(self):
        """Test print_error_with_message decorator with successful execution."""

        @print_error_with_message("Custom error message")
        def test_function(x, y):
            return x * y

        result = test_function(3, 4)
        self.assertEqual(result, 12)

    def test_print_error_with_message_decorator_with_exception(self):
        """Test print_error_with_message decorator with exception."""

        @print_error_with_message("Custom error message")
        def test_function():
            raise RuntimeError("Test error")

        with patch("builtins.print") as mock_print:
            result = test_function()

            mock_print.assert_called_once_with("Custom error message")
            self.assertIsNone(result)

    def test_print_error_with_message_decorator_with_configuration_error_exception(
        self,
    ):
        """Test print_error_with_message decorator with configuration error exception."""

        @print_error_with_message("Custom error message")
        def test_function():
            raise custom_exceptions.ConfigurationError("Test error")

        with patch("builtins.print") as mock_print:
            result = test_function()

            expected_calls = [
                call("Custom error message"),
                call("Configuration file error: Test error"),
            ]
            mock_print.assert_has_calls(expected_calls)
            self.assertIsNone(result)

    def test_print_error_with_message_decorator_without_message(self):
        """Test print_error_with_message decorator without custom message."""

        @print_error_with_message()
        def test_function():
            raise RuntimeError("Test error")

        with patch("builtins.print") as mock_print:
            result = test_function()

            mock_print.assert_called_once_with(None)
            self.assertIsNone(result)

    def test_api_endpoint_error_decorator_success(self):
        """Test api_endpoint_error decorator with successful execution."""

        @api_endpoint_error
        def test_endpoint():
            return {"message": "success"}, 200

        result = test_endpoint()
        self.assertEqual(result, ({"message": "success"}, 200))

    def test_api_endpoint_error_decorator_with_exception(self):
        """Test api_endpoint_error decorator with exception."""

        @api_endpoint_error
        def test_endpoint():
            raise ValueError("API error")

        with patch("data_exchange_agent.utils.decorators.jsonify") as mock_jsonify:
            mock_jsonify.return_value = {"error": "API error"}

            result = test_endpoint()

            mock_jsonify.assert_called_once_with({"error": "API error"})
            self.assertEqual(result, ({"error": "API error"}, 500))

    def test_api_endpoint_error_decorator_preserves_function_metadata(self):
        """Test that decorators preserve function metadata."""

        @api_endpoint_error
        def test_function():
            """Test function.

            Validates the expected behavior and ensures proper functionality
            under the tested conditions.
            """
            pass

        self.assertEqual(test_function.__name__, "test_function")
        expected_docstring = """Test function.

            Validates the expected behavior and ensures proper functionality
            under the tested conditions.
            """
        self.assertEqual(test_function.__doc__, expected_docstring)

    def test_log_error_decorator_preserves_function_metadata(self):
        """Test that log_error decorator preserves function metadata."""

        @log_error
        def test_function():
            """Test function.

            Validates the expected behavior and ensures proper functionality
            under the tested conditions.
            """
            pass

        self.assertEqual(test_function.__name__, "test_function")
        expected_docstring = """Test function.

            Validates the expected behavior and ensures proper functionality
            under the tested conditions.
            """
        self.assertEqual(test_function.__doc__, expected_docstring)

    def test_print_error_with_message_decorator_preserves_function_metadata(self):
        """Test that print_error_with_message decorator preserves function metadata."""

        @print_error_with_message("Error message")
        def test_function():
            """Test function.

            Validates the expected behavior and ensures proper functionality
            under the tested conditions.
            """
            pass

        self.assertEqual(test_function.__name__, "test_function")
        expected_docstring = """Test function.

            Validates the expected behavior and ensures proper functionality
            under the tested conditions.
            """
        self.assertEqual(test_function.__doc__, expected_docstring)

    def test_decorators_with_function_arguments(self):
        """Test decorators work correctly with function arguments."""

        @log_error
        def test_function(a, b, c=None, *args, **kwargs):
            return {"a": a, "b": b, "c": c, "args": args, "kwargs": kwargs}

        result = test_function(1, 2, 4, 5, x=6, y=7)

        if "logger" in result["kwargs"]:
            del result["kwargs"]["logger"]

        expected = {
            "a": 1,
            "b": 2,
            "c": 4,  # c gets the third positional argument
            "args": (5,),
            "kwargs": {"x": 6, "y": 7},
        }
        self.assertEqual(result, expected)

    def test_multiple_decorators_stacking(self):
        """Test that multiple decorators can be stacked."""

        @api_endpoint_error
        @log_error
        def test_function():
            raise ValueError("Test error")

        with patch("data_exchange_agent.utils.decorators.jsonify") as mock_jsonify:

            mock_jsonify.return_value = {"error": "Test error"}

            result = test_function()

            self.assertEqual(result, ({"error": "Test error"}, 500))

            self.mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()

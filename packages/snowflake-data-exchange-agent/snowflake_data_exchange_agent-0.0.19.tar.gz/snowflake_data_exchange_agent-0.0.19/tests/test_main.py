import unittest
from unittest.mock import Mock, patch

from data_exchange_agent.main import main


class TestMain(unittest.TestCase):
    """
    Test suite for the main application entry point.

    This test class validates the main() function behavior, including:
    - Command-line argument parsing and validation
    - Flask application initialization with correct configuration
    - Server startup with proper host, port, and worker settings
    - Debug mode handling and development server configuration
    - Integration between CLI arguments and application config
    - Proper error handling for invalid arguments

    Tests use extensive mocking to avoid actually starting servers during
    test execution, ensuring fast and reliable test runs.
    """

    @patch("data_exchange_agent.main.FlaskApp")
    @patch("data_exchange_agent.main.argparse.ArgumentParser")
    def test_main_creates_flask_app_and_starts_server(
        self, mock_parser_class, mock_flask_app_class
    ):
        """
        Test that main() creates FlaskApp and starts server with correct configuration.

        Validates the complete application startup process:
        - Argument parser creation and configuration
        - Command-line argument parsing with expected defaults
        - FlaskApp instantiation with parsed configuration
        - Server startup with proper parameters

        Args:
            mock_parser_class: Mock for argparse.ArgumentParser
            mock_flask_app_class: Mock for FlaskApp class
        """
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        mock_args = Mock()
        mock_args.workers = 4
        mock_args.interval = 120
        mock_args.host = "0.0.0.0"
        mock_args.port = 5001
        mock_args.debug = False
        mock_parser.parse_args.return_value = mock_args

        mock_flask_app = Mock()
        mock_flask_app_class.return_value = mock_flask_app

        main()

        mock_flask_app_class.assert_called_once()

        expected_config = {
            "WORKERS": 4,
            "TASKS_FETCH_INTERVAL": 120,
            "DEBUG": False,
            "HOST": "0.0.0.0",
            "PORT": 5001,
            "USE_DEV_SERVER": False,
        }
        mock_flask_app.create_app.assert_called_once_with(expected_config)

        mock_flask_app.start_server.assert_called_once()

    @patch("data_exchange_agent.main.FlaskApp")
    @patch("data_exchange_agent.main.argparse.ArgumentParser")
    def test_main_with_debug_mode(self, mock_parser_class, mock_flask_app_class):
        """Test main with debug mode enabled."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        mock_args = Mock()
        mock_args.workers = 2
        mock_args.interval = 60
        mock_args.host = "127.0.0.1"
        mock_args.port = 8000
        mock_args.debug = True
        mock_parser.parse_args.return_value = mock_args

        mock_flask_app = Mock()
        mock_flask_app_class.return_value = mock_flask_app

        main()

        expected_config = {
            "WORKERS": 2,
            "TASKS_FETCH_INTERVAL": 60,
            "DEBUG": True,
            "HOST": "127.0.0.1",
            "PORT": 8000,
            "USE_DEV_SERVER": True,  # Should be True when debug is True
        }
        mock_flask_app.create_app.assert_called_once_with(expected_config)

    @patch("data_exchange_agent.main.FlaskApp")
    @patch("data_exchange_agent.main.argparse.ArgumentParser")
    def test_main_argument_parser_setup(self, mock_parser_class, mock_flask_app_class):
        """Test that argument parser is set up correctly."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_args.return_value = Mock(
            workers=4, interval=120, host="0.0.0.0", port=5001, debug=False
        )
        mock_flask_app_class.return_value = Mock()

        main()

        mock_parser_class.assert_called_once_with(
            description="Data Exchange Agent Flask Server"
        )

        [
            unittest.mock.call(
                "-w", "--workers", type=int, default=4, help="Number of worker threads"
            ),
            unittest.mock.call(
                "-i",
                "--interval",
                type=int,
                default=120,
                help="Interval in seconds to fetch tasks from the API",
            ),
            unittest.mock.call("--host", default="0.0.0.0", help="Host to bind to"),
            unittest.mock.call(
                "-p", "--port", type=int, default=5001, help="Port to bind to"
            ),
            unittest.mock.call(
                "-d", "--debug", action="store_true", help="Enable debug mode"
            ),
        ]

        self.assertEqual(mock_parser.add_argument.call_count, 5)

    @patch("data_exchange_agent.main.FlaskApp")
    @patch("data_exchange_agent.main.argparse.ArgumentParser")
    def test_main_with_exception_handling(
        self, mock_parser_class, mock_flask_app_class
    ):
        """Test that main handles exceptions properly with decorator."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_args.side_effect = Exception("Test exception")

        with patch("builtins.print") as mock_print:
            main()
            mock_print.assert_called_with(
                "Error starting the Data Exchange Agent application."
            )

    @patch("data_exchange_agent.main.FlaskApp")
    @patch(
        "sys.argv",
        ["main.py", "-w", "8", "-i", "60", "--host", "192.168.1.1", "-p", "9000", "-d"],
    )
    def test_main_with_command_line_args(self, mock_flask_app_class):
        """Test main with actual command line arguments."""
        mock_flask_app = Mock()
        mock_flask_app_class.return_value = mock_flask_app

        main()

        expected_config = {
            "WORKERS": 8,
            "TASKS_FETCH_INTERVAL": 60,
            "DEBUG": True,
            "HOST": "192.168.1.1",
            "PORT": 9000,
            "USE_DEV_SERVER": True,
        }
        mock_flask_app.create_app.assert_called_once_with(expected_config)


if __name__ == "__main__":
    unittest.main()

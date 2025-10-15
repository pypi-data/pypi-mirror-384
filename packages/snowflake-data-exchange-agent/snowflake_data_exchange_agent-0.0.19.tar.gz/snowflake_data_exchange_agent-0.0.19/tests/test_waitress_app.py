import os
import unittest
from unittest.mock import Mock, patch

from flask import Flask
from waitress import task
from waitress.server import WSGIServer

from data_exchange_agent.container import Container
from data_exchange_agent.servers.flask_app import FlaskApp
from data_exchange_agent.servers.waitress_app import WaitressApp
from data_exchange_agent.tasks.manager import TaskManager


class TestWaitressApp(unittest.TestCase):
    """Comprehensive test suite for the WaitressApp class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        container = Container()
        self.mock_flask_app = Mock(spec=Flask)
        self.mock_flask_app.container = container
        self.test_options = {
            "host": "0.0.0.0",
            "port": 8000,
            "threads": 4,
            "channel_timeout": 30,
        }

    def test_waitress_app_initialization(self):
        """Test WaitressApp initialization."""
        waitress_app = WaitressApp(self.mock_flask_app, self.test_options)

        self.assertEqual(waitress_app.app, self.mock_flask_app)
        self.assertEqual(waitress_app.options, self.test_options)

    def test_initialization_with_options(self):
        """Test WaitressApp initialization with options."""
        waitress_app = WaitressApp(self.mock_flask_app, self.test_options)

        self.assertEqual(waitress_app.options, self.test_options)
        self.assertEqual(waitress_app.app, self.mock_flask_app)

    def test_initialization_without_options(self):
        """Test WaitressApp initialization without options."""
        waitress_app = WaitressApp(self.mock_flask_app)

        self.assertEqual(waitress_app.options, {})
        self.assertEqual(waitress_app.app, self.mock_flask_app)

    def test_initialization_with_none_options(self):
        """Test WaitressApp initialization with None options."""
        waitress_app = WaitressApp(self.mock_flask_app, None)

        self.assertEqual(waitress_app.options, {})
        self.assertEqual(waitress_app.app, self.mock_flask_app)

    @patch("data_exchange_agent.servers.waitress_app.serve")
    def test_run_method(self, mock_serve):
        """Test run method calls waitress serve with correct parameters."""
        waitress_app = WaitressApp(self.mock_flask_app, self.test_options)

        waitress_app.run()

        mock_serve.assert_called_once_with(self.mock_flask_app, **self.test_options)

    @patch("data_exchange_agent.servers.waitress_app.serve")
    def test_run_with_empty_options(self, mock_serve):
        """Test run method with empty options."""
        waitress_app = WaitressApp(self.mock_flask_app, {})

        waitress_app.run()

        mock_serve.assert_called_once_with(self.mock_flask_app)

    @patch("data_exchange_agent.servers.waitress_app.serve")
    def test_run_with_task_manager_initialization(self, mock_serve):
        """Test run method when Flask app has container with task manager."""
        mock_flask_app = Mock(spec=Flask)
        mock_container = Mock()
        mock_task_manager = Mock(spec=TaskManager)
        mock_container.task_manager.provided.return_value = mock_task_manager
        mock_flask_app.container = mock_container

        waitress_app = WaitressApp(mock_flask_app, self.test_options)

        with patch("builtins.print") as mock_print:
            waitress_app.run(task_manager=mock_task_manager)

            mock_task_manager.handle_tasks.assert_called_once()
            mock_print.assert_any_call(
                "Task manager initialized and started to handle tasks"
            )

        mock_serve.assert_called_once_with(mock_flask_app, **self.test_options)

    @patch("data_exchange_agent.servers.waitress_app.serve")
    def test_run_with_container_exception(self, mock_serve):
        """Test run method when TaskManager startup raises exception."""
        mock_flask_app = Mock(spec=FlaskApp)
        mock_container = Mock()
        mock_task_manager = Mock(spec=TaskManager)
        mock_task_manager.handle_tasks.side_effect = Exception(
            "TaskManager startup failed"
        )

        mock_flask_app.container = mock_container

        waitress_app = WaitressApp(mock_flask_app, self.test_options)

        with patch("builtins.print") as mock_print:
            with self.assertRaises(Exception) as context:
                waitress_app.run(task_manager=mock_task_manager)
            self.assertEqual(len(context.exception.args), 1)
            self.assertEqual(context.exception.args[0], "TaskManager startup failed")

    @patch("data_exchange_agent.servers.waitress_app.serve")
    def test_run_container_attribute_error(self, mock_serve):
        """Test run method when container access raises AttributeError."""

        class MockFlaskApp:
            def __getattribute__(self, attr):
                if attr == "container":
                    raise AttributeError("No such attribute")
                return Mock()

        mock_flask_app = MockFlaskApp()

        waitress_app = WaitressApp(mock_flask_app, self.test_options)

        with self.assertRaises(Exception) as context:
            waitress_app.run()
            self.assertEqual(len(context.exception.args), 1)
            self.assertEqual(context.exception.args[0], "No such attribute")

    def test_run_method_is_callable(self):
        """Test that run method is callable."""
        waitress_app = WaitressApp(self.mock_flask_app, self.test_options)

        self.assertTrue(callable(waitress_app.run))

    def test_complex_options_configuration(self):
        """Test WaitressApp with complex options configuration."""
        complex_options = {
            "host": "127.0.0.1",
            "port": 9000,
            "threads": 8,
            "channel_timeout": 120,
            "connection_limit": 1000,
            "cleanup_interval": 30,
            "send_bytes": 18000,
        }

        waitress_app = WaitressApp(self.mock_flask_app, complex_options)

        self.assertEqual(waitress_app.options, complex_options)
        self.assertEqual(waitress_app.app, self.mock_flask_app)

    def test_waitress_app_with_real_flask_app(self):
        """Test WaitressApp with a real Flask application."""
        real_flask_app = Flask(__name__)

        waitress_app = WaitressApp(real_flask_app, self.test_options)

        self.assertEqual(waitress_app.app, real_flask_app)
        self.assertEqual(waitress_app.options, self.test_options)


if __name__ == "__main__":
    unittest.main()

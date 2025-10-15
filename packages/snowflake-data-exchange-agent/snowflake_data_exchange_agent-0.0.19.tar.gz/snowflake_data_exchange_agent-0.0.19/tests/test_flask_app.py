import functools
import json
import platform
import unittest

from unittest.mock import Mock, patch

from dependency_injector import providers
from flask import Flask, jsonify
import pytest
from data_exchange_agent.servers.flask_app import FlaskApp
from data_exchange_agent.utils.decorators import api_endpoint_error


class TestFlaskApp(unittest.TestCase):
    """Comprehensive test suite for the FlaskApp class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.flask_app = FlaskApp()

    @pytest.fixture(autouse=True)
    def mock_toml(self):
        with patch("data_exchange_agent.utils.toml.load_toml_file") as mock_toml:
            mock_toml.return_value = {
                "connection": {
                    "test_engine": {
                        "driver_name": "postgresql",
                        "host": "localhost",
                        "port": 5432,
                        "database": "test",
                        "username": "test",
                        "password": "test",
                    }
                },
                "cloud_storage": {
                    "test_bucket": {
                        "bucket": "test",
                        "region": "us-west-2",
                    }
                },
            }
            yield mock_toml

    def test_flask_app_initialization(self):
        """Test flask app initialization.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        self.assertIsInstance(self.flask_app, FlaskApp)

    @patch("data_exchange_agent.servers.flask_app.Container")
    def test_create_app_with_config(self, mock_container_class):
        """Test creating Flask app with custom configuration."""
        mock_container = Mock()
        mock_container_class.return_value = mock_container
        config = {
            "WORKERS": 8,
            "TASKS_FETCH_INTERVAL": 60,
            "DEBUG": True,
            "HOST": "127.0.0.1",
            "PORT": 8000,
        }

        self.flask_app.create_app(config)
        app = self.flask_app.app

        self.assertIsInstance(app, Flask)

        self.assertEqual(app.config["WORKERS"], 8)
        self.assertEqual(app.config["TASKS_FETCH_INTERVAL"], 60)
        self.assertTrue(app.config["DEBUG"])
        self.assertEqual(app.config["HOST"], "127.0.0.1")
        self.assertEqual(app.config["PORT"], 8000)

        self.assertEqual(app.container, mock_container)

    @patch("data_exchange_agent.servers.flask_app.Container")
    def test_create_app_with_default_config(self, mock_container_class):
        """Test creating Flask app with default configuration."""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        self.flask_app.create_app()

        self.assertIsInstance(self.flask_app.app, Flask)

        mock_container_class.assert_called_once()

    @patch("data_exchange_agent.servers.flask_app.Container")
    def test_create_app_task_manager_override(self, mock_container_class):
        """Test that TaskManager is properly overridden with config values."""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        config = {"WORKERS": 6, "TASKS_FETCH_INTERVAL": 90}

        self.flask_app.create_app(config)

        mock_container.task_manager.override.assert_called_once()

        call_args = mock_container.task_manager.override.call_args[0][0]
        self.assertIsInstance(call_args, providers.Singleton)

    @patch("data_exchange_agent.servers.flask_app.Container")
    def test_create_app_wiring(self, mock_container_class):
        """Test that dependency injection wiring is configured correctly."""
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        self.flask_app.create_app()

        mock_container.wire.assert_called_once()
        call_args = mock_container.wire.call_args
        modules = call_args[1]["modules"]

        expected_modules = [
            "data_exchange_agent.servers.flask_app",
            "data_exchange_agent.utils.decorators",
            "data_exchange_agent.tasks.manager",
            "data_exchange_agent.api.manager",
            "data_exchange_agent.data_sources.extractor",
            "data_exchange_agent.servers.flask_app",
        ]

        for module in expected_modules:
            self.assertIn(module, modules)

    def test_flask_app_routes_registration(self):
        """Test that all Flask routes are properly registered."""

        self.flask_app.create_app({"TESTING": True})

        routes = [rule.rule for rule in self.flask_app.app.url_map.iter_rules()]

        expected_routes = [
            "/health",
            "/stop",
            "/handle_tasks",
            "/get_handling_tasks_status",
            "/tasks",
            "/get_tasks_count",
            "/tasks_processed",
        ]

        for route in expected_routes:
            self.assertIn(route, routes)

    def test_health_endpoint(self):
        """Test the health check endpoint."""

        self.flask_app.create_app({"TESTING": True})

        with self.flask_app.app.test_client() as client:
            response = client.get("/health")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["service"], "data_exchange_agent")

    def test_stop_endpoint(self):
        """Test stop endpoint.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        self.flask_app.create_app({"TESTING": True})

        with self.flask_app.app.test_client() as client:
            response = client.get("/stop")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["message"], "Task manager stopped")

    def test_handle_tasks_endpoint(self):
        """Test the handle tasks endpoint."""

        self.flask_app.create_app({"TESTING": True})

        with self.flask_app.app.test_client() as client:
            response = client.get("/handle_tasks")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["message"], "Task manager started")

    def test_get_handling_tasks_status_endpoint(self):
        """Test the get handling tasks status endpoint."""
        self.flask_app.create_app({"TESTING": True})

        with self.flask_app.app.test_client() as client:
            response = client.get("/get_handling_tasks_status")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("handling_tasks", data)
            self.assertIsInstance(data["handling_tasks"], bool)

    def test_add_task_endpoint(self):
        """Test add task endpoint.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        self.flask_app.create_app({"TESTING": True})

        test_task = {
            "id": "123",
            "name": "test_task",
            "statement": "SELECT * FROM test",
        }

        with self.flask_app.app.test_client() as client:
            response = client.post(
                "/tasks", data=json.dumps(test_task), content_type="application/json"
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["message"], "Task added successfully")
            self.assertIn("id_task", data)

    def test_get_tasks_count_endpoint(self):
        """Test the get tasks count endpoint."""
        self.flask_app.create_app({"TESTING": True})

        with self.flask_app.app.test_client() as client:
            response = client.get("/get_tasks_count")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("tasks_count", data)
            self.assertIn("id_task", data)
            self.assertIn("worker_pid", data)
            self.assertIn("deque_id", data)
            self.assertIsInstance(data["tasks_count"], int)

    def test_get_tasks_processed_endpoint(self):
        """Test the get tasks processed endpoint."""
        self.flask_app.create_app({"TESTING": True})

        with self.flask_app.app.test_client() as client:
            response = client.get("/tasks_processed")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("tasks_processed", data)
            self.assertIsInstance(data["tasks_processed"], int)

    def test_endpoint_error_handling(self):
        """Test that endpoints handle errors gracefully."""
        app = Flask("test_app")

        @app.route("/test_error")
        @api_endpoint_error
        def test_error_route():
            raise Exception("Test error")

        with app.test_client() as client:
            response = client.get("/test_error")
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn("error", data)
            self.assertEqual(data["error"], "Test error")

    def test_start_handling_tasks(self):
        """Test start_handling_tasks method."""
        mock_task_manager = Mock()

        with patch("data_exchange_agent.servers.flask_app.Provide") as mock_provide:
            mock_provide.__getitem__.return_value = mock_task_manager

            self.flask_app.start_handling_tasks(task_manager=mock_task_manager)

            mock_task_manager.handle_tasks.assert_called_once()

    @patch("data_exchange_agent.servers.waitress_app.WaitressApp")
    def test_start_server_production_mode(self, mock_waitress_app_class):
        """Test starting server in production mode."""
        mock_waitress_app = Mock()
        mock_waitress_app_class.return_value = mock_waitress_app

        self.flask_app.create_app(
            {"DEBUG": False, "USE_DEV_SERVER": False, "HOST": "0.0.0.0", "PORT": 5001}
        )

        self.flask_app.start_server()

        mock_waitress_app_class.assert_called_once()
        mock_waitress_app.run.assert_called_once()

        call_args = mock_waitress_app_class.call_args
        options = call_args[0][1]

        self.assertEqual(options["host"], "0.0.0.0")
        self.assertEqual(options["port"], 5001)
        self.assertEqual(options["channel_timeout"], 300)
        self.assertEqual(options["cleanup_interval"], 30)
        self.assertEqual(options["connection_limit"], 1000)
        self.assertEqual(options["max_request_body_size"], 1073741824)

    def test_start_server_development_mode(self):
        """Test starting server in development mode."""
        with (
            patch.object(self.flask_app, "start_handling_tasks") as mock_start_handling,
            patch("flask.Flask.run") as mock_flask_run,
        ):
            self.flask_app.create_app(
                {
                    "DEBUG": True,
                    "USE_DEV_SERVER": True,
                    "HOST": "127.0.0.1",
                    "PORT": 8000,
                }
            )

            self.flask_app.start_server()

            mock_start_handling.assert_called_once()

            mock_flask_run.assert_called_once_with(
                host="127.0.0.1", port=8000, debug=True, threaded=True
            )

    def test_start_server_use_dev_server_flag(self):
        """Test starting server with USE_DEV_SERVER flag."""
        with (
            patch.object(self.flask_app, "start_handling_tasks") as mock_start_handling,
            patch("flask.Flask.run") as mock_flask_run,
        ):
            self.flask_app.create_app(
                {
                    "DEBUG": False,
                    "USE_DEV_SERVER": True,
                    "HOST": "localhost",
                    "PORT": 9000,
                }
            )

            self.flask_app.start_server()

            mock_start_handling.assert_called_once()
            mock_flask_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()

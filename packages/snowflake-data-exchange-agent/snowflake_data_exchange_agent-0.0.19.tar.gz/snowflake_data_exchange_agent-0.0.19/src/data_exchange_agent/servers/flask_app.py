"""
Flask web application server for the data exchange agent.

This module provides the FlaskApp class which implements a Flask-based
REST API server for the data exchange agent. It provides endpoints for
task management, health checks, and system status monitoring.
"""

import os

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from flask import Flask, jsonify, request

from data_exchange_agent.container import Container
from data_exchange_agent.tasks.manager import TaskManager
from data_exchange_agent.utils.decorators import api_endpoint_error


class FlaskApp:
    """
    Flask application class for the Data Exchange Agent.

    This class handles setting up and running a Flask web server that manages data processing tasks.
    It provides endpoints for:
    - Health checks
    - Starting/stopping task processing
    - Getting task status
    - Adding new tasks
    - Getting task counts and metrics

    The server can run in either development mode using Flask's built-in server,
    or production mode using Waitress. In production, it uses a single worker to ensure
    proper handling of the TaskManager singleton.
    """

    def create_app(self, config: dict | None = None) -> Flask:
        """
        Application factory for creating Flask app instances.

        Args:
            config: Configuration object or dictionary

        Returns:
            Flask application instance

        """
        self.app = Flask(__name__)

        # Configure the app
        if config:
            self.app.config.update(config)
        else:
            # Default configuration
            self.app.config.from_object("data_exchange_agent.config.Config")

        container = Container()
        self.app.container = container

        # Configure TaskManager with dynamic parameters from config
        container.task_manager.override(
            providers.Singleton(
                TaskManager,
                workers=self.app.config.get("WORKERS", 4),
                tasks_fetch_interval=self.app.config.get("TASKS_FETCH_INTERVAL", 120),
            )
        )

        # Wire all modules that use dependency injection AFTER configuring TaskManager
        container.wire(
            modules=[
                __name__,
                "data_exchange_agent.utils.decorators",  # Uses sf_logger
                "data_exchange_agent.tasks.manager",  # Uses sf_logger
                "data_exchange_agent.api.manager",  # Uses sf_logger
                "data_exchange_agent.data_sources.extractor",  # Uses sf_logger
                "data_exchange_agent.servers.flask_app",  # Uses task_manager
                "data_exchange_agent.servers.waitress_app",  # Uses task_manager
                "data_exchange_agent.uploaders.sf_stage_uploader",  # Uses snowflake_datasource
            ]
        )

        self.register_routes(self.app)
        return self.app

    @inject
    def start_handling_tasks(
        self, task_manager: TaskManager = Provide[Container.task_manager]
    ) -> None:
        """
        Start the task manager to begin processing tasks.

        This method initiates the task manager's task handling process. The task manager
        will begin fetching and processing tasks according to its configured interval.

        Args:
            task_manager: The TaskManager instance to start (injected dependency)

        Returns:
            None

        """
        task_manager.handle_tasks()

    @inject
    def register_routes(
        self, app: Flask, task_manager: TaskManager = Provide[Container.task_manager]
    ) -> None:
        """
        Register Flask routes with the application.

        This method registers the following endpoints:
        - /health: Health check endpoint for production monitoring
        - /stop: Stop the task manager
        - /handle_tasks: Start handling tasks
        - /get_handling_tasks_status: Get the status of tasks being handled
        - /tasks: Add a task to the task manager
        - /get_tasks_count: Get the number of tasks in the task manager
        - /tasks_processed: Get the number of tasks processed by the task manager

        Args:
            app: Flask application instance
            task_manager: TaskManager instance

        Returns:
            None

        Returns:
            None

        """

        @api_endpoint_error
        @app.route("/health")
        def health_check() -> tuple[dict, int]:
            """Health check endpoint for production monitoring."""
            return jsonify({"status": "healthy", "service": "data_exchange_agent"}), 200

        @api_endpoint_error
        @app.route("/stop")
        def stop_tasks() -> tuple[dict, int]:
            """Stop the task manager."""
            task_manager.stop_queue = True
            return jsonify({"message": "Task manager stopped"}), 200

        @api_endpoint_error
        @app.route("/handle_tasks")
        def handle_tasks() -> tuple[dict, int]:
            """Start handling tasks."""
            task_manager.handle_tasks()
            return jsonify({"message": "Task manager started"}), 200

        @api_endpoint_error
        @app.route("/get_handling_tasks_status")
        def get_handling_tasks_status() -> tuple[dict, int]:
            """Get the status of tasks being handled."""
            return jsonify({"handling_tasks": task_manager.handling_tasks}), 200

        @api_endpoint_error
        @app.route("/tasks", methods=["POST"])
        def add_task() -> tuple[dict, int]:
            """Add a task to the task manager."""
            json_data = request.get_json()
            task_manager.add_task(json_data)
            id_task = id(task_manager)
            return (
                jsonify(
                    {
                        "message": "Task added successfully",
                        "id_task": id_task,
                    }
                ),
                200,
            )

        @api_endpoint_error
        @app.route("/get_tasks_count")
        def get_tasks_count() -> tuple[dict, int]:
            """Get the number of tasks in the task manager."""
            tasks_count = task_manager.get_tasks_count()
            return (
                jsonify(
                    {
                        "tasks_count": tasks_count,
                        "id_task": id(task_manager),
                        "worker_pid": os.getpid(),
                        "deque_id": task_manager.get_deque_id(),
                    }
                ),
                200,
            )

        @api_endpoint_error
        @app.route("/tasks_processed")
        def get_tasks_processed() -> tuple[dict, int]:
            """Get the number of tasks processed by the task manager."""
            return jsonify({"tasks_processed": task_manager.get_completed_count()}), 200

    def start_server(self) -> None:
        """
        Start the Flask server.

        This method starts the server in either development or production mode.
        In development mode, it uses Flask's built-in server for easier debugging.
        In production mode, it uses Waitress with a single worker to ensure proper handling
        of the TaskManager singleton.

        Returns:
            None

        """
        if self.app.config.get("DEBUG", False) or self.app.config.get(
            "USE_DEV_SERVER", False
        ):
            self.start_handling_tasks()
            self.app.run(
                host=self.app.config.get("HOST", "0.0.0.0"),
                port=self.app.config.get("PORT", 5001),
                debug=self.app.config.get("DEBUG", False),
                threaded=True,
            )
        else:
            from data_exchange_agent.servers.waitress_app import WaitressApp

            options = {
                "host": self.app.config.get("HOST", "0.0.0.0"),
                "port": self.app.config.get("PORT", 5001),
                "channel_timeout": 300,
                "cleanup_interval": 30,
                "connection_limit": 1000,
                "max_request_body_size": 1073741824,
            }

            WaitressApp(self.app, options).run()

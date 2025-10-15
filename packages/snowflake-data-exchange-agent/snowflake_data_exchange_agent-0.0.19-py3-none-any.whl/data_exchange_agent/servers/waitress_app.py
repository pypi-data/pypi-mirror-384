"""Waitress WSGI server wrapper for Flask applications."""

from dependency_injector.wiring import Provide, inject
from flask import Flask
from waitress import serve

from data_exchange_agent.interfaces.wsgi_server import WSGIServerInterface
from data_exchange_agent.tasks.manager import TaskManager
from data_exchange_agent.utils.decorators import log_error


class WaitressApp(WSGIServerInterface):
    """
    A Waitress application wrapper for Flask.

    This class provides a production-ready WSGI server implementation using Waitress.
    It wraps a Flask application and allows configuring Waitress server options.

    Args:
        app (Flask): The Flask application instance to serve
        options (dict | None): Dictionary of Waitress server options. Common options include:
            - host: The server host to bind to (e.g. "0.0.0.0")
            - port: The port number to listen on
            - channel_timeout: Connection timeout in seconds
            - cleanup_interval: How often to clean up inactive connections
            - connection_limit: Maximum number of concurrent connections
            - max_request_body_size: Maximum request body size in bytes

    """

    @log_error
    def __init__(self, app: Flask, options: dict | None = None):
        """
        Initialize the Waitress application wrapper.

        Args:
            app (Flask): The Flask application instance to serve
            options (dict | None): Dictionary of Waitress configuration options.
                                If None, an empty dictionary is used.

        """
        self.app = app
        self.options = options or {}

    @log_error
    @inject
    def run(self, task_manager: TaskManager = Provide["task_manager"]) -> None:
        """
        Start the Waitress WSGI server.

        Starts serving the Flask application using the configured Waitress WSGI server.
        This method blocks until the server is stopped.
        """
        task_manager.handle_tasks()
        print("Task manager initialized and started to handle tasks")
        serve(
            self.app,
            **self.options,
        )

    @log_error
    def start(self) -> None:
        """Start the Waitress server."""
        self.run()

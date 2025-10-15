"""
Main entry point for the data exchange agent application.

This module provides the main function and command-line interface for starting
the data exchange agent server with configurable parameters.
"""

import argparse

from data_exchange_agent.servers.flask_app import FlaskApp
from data_exchange_agent.utils.decorators import print_error_with_message


@print_error_with_message(
    error_message="Error starting the Data Exchange Agent application."
)
def main() -> None:
    """
    Start the data exchange agent application.

    Starts a Flask web server that manages data processing tasks. The server provides endpoints to:
    - Start and stop task processing
    - Get status of tasks being handled
    - Add new tasks to be processed

    Command line arguments:
        -w, --workers: Number of worker threads (default: 4)
        -i, --interval: Interval in seconds to fetch tasks from the API (default: 120)
        --host: Host to bind to (default: 0.0.0.0)
        --port: Port to bind to (default: 5001)
        --debug: Enable debug mode (default: False)

    Returns:
        None

    """
    parser = argparse.ArgumentParser(description="Data Exchange Agent Flask Server")
    parser.add_argument(
        "-w", "--workers", type=int, default=4, help="Number of worker threads"
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=120,
        help="Interval in seconds to fetch tasks from the API",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("-p", "--port", type=int, default=5001, help="Port to bind to")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    flask_app = FlaskApp()
    flask_app.create_app(
        {
            "WORKERS": args.workers,
            "TASKS_FETCH_INTERVAL": args.interval,
            "DEBUG": args.debug,
            "HOST": args.host,
            "PORT": args.port,
            "USE_DEV_SERVER": args.debug,
        }
    )

    flask_app.start_server()


if __name__ == "__main__":
    main()

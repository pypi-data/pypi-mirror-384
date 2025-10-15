"""
Configuration module for the data exchange agent.

This module defines the default configuration class and settings for the
data exchange agent application.
"""


class Config:
    """
    Default configuration for the data exchange agent.

    Attributes:
        WORKERS (int): Number of worker threads for task processing (default: 4)
        TASKS_FETCH_INTERVAL (int): Interval in seconds between task fetches (default: 120)
        DEBUG (bool): Enable debug mode (default: False)

    """

    WORKERS = 4
    TASKS_FETCH_INTERVAL = 120
    DEBUG = False

"""
Task management and execution system.

This module provides the TaskManager class which orchestrates task execution
across multiple worker threads, handles task lifecycle management, API
communication, and integrates with various data sources and uploaders.
"""

import os
import threading
import time

from concurrent.futures import ThreadPoolExecutor

from dependency_injector.wiring import Provide, inject

from data_exchange_agent.api.manager import APIManager
from data_exchange_agent.constants.container import SF_LOGGER
from data_exchange_agent.constants.manager import MAX_WORKERS, TASKS_FETCH_INTERVAL
from data_exchange_agent.constants.paths import (
    CONFIGURATION_FILE_PATH,
    build_actual_results_folder_path,
)
from data_exchange_agent.constants.task import (
    ENGINE,
    ID,
    STATEMENT,
    UPLOAD_PATH,
    UPLOAD_TYPE,
)
from data_exchange_agent.data_sources.extractor import DataSourceExtractor
from data_exchange_agent.data_sources.pyspark import PySparkDataSource
from data_exchange_agent.enums.task_status import TaskStatus
from data_exchange_agent.interfaces.data_source import DataSourceInterface
from data_exchange_agent.interfaces.task_queue import TaskQueueInterface
from data_exchange_agent.providers.storageProvider import StorageProvider
from data_exchange_agent.queues.sqlite_task_queue import SQLiteTaskQueue
from data_exchange_agent.utils.decorators import log_error
from data_exchange_agent.utils.sf_logger import SFLogger
from data_exchange_agent.utils.toml import get_connection_and_cloud_storage_toml


class TaskManager:
    """
    Manages asynchronous task processing using a thread pool and task queue.

    This class handles fetching, queueing and processing of data extraction tasks.
    It maintains a thread pool for parallel task execution and uses a thread-safe
    task queue.

    Attributes:
        executor (ThreadPoolExecutor): Thread pool for executing tasks
        task_queue (TaskQueueInterface): Thread-safe queue of tasks to process
        stop_queue (bool): Flag to stop task processing
        api_manager (APIManager): Manager for API interactions
        tasks_fetch_interval (int): Seconds between task fetch attempts
        handling_tasks (bool): Whether tasks are currently being handled
        connection_toml (dict): Database connection configurations

    Args:
        workers (int, optional): Number of worker threads. Defaults to 4.
        tasks_fetch_interval (int, optional): Task fetch interval in seconds. Defaults to 120.

    """

    @property
    def stop_queue(self) -> bool:
        """
        Get the stop queue flag.

        Returns:
            bool: True if queue processing should stop, False otherwise

        """
        return self._stop_queue

    @stop_queue.setter
    def stop_queue(self, value: bool) -> None:
        """
        Set the stop queue flag.

        Args:
            value (bool): True to stop queue processing, False to continue

        """
        self._stop_queue = value

    @log_error
    @inject
    def __init__(
        self,
        workers: int = MAX_WORKERS,
        tasks_fetch_interval: int = TASKS_FETCH_INTERVAL,
        logger: SFLogger = Provide[SF_LOGGER],
    ) -> None:
        """
        Initialize the TaskManager with specified configuration.

        Sets up the task execution environment including thread pool executor,
        task queue, API manager, and loads configuration from TOML file.
        Initializes all necessary components for managing and processing tasks.

        Args:
            workers (int): Number of worker threads for concurrent task execution.
                         Defaults to 4.
            tasks_fetch_interval (int): Interval in seconds between API task fetches.
                                      Defaults to 120 seconds.
            logger (SFLogger): Logger instance for logging messages.
                             Defaults to injected sf_logger.

        Raises:
            Exception: If the configuration TOML file cannot be loaded.
            custom_exceptions.ConfigurationError: If something was wrong with the configuration TOML file.

        """
        self.logger = logger
        self.executor = ThreadPoolExecutor(max_workers=workers)
        self.task_queue: TaskQueueInterface = SQLiteTaskQueue()
        self.stop_queue = False
        self.api_manager = APIManager()
        self.tasks_fetch_interval = tasks_fetch_interval
        self.handling_tasks = False

        (
            self.connection_toml,
            self.cloud_storage_toml,
        ) = get_connection_and_cloud_storage_toml(CONFIGURATION_FILE_PATH)
        self.sources = {"PySparkDataSource": PySparkDataSource}

    @log_error
    def add_task(self, task: dict[str, any]) -> None:
        """
        Add a single task to the task queue.

        Args:
            task (dict[str, any]): Task configuration dictionary

        """
        self.task_queue.add_task(task)

    @log_error
    def get_tasks(self) -> None:
        """Fetch tasks from API and add them to the task queue."""
        tasks = self.api_manager.get_tasks()["tasks"]
        for task in tasks:
            self.task_queue.add_task(task)

    @log_error
    def get_tasks_count(self) -> int:
        """
        Get current number of tasks in queue.

        Returns:
            int: Number of tasks in queue

        """
        return self.task_queue.get_queue_size()

    @log_error
    def get_deque_id(self) -> int:
        """
        Get memory ID of task queue.

        Returns:
            int: Memory ID of task queue object

        """
        return id(self.task_queue)

    @log_error
    def get_completed_count(self) -> int:
        """
        Get the number of completed tasks.

        Returns:
            Number of completed tasks

        """
        return self.task_queue.get_completed_count()

    @log_error
    def handle_tasks(self) -> None:
        """
        Start task handling in a background thread.

        Creates a daemon thread to process tasks if not already running.
        """
        if self.handling_tasks:
            self.logger.info(f"*** TaskManager already handling tasks in PID: {os.getpid()} ***")
            return
        self.handling_tasks = True
        task_thread = threading.Thread(target=self.task_loop, daemon=True)
        task_thread.start()

    def task_loop(self) -> None:
        """
        Process tasks continuously in a loop.

        Continuously fetches and processes tasks from the queue until stopped.
        Handles task retrieval, execution and error handling.
        """
        while True:
            try:
                if self.stop_queue:
                    self.handling_tasks = False
                    self.stop_queue = False
                    break

                self.get_tasks()

                while True:
                    task = None
                    task = self.task_queue.get_task()

                    if task:
                        self.logger.info(f"🚀 Processing task: {task}")
                        self.executor.submit(
                            self.process_task,
                            task,
                        )
                        time.sleep(0.5)
                    else:
                        break

            except Exception as e:
                self.logger.error(f"Error in task_loop: {str(e)}", exception=e)
            finally:
                time.sleep(self.tasks_fetch_interval)

    def process_task(self, task: dict[str, any]) -> None:
        """
        Process a single data extraction task.

        Creates appropriate data source, extracts data and saves to parquet.
        Updates task status on completion.

        Args:
            task (dict[str, any]): Task configuration dictionary

        """
        try:
            data_source: DataSourceInterface | None = None
            data_source_class = self.sources[task["source_type"]]
            if task["engine"] not in self.connection_toml:
                raise Exception(f"Engine {task['engine']} not found in connection section in the TOML file.")

            engine_toml = self.connection_toml[task[ENGINE]]

            data_source = data_source_class(
                **engine_toml,
            )

            data_source.create_connection()

            data_source_extractor = DataSourceExtractor(
                statement=task[STATEMENT],
                connection=data_source,
            )
            results_folder_path = build_actual_results_folder_path(task[ID])
            data_source_extractor.extract_data(results_folder_path)

            storage_provider = StorageProvider(task[UPLOAD_TYPE], self.cloud_storage_toml)
            storage_provider.upload_files(results_folder_path, task[UPLOAD_PATH])

            self.api_manager.update_task(
                {
                    "task_id": task[ID],
                    "status": TaskStatus.SUCCESSFUL.value,
                    "details": None,
                }
            )
            self.task_queue.complete_task(task)
        except Exception as e:
            self.logger.error(f"Error in process_task: {str(e)}", exception=e)
            self.api_manager.update_task(
                {
                    "task_id": task[ID],
                    "status": TaskStatus.FAILED.value,
                    "details": str(e),
                }
            )
            self.task_queue.fail_task(task, str(e))

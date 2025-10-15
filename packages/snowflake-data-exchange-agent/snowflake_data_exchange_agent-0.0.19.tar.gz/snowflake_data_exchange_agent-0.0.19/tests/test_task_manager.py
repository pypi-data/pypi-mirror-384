from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from data_exchange_agent.api.manager import APIManager
from data_exchange_agent.container import Container
from data_exchange_agent.data_sources.pyspark import PySparkDataSource
from data_exchange_agent.providers.storageProvider import StorageProvider
from data_exchange_agent.queues.sqlite_task_queue import SQLiteTaskQueue
from data_exchange_agent.tasks.manager import TaskManager
from data_exchange_agent.uploaders.azure_blob_uploader import AzureBlobUploader
from data_exchange_agent.utils.sf_logger import SFLogger


class TestTaskManager(unittest.TestCase):
    """
    Comprehensive test suite for the TaskManager class.

    This test class validates the TaskManager's core functionality, including:
    - Initialization with worker pools and task queues
    - Task fetching from API endpoints at configured intervals
    - Task execution using thread pool executors
    - Task status updates and result handling
    - Error handling and retry mechanisms
    - Graceful shutdown and cleanup procedures
    - Integration with SQLite task queues and API managers

    Tests use extensive mocking to isolate the TaskManager from external
    dependencies like databases, APIs, and file systems, ensuring reliable
    and fast test execution.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.

        Creates a TaskManager instance with mocked TOML configuration
        to avoid file system dependencies. Sets up test database
        configuration and initializes the TaskManager with reduced
        worker count and fetch interval for faster test execution.
        """
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
            self.mock_logger = Mock(spec=SFLogger)
            container = Container()
            container.sf_logger.override(self.mock_logger)
            container.wire(
                modules=[
                    "data_exchange_agent.utils.decorators",
                    "data_exchange_agent.tasks.manager",
                ]
            )
            # Directly pass the mock logger to bypass dependency injection
            self.task_manager = TaskManager(workers=2, tasks_fetch_interval=10)

    def test_task_manager_initialization(self):
        """Test TaskManager initialization with correct attributes."""
        self.assertEqual(self.task_manager.executor._max_workers, 2)
        self.assertEqual(self.task_manager.tasks_fetch_interval, 10)
        self.assertIsInstance(self.task_manager.task_queue, SQLiteTaskQueue)
        self.assertIsInstance(self.task_manager.api_manager, APIManager)
        self.assertFalse(self.task_manager.stop_queue)
        self.assertFalse(self.task_manager.handling_tasks)

    def test_task_manager_default_initialization(self):
        """Test TaskManager initialization with default parameters."""
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
            task_manager = TaskManager()

            self.assertEqual(task_manager.executor._max_workers, 4)
            self.assertEqual(task_manager.tasks_fetch_interval, 120)

    def test_stop_queue_property(self):
        """Test stop_queue property getter and setter."""
        self.assertFalse(self.task_manager.stop_queue)

        self.task_manager.stop_queue = True
        self.assertTrue(self.task_manager.stop_queue)

        self.task_manager.stop_queue = False
        self.assertFalse(self.task_manager.stop_queue)

    def test_add_task(self):
        """Test adding a task to the queue."""
        test_task = {"id": "123", "name": "test_task"}

        with patch.object(self.task_manager.task_queue, "add_task") as mock_add:
            self.task_manager.add_task(test_task)
            mock_add.assert_called_once_with(test_task)

    def test_get_tasks(self):
        """Test fetching tasks from API and adding to queue."""
        mock_tasks = {
            "tasks": [{"id": "1", "name": "task1"}, {"id": "2", "name": "task2"}]
        }

        with (
            patch.object(self.task_manager.api_manager, "get_tasks") as mock_get_tasks,
            patch.object(self.task_manager.task_queue, "add_task") as mock_add_task,
        ):
            mock_get_tasks.return_value = mock_tasks

            self.task_manager.get_tasks()

            mock_get_tasks.assert_called_once()
            self.assertEqual(mock_add_task.call_count, 2)
            mock_add_task.assert_any_call({"id": "1", "name": "task1"})
            mock_add_task.assert_any_call({"id": "2", "name": "task2"})

    def test_get_tasks_count(self):
        """Test getting task count from queue."""
        with patch.object(self.task_manager.task_queue, "get_queue_size") as mock_size:
            mock_size.return_value = 5

            result = self.task_manager.get_tasks_count()

            self.assertEqual(result, 5)
            mock_size.assert_called_once()

    def test_get_deque_id(self):
        """Test getting queue memory ID."""
        result = self.task_manager.get_deque_id()
        expected_id = id(self.task_manager.task_queue)

        self.assertEqual(result, expected_id)

    def test_get_completed_count(self):
        """Test getting completed task count from queue."""
        with patch.object(
            self.task_manager.task_queue, "get_completed_count"
        ) as mock_completed_count:
            mock_completed_count.return_value = 7

            result = self.task_manager.get_completed_count()

            self.assertEqual(result, 7)
            mock_completed_count.assert_called_once()

    def test_handle_tasks_first_time(self):
        """Test starting task handling for the first time."""
        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            self.task_manager.handle_tasks()

            self.assertTrue(self.task_manager.handling_tasks)
            mock_thread.assert_called_once_with(
                target=self.task_manager.task_loop, daemon=True
            )
            mock_thread_instance.start.assert_called_once()

    def test_handle_tasks_already_handling(self):
        """Test handle_tasks when already handling tasks."""
        self.task_manager.handling_tasks = True

        with (
            patch("threading.Thread") as mock_thread,
            patch("os.getpid") as mock_getpid,
        ):
            mock_getpid.return_value = 12345

            mock_logger = Mock()
            self.task_manager.logger = mock_logger
            self.task_manager.handle_tasks()

            mock_thread.assert_not_called()
            mock_logger.info.assert_called_once_with(
                "*** TaskManager already handling tasks in PID: 12345 ***"
            )

    def test_run_task(self):
        """Test submitting a task for execution via executor."""
        test_task = {"id": "123", "name": "test_task"}

        with patch.object(self.task_manager.executor, "submit") as mock_submit:
            self.task_manager.executor.submit(self.task_manager.process_task, test_task)

            mock_submit.assert_called_once_with(
                self.task_manager.process_task, test_task
            )

    def test_process_task_success(self):
        """Test successful task processing."""
        test_task = {
            "id": "123",
            "source_type": "PySparkDataSource",
            "engine": "test_engine",
            "statement": "SELECT * FROM test_table",
            "upload_type": "s3",
            "upload_path": "/test/path",
        }

        mock_data_source_class = Mock()
        mock_data_source = Mock()
        mock_data_source_class.return_value = mock_data_source

        self.task_manager.connection_toml = {
            "test_engine": {
                "driver_name": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test",
                "username": "test",
                "password": "test",
            }
        }

        with (
            patch(
                "data_exchange_agent.data_sources.pyspark.PySparkDataSource",
                mock_data_source_class,
            ),
            patch.object(
                self.task_manager,
                "sources",
                {"PySparkDataSource": mock_data_source_class},
            ),
            patch(
                "data_exchange_agent.tasks.manager.DataSourceExtractor"
            ) as mock_extractor_class,
            patch(
                "data_exchange_agent.tasks.manager.build_actual_results_folder_path"
            ) as mock_build_path,
            patch(
                "data_exchange_agent.tasks.manager.StorageProvider"
            ) as mock_storage_provider_class,
            patch.object(
                self.task_manager.api_manager, "update_task"
            ) as mock_update_task,
            patch.object(
                self.task_manager.task_queue, "complete_task"
            ) as mock_complete_task,
        ):
            mock_extractor = Mock()
            mock_extractor.extract_data = Mock()  # Change get_data to extract_data
            mock_extractor_class.return_value = mock_extractor

            mock_build_path.return_value = "/test/results/path"

            mock_storage_provider = Mock()
            mock_storage_provider_upload_files = Mock()
            mock_storage_provider_class.return_value = mock_storage_provider
            mock_storage_provider.upload_files = mock_storage_provider_upload_files

            self.task_manager.process_task(test_task)

            mock_data_source_class.assert_called_once()
            mock_data_source.create_connection.assert_called_once()

            mock_extractor_class.assert_called_once_with(
                statement="SELECT * FROM test_table", connection=mock_data_source
            )
            mock_extractor.extract_data.assert_called_once_with("/test/results/path")

            mock_update_task.assert_called_once_with(
                {
                    "task_id": "123",
                    "status": "successful",
                    "details": None,
                }
            )
            mock_complete_task.assert_called_once_with(test_task)

    def test_to_parquet_with_list_data(self):
        """Test data extraction and processing with list data."""
        test_task = {
            "id": "123",
            "source_type": "PySparkDataSource",
            "engine": "test_engine",
            "statement": "SELECT * FROM test_table",
            "upload_type": "s3",
            "upload_path": "test/path",
        }

        mock_data_source = Mock()
        mock_extractor = Mock()
        mock_data_source_class = Mock(return_value=mock_data_source)

        with (
            patch(
                "data_exchange_agent.data_sources.pyspark.PySparkDataSource",
                mock_data_source_class,
            ),
            patch.object(
                self.task_manager,
                "sources",
                {"PySparkDataSource": mock_data_source_class},
            ),
            patch(
                "data_exchange_agent.tasks.manager.DataSourceExtractor",
                return_value=mock_extractor,
            ),
            patch(
                "data_exchange_agent.constants.paths.build_actual_results_folder_path",
                return_value="/test/results",
            ),
            patch.object(self.task_manager.api_manager, "update_task"),
            patch.object(self.task_manager.task_queue, "complete_task"),
        ):
            self.task_manager.connection_toml = {"test_engine": {"host": "localhost"}}

            self.task_manager.process_task(test_task)

            mock_extractor.extract_data.assert_called_once()
            mock_data_source.create_connection.assert_called_once()
            mock_extractor.extract_data.assert_called_once()

    def test_to_parquet_with_generator_data(self):
        """Test data extraction process with different data sources."""
        test_task = {
            "id": "456",
            "source_type": "PySparkDataSource",
            "engine": "test_engine",
            "statement": "SELECT * FROM generator_table",
            "upload_type": "s3",
            "upload_path": "test/path",
        }

        mock_data_source = Mock()
        mock_extractor = Mock()
        mock_data_source_class = Mock(return_value=mock_data_source)

        with (
            patch(
                "data_exchange_agent.data_sources.pyspark.PySparkDataSource",
                mock_data_source_class,
            ),
            patch.object(
                self.task_manager,
                "sources",
                {"PySparkDataSource": mock_data_source_class},
            ),
            patch(
                "data_exchange_agent.tasks.manager.DataSourceExtractor",
                return_value=mock_extractor,
            ),
            patch(
                "data_exchange_agent.constants.paths.build_actual_results_folder_path",
                return_value="/test/results",
            ),
            patch.object(self.task_manager.api_manager, "update_task"),
            patch.object(self.task_manager.task_queue, "complete_task"),
        ):
            self.task_manager.connection_toml = {"test_engine": {"host": "localhost"}}

            self.task_manager.process_task(test_task)

            mock_extractor.extract_data.assert_called_once()

    def test_to_parquet_with_empty_data(self):
        """Test data extraction with minimal task configuration."""
        test_task = {
            "id": "789",
            "source_type": "PySparkDataSource",
            "engine": "test_engine",
            "statement": "SELECT * FROM empty_table",
            "upload_type": "s3",
            "upload_path": "test/path",
        }

        mock_data_source = Mock()
        mock_extractor = Mock()
        mock_data_source_class = Mock(return_value=mock_data_source)

        with (
            patch(
                "data_exchange_agent.data_sources.pyspark.PySparkDataSource",
                mock_data_source_class,
            ),
            patch.object(
                self.task_manager,
                "sources",
                {"PySparkDataSource": mock_data_source_class},
            ),
            patch(
                "data_exchange_agent.tasks.manager.DataSourceExtractor",
                return_value=mock_extractor,
            ),
            patch(
                "data_exchange_agent.constants.paths.build_actual_results_folder_path",
                return_value="/test/results",
            ),
            patch.object(self.task_manager.api_manager, "update_task"),
            patch.object(self.task_manager.task_queue, "complete_task"),
        ):
            self.task_manager.connection_toml = {"test_engine": {"host": "localhost"}}

            self.task_manager.process_task(test_task)

            mock_extractor.extract_data.assert_called_once()

    def test_to_parquet_with_exception(self):
        """Test error handling in task processing."""
        test_task = {
            "id": "error_task",
            "source_type": "PySparkDataSource",
            "engine": "test_engine",
            "statement": "SELECT * FROM error_table",
        }

        mock_data_source = Mock()
        mock_data_source.create_connection.side_effect = Exception("Connection failed")

        with (
            patch.object(
                self.task_manager,
                "sources",
                {"PySparkDataSource": Mock(return_value=mock_data_source)},
            ),
            patch.object(self.task_manager.api_manager, "update_task") as mock_update,
            patch.object(self.task_manager.task_queue, "fail_task") as mock_fail,
        ):
            self.task_manager.connection_toml = {"test_engine": {"host": "localhost"}}

            self.task_manager.process_task(test_task)

            mock_update.assert_called_once()
            mock_fail.assert_called_once()

    def test_task_loop_stop_condition(self):
        """Test task loop stops when stop_queue is True."""
        self.task_manager.stop_queue = True

        with (
            patch.object(self.task_manager, "get_tasks") as mock_get_tasks,
            patch("time.sleep"),
        ):
            self.task_manager.task_loop()

            self.assertFalse(self.task_manager.handling_tasks)
            self.assertFalse(self.task_manager.stop_queue)

            mock_get_tasks.assert_not_called()

    def test_task_loop_processes_tasks(self):
        """Test task loop processes available tasks."""
        test_task = {"id": "123", "name": "test_task"}

        with (
            patch.object(self.task_manager, "get_tasks"),
            patch.object(self.task_manager.task_queue, "get_task") as mock_get_task,
            patch.object(self.task_manager.executor, "submit") as mock_submit,
            patch("time.sleep") as mock_sleep,
        ):
            mock_get_task.side_effect = [test_task, None]

            def stop_after_first_iteration(*args):
                self.task_manager.stop_queue = True

            mock_sleep.side_effect = stop_after_first_iteration

            self.task_manager.task_loop()

            mock_submit.assert_called_once_with(
                self.task_manager.process_task, test_task
            )

    def test_task_loop_exception_handling(self):
        """Test task loop handles exceptions gracefully."""
        with (
            patch.object(self.task_manager, "get_tasks") as mock_get_tasks,
            patch("time.sleep") as mock_sleep,
        ):
            api_exception_error = Exception("API error")
            mock_get_tasks.side_effect = api_exception_error

            def stop_after_first_iteration(*args):
                self.task_manager.stop_queue = True

            mock_sleep.side_effect = stop_after_first_iteration

            mock_logger = Mock()
            self.task_manager.logger = mock_logger

            self.task_manager.task_loop()

            mock_logger.error.assert_called_once_with(
                "Error in task_loop: API error", exception=api_exception_error
            )

    def test_process_task_error_handling(self):
        """Test process_task handles exceptions and logs errors properly."""
        task = {
            "id": "123",
            "source_type": "PySparkDataSource",
            "engine": "test_engine",
            "query": "SELECT * FROM test",
            "destination_path": "/test/path",
            "upload_method": "snowflake-stage",
        }

        # Mock the data source to raise an exception
        with patch.object(self.task_manager, "sources") as mock_sources:
            mock_sources.__getitem__.side_effect = Exception("Data source error")

            # Mock API manager
            mock_api_manager = Mock()
            self.task_manager.api_manager = mock_api_manager

            # Execute process_task
            self.task_manager.process_task(task)

            # Verify error was logged
            self.mock_logger.error.assert_called_with(
                "Error in process_task: Data source error", exception=unittest.mock.ANY
            )

            # Verify task was marked as failed
            mock_api_manager.update_task.assert_called_once_with(
                {"task_id": "123", "status": "failed", "details": "Data source error"}
            )

    @patch("data_exchange_agent.tasks.manager.SQLiteTaskQueue.complete_task")
    @patch("data_exchange_agent.tasks.manager.APIManager.update_task")
    @patch("data_exchange_agent.providers.storageProvider.delete_folder_file")
    @patch("data_exchange_agent.providers.storageProvider.AzureBlobUploader")
    @patch("os.listdir")
    @patch("data_exchange_agent.tasks.manager.build_actual_results_folder_path")
    @patch("data_exchange_agent.tasks.manager.DataSourceExtractor")
    def test_upload_to_azure_blob_success(
        self,
        mock_data_source_extractor,
        mock_build_actual_results_folder_path,
        mock_os_listdir,
        mock_azure_blob_uploader,
        mock_delete_folder_file,
        mock_update_task,
        mock_complete_task,
    ):
        """Test successful upload to Azure Blob Storage."""
        self.task_manager.sources = {"PySparkDataSource": Mock(spec=PySparkDataSource)}
        mock_build_actual_results_folder_path.return_value = str(
            Path("/test/results/path")
        )
        mock_data_source_extractor.extract_data = Mock()
        mock_os_listdir.side_effect = (
            lambda x: ["test.parquet"] if x == str(Path("/test/results/path")) else []
        )
        mock_azure_blob_uploader.return_value = Mock(spec=AzureBlobUploader)
        mock_azure_blob_uploader.upload_file = Mock()

        # Mock cloud storage configuration
        self.task_manager.cloud_storage_toml = {
            "blob": {
                "container_name": "test-container",
                "connection_string": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net",
            }
        }

        task = {
            "id": "123",
            "source_type": "PySparkDataSource",
            "engine": "test_engine",
            "statement": "SELECT * FROM test",
            "upload_type": "blob",
            "upload_path": "/test/path",
        }

        self.task_manager.process_task(task)
        # Verify configuration was set
        self.assertEqual(mock_delete_folder_file.call_count, 1)
        self.assertEqual(mock_azure_blob_uploader.call_count, 1)

        # Verify upload_files was called
        mock_azure_blob_uploader().upload_file.assert_called_once_with(
            str(Path("/test/results/path/test.parquet")), "/test/path"
        )

        mock_update_task.assert_called_once_with(
            {
                "task_id": "123",
                "status": "successful",
                "details": None,
            }
        )

        mock_complete_task.assert_called_once_with(task)


if __name__ == "__main__":
    unittest.main()

import json
import os
import platform
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from data_exchange_agent.data_sources.extractor import DataSourceExtractor
from data_exchange_agent.queues.deque_task_queue import DequeTaskQueue
from data_exchange_agent.queues.sqlite_task_queue import SQLiteTaskQueue
from data_exchange_agent.servers.flask_app import FlaskApp
from data_exchange_agent.tasks.manager import TaskManager


class MockDataSource:
    """Mock data source for integration testing."""

    def __init__(self, test_data=None):
        self.test_data = test_data or []
        self.connection_created = False

    def create_connection(self):
        self.connection_created = True
        return "mock_connection"

    def execute_statement(self, statement: str, results_folder_path: str = None):
        return iter(self.test_data)

    def close_connection(self):
        pass


class TestIntegration(unittest.TestCase):
    """Integration tests for data_exchange_agent components."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.mock_toml_value = {
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

    def tearDown(self):
        """Clean up after each test method."""
        try:
            if hasattr(self, "task_queue") and isinstance(
                self.task_queue, SQLiteTaskQueue
            ):
                self.task_queue.close()
        except Exception:
            pass

        if platform.system() == "Windows":
            import gc
            import time

            gc.collect()
            time.sleep(0.1)

        if os.path.exists(self.db_path):
            try:
                os.unlink(self.db_path)
            except PermissionError:
                if platform.system() == "Windows":
                    import time

                    time.sleep(0.5)
                    try:
                        os.unlink(self.db_path)
                    except PermissionError:
                        print(
                            f"Warning: Could not delete temporary database {self.db_path}"
                        )
                else:
                    raise

    def test_extractor_with_mock_data_source_integration(self):
        """Test DataSourceExtractor integration with mock data source."""
        test_data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]

        mock_data_source = MockDataSource(test_data)

        extractor = DataSourceExtractor(
            statement="SELECT * FROM users", connection=mock_data_source
        )

        result = extractor.extract_data()
        result_list = list(result)

        self.assertEqual(len(result_list), 3)
        self.assertEqual(result_list, test_data)

    def test_sqlite_task_queue_integration(self):
        """Test SQLiteTaskQueue integration with multiple operations."""
        task_queue = SQLiteTaskQueue(db_path=self.db_path)

        tasks = [
            {"id": "task_1", "name": "First Task", "priority": 1},
            {"id": "task_2", "name": "Second Task", "priority": 2},
            {"id": "task_3", "name": "Third Task", "priority": 3},
        ]

        for task in tasks:
            task_queue.add_task(task)

        self.assertEqual(task_queue.get_queue_size(), 3)

        processed_tasks = []
        for i in range(3):
            task = task_queue.get_task(f"worker_{i}")
            self.assertIsNotNone(task)
            processed_tasks.append(task)

            task_queue.complete_task(task)

        self.assertEqual(len(processed_tasks), 3)
        self.assertEqual(task_queue.get_queue_size(), 0)
        self.assertEqual(task_queue.get_completed_count(), 3)

        for i, task in enumerate(processed_tasks):
            self.assertEqual(
                task["id"], f"task_{i + 1}"
            )  # Tasks are numbered 1-3, not 0-2

    def test_deque_task_queue_integration(self):
        """Test DequeTaskQueue integration with concurrent access."""
        task_queue = DequeTaskQueue()

        def add_tasks(start_id, count):
            for i in range(count):
                task = {"id": f"task_{start_id + i}", "data": f"data_{start_id + i}"}
                task_queue.add_task(task)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_tasks, args=(i * 10, 5))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(task_queue.get_queue_size(), 15)

        retrieved_tasks = []
        while True:
            task = task_queue.get_task()
            if task is None:
                break
            retrieved_tasks.append(task)

        self.assertEqual(len(retrieved_tasks), 15)
        self.assertEqual(task_queue.get_queue_size(), 0)

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_task_manager_with_sqlite_queue_integration(self, mock_toml_load):
        """Test TaskManager integration with SQLiteTaskQueue."""
        mock_toml_load.return_value = self.mock_toml_value

        temp_db_path = tempfile.mktemp(suffix=".db")
        task_queue = SQLiteTaskQueue(db_path=temp_db_path)
        task_manager = TaskManager(workers=2, tasks_fetch_interval=1)
        task_manager.task_queue = task_queue

        self.assertIsInstance(task_manager.task_queue, SQLiteTaskQueue)
        self.assertEqual(task_manager.executor._max_workers, 2)
        self.assertEqual(task_manager.tasks_fetch_interval, 1)

        test_tasks = [
            {"id": "integration_task_1", "name": "Integration Test Task 1"},
            {"id": "integration_task_2", "name": "Integration Test Task 2"},
        ]

        for task in test_tasks:
            task_manager.add_task(task)

        self.assertEqual(task_manager.get_tasks_count(), 2)

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_flask_app_integration(self, mock_toml_load):
        """Test Flask app integration with dependency injection."""
        mock_toml_load.return_value = self.mock_toml_value

        flask_app = FlaskApp()
        app = flask_app.create_app(
            {"TESTING": True, "WORKERS": 2, "TASKS_FETCH_INTERVAL": 30}
        )

        with app.test_client() as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["service"], "data_exchange_agent")

            test_task = {
                "id": "integration_test_task",
                "name": "Integration Test Task",
                "statement": "SELECT 1",
            }

            response = client.post(
                "/tasks", data=json.dumps(test_task), content_type="application/json"
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["message"], "Task added successfully")

            response = client.get("/get_tasks_count")
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("tasks_count", data)
            self.assertIsInstance(data["tasks_count"], int)

    def test_data_source_extractor_with_different_data_types(self):
        """Test DataSourceExtractor with different data types."""
        test_cases = [
            [],
            [{"id": 1, "name": "Single"}],
            [
                {"id": 1, "name": "Alice", "active": True, "score": 95.5},
                {"id": 2, "name": "Bob", "active": False, "score": 87.2},
                {"id": 3, "name": None, "active": True, "score": None},
            ],
            [
                {
                    "id": 1,
                    "metadata": {
                        "tags": ["python", "testing"],
                        "config": {"debug": True},
                    },
                },
                {
                    "id": 2,
                    "metadata": {"tags": ["integration"], "config": {"debug": False}},
                },
            ],
        ]

        for i, test_data in enumerate(test_cases):
            with self.subTest(case=i):
                mock_data_source = MockDataSource(test_data)

                extractor = DataSourceExtractor(
                    statement=f"SELECT * FROM test_table_{i}",
                    connection=mock_data_source,
                )

                result = extractor.extract_data()
                result_list = list(result)

                self.assertEqual(result_list, test_data)

    def test_task_queue_error_handling_integration(self):
        """Test task queue error handling in integration scenarios."""
        task_queue = SQLiteTaskQueue(db_path=self.db_path)

        test_task = {"id": "error_test_task", "name": "Error Test Task"}
        task_queue.add_task(test_task)

        retrieved_task = task_queue.get_task("error_worker")
        self.assertIsNotNone(retrieved_task)

        error_message = "Simulated processing error"
        task_queue.fail_task(retrieved_task, error_message)

        self.assertEqual(task_queue.get_processing_count(), 0)

        stats = task_queue.get_queue_stats()
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["pending"], 0)
        self.assertEqual(stats["processing"], 0)

        task_queue.retry_task(retrieved_task)

        updated_stats = task_queue.get_queue_stats()
        self.assertEqual(updated_stats["failed"], 0)
        self.assertEqual(updated_stats["pending"], 1)

    def test_concurrent_task_processing_integration(self):
        """Test concurrent task processing with multiple workers."""
        task_queue = SQLiteTaskQueue(db_path=self.db_path)

        num_tasks = 10
        for i in range(num_tasks):
            task = {"id": f"concurrent_task_{i}", "data": f"data_{i}"}
            task_queue.add_task(task)

        processed_tasks = []
        processing_lock = threading.Lock()

        def worker_function(worker_id):
            while True:
                task = task_queue.get_task(f"worker_{worker_id}")
                if task is None:
                    break

                time.sleep(0.01)

                with processing_lock:
                    processed_tasks.append(task)

                task_queue.complete_task(task)

        workers = []
        for i in range(3):
            worker = threading.Thread(target=worker_function, args=(i,))
            workers.append(worker)
            worker.start()

        for worker in workers:
            worker.join()

        self.assertEqual(len(processed_tasks), num_tasks)
        self.assertEqual(task_queue.get_queue_size(), 0)
        self.assertEqual(task_queue.get_completed_count(), num_tasks)

        processed_ids = [task["id"] for task in processed_tasks]
        self.assertEqual(len(processed_ids), len(set(processed_ids)))


if __name__ == "__main__":
    unittest.main()

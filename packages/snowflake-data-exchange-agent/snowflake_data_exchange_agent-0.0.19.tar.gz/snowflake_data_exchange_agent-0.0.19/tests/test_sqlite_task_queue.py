import json
import os
import platform
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from data_exchange_agent.queues.sqlite_task_queue import SQLiteTaskQueue


class TestSQLiteTaskQueue(unittest.TestCase):
    """Comprehensive test suite for the SQLiteTaskQueue class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.task_queue = SQLiteTaskQueue(db_path=self.db_path)

    def tearDown(self):
        """Clean up after each test method."""
        self.task_queue.close()

        import platform

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

    def test_initialization(self):
        """Test SQLiteTaskQueue initialization."""
        self.assertEqual(self.task_queue.db_path, self.db_path)
        self.assertTrue(os.path.exists(self.db_path))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        )
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='task_status'"
        )
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_initialization_with_default_path(self):
        """Test initialization with default database path."""
        with patch(
            "data_exchange_agent.queues.sqlite_task_queue.DB_TASKS_FILE_PATH",
            os.path.join(tempfile.gettempdir(), "test_tasks.db"),
        ):
            with patch("os.makedirs") as mock_makedirs:
                SQLiteTaskQueue()
                mock_makedirs.assert_called_once()

    def test_add_task_new(self):
        """Test adding a new task to the queue."""
        test_task = {
            "id": "123",
            "name": "test_task",
            "statement": "SELECT * FROM test",
        }

        self.task_queue.add_task(test_task)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT task_id, task_data, status FROM tasks WHERE task_id = ?", ("123",)
        )
        row = cursor.fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "123")
        self.assertEqual(json.loads(row[1]), test_task)
        self.assertEqual(row[2], "pending")

        conn.close()

    def test_add_task_duplicate(self):
        """Test adding a duplicate task (should update existing)."""
        test_task = {
            "id": "123",
            "name": "test_task",
            "statement": "SELECT * FROM test",
        }

        self.task_queue.add_task(test_task)

        updated_task = {
            "id": "123",
            "name": "updated_task",
            "statement": "SELECT * FROM updated_test",
        }
        self.task_queue.add_task(updated_task)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT task_data, status FROM tasks WHERE task_id = ?", ("123",)
        )
        row = cursor.fetchone()

        self.assertEqual(json.loads(row[0]), updated_task)
        self.assertEqual(row[1], "pending")

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_id = ?", ("123",))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

        conn.close()

    def test_get_task_success(self):
        """Test successfully getting a task from the queue."""
        test_task = {
            "id": "123",
            "name": "test_task",
            "statement": "SELECT * FROM test",
        }

        self.task_queue.add_task(test_task)

        result = self.task_queue.get_task("worker_123")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "123")
        self.assertEqual(result["name"], "test_task")
        self.assertIn("_db_id", result)
        self.assertIn("_worker_id", result)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, worker_thread FROM tasks WHERE task_id = ?", ("123",)
        )
        row = cursor.fetchone()

        self.assertEqual(row[0], "processing")
        self.assertEqual(row[1], "worker_123")

        conn.close()

    def test_get_task_empty_queue(self):
        """Test getting task from empty queue."""
        result = self.task_queue.get_task("worker_123")
        self.assertIsNone(result)

    def test_get_task_fifo_order(self):
        """Test that tasks are retrieved in FIFO order."""
        for i in range(3):
            task = {"id": str(i), "name": f"task_{i}"}
            self.task_queue.add_task(task)

        task1 = self.task_queue.get_task("worker_1")
        task2 = self.task_queue.get_task("worker_2")
        task3 = self.task_queue.get_task("worker_3")

        self.assertEqual(task1["id"], "0")
        self.assertEqual(task2["id"], "1")
        self.assertEqual(task3["id"], "2")

    def test_complete_task(self):
        """Test marking a task as completed."""
        test_task = {"id": "123", "name": "test_task"}

        self.task_queue.add_task(test_task)
        retrieved_task = self.task_queue.get_task("worker_123")

        self.task_queue.complete_task(retrieved_task)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, completed_at FROM tasks WHERE task_id = ?", ("123",)
        )
        row = cursor.fetchone()

        self.assertEqual(row[0], "completed")
        self.assertIsNotNone(row[1])  # completed_at should be set

        conn.close()

    def test_fail_task(self):
        """Test marking a task as failed."""
        test_task = {"id": "123", "name": "test_task"}
        error_message = "Task failed due to network error"

        self.task_queue.add_task(test_task)
        retrieved_task = self.task_queue.get_task("worker_123")

        self.task_queue.fail_task(retrieved_task, error_message)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, error_message, completed_at FROM tasks WHERE task_id = ?",
            ("123",),
        )
        row = cursor.fetchone()

        self.assertEqual(row[0], "failed")
        self.assertEqual(row[1], error_message)
        self.assertIsNotNone(row[2])  # completed_at should be set

        conn.close()

    def test_retry_task(self):
        """Test moving a failed task back to pending."""
        test_task = {"id": "123", "name": "test_task"}

        self.task_queue.add_task(test_task)
        retrieved_task = self.task_queue.get_task("worker_123")
        self.task_queue.fail_task(retrieved_task, "Test error")

        self.task_queue.retry_task(retrieved_task)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT status, worker_pid, worker_thread, started_at, completed_at, error_message
            FROM tasks WHERE task_id = ?
        """,
            ("123",),
        )
        row = cursor.fetchone()

        self.assertEqual(row[0], "pending")
        self.assertIsNone(row[1])  # worker_pid
        self.assertIsNone(row[2])  # worker_thread
        self.assertIsNone(row[3])  # started_at
        self.assertIsNone(row[4])  # completed_at
        self.assertIsNone(row[5])  # error_message

        conn.close()

    def test_get_queue_size(self):
        """Test getting the number of pending tasks."""
        self.assertEqual(self.task_queue.get_queue_size(), 0)

        for i in range(3):
            self.task_queue.add_task({"id": str(i), "name": f"task_{i}"})

        self.assertEqual(self.task_queue.get_queue_size(), 3)

        self.task_queue.get_task("worker_1")
        self.assertEqual(self.task_queue.get_queue_size(), 2)

    def test_get_processing_count(self):
        """Test getting the number of processing tasks."""
        self.assertEqual(self.task_queue.get_processing_count(), 0)

        for i in range(3):
            self.task_queue.add_task({"id": str(i), "name": f"task_{i}"})

        self.task_queue.get_task("worker_1")
        self.task_queue.get_task("worker_2")

        self.assertEqual(self.task_queue.get_processing_count(), 2)

    def test_get_completed_count(self):
        """Test getting the number of completed tasks."""
        self.assertEqual(self.task_queue.get_completed_count(), 0)

        for i in range(2):
            task = {"id": str(i), "name": f"task_{i}"}
            self.task_queue.add_task(task)
            retrieved_task = self.task_queue.get_task(f"worker_{i}")
            self.task_queue.complete_task(retrieved_task)

        self.assertEqual(self.task_queue.get_completed_count(), 2)

    def test_get_queue_stats(self):
        """Test getting comprehensive queue statistics."""
        for i in range(5):
            task = {"id": str(i), "name": f"task_{i}"}
            self.task_queue.add_task(task)

        task1 = self.task_queue.get_task("worker_1")
        task2 = self.task_queue.get_task("worker_2")

        self.task_queue.complete_task(task1)

        self.task_queue.fail_task(task2, "Test error")

        stats = self.task_queue.get_queue_stats()

        expected_stats = {
            "pending": 3,
            "processing": 0,
            "completed": 1,
            "failed": 1,
            "total": 5,
        }

        self.assertEqual(stats, expected_stats)

    def test_cleanup_stale_tasks(self):
        """Test cleaning up stale processing tasks."""
        task = {"id": "123", "name": "stale_task"}
        self.task_queue.add_task(task)
        self.task_queue.get_task("worker_123")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET started_at = datetime('now', '-400 seconds')
            WHERE task_id = ?
        """,
            ("123",),
        )
        conn.commit()
        conn.close()

        cleaned_count = self.task_queue.cleanup_stale_tasks(300)

        self.assertEqual(cleaned_count, 1)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM tasks WHERE task_id = ?", ("123",))
        status = cursor.fetchone()[0]
        self.assertEqual(status, "pending")
        conn.close()

    def test_clear_completed_tasks(self):
        """Test clearing old completed tasks."""
        task = {"id": "123", "name": "old_task"}
        self.task_queue.add_task(task)
        retrieved_task = self.task_queue.get_task("worker_123")
        self.task_queue.complete_task(retrieved_task)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET completed_at = datetime('now', '-25 hours')
            WHERE task_id = ?
        """,
            ("123",),
        )
        conn.commit()
        conn.close()

        deleted_count = self.task_queue.clear_completed_tasks(24)

        self.assertEqual(deleted_count, 1)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_id = ?", ("123",))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
        conn.close()

    def test_thread_safety(self):
        """Test thread safety of queue operations."""
        for i in range(10):
            self.task_queue.add_task({"id": str(i), "name": f"task_{i}"})

        results = []

        def worker_thread(worker_id):
            task = self.task_queue.get_task(f"worker_{worker_id}")
            if task:
                results.append(task["id"])

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(results), len(set(results)))
        self.assertEqual(len(results), 5)  # 5 threads should get 5 different tasks

    def test_database_connection_per_thread(self):
        """Test that each thread gets its own database connection."""
        connections_by_thread = {}
        connection_lock = threading.Lock()

        def get_connection():
            thread_id = threading.get_ident()
            conn = self.task_queue._get_connection()
            with connection_lock:
                connections_by_thread[thread_id] = id(conn)
            time.sleep(0.01)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=get_connection)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        unique_connections = set(connections_by_thread.values())
        self.assertEqual(
            len(unique_connections),
            3,
            f"Expected 3 different connections, but got {len(unique_connections)}: {connections_by_thread}",
        )


if __name__ == "__main__":
    unittest.main()

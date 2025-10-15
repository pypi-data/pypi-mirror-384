import threading
import time
import unittest
from unittest.mock import patch

from data_exchange_agent.queues.deque_task_queue import DequeTaskQueue


class TestDequeTaskQueue(unittest.TestCase):
    """Comprehensive test suite for the DequeTaskQueue class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.task_queue = DequeTaskQueue()

    def test_initialization(self):
        """Test DequeTaskQueue initialization."""
        self.assertIsNotNone(self.task_queue.task_queue)
        self.assertIsNotNone(self.task_queue.task_deque_lock)
        self.assertTrue(hasattr(self.task_queue.task_deque_lock, "acquire"))
        self.assertTrue(hasattr(self.task_queue.task_deque_lock, "release"))
        self.assertEqual(len(self.task_queue.task_queue), 0)

    def test_add_task(self):
        """Test adding a task to the queue."""
        test_task = {"id": "123", "name": "test_task"}

        self.task_queue.add_task(test_task)

        self.assertEqual(len(self.task_queue.task_queue), 1)
        self.assertEqual(self.task_queue.task_queue[0], test_task)

    def test_add_multiple_tasks(self):
        """Test adding multiple tasks to the queue."""
        tasks = [
            {"id": "1", "name": "task1"},
            {"id": "2", "name": "task2"},
            {"id": "3", "name": "task3"},
        ]

        for task in tasks:
            self.task_queue.add_task(task)

        self.assertEqual(len(self.task_queue.task_queue), 3)

        for i, task in enumerate(tasks):
            self.assertEqual(self.task_queue.task_queue[i], task)

    def test_get_task_success(self):
        """Test successfully getting a task from the queue."""
        test_task = {"id": "123", "name": "test_task"}

        self.task_queue.add_task(test_task)

        result = self.task_queue.get_task()

        self.assertEqual(result, test_task)

        self.assertEqual(len(self.task_queue.task_queue), 0)

    def test_get_task_empty_queue(self):
        """Test getting task from empty queue."""
        result = self.task_queue.get_task()
        self.assertIsNone(result)

    def test_get_task_fifo_order(self):
        """Test that tasks are retrieved in FIFO order."""
        tasks = [
            {"id": "1", "name": "first"},
            {"id": "2", "name": "second"},
            {"id": "3", "name": "third"},
        ]

        for task in tasks:
            self.task_queue.add_task(task)

        for expected_task in tasks:
            result = self.task_queue.get_task()
            self.assertEqual(result, expected_task)

        self.assertEqual(len(self.task_queue.task_queue), 0)
        self.assertIsNone(self.task_queue.get_task())

    def test_get_queue_size(self):
        """Test getting the current size of the queue."""
        self.assertEqual(self.task_queue.get_queue_size(), 0)

        for i in range(5):
            self.task_queue.add_task({"id": str(i), "name": f"task_{i}"})

        self.assertEqual(self.task_queue.get_queue_size(), 5)

        self.task_queue.get_task()
        self.assertEqual(self.task_queue.get_queue_size(), 4)

        while self.task_queue.get_task():
            pass

        self.assertEqual(self.task_queue.get_queue_size(), 0)

    def test_complete_task_not_implemented(self):
        """Test that complete_task method exists but doesn't do anything."""
        test_task = {"id": "123", "name": "test_task"}

        self.task_queue.complete_task(test_task)

        self.assertTrue(hasattr(self.task_queue, "complete_task"))
        self.assertTrue(callable(getattr(self.task_queue, "complete_task")))

    def test_fail_task_not_implemented(self):
        """Test that fail_task method exists but doesn't do anything."""
        test_task = {"id": "123", "name": "test_task"}
        error_message = "Test error"

        self.task_queue.fail_task(test_task, error_message)

        self.assertTrue(hasattr(self.task_queue, "fail_task"))
        self.assertTrue(callable(getattr(self.task_queue, "fail_task")))

    def test_retry_task_not_implemented(self):
        """Test that retry_task method exists but doesn't do anything."""
        test_task = {"id": "123", "name": "test_task"}

        self.task_queue.retry_task(test_task)

        self.assertTrue(hasattr(self.task_queue, "retry_task"))
        self.assertTrue(callable(getattr(self.task_queue, "retry_task")))

    def test_cleanup_stale_tasks_not_implemented(self):
        """Test that cleanup_stale_tasks method exists but doesn't do anything."""
        result = self.task_queue.cleanup_stale_tasks(300)

        self.assertTrue(hasattr(self.task_queue, "cleanup_stale_tasks"))
        self.assertTrue(callable(getattr(self.task_queue, "cleanup_stale_tasks")))
        self.assertIsNone(result)

    def test_clear_completed_tasks_not_implemented(self):
        """Test that clear_completed_tasks method exists but doesn't do anything."""
        result = self.task_queue.clear_completed_tasks(24)

        self.assertTrue(hasattr(self.task_queue, "clear_completed_tasks"))
        self.assertTrue(callable(getattr(self.task_queue, "clear_completed_tasks")))
        self.assertIsNone(result)

    def test_get_processing_count_not_implemented(self):
        """Test that get_processing_count method exists but doesn't do anything."""
        result = self.task_queue.get_processing_count()

        self.assertTrue(hasattr(self.task_queue, "get_processing_count"))
        self.assertTrue(callable(getattr(self.task_queue, "get_processing_count")))
        self.assertIsNone(result)

    def test_get_completed_count_not_implemented(self):
        """Test that get_completed_count method exists but doesn't do anything."""
        result = self.task_queue.get_completed_count()

        self.assertTrue(hasattr(self.task_queue, "get_completed_count"))
        self.assertTrue(callable(getattr(self.task_queue, "get_completed_count")))
        self.assertIsNone(result)

    def test_get_queue_stats_not_implemented(self):
        """Test that get_queue_stats method exists but doesn't do anything."""
        result = self.task_queue.get_queue_stats()

        self.assertTrue(hasattr(self.task_queue, "get_queue_stats"))
        self.assertTrue(callable(getattr(self.task_queue, "get_queue_stats")))
        self.assertIsNone(result)

    def test_thread_safety(self):
        """Test thread safety of queue operations."""
        for i in range(20):
            self.task_queue.add_task({"id": str(i), "name": f"task_{i}"})

        results = []

        def worker_thread():
            while True:
                task = self.task_queue.get_task()
                if task is None:
                    break
                results.append(task["id"])
                time.sleep(0.001)  # Small delay to increase chance of race conditions

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(results), 20)
        self.assertEqual(len(set(results)), 20)  # No duplicates

        self.assertEqual(self.task_queue.get_queue_size(), 0)

    def test_concurrent_add_and_get(self):
        """Test concurrent adding and getting of tasks."""
        results = []

        def producer():
            for i in range(10):
                self.task_queue.add_task({"id": f"producer_{i}", "name": f"task_{i}"})
                time.sleep(0.001)

        def consumer():
            while len(results) < 10:
                task = self.task_queue.get_task()
                if task:
                    results.append(task["id"])
                time.sleep(0.001)

        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()

        self.assertEqual(len(results), 10)
        self.assertEqual(len(set(results)), 10)  # No duplicates

    def test_lock_usage(self):
        """Test that the lock is properly used for thread safety."""
        with patch.object(self.task_queue, "task_deque_lock") as mock_lock:
            self.task_queue.add_task({"id": "test"})
            mock_lock.__enter__.assert_called()
            mock_lock.__exit__.assert_called()

            mock_lock.__enter__.reset_mock()
            mock_lock.__exit__.reset_mock()

            self.task_queue.get_task()
            mock_lock.__enter__.assert_called()
            mock_lock.__exit__.assert_called()

            mock_lock.__enter__.reset_mock()
            mock_lock.__exit__.reset_mock()

            self.task_queue.get_queue_size()
            mock_lock.__enter__.assert_called()
            mock_lock.__exit__.assert_called()


if __name__ == "__main__":
    unittest.main()

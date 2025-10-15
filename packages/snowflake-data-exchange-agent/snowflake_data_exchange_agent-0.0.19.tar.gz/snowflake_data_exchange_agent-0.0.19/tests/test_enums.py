"""
Tests for enum modules.

This module tests all the enum classes defined in the enums package
to ensure they maintain their expected values and behavior.
"""

import unittest
from enum import Enum

from data_exchange_agent.enums.task_status import TaskStatus


class TestTaskStatus(unittest.TestCase):
    """Test TaskStatus enum."""

    def test_task_status_is_enum(self):
        """Test that TaskStatus is an Enum class."""
        self.assertTrue(issubclass(TaskStatus, Enum))

    def test_pending_status(self):
        """Test PENDING status value."""
        self.assertEqual(TaskStatus.PENDING.value, "pending")
        self.assertEqual(str(TaskStatus.PENDING), "TaskStatus.PENDING")

    def test_processing_status(self):
        """Test PROCESSING status value."""
        self.assertEqual(TaskStatus.PROCESSING.value, "processing")
        self.assertEqual(str(TaskStatus.PROCESSING), "TaskStatus.PROCESSING")

    def test_successful_status(self):
        """Test SUCCESSFUL status value."""
        self.assertEqual(TaskStatus.SUCCESSFUL.value, "successful")
        self.assertEqual(str(TaskStatus.SUCCESSFUL), "TaskStatus.SUCCESSFUL")

    def test_failed_status(self):
        """Test FAILED status value."""
        self.assertEqual(TaskStatus.FAILED.value, "failed")
        self.assertEqual(str(TaskStatus.FAILED), "TaskStatus.FAILED")

    def test_completed_status(self):
        """Test COMPLETED status value."""
        self.assertEqual(TaskStatus.COMPLETED.value, "completed")
        self.assertEqual(str(TaskStatus.COMPLETED), "TaskStatus.COMPLETED")

    def test_all_status_values_are_strings(self):
        """Test that all status values are strings."""
        for status in TaskStatus:
            self.assertIsInstance(status.value, str)
            self.assertTrue(len(status.value) > 0)

    def test_status_values_uniqueness(self):
        """Test that all status values are unique."""
        values = [status.value for status in TaskStatus]
        unique_values = set(values)
        self.assertEqual(len(values), len(unique_values))

    def test_status_count(self):
        """Test that we have the expected number of statuses."""
        self.assertEqual(len(TaskStatus), 5)

    def test_status_membership(self):
        """Test status membership using 'in' operator."""
        self.assertIn(TaskStatus.PENDING, TaskStatus)
        self.assertIn(TaskStatus.PROCESSING, TaskStatus)
        self.assertIn(TaskStatus.SUCCESSFUL, TaskStatus)
        self.assertIn(TaskStatus.FAILED, TaskStatus)
        self.assertIn(TaskStatus.COMPLETED, TaskStatus)

    def test_status_comparison(self):
        """Test status comparison."""
        self.assertEqual(TaskStatus.PENDING, TaskStatus.PENDING)
        self.assertNotEqual(TaskStatus.PENDING, TaskStatus.PROCESSING)

    def test_status_from_value(self):
        """Test creating status from value."""
        self.assertEqual(TaskStatus("pending"), TaskStatus.PENDING)
        self.assertEqual(TaskStatus("processing"), TaskStatus.PROCESSING)
        self.assertEqual(TaskStatus("successful"), TaskStatus.SUCCESSFUL)
        self.assertEqual(TaskStatus("failed"), TaskStatus.FAILED)
        self.assertEqual(TaskStatus("completed"), TaskStatus.COMPLETED)

    def test_invalid_status_value(self):
        """Test that invalid status values raise ValueError."""
        with self.assertRaises(ValueError):
            TaskStatus("invalid_status")

    def test_status_iteration(self):
        """Test iterating over TaskStatus enum."""
        expected_values = ["pending", "processing", "successful", "failed", "completed"]
        actual_values = [status.value for status in TaskStatus]
        self.assertEqual(actual_values, expected_values)


if __name__ == "__main__":
    unittest.main()

"""
Tests for constants modules.

This module tests all the constant values defined in the constants package
to ensure they maintain their expected values and types.
"""

import unittest

from data_exchange_agent.constants.container import SF_LOGGER
from data_exchange_agent.constants.manager import MAX_WORKERS, TASKS_FETCH_INTERVAL
from data_exchange_agent.constants.task import (
    DETAILS,
    ENGINE,
    ID,
    SOURCE_TYPE,
    STATEMENT,
    STATUS,
    TOTAL,
    UPLOAD_PATH,
    UPLOAD_TYPE,
)


class TestContainerConstants(unittest.TestCase):
    """Test container-related constants."""

    def test_sf_logger_constant(self):
        """Test SF_LOGGER constant value and type."""
        self.assertEqual(SF_LOGGER, "sf_logger")
        self.assertIsInstance(SF_LOGGER, str)


class TestManagerConstants(unittest.TestCase):
    """Test task manager configuration constants."""

    def test_max_workers_constant(self):
        """Test MAX_WORKERS constant value and type."""
        self.assertEqual(MAX_WORKERS, 4)
        self.assertIsInstance(MAX_WORKERS, int)
        self.assertGreater(MAX_WORKERS, 0)

    def test_tasks_fetch_interval_constant(self):
        """Test TASKS_FETCH_INTERVAL constant value and type."""
        self.assertEqual(TASKS_FETCH_INTERVAL, 120)
        self.assertIsInstance(TASKS_FETCH_INTERVAL, int)
        self.assertGreater(TASKS_FETCH_INTERVAL, 0)


class TestTaskConstants(unittest.TestCase):
    """Test task-related constants."""

    def test_source_type_constant(self):
        """Test SOURCE_TYPE constant value and type."""
        self.assertEqual(SOURCE_TYPE, "source_type")
        self.assertIsInstance(SOURCE_TYPE, str)

    def test_engine_constant(self):
        """Test ENGINE constant value and type."""
        self.assertEqual(ENGINE, "engine")
        self.assertIsInstance(ENGINE, str)

    def test_statement_constant(self):
        """Test STATEMENT constant value and type."""
        self.assertEqual(STATEMENT, "statement")
        self.assertIsInstance(STATEMENT, str)

    def test_upload_path_constant(self):
        """Test UPLOAD_PATH constant value and type."""
        self.assertEqual(UPLOAD_PATH, "upload_path")
        self.assertIsInstance(UPLOAD_PATH, str)

    def test_id_constant(self):
        """Test ID constant value and type."""
        self.assertEqual(ID, "id")
        self.assertIsInstance(ID, str)

    def test_status_constant(self):
        """Test STATUS constant value and type."""
        self.assertEqual(STATUS, "status")
        self.assertIsInstance(STATUS, str)

    def test_details_constant(self):
        """Test DETAILS constant value and type."""
        self.assertEqual(DETAILS, "details")
        self.assertIsInstance(DETAILS, str)

    def test_upload_type_constant(self):
        """Test UPLOAD_TYPE constant value and type."""
        self.assertEqual(UPLOAD_TYPE, "upload_type")
        self.assertIsInstance(UPLOAD_TYPE, str)

    def test_total_constant(self):
        """Test TOTAL constant value and type."""
        self.assertEqual(TOTAL, "total")
        self.assertIsInstance(TOTAL, str)

    def test_all_constants_are_strings(self):
        """Test that all task constants are strings."""
        constants = [
            SOURCE_TYPE,
            ENGINE,
            STATEMENT,
            UPLOAD_PATH,
            ID,
            STATUS,
            DETAILS,
            UPLOAD_TYPE,
            TOTAL,
        ]
        for constant in constants:
            self.assertIsInstance(constant, str)
            self.assertTrue(len(constant) > 0)


if __name__ == "__main__":
    unittest.main()

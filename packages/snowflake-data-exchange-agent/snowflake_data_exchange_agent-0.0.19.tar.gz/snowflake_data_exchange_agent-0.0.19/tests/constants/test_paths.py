import os
import time
import unittest
from unittest.mock import patch

from data_exchange_agent.constants.paths import (
    APP_FOLDER_PATH,
    CONFIGURATION_FILE_PATH,
    DB_TASKS_FILE_PATH,
    ROOT_DBS_FOLDER_PATH,
    ROOT_JARS_FOLDER_PATH,
    ROOT_LOGS_FOLDER_PATH,
    ROOT_RESULTS_FOLDER_PATH,
    _get_home_dir,
    build_actual_results_folder_path,
)


class TestConstantsPaths(unittest.TestCase):
    """Comprehensive test suite for the ConstantsPaths class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def test_get_home_dir(self):
        """Test _get_home_dir function returns correct home directory."""
        with patch("os.path.expanduser") as mock_expanduser:
            import tempfile

            test_home = tempfile.gettempdir()
            mock_expanduser.return_value = test_home

            result = _get_home_dir()

            mock_expanduser.assert_called_once_with("~")
            self.assertEqual(result, test_home)

    def test_get_home_dir_with_real_system(self):
        """Test _get_home_dir function with real system call."""
        result = _get_home_dir()
        expected = os.path.expanduser("~")

        self.assertEqual(result, expected)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_app_folder_path(self):
        """Test APP_FOLDER_PATH constant structure."""
        self.assertIsInstance(APP_FOLDER_PATH, str)
        self.assertTrue(APP_FOLDER_PATH.endswith(".data_exchange_agent"))
        self.assertGreater(len(APP_FOLDER_PATH), len(".data_exchange_agent"))

    def test_path_constants_are_strings(self):
        """Test that all path constants are strings."""
        constants = [
            APP_FOLDER_PATH,
            ROOT_DBS_FOLDER_PATH,
            ROOT_JARS_FOLDER_PATH,
            ROOT_LOGS_FOLDER_PATH,
            ROOT_RESULTS_FOLDER_PATH,
            DB_TASKS_FILE_PATH,
            CONFIGURATION_FILE_PATH,
        ]

        for constant in constants:
            self.assertIsInstance(constant, str)
            self.assertGreater(len(constant), 0)  # Should not be empty

    def test_path_constants_relationships(self):
        """Test that path constants have correct relationships."""
        self.assertTrue(ROOT_DBS_FOLDER_PATH.startswith(APP_FOLDER_PATH))
        self.assertTrue(ROOT_JARS_FOLDER_PATH.startswith(APP_FOLDER_PATH))
        self.assertTrue(ROOT_LOGS_FOLDER_PATH.startswith(APP_FOLDER_PATH))
        self.assertTrue(ROOT_RESULTS_FOLDER_PATH.startswith(APP_FOLDER_PATH))

        self.assertTrue(DB_TASKS_FILE_PATH.startswith(ROOT_DBS_FOLDER_PATH))

    def test_path_constants_structure(self):
        """Test the expected directory structure."""
        self.assertTrue(ROOT_DBS_FOLDER_PATH.endswith("dbs"))
        self.assertTrue(ROOT_JARS_FOLDER_PATH.endswith("jars"))
        self.assertTrue(ROOT_LOGS_FOLDER_PATH.endswith("logs"))
        self.assertTrue(
            ROOT_RESULTS_FOLDER_PATH.endswith(("data_chunks", "result_data"))
        )

        self.assertTrue(DB_TASKS_FILE_PATH.endswith(".db"))
        self.assertTrue(CONFIGURATION_FILE_PATH.endswith(".toml"))

    def test_specific_path_values(self):
        """Test specific expected values for path constants."""
        home_dir = _get_home_dir()
        expected_app_folder = os.path.join(home_dir, ".data_exchange_agent")

        self.assertEqual(APP_FOLDER_PATH, expected_app_folder)
        self.assertEqual(ROOT_DBS_FOLDER_PATH, os.path.join(expected_app_folder, "dbs"))
        self.assertEqual(
            ROOT_JARS_FOLDER_PATH, os.path.join(expected_app_folder, "jars")
        )
        self.assertEqual(
            ROOT_LOGS_FOLDER_PATH, os.path.join(expected_app_folder, "logs")
        )
        self.assertTrue(ROOT_RESULTS_FOLDER_PATH.startswith(expected_app_folder))
        self.assertTrue(
            "data" in ROOT_RESULTS_FOLDER_PATH or "result" in ROOT_RESULTS_FOLDER_PATH
        )
        self.assertEqual(
            DB_TASKS_FILE_PATH,
            os.path.join(ROOT_DBS_FOLDER_PATH, "data_exchange_tasks.db"),
        )
        self.assertEqual(
            CONFIGURATION_FILE_PATH, "src/data_exchange_agent/configuration.toml"
        )

    @patch("time.strftime")
    def test_build_actual_results_folder_path_without_task_id(self, mock_strftime):
        """Test build_actual_results_folder_path without task_id."""
        mock_strftime.return_value = "20240101_120000123456"

        result = build_actual_results_folder_path()

        self.assertTrue(result.startswith(ROOT_RESULTS_FOLDER_PATH))
        self.assertTrue(os.path.isabs(result))
        basename = os.path.basename(result)
        self.assertTrue(any(c.isdigit() for c in basename))

    @patch("time.strftime")
    def test_build_actual_results_folder_path_with_task_id(self, mock_strftime):
        """Test build_actual_results_folder_path with task_id."""
        mock_strftime.return_value = "20240101_120000123456"
        task_id = "test_task_123"

        result = build_actual_results_folder_path(task_id)

        self.assertTrue(result.startswith(ROOT_RESULTS_FOLDER_PATH))
        self.assertIn(task_id, result)
        self.assertTrue(os.path.isabs(result))

    @patch("time.strftime")
    def test_build_actual_results_folder_path_with_empty_task_id(self, mock_strftime):
        """Test build_actual_results_folder_path with empty string task_id."""
        mock_strftime.return_value = "20240101_120000123456"

        result = build_actual_results_folder_path("")

        self.assertTrue(result.startswith(ROOT_RESULTS_FOLDER_PATH))
        self.assertTrue(os.path.isabs(result))

    def test_build_actual_results_folder_path_returns_different_timestamps(self):
        """Test that consecutive calls return different timestamps."""
        result1 = build_actual_results_folder_path()
        time.sleep(0.001)  # Small delay to ensure different microseconds
        result2 = build_actual_results_folder_path()

        self.assertNotEqual(result1, result2)

        self.assertTrue(result1.startswith(ROOT_RESULTS_FOLDER_PATH))
        self.assertTrue(result2.startswith(ROOT_RESULTS_FOLDER_PATH))

    def test_build_actual_results_folder_path_timestamp_format(self):
        """Test that timestamp format is correct in the actual function."""
        result = build_actual_results_folder_path()

        timestamp_part = os.path.basename(result)

        self.assertIsInstance(timestamp_part, str)
        self.assertGreater(len(timestamp_part), 0)

        self.assertRegex(timestamp_part, r"^.+$")  # Just ensure it's not empty

        self.assertTrue(
            any(c.isdigit() for c in timestamp_part),
            f"Timestamp should contain digits: {timestamp_part}",
        )

        self.assertGreaterEqual(
            len(timestamp_part), 8, f"Timestamp too short: {timestamp_part}"
        )

    def test_build_actual_results_folder_path_task_id_types(self):
        """Test build_actual_results_folder_path with different task_id types."""
        result_str = build_actual_results_folder_path("string_task")
        self.assertIn("string_task", result_str)

        result_num = build_actual_results_folder_path("12345")
        self.assertIn("12345", result_num)

        result_special = build_actual_results_folder_path("task-with_special.chars")
        self.assertIn("task-with_special.chars", result_special)

    def test_configuration_file_path_is_relative(self):
        """Test that CONFIGURATION_FILE_PATH is a relative path."""
        self.assertFalse(os.path.isabs(CONFIGURATION_FILE_PATH))
        self.assertTrue(CONFIGURATION_FILE_PATH.startswith("src/"))

    def test_all_other_paths_are_absolute(self):
        """Test that all paths except CONFIGURATION_FILE_PATH are absolute."""
        absolute_paths = [
            APP_FOLDER_PATH,
            ROOT_DBS_FOLDER_PATH,
            ROOT_JARS_FOLDER_PATH,
            ROOT_LOGS_FOLDER_PATH,
            ROOT_RESULTS_FOLDER_PATH,
            DB_TASKS_FILE_PATH,
        ]

        for path in absolute_paths:
            self.assertTrue(os.path.isabs(path), f"Path {path} should be absolute")

    def test_path_consistency_across_imports(self):
        """Test that paths remain consistent across multiple imports."""
        original_values = {
            "APP_FOLDER_PATH": APP_FOLDER_PATH,
            "ROOT_DBS_FOLDER_PATH": ROOT_DBS_FOLDER_PATH,
            "ROOT_JARS_FOLDER_PATH": ROOT_JARS_FOLDER_PATH,
            "ROOT_LOGS_FOLDER_PATH": ROOT_LOGS_FOLDER_PATH,
            "ROOT_RESULTS_FOLDER_PATH": ROOT_RESULTS_FOLDER_PATH,
            "DB_TASKS_FILE_PATH": DB_TASKS_FILE_PATH,
            "CONFIGURATION_FILE_PATH": CONFIGURATION_FILE_PATH,
        }

        from importlib import reload

        import data_exchange_agent.constants.paths as paths_module

        reload(paths_module)

        self.assertEqual(
            paths_module.APP_FOLDER_PATH, original_values["APP_FOLDER_PATH"]
        )
        self.assertEqual(
            paths_module.ROOT_DBS_FOLDER_PATH, original_values["ROOT_DBS_FOLDER_PATH"]
        )
        self.assertEqual(
            paths_module.ROOT_JARS_FOLDER_PATH, original_values["ROOT_JARS_FOLDER_PATH"]
        )
        self.assertEqual(
            paths_module.ROOT_LOGS_FOLDER_PATH, original_values["ROOT_LOGS_FOLDER_PATH"]
        )
        self.assertEqual(
            paths_module.ROOT_RESULTS_FOLDER_PATH,
            original_values["ROOT_RESULTS_FOLDER_PATH"],
        )
        self.assertEqual(
            paths_module.DB_TASKS_FILE_PATH, original_values["DB_TASKS_FILE_PATH"]
        )
        self.assertEqual(
            paths_module.CONFIGURATION_FILE_PATH,
            original_values["CONFIGURATION_FILE_PATH"],
        )


if __name__ == "__main__":
    unittest.main()

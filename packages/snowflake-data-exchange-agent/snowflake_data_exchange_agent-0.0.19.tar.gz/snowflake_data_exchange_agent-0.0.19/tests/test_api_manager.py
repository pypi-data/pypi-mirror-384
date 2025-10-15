import unittest
from unittest.mock import Mock, patch

import requests

from data_exchange_agent.api.manager import APIManager


class TestAPIManager(unittest.TestCase):
    """
    Comprehensive test suite for the APIManager class.

    This test class validates the functionality of the APIManager, including:
    - API key loading from TOML configuration files
    - Task retrieval from remote API endpoints
    - Task status updates via API calls
    - Error handling for network failures and invalid responses
    - Proper authentication header management

    The tests use mocking to isolate the APIManager from external dependencies
    and ensure reliable, fast test execution.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.

        Creates a mock APIManager instance with a test API key to avoid
        file system dependencies during testing. This ensures consistent
        test behavior regardless of the presence of configuration files.
        """
        with patch.object(APIManager, "load_api_key"):
            self.api_manager = APIManager()
            self.api_manager.api_key = "test_api_key"

    @patch("data_exchange_agent.api.manager.os.path.exists")
    @patch("data_exchange_agent.api.manager.toml.load")
    def test_load_api_key_success(self, mock_toml_load, mock_exists):
        """
        Test successful API key loading from TOML configuration file.

        Verifies that when a valid TOML configuration file exists with the
        proper structure (api_configuration.key), the APIManager correctly
        loads and stores the API key for subsequent use in API requests.

        Args:
            mock_toml_load: Mock for the toml.load function
            mock_exists: Mock for os.path.exists function
        """
        mock_exists.return_value = True
        mock_toml_load.return_value = {
            "api_configuration": {"key": "test_api_key_from_file"}
        }

        api_manager = APIManager()

        self.assertEqual(api_manager.api_key, "test_api_key_from_file")
        mock_toml_load.assert_called_once()

    @patch("data_exchange_agent.api.manager.os.path.exists")
    def test_load_api_key_file_not_exists(self, mock_exists):
        """Test API key loading when file doesn't exist."""
        mock_exists.return_value = False

        api_manager = APIManager()

        self.assertIsNone(api_manager.api_key)

    @patch("data_exchange_agent.api.manager.os.path.exists")
    @patch("data_exchange_agent.api.manager.toml.load")
    def test_load_api_key_missing_api_configuration(self, mock_toml_load, mock_exists):
        """Test API key loading when api_configuration section is missing."""
        mock_exists.return_value = True
        mock_toml_load.return_value = {"other_section": {"key": "value"}}

        api_manager = APIManager()

        self.assertIsNone(api_manager.api_key)

    @patch("data_exchange_agent.api.manager.os.path.exists")
    @patch("data_exchange_agent.api.manager.toml.load")
    def test_load_api_key_missing_key_field(self, mock_toml_load, mock_exists):
        """Test API key loading when key field is missing."""
        mock_exists.return_value = True
        mock_toml_load.return_value = {"api_configuration": {"other_field": "value"}}

        api_manager = APIManager()

        self.assertIsNone(api_manager.api_key)

    @patch("data_exchange_agent.api.manager.requests.get")
    def test_get_tasks_success(self, mock_get):
        """
        Test successful task retrieval from the remote API endpoint.

        Validates that the APIManager correctly:
        - Makes GET requests to the tasks endpoint with proper parameters
        - Includes authentication headers with the API key
        - Returns the JSON response data when the request succeeds
        - Handles the expected response format with task lists

        Args:
            mock_get: Mock for the requests.get function
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tasks": [{"id": 1, "name": "task1"}, {"id": 2, "name": "task2"}]
        }
        mock_get.return_value = mock_response

        result = self.api_manager.get_tasks()

        mock_get.assert_called_once_with(
            "http://127.0.0.1:5000/tasks?agent_id=1&group_id=1",
            headers={"Authorization": "Bearer test_api_key"},
        )

        expected_result = {
            "tasks": [{"id": 1, "name": "task1"}, {"id": 2, "name": "task2"}]
        }
        self.assertEqual(result, expected_result)

    @patch("data_exchange_agent.api.manager.requests.get")
    def test_get_tasks_failure(self, mock_get):
        """Test task retrieval failure from API."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.api_manager.get_tasks()

        self.assertEqual(str(context.exception), "Failed to get tasks: 404")

    @patch("data_exchange_agent.api.manager.requests.put")
    def test_update_task_success(self, mock_put):
        """Test successful task update."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Task updated successfully"}
        mock_put.return_value = mock_response

        update_data = {
            "task_id": "123",
            "status": "completed",
            "details": "Task completed successfully",
        }

        result = self.api_manager.update_task(update_data)

        mock_put.assert_called_once_with(
            "http://127.0.0.1:5000/tasks/123",
            json={"status": "completed", "details": "Task completed successfully"},
        )

        self.assertEqual(result, {"message": "Task updated successfully"})

    @patch("data_exchange_agent.api.manager.requests.put")
    def test_update_task_failure(self, mock_put):
        """Test task update failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_put.return_value = mock_response

        update_data = {"task_id": "123", "status": "failed", "details": "Task failed"}

        result = self.api_manager.update_task(update_data)

        self.assertEqual(result, {"message": "Failed to update task: 500"})

    @patch("data_exchange_agent.api.manager.requests.get")
    def test_get_tasks_with_network_error(self, mock_get):
        """Test get_tasks with network error."""
        mock_get.side_effect = requests.RequestException("Network error")

        with self.assertRaises(requests.RequestException):
            self.api_manager.get_tasks()

    @patch("data_exchange_agent.api.manager.requests.put")
    def test_update_task_with_network_error(self, mock_put):
        """Test update_task with network error."""
        mock_put.side_effect = requests.RequestException("Network error")

        update_data = {"task_id": "123", "status": "failed", "details": "Task failed"}

        with self.assertRaises(requests.RequestException):
            self.api_manager.update_task(update_data)

    def test_api_manager_initialization(self):
        """Test APIManager initialization."""
        with patch.object(APIManager, "load_api_key") as mock_load:
            api_manager = APIManager()

            mock_load.assert_called_once()

            self.assertTrue(hasattr(api_manager, "api_key"))


if __name__ == "__main__":
    unittest.main()

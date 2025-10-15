import unittest

from data_exchange_agent.config import Config


class TestConfig(unittest.TestCase):
    """
    Test suite for the Config class configuration management.

    This test class validates the Config class which provides application-wide
    configuration constants including:
    - Worker thread configuration (WORKERS)
    - Task fetching intervals (TASKS_FETCH_INTERVAL)
    - Debug mode settings (DEBUG)

    Tests ensure that default values are properly set and that all
    configuration attributes have the correct types and values.
    """

    def test_config_default_values(self):
        """
        Test that Config class has correct default values for all settings.

        Validates the default configuration values:
        - WORKERS: 4 (number of worker threads)
        - TASKS_FETCH_INTERVAL: 120 (seconds between task fetches)
        - DEBUG: False (production mode by default)

        These defaults ensure the application runs with sensible settings
        when no custom configuration is provided.
        """
        self.assertEqual(Config.WORKERS, 4)
        self.assertEqual(Config.TASKS_FETCH_INTERVAL, 120)
        self.assertFalse(Config.DEBUG)

    def test_config_attributes_exist(self):
        """
        Test that all expected configuration attributes exist on the Config class.

        Ensures that the Config class has all required attributes defined:
        - WORKERS: For controlling thread pool size
        - TASKS_FETCH_INTERVAL: For controlling API polling frequency
        - DEBUG: For controlling debug mode behavior

        This test prevents runtime AttributeError exceptions when accessing
        configuration values throughout the application.
        """
        self.assertTrue(hasattr(Config, "WORKERS"))
        self.assertTrue(hasattr(Config, "TASKS_FETCH_INTERVAL"))
        self.assertTrue(hasattr(Config, "DEBUG"))

    def test_config_types(self):
        """
        Test that configuration attributes have the correct data types.

        Validates type safety for configuration values:
        - WORKERS: Must be an integer for thread pool sizing
        - TASKS_FETCH_INTERVAL: Must be an integer for time calculations
        - DEBUG: Must be a boolean for conditional logic

        Type validation prevents runtime errors and ensures configuration
        values can be used safely in their intended contexts.
        """
        self.assertIsInstance(Config.WORKERS, int)
        self.assertIsInstance(Config.TASKS_FETCH_INTERVAL, int)
        self.assertIsInstance(Config.DEBUG, bool)


if __name__ == "__main__":
    unittest.main()

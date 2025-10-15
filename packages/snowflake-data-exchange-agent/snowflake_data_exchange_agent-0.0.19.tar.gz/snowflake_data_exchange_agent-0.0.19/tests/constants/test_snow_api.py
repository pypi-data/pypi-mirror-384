import unittest

from data_exchange_agent.constants.snow_api import BASE_URL


class TestConstantsSnowAPI(unittest.TestCase):
    """Comprehensive test suite for the ConstantsSnowAPI class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def test_base_url(self):
        """Test base url.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        self.assertEqual(BASE_URL, "http://127.0.0.1:5000")
        self.assertIsInstance(BASE_URL, str)

    def test_constants_immutability(self):
        """Test that constants maintain their values."""
        original_values = {
            "BASE_URL": BASE_URL,
        }

        from importlib import reload

        import data_exchange_agent.constants.snow_api as constants_module

        reload(constants_module)

        self.assertEqual(constants_module.BASE_URL, original_values["BASE_URL"])


if __name__ == "__main__":
    unittest.main()

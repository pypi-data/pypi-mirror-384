import unittest
from unittest.mock import patch

from dependency_injector import containers, providers

from data_exchange_agent.container import Container
from data_exchange_agent.tasks.manager import TaskManager
from data_exchange_agent.uploaders.azure_blob_uploader import AzureBlobUploader
from data_exchange_agent.utils.sf_logger import SFLogger


class TestContainer(unittest.TestCase):
    """
    Comprehensive test suite for the Container dependency injection class.

    This test class validates the Container's dependency injection functionality,
    including:
    - Provider registration and configuration
    - Singleton pattern implementation for services
    - Service instantiation and dependency wiring
    - Configuration management integration
    - Proper inheritance from DeclarativeContainer

    The tests ensure that the dependency injection container works correctly
    and provides the expected services to the application components.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.

        Creates a fresh Container instance for each test to ensure
        test isolation and prevent side effects between tests.
        """
        self.container = Container()
        self.toml_config = {
            "blob": {
                "container_name": "test-container",
                "connection_string": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net",
            }
        }

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

    def test_container_is_declarative_container(self):
        """
        Test that Container properly inherits from DeclarativeContainer.

        Validates that the Container class follows the dependency-injector
        pattern by inheriting from either DeclarativeContainer or
        DynamicContainer (which can happen after initialization).
        This ensures proper dependency injection functionality.
        """
        self.assertTrue(
            isinstance(self.container, containers.DeclarativeContainer)
            or isinstance(self.container, containers.DynamicContainer)
        )

    def test_container_has_config_provider(self):
        """Test that container has config provider."""
        self.assertTrue(hasattr(self.container, "config"))
        self.assertIsInstance(self.container.config, providers.Configuration)

    def test_container_has_task_manager_provider(self):
        """Test that container has task_manager provider."""
        self.assertTrue(hasattr(self.container, "task_manager"))
        self.assertIsInstance(self.container.task_manager, providers.Singleton)

    def test_container_has_sf_logger_provider(self):
        """Test that container has sf_logger provider."""
        self.assertTrue(hasattr(self.container, "sf_logger"))
        self.assertIsInstance(self.container.sf_logger, providers.Singleton)

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_task_manager_provider_creates_instance(self, mock_toml_load):
        """Test that task_manager provider creates TaskManager instance."""
        mock_toml_load.return_value = self.mock_toml_value

        task_manager = self.container.task_manager()
        self.assertIsInstance(task_manager, TaskManager)

    def test_sf_logger_provider_creates_instance(self):
        """Test that sf_logger provider creates SFLogger instance."""
        sf_logger = self.container.sf_logger()
        self.assertIsInstance(sf_logger, SFLogger)

    def test_task_manager_default_parameters(self):
        """Test that task_manager has correct default parameters."""
        provider = self.container.task_manager
        self.assertEqual(provider.kwargs["workers"], 4)
        self.assertEqual(provider.kwargs["tasks_fetch_interval"], 120)

    def test_container_has_azure_blob_uploader_provider(self):
        """Test that container has azure_blob_uploader provider."""
        self.assertTrue(hasattr(self.container, "azure_blob_uploader"))
        self.assertIsInstance(self.container.azure_blob_uploader, providers.Singleton)

    def test_azure_blob_uploader_provider_creates_instance(self):
        """Test that azure_blob_uploader provider creates AzureBlobUploader instance."""
        azure_blob_uploader = self.container.azure_blob_uploader(
            cloud_storage_toml=self.toml_config
        )
        self.assertIsInstance(azure_blob_uploader, AzureBlobUploader)

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_container_providers_are_singletons(self, mock_toml_load):
        """Test that providers return singleton instances."""
        mock_toml_load.return_value = self.mock_toml_value

        task_manager1 = self.container.task_manager()
        task_manager2 = self.container.task_manager()

        sf_logger1 = self.container.sf_logger()
        sf_logger2 = self.container.sf_logger()

        azure_blob_uploader1 = self.container.azure_blob_uploader(
            cloud_storage_toml=self.toml_config
        )
        azure_blob_uploader2 = self.container.azure_blob_uploader(
            cloud_storage_toml=self.toml_config
        )

        self.assertIs(task_manager1, task_manager2)
        self.assertIs(sf_logger1, sf_logger2)
        self.assertIs(azure_blob_uploader1, azure_blob_uploader2)


if __name__ == "__main__":
    unittest.main()

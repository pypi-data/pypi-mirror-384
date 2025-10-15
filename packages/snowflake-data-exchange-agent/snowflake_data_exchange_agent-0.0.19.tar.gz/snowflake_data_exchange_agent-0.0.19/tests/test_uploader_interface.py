"""
Tests for UploaderInterface class.

This module tests the UploaderInterface abstract base class and its new methods
including initialization, configuration, and context manager functionality.
"""

import unittest
from unittest.mock import Mock, patch

from data_exchange_agent.interfaces.uploader import UploaderInterface


class ConcreteUploader(UploaderInterface):
    """Concrete implementation of UploaderInterface for testing."""

    def __init__(self, cloud_storage_toml=None):
        """Initialize with call tracking."""
        self.configure_called = False
        self.connect_called = False
        self.disconnect_called = False
        super().__init__(cloud_storage_toml)

    def configure(self):
        """Mock configure implementation."""
        self.configure_called = True

    def connect(self):
        """Mock connect implementation."""
        self.connect_called = True

    def disconnect(self):
        """Mock disconnect implementation."""
        self.disconnect_called = True

    def upload_file(self, source_path, destination_path):
        """Mock upload_file implementation."""
        pass


class TestUploaderInterface(unittest.TestCase):
    """Test UploaderInterface abstract base class."""

    def test_init_with_cloud_storage_toml(self):
        """Test initialization with cloud storage configuration."""
        test_config = {
            "bucket": "test-bucket",
            "region": "us-west-2",
            "credentials": {"key": "value"},
        }

        uploader = ConcreteUploader(test_config)

        self.assertEqual(uploader.cloud_storage_toml, test_config)
        self.assertTrue(uploader.configure_called)

    def test_init_with_none_cloud_storage_toml(self):
        """Test initialization with None cloud storage configuration."""
        uploader = ConcreteUploader(None)

        self.assertEqual(uploader.cloud_storage_toml, {})
        self.assertTrue(uploader.configure_called)

    def test_init_without_cloud_storage_toml(self):
        """Test initialization without cloud storage configuration parameter."""
        uploader = ConcreteUploader()

        self.assertEqual(uploader.cloud_storage_toml, {})
        self.assertTrue(uploader.configure_called)

    def test_init_calls_configure(self):
        """Test that initialization calls configure method."""
        uploader = ConcreteUploader({"test": "config"})

        self.assertTrue(uploader.configure_called)

    def test_context_manager_enter(self):
        """Test context manager __enter__ method."""
        uploader = ConcreteUploader()

        result = uploader.__enter__()

        self.assertEqual(result, uploader)
        self.assertTrue(uploader.connect_called)

    def test_context_manager_exit_without_exception(self):
        """Test context manager __exit__ method without exception."""
        uploader = ConcreteUploader()

        uploader.__exit__(None, None, None)

        self.assertTrue(uploader.disconnect_called)

    def test_context_manager_exit_with_exception(self):
        """Test context manager __exit__ method with exception."""
        uploader = ConcreteUploader()

        uploader.__exit__(Exception, Exception("test error"), None)

        self.assertTrue(uploader.disconnect_called)

    def test_context_manager_full_usage(self):
        """Test full context manager usage with 'with' statement."""
        uploader = ConcreteUploader({"test": "config"})

        with uploader as ctx_uploader:
            self.assertEqual(ctx_uploader, uploader)
            self.assertTrue(uploader.connect_called)
            self.assertFalse(uploader.disconnect_called)

        self.assertTrue(uploader.disconnect_called)

    def test_context_manager_with_exception(self):
        """Test context manager handles exceptions properly."""
        uploader = ConcreteUploader()

        try:
            with uploader:
                self.assertTrue(uploader.connect_called)
                raise ValueError("Test exception")
        except ValueError:
            pass

        self.assertTrue(uploader.disconnect_called)

    def test_abstract_methods_exist(self):
        """Test that abstract methods are defined."""
        # These should be abstract methods
        abstract_methods = {"configure", "connect", "disconnect", "upload_file"}

        interface_abstract_methods = set(UploaderInterface.__abstractmethods__)

        self.assertEqual(interface_abstract_methods, abstract_methods)

    def test_cannot_instantiate_abstract_class(self):
        """Test that UploaderInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            UploaderInterface()

    def test_cloud_storage_toml_attribute_assignment(self):
        """Test that cloud_storage_toml attribute is properly assigned."""
        test_config = {
            "nested": {"config": {"value": 123}},
            "list_config": [1, 2, 3],
            "string_config": "test",
        }

        uploader = ConcreteUploader(test_config)

        # Should be the same object reference
        self.assertIs(uploader.cloud_storage_toml, test_config)

        # Modifications should be reflected
        test_config["new_key"] = "new_value"
        self.assertEqual(uploader.cloud_storage_toml["new_key"], "new_value")

    def test_empty_dict_default(self):
        """Test that empty dict is used as default when None is passed."""
        uploader = ConcreteUploader(None)

        # Should be an empty dict, not None
        self.assertEqual(uploader.cloud_storage_toml, {})
        self.assertIsInstance(uploader.cloud_storage_toml, dict)

        # Should be able to add items
        uploader.cloud_storage_toml["test"] = "value"
        self.assertEqual(uploader.cloud_storage_toml["test"], "value")


class TestUploaderInterfaceMethodSignatures(unittest.TestCase):
    """Test UploaderInterface method signatures and contracts."""

    def test_configure_method_signature(self):
        """Test configure method signature."""
        uploader = ConcreteUploader()

        # Should be callable with no arguments
        uploader.configure()

        # Should return None
        result = uploader.configure()
        self.assertIsNone(result)

    def test_connect_method_signature(self):
        """Test connect method signature."""
        uploader = ConcreteUploader()

        # Should be callable with no arguments
        uploader.connect()

        # Should return None
        result = uploader.connect()
        self.assertIsNone(result)

    def test_disconnect_method_signature(self):
        """Test disconnect method signature."""
        uploader = ConcreteUploader()

        # Should be callable with no arguments
        uploader.disconnect()

        # Should return None
        result = uploader.disconnect()
        self.assertIsNone(result)

    def test_upload_file_method_signature(self):
        """Test upload_file method signature."""
        uploader = ConcreteUploader()

        # Should be callable with two string arguments
        result = uploader.upload_file("/source/path", "/dest/path")

        # Should return None (abstract method doesn't specify return type)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

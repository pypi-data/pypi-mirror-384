"""Unit tests for the toml module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from data_exchange_agent import custom_exceptions
from data_exchange_agent.utils.toml import (
    get_connection_and_cloud_storage_toml,
    get_snowflake_connection_name,
    load,
    load_toml_file,
)


class TestLoadTomlFile:
    """Test class for load_toml_file function."""

    @patch("data_exchange_agent.utils.toml.os.path.exists")
    def test_load_nonexistent_file_returns_none(self, mock_exists):
        """Test that loading a non-existent file returns None."""
        mock_exists.return_value = False

        result = load_toml_file("/path/to/nonexistent/file.toml")

        assert result is None
        mock_exists.assert_called_once_with("/path/to/nonexistent/file.toml")

    @patch("data_exchange_agent.utils.toml.toml.load")
    @patch("data_exchange_agent.utils.toml.os.path.exists")
    def test_load_existing_file_returns_dict(self, mock_exists, mock_toml_load):
        """Test that loading an existing file returns parsed TOML content."""
        mock_exists.return_value = True
        expected_content = {
            "database": {"host": "localhost", "port": 5432},
            "app": {"name": "test-app"},
        }
        mock_toml_load.return_value = expected_content

        result = load_toml_file("/path/to/existing/file.toml")

        assert result == expected_content
        mock_exists.assert_called_once_with("/path/to/existing/file.toml")
        mock_toml_load.assert_called_once_with("/path/to/existing/file.toml")

    @patch("data_exchange_agent.utils.toml.toml.load")
    @patch("data_exchange_agent.utils.toml.os.path.exists")
    def test_load_empty_file_returns_empty_dict(self, mock_exists, mock_toml_load):
        """Test that loading an empty TOML file returns empty dict."""
        mock_exists.return_value = True
        mock_toml_load.return_value = {}

        result = load_toml_file("/path/to/empty/file.toml")

        assert result == {}
        mock_toml_load.assert_called_once_with("/path/to/empty/file.toml")

    @patch("data_exchange_agent.utils.toml.toml.load")
    @patch("data_exchange_agent.utils.toml.os.path.exists")
    def test_load_file_with_toml_error_raises_exception(
        self, mock_exists, mock_toml_load
    ):
        """Test that TOML parsing errors are propagated."""
        mock_exists.return_value = True
        mock_toml_load.side_effect = Exception("Invalid TOML syntax")

        with pytest.raises(Exception, match="Invalid TOML syntax"):
            load_toml_file("/path/to/invalid/file.toml")

    @patch("data_exchange_agent.utils.toml.os.path.exists")
    @patch("data_exchange_agent.utils.toml.toml.load")
    def test_load_alias_function(self, mock_toml_load, mock_exists):
        """Test that the load alias function works the same as load_toml_file."""
        mock_exists.return_value = True
        mock_toml_load.return_value = {"test": "data"}

        result = load("/test/path.toml")

        assert result == {"test": "data"}
        mock_exists.assert_called_once_with("/test/path.toml")
        mock_toml_load.assert_called_once_with("/test/path.toml")

    def test_integration_with_real_temp_file(self):
        """Integration test with a real temporary TOML file."""
        toml_content = """
[connection]
host = "localhost"
port = 5432

[app]
name = "test-app"
version = "1.0.0"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as temp_file:
            temp_file.write(toml_content)
            temp_file_path = temp_file.name

        try:
            result = load_toml_file(temp_file_path)

            assert result is not None
            assert result["connection"]["host"] == "localhost"
            assert result["connection"]["port"] == 5432
            assert result["app"]["name"] == "test-app"
            assert result["app"]["version"] == "1.0.0"
        finally:
            Path(temp_file_path).unlink()


class TestGetSnowflakeConnectionName:
    """Test class for get_snowflake_connection_name function."""

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_valid_snowflake_connection_name_returns_name(self, mock_load_toml):
        """Test that valid Snowflake connection config returns the connection name."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {"connection_name": "my_snowflake_connection"}}
        }

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result == "my_snowflake_connection"
        mock_load_toml.assert_called_once_with("/path/to/config.toml")

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_missing_config_file_returns_none(self, mock_load_toml):
        """Test that missing config file returns None."""
        mock_load_toml.return_value = None

        result = get_snowflake_connection_name("/path/to/nonexistent.toml")

        assert result is None

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_missing_connection_section_returns_none(self, mock_load_toml):
        """Test that missing connection section returns None."""
        mock_load_toml.return_value = {"app": {"name": "test-app"}}

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result is None

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_missing_snowflake_section_returns_none(self, mock_load_toml):
        """Test that missing snowflake section returns None."""
        mock_load_toml.return_value = {
            "connection": {"database": {"host": "localhost"}}
        }

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result is None

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_missing_connection_name_returns_none(self, mock_load_toml):
        """Test that missing connection_name field returns None."""
        mock_load_toml.return_value = {
            "connection": {
                "snowflake": {
                    "host": "account.snowflakecomputing.com",
                    "database": "mydb",
                }
            }
        }

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result is None

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_empty_connection_name_returns_empty_string(self, mock_load_toml):
        """Test that empty connection_name returns empty string."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {"connection_name": ""}}
        }

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result == ""

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_snowflake_connection_with_other_configs(self, mock_load_toml):
        """Test Snowflake connection extraction with other configurations present."""
        mock_load_toml.return_value = {
            "connection": {
                "snowflake": {
                    "connection_name": "prod_snowflake",
                    "account": "myaccount",
                    "warehouse": "COMPUTE_WH",
                },
                "postgresql": {"host": "localhost", "port": 5432},
            },
            "cloud_storage": {"aws": {"bucket": "my-bucket"}},
        }

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result == "prod_snowflake"


class TestGetConnectionAndCloudStorageToml:
    """Test class for get_connection_and_cloud_storage_toml function."""

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_valid_config_returns_both_sections(self, mock_load_toml):
        """Test that valid config returns both connection and cloud storage sections."""
        connection_config = {"snowflake": {"connection_name": "my_connection"}}
        cloud_storage_config = {"aws": {"bucket": "my-bucket", "region": "us-west-2"}}
        mock_load_toml.return_value = {
            "connection": connection_config,
            "cloud_storage": cloud_storage_config,
        }

        conn_result, storage_result = get_connection_and_cloud_storage_toml(
            "/path/to/config.toml"
        )

        assert conn_result == connection_config
        assert storage_result == cloud_storage_config
        mock_load_toml.assert_called_once_with("/path/to/config.toml")

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_missing_config_file_raises_configuration_error(self, mock_load_toml):
        """Test that missing config file raises ConfigurationError."""
        mock_load_toml.return_value = None

        with pytest.raises(custom_exceptions.ConfigurationError) as exc_info:
            get_connection_and_cloud_storage_toml("/path/to/nonexistent.toml")

        assert "Failed to load configuration file" in str(exc_info.value)
        assert "/path/to/nonexistent.toml" in str(exc_info.value)
        assert "Please check if the file exists and is a valid TOML file" in str(
            exc_info.value
        )

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_missing_connection_section_raises_configuration_error(
        self, mock_load_toml
    ):
        """Test that missing connection section raises ConfigurationError."""
        mock_load_toml.return_value = {
            "cloud_storage": {"aws": {"bucket": "my-bucket"}}
        }

        with pytest.raises(custom_exceptions.ConfigurationError) as exc_info:
            get_connection_and_cloud_storage_toml("/path/to/config.toml")

        assert "Connection configuration not found" in str(exc_info.value)
        assert "/path/to/config.toml" in str(exc_info.value)

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_missing_cloud_storage_section_raises_configuration_error(
        self, mock_load_toml
    ):
        """Test that missing cloud storage section raises ConfigurationError."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {"connection_name": "my_connection"}}
        }

        with pytest.raises(custom_exceptions.ConfigurationError) as exc_info:
            get_connection_and_cloud_storage_toml("/path/to/config.toml")

        assert "Cloud storage configuration not found" in str(exc_info.value)
        assert "/path/to/config.toml" in str(exc_info.value)

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_empty_connection_section_returns_empty_dict(self, mock_load_toml):
        """Test that empty connection section returns empty dict."""
        mock_load_toml.return_value = {
            "connection": {},
            "cloud_storage": {"aws": {"bucket": "my-bucket"}},
        }

        conn_result, storage_result = get_connection_and_cloud_storage_toml(
            "/path/to/config.toml"
        )

        assert conn_result == {}
        assert storage_result == {"aws": {"bucket": "my-bucket"}}

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_empty_cloud_storage_section_returns_empty_dict(self, mock_load_toml):
        """Test that empty cloud storage section returns empty dict."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {"connection_name": "my_connection"}},
            "cloud_storage": {},
        }

        conn_result, storage_result = get_connection_and_cloud_storage_toml(
            "/path/to/config.toml"
        )

        assert conn_result == {"snowflake": {"connection_name": "my_connection"}}
        assert storage_result == {}

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_complex_config_structure(self, mock_load_toml):
        """Test with complex nested configuration structure."""
        mock_load_toml.return_value = {
            "connection": {
                "snowflake": {
                    "connection_name": "prod_snowflake",
                    "account": "myaccount.us-west-2",
                    "warehouse": "COMPUTE_WH",
                    "database": "MYDB",
                    "schema": "PUBLIC",
                },
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "mydb",
                    "user": "postgres",
                },
            },
            "cloud_storage": {
                "aws": {
                    "bucket": "my-data-bucket",
                    "region": "us-west-2",
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
                "gcp": {"bucket": "my-gcp-bucket", "project_id": "my-project"},
            },
            "app": {"name": "data-exchange-agent", "version": "1.0.0"},
        }

        conn_result, storage_result = get_connection_and_cloud_storage_toml(
            "/path/to/config.toml"
        )

        # Verify connection config
        assert "snowflake" in conn_result
        assert "postgresql" in conn_result
        assert conn_result["snowflake"]["connection_name"] == "prod_snowflake"
        assert conn_result["postgresql"]["host"] == "localhost"

        # Verify cloud storage config
        assert "aws" in storage_result
        assert "gcp" in storage_result
        assert storage_result["aws"]["bucket"] == "my-data-bucket"
        assert storage_result["gcp"]["project_id"] == "my-project"

    def test_integration_with_real_temp_file(self):
        """Integration test with a real temporary TOML file."""
        toml_content = """
[connection]
[connection.snowflake]
connection_name = "test_connection"
account = "myaccount.us-west-2"

[connection.postgresql]
host = "localhost"
port = 5432

[cloud_storage]
[cloud_storage.aws]
bucket = "test-bucket"
region = "us-west-2"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as temp_file:
            temp_file.write(toml_content)
            temp_file_path = temp_file.name

        try:
            conn_result, storage_result = get_connection_and_cloud_storage_toml(
                temp_file_path
            )

            assert conn_result["snowflake"]["connection_name"] == "test_connection"
            assert conn_result["postgresql"]["host"] == "localhost"
            assert storage_result["aws"]["bucket"] == "test-bucket"
        finally:
            Path(temp_file_path).unlink()


class TestDecoratorIntegration:
    """Test class for decorator integration."""

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_log_error_decorator_on_successful_call(self, mock_load_toml):
        """Test that @log_error decorator doesn't interfere with successful calls."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {"connection_name": "test"}},
            "cloud_storage": {"aws": {"bucket": "test"}},
        }

        # This should work normally without any decorator interference
        conn, storage = get_connection_and_cloud_storage_toml("/test/path.toml")

        assert conn == {"snowflake": {"connection_name": "test"}}
        assert storage == {"aws": {"bucket": "test"}}

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_functions_have_log_error_decorator(self, mock_load_toml):
        """Test that functions are properly decorated with @log_error."""
        # Check that the decorator is applied by verifying function attributes
        assert hasattr(load_toml_file, "__wrapped__")
        assert hasattr(get_snowflake_connection_name, "__wrapped__")
        assert hasattr(get_connection_and_cloud_storage_toml, "__wrapped__")


class TestEdgeCases:
    """Test class for edge cases and boundary conditions."""

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_none_values_in_config(self, mock_load_toml):
        """Test handling of None values in configuration."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {"connection_name": None}}
        }

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result is None

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_non_string_connection_name(self, mock_load_toml):
        """Test handling of non-string connection name."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {"connection_name": 12345}}
        }

        result = get_snowflake_connection_name("/path/to/config.toml")

        assert result == 12345  # Should return the actual value

    @patch("data_exchange_agent.utils.toml.load_toml_file")
    def test_nested_empty_structures(self, mock_load_toml):
        """Test with deeply nested empty structures."""
        mock_load_toml.return_value = {
            "connection": {"snowflake": {}},
            "cloud_storage": {"aws": {}},
        }

        conn, storage = get_connection_and_cloud_storage_toml("/path/to/config.toml")

        assert conn == {"snowflake": {}}
        assert storage == {"aws": {}}

    def test_file_path_with_special_characters(self):
        """Test file paths with special characters."""
        special_paths = [
            "/path with spaces/config.toml",
            "/path-with-dashes/config.toml",
            "/path_with_underscores/config.toml",
            "/path/with/unicode/café.toml",
        ]

        for path in special_paths:
            with patch("data_exchange_agent.utils.toml.os.path.exists") as mock_exists:
                mock_exists.return_value = False

                result = load_toml_file(path)

                assert result is None
                mock_exists.assert_called_once_with(path)

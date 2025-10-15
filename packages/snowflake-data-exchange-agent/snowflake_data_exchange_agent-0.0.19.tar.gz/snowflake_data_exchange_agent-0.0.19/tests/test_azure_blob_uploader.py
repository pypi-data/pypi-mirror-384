import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from data_exchange_agent.uploaders.azure_blob_uploader import AzureBlobUploader


@pytest.mark.unit
class TestAzureBlobUploader(unittest.TestCase):
    """
    Comprehensive test suite for the AzureBlobUploader class.

    This test class validates the AzureBlobUploader's functionality, including:
    - Initialization with various authentication methods
    - Connection establishment using different credential types
    - File upload operations to Azure Blob Storage
    - Error handling for missing files and invalid configurations
    - Proper cleanup and disconnection procedures

    Tests use extensive mocking to isolate the uploader from external
    Azure dependencies, ensuring reliable and fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.toml_config = {
            "blob": {
                "container_name": "test-container",
                "connection_string": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net",
            }
        }
        self.uploader = AzureBlobUploader(cloud_storage_toml=self.toml_config)

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        with self.assertRaises(Exception) as context:
            uploader = AzureBlobUploader()
        self.assertEqual(len(context.exception.args), 1)
        self.assertEqual(
            context.exception.args[0],
            "Cloud storage configuration not found. Check if configuration TOML file exists and if Azure Blob Storage profile name was added.",
        )

    def test_init_with_connection_string(self):
        """Test initialization with connection string."""
        connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net"

        self.assertEqual(self.uploader.container_name, "test-container")
        self.assertEqual(self.uploader.connection_string, connection_string)

    def test_init_with_account_name_and_key(self):
        """Test initialization with account name and key."""
        toml_config = {
            "blob": {
                "container_name": "test-container",
                "account_name": "testaccount",
                "account_key": "testkey",
            }
        }
        uploader = AzureBlobUploader(cloud_storage_toml=toml_config)

        self.assertEqual(uploader.container_name, "test-container")
        self.assertEqual(uploader.account_name, "testaccount")
        self.assertEqual(uploader.account_key, "testkey")

    def test_init_with_account_name_and_sas_token(self):
        """Test initialization with account name and SAS token."""
        toml_config = {
            "blob": {
                "container_name": "test-container",
                "account_name": "testaccount",
                "sas_token": "?sv=2020-08-04&ss=bfqt&srt=sco&sp=rwdlacupx&se=2021-01-01T00:00:00Z&st=2020-01-01T00:00:00Z&spr=https&sig=test",
            }
        }
        uploader = AzureBlobUploader(cloud_storage_toml=toml_config)

        self.assertEqual(uploader.container_name, "test-container")
        self.assertEqual(uploader.account_name, "testaccount")
        self.assertEqual(
            uploader.sas_token,
            "?sv=2020-08-04&ss=bfqt&srt=sco&sp=rwdlacupx&se=2021-01-01T00:00:00Z&st=2020-01-01T00:00:00Z&spr=https&sig=test",
        )

    def test_init_with_default_credential(self):
        """Test initialization with default Azure credential."""
        config = {
            "blob": {
                "container_name": "test-container",
                "account_name": "testaccount",
                "use_default_credential": True,
            }
        }
        uploader = AzureBlobUploader(cloud_storage_toml=config)

        self.assertEqual(uploader.container_name, "test-container")
        self.assertEqual(uploader.account_name, "testaccount")
        self.assertTrue(uploader.use_default_credential)

    @patch("data_exchange_agent.uploaders.azure_blob_uploader.BlobServiceClient")
    def test_connect_with_connection_string(self, mock_blob_service_client):
        """Test connection using connection string."""

        mock_client = Mock()
        mock_blob_service_client.from_connection_string.return_value = mock_client

        self.uploader.connect()

        mock_blob_service_client.from_connection_string.assert_called_once_with(
            self.uploader.connection_string
        )
        self.assertEqual(self.uploader.blob_service_client, mock_client)

    @patch("data_exchange_agent.uploaders.azure_blob_uploader.BlobServiceClient")
    def test_connect_with_account_name_and_key(self, mock_blob_service_client):
        """Test connection using account name and key."""
        toml_config = {
            "blob": {
                "container_name": "test-container",
                "account_name": "testaccount",
                "account_key": "testkey",
            }
        }
        uploader = AzureBlobUploader(cloud_storage_toml=toml_config)

        mock_client = Mock()
        mock_blob_service_client.return_value = mock_client

        uploader.connect()

        expected_url = "https://testaccount.blob.core.windows.net"
        mock_blob_service_client.assert_called_once_with(
            account_url=expected_url, credential="testkey"
        )
        self.assertEqual(uploader.blob_service_client, mock_client)

    @patch("data_exchange_agent.uploaders.azure_blob_uploader.BlobServiceClient")
    def test_connect_with_account_name_and_sas_token(self, mock_blob_service_client):
        """Test connection using account name and SAS token."""
        sas_token = "?sv=2020-08-04&ss=bfqt&srt=sco&sp=rwdlacupx&se=2021-01-01T00:00:00Z&st=2020-01-01T00:00:00Z&spr=https&sig=test"
        config = {
            "blob": {
                "container_name": "test-container",
                "account_name": "testaccount",
                "sas_token": sas_token,
            }
        }
        uploader = AzureBlobUploader(cloud_storage_toml=config)

        mock_client = Mock()
        mock_blob_service_client.return_value = mock_client

        uploader.connect()

        expected_url = "https://testaccount.blob.core.windows.net"
        mock_blob_service_client.assert_called_once_with(
            account_url=expected_url, credential=sas_token
        )
        self.assertEqual(uploader.blob_service_client, mock_client)

    @patch("data_exchange_agent.uploaders.azure_blob_uploader.DefaultAzureCredential")
    @patch("data_exchange_agent.uploaders.azure_blob_uploader.BlobServiceClient")
    def test_connect_with_default_credential(
        self, mock_blob_service_client, mock_default_credential
    ):
        """Test connection using default Azure credential."""
        config = {
            "blob": {
                "container_name": "test-container",
                "account_name": "testaccount",
                "use_default_credential": True,
            }
        }
        uploader = AzureBlobUploader(cloud_storage_toml=config)

        mock_client = Mock()
        mock_credential = Mock()
        mock_blob_service_client.return_value = mock_client
        mock_default_credential.return_value = mock_credential

        uploader.connect()

        expected_url = "https://testaccount.blob.core.windows.net"
        mock_default_credential.assert_called_once()
        mock_blob_service_client.assert_called_once_with(
            account_url=expected_url, credential=mock_credential
        )
        self.assertEqual(uploader.blob_service_client, mock_client)

    def test_connect_with_invalid_configuration(self):
        """Test connection with invalid configuration raises ValueError."""
        uploader = AzureBlobUploader(cloud_storage_toml=self.toml_config)
        uploader.blob_service_client = None
        uploader.connection_string = None
        uploader.account_name = None
        uploader.account_url = None
        uploader.account_key = None
        uploader.sas_token = None
        uploader.use_default_credential = None

        with self.assertRaises(ValueError) as context:
            uploader.connect()

        self.assertIn("Must provide either connection_string", str(context.exception))

    def test_connect_already_connected(self):
        """Test that connect() returns early if already connected."""
        mock_client = Mock()
        self.uploader.blob_service_client = mock_client

        # Should not raise any exceptions and should not create new client
        self.uploader.connect()

        self.assertEqual(self.uploader.blob_service_client, mock_client)

    def test_disconnect_when_connected(self):
        """Test disconnection when client exists."""
        mock_client = Mock()
        self.uploader.blob_service_client = mock_client

        self.uploader.disconnect()

        mock_client.close.assert_called_once()
        self.assertIsNone(self.uploader.blob_service_client)

    def test_disconnect_when_not_connected(self):
        """Test disconnection when no client exists."""
        # Should not raise any exceptions
        self.uploader.disconnect()

        self.assertIsNone(self.uploader.blob_service_client)

    @patch("builtins.open", new_callable=mock_open, read_data=b"test file content")
    @patch("data_exchange_agent.uploaders.azure_blob_uploader.Path")
    def test_upload_file_success(self, mock_path, mock_file):
        """Test successful file upload."""
        mock_client = Mock()
        mock_blob_client = Mock()
        self.uploader.blob_service_client = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        # Execute
        self.uploader.upload_file("/path/to/test.parquet", "destination/path")

        # Verify
        mock_path.assert_called_with("/path/to/test.parquet")
        mock_path_instance.exists.assert_called_once()
        mock_client.get_blob_client.assert_called_once_with(
            container="test-container", blob="destination/path/test.parquet"
        )
        mock_blob_client.upload_blob.assert_called_once_with(
            mock_file.return_value, overwrite=True
        )

    @patch("data_exchange_agent.uploaders.azure_blob_uploader.Path")
    def test_upload_file_not_found(self, mock_path):
        """Test upload with non-existent file raises exception."""
        # Mock Path.exists() to return False
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        with self.assertRaises(Exception) as context:
            self.uploader.upload_file(
                "/path/to/nonexistent.parquet", "destination/path"
            )

        self.assertIn(
            "File not found: /path/to/nonexistent.parquet", str(context.exception)
        )

    @patch("builtins.open", new_callable=mock_open, read_data=b"test file content")
    @patch("data_exchange_agent.uploaders.azure_blob_uploader.Path")
    @patch("data_exchange_agent.uploaders.azure_blob_uploader.BlobServiceClient")
    def test_upload_file_auto_connect(
        self, mock_blob_service_client, mock_path, mock_file
    ):
        """Test that upload_file automatically connects if not connected."""
        mock_client = Mock()
        mock_blob_client = Mock()
        mock_blob_service_client.from_connection_string.return_value = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        # Execute
        self.uploader.upload_file("/path/to/test.parquet", "destination/path")

        # Verify connection was established
        mock_blob_service_client.from_connection_string.assert_called_once_with(
            self.toml_config["blob"]["connection_string"]
        )
        self.assertEqual(self.uploader.blob_service_client, mock_client)

    @patch("builtins.open", new_callable=mock_open, read_data=b"test file content")
    @patch("data_exchange_agent.uploaders.azure_blob_uploader.Path")
    def test_upload_file_empty_destination_path(self, mock_path, mock_file):
        """Test upload with empty destination path."""
        mock_client = Mock()
        mock_blob_client = Mock()
        self.uploader.blob_service_client = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        # Execute with empty destination path
        self.uploader.upload_file("/path/to/test.parquet", "")

        # Verify blob name is just the filename
        mock_client.get_blob_client.assert_called_once_with(
            container="test-container", blob="test.parquet"
        )

    @patch("builtins.open", new_callable=mock_open, read_data=b"test file content")
    @patch("data_exchange_agent.uploaders.azure_blob_uploader.Path")
    def test_upload_file_none_destination_path(self, mock_path, mock_file):
        """Test upload with None destination path."""
        mock_client = Mock()
        mock_blob_client = Mock()
        self.uploader.blob_service_client = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        # Execute with None destination path
        self.uploader.upload_file("/path/to/test.parquet", None)

        # Verify blob name is just the filename
        mock_client.get_blob_client.assert_called_once_with(
            container="test-container", blob="test.parquet"
        )

    @patch("builtins.open", new_callable=mock_open, read_data=b"test file content")
    @patch("data_exchange_agent.uploaders.azure_blob_uploader.Path")
    def test_upload_file_destination_path_with_trailing_slash(
        self, mock_path, mock_file
    ):
        """Test upload with destination path that has trailing slash."""
        mock_client = Mock()
        mock_blob_client = Mock()
        self.uploader.blob_service_client = mock_client
        mock_client.get_blob_client.return_value = mock_blob_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        # Execute with trailing slash
        self.uploader.upload_file("/path/to/test.parquet", "destination/path/")

        # Verify trailing slash is stripped
        mock_client.get_blob_client.assert_called_once_with(
            container="test-container", blob="destination/path/test.parquet"
        )


if __name__ == "__main__":
    unittest.main()

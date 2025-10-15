import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import boto3
import pytest

from data_exchange_agent.uploaders.amazon_s3_uploader import AmazonS3Uploader


@pytest.mark.unit
class TestAmazonS3Uploader(unittest.TestCase):
    """
    Comprehensive test suite for the AmazonS3Uploader class.

    This test class validates the AmazonS3Uploader's functionality, including:
    - Initialization with various authentication methods
    - Connection establishment using AWS profiles
    - File upload operations to Amazon S3
    - Error handling for missing files and invalid configurations
    - Proper cleanup and disconnection procedures

    Tests use extensive mocking to isolate the uploader from external
    AWS dependencies, ensuring reliable and fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.toml_config = {
            "s3": {
                "bucket_name": "test-bucket",
                "profile_name": "test-profile",
            }
        }
        self.uploader = AmazonS3Uploader(cloud_storage_toml=self.toml_config)

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        with self.assertRaises(Exception) as context:
            AmazonS3Uploader()
        self.assertEqual(
            context.exception.args[0],
            "Cloud storage configuration not found. Check if configuration TOML file exits and if Amazon S3 profile name was added.",
        )

    def test_init_with_parameters(self):
        """Test initialization with specific parameters."""

        self.assertEqual(self.uploader.bucket_name, "test-bucket")
        self.assertEqual(self.uploader.profile_name, "test-profile")
        self.assertIsNone(self.uploader.s3_client)

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.boto3")
    def test_connect_success(self, mock_boto3):
        """Test successful connection to S3."""
        mock_session = Mock()
        mock_client = Mock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        self.uploader.connect()

        mock_boto3.Session.assert_called_once_with(profile_name="test-profile")
        mock_session.client.assert_called_once_with("s3")
        self.assertEqual(self.uploader.s3_client, mock_client)

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.boto3")
    def test_connect_with_none_profile(self, mock_boto3):
        """Test connection with None profile name."""
        self.toml_config = {
            "s3": {
                "bucket_name": "test-bucket",
                "profile_name": None,
            }
        }
        uploader = AmazonS3Uploader(cloud_storage_toml=self.toml_config)

        mock_session = Mock()
        mock_client = Mock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        uploader.connect()

        mock_boto3.Session.assert_called_once_with(profile_name=None)
        mock_session.client.assert_called_once_with("s3")
        self.assertEqual(uploader.s3_client, mock_client)

    def test_disconnect_when_connected(self):
        """Test disconnection when client exists."""
        mock_client = Mock()
        self.uploader.s3_client = mock_client

        self.uploader.disconnect()

        mock_client.close.assert_called_once()
        self.assertIsNone(self.uploader.s3_client)

    def test_disconnect_when_not_connected(self):
        """Test disconnection when no client exists."""

        # Should not raise any exceptions
        self.uploader.disconnect()

        self.assertIsNone(self.uploader.s3_client)

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.Path")
    def test_upload_file_success(self, mock_path):
        """Test successful file upload."""
        mock_client = Mock()
        self.uploader.s3_client = mock_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        self.uploader.upload_file("/path/to/test.parquet", "destination/path")

        mock_path.assert_called_with("/path/to/test.parquet")
        mock_path_instance.exists.assert_called_once()
        mock_client.upload_file.assert_called_once_with(
            Filename="/path/to/test.parquet", Bucket="test-bucket", Key="test.parquet"
        )

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.Path")
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

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.boto3")
    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.Path")
    def test_upload_file_auto_connect(self, mock_path, mock_boto3):
        """Test that upload_file automatically connects if not connected."""
        mock_session = Mock()
        mock_client = Mock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        self.uploader.upload_file("/path/to/test.parquet", "destination/path")

        # Verify connection was established
        mock_boto3.Session.assert_called_once_with(profile_name="test-profile")
        mock_session.client.assert_called_once_with("s3")
        self.assertEqual(self.uploader.s3_client, mock_client)

        # Verify upload was called
        mock_client.upload_file.assert_called_once_with(
            Filename="/path/to/test.parquet", Bucket="test-bucket", Key="test.parquet"
        )

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.Path")
    def test_upload_file_different_file_extensions(self, mock_path):
        """Test upload with different file extensions."""
        mock_client = Mock()
        self.uploader.s3_client = mock_client

        test_files = [
            "/path/to/data.parquet",
            "/path/to/data.csv",
            "/path/to/data.json",
            "/path/to/data.txt",
        ]

        for file_path in test_files:
            with self.subTest(file_path=file_path):
                # Mock Path.exists() to return True
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_instance.name = Path(file_path).name
                mock_path.return_value = mock_path_instance

                self.uploader.upload_file(file_path, "destination/path")

                mock_client.upload_file.assert_called_with(
                    Filename=file_path, Bucket="test-bucket", Key=Path(file_path).name
                )

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.Path")
    def test_upload_file_with_spaces_in_path(self, mock_path):
        """Test upload with file path containing spaces."""
        mock_client = Mock()
        self.uploader.s3_client = mock_client

        file_path = "/path/to/file with spaces.parquet"

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "file with spaces.parquet"
        mock_path.return_value = mock_path_instance

        self.uploader.upload_file(file_path, "destination/path")

        mock_client.upload_file.assert_called_once_with(
            Filename=file_path, Bucket="test-bucket", Key="file with spaces.parquet"
        )

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.boto3")
    def test_connect_boto3_exception(self, mock_boto3):
        """Test connection handles boto3 exceptions."""

        mock_boto3.Session.side_effect = Exception("Invalid profile")

        with self.assertRaises(Exception) as context:
            self.uploader.connect()

        self.assertIn("Invalid profile", str(context.exception))

    @patch("data_exchange_agent.uploaders.amazon_s3_uploader.Path")
    def test_upload_file_s3_exception(self, mock_path):
        """Test upload_file handles S3 exceptions."""
        mock_client = Mock()
        self.uploader.s3_client = mock_client

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.parquet"
        mock_path.return_value = mock_path_instance

        # Mock S3 client to raise exception
        mock_client.upload_file.side_effect = Exception("S3 upload failed")

        with self.assertRaises(Exception) as context:
            self.uploader.upload_file("/path/to/test.parquet", "destination/path")

        self.assertIn("S3 upload failed", str(context.exception))

    def test_upload_file_no_bucket_name(self):
        """Test upload_file with no bucket name set."""
        toml_config = {
            "s3": {
                "bucket_name": None,
                "profile_name": "test-profile",
            }
        }
        uploader = AmazonS3Uploader(cloud_storage_toml=toml_config)
        mock_client = Mock()
        uploader.s3_client = mock_client

        with patch(
            "data_exchange_agent.uploaders.amazon_s3_uploader.Path"
        ) as mock_path:
            # Mock Path.exists() to return True
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.name = "test.parquet"
            mock_path.return_value = mock_path_instance

            uploader.upload_file("/path/to/test.parquet", "destination/path")

            # Should still call upload_file with None bucket name
            mock_client.upload_file.assert_called_once_with(
                Filename="/path/to/test.parquet", Bucket=None, Key="test.parquet"
            )


if __name__ == "__main__":
    unittest.main()

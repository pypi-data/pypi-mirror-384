import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from data_exchange_agent.data_sources.sf_connection import SnowflakeDataSource
from data_exchange_agent.uploaders.sf_stage_uploader import SFStageUploader


@pytest.mark.unit
class TestSFStageUploader(unittest.TestCase):
    """
    Comprehensive test suite for the SFStageUploader class.

    This test class validates the SFStageUploader's functionality, including:
    - Connection establishment to Snowflake data sources
    - File upload operations to Snowflake stages
    - Error handling for upload failures and connection issues
    - Proper cleanup and disconnection procedures
    - Integration with dependency injection

    Tests use extensive mocking to isolate the uploader from external
    Snowflake dependencies, ensuring reliable and fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.uploader = SFStageUploader(cloud_storage_toml={})
        self.mock_snowflake_datasource = Mock(spec=SnowflakeDataSource)
        self.uploader.snowflake_datasource = self.mock_snowflake_datasource

    def test_init(self):
        """Test SFStageUploader initialization."""
        self.assertIsInstance(self.uploader, SFStageUploader)

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_connect_with_existing_open_connection(self, mock_provide):
        """Test connect when Snowflake connection already exists and is open."""
        self.mock_snowflake_datasource.is_closed.return_value = False

        self.uploader.connect()

        # Should not call create_connection since connection is already open
        self.mock_snowflake_datasource.create_connection.assert_not_called()
        self.mock_snowflake_datasource.is_closed.assert_called_once()

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_connect_with_closed_connection(self, mock_provide):
        """Test connect when Snowflake connection is closed."""
        self.mock_snowflake_datasource.is_closed.return_value = True

        self.uploader.connect()

        # Should call create_connection since connection is closed
        self.mock_snowflake_datasource.is_closed.assert_called_once()
        self.mock_snowflake_datasource.create_connection.assert_called_once()

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_connect_with_no_existing_connection(self, mock_provide):
        """Test connect when no Snowflake connection exists."""
        # Simulate no existing connection by making the datasource None initially
        self.mock_snowflake_datasource.is_closed.return_value = True

        self.uploader.connect()

        # Should call create_connection
        self.mock_snowflake_datasource.create_connection.assert_called_once()

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_disconnect_with_open_connection(self, mock_provide):
        """Test disconnect when Snowflake connection is open."""
        self.mock_snowflake_datasource.is_closed.return_value = False

        self.uploader.disconnect()

        # Should call close_connection since connection is open
        self.mock_snowflake_datasource.is_closed.assert_called_once()
        self.mock_snowflake_datasource.close_connection.assert_called_once()

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_disconnect_with_closed_connection(self, mock_provide):
        """Test disconnect when Snowflake connection is already closed."""
        self.mock_snowflake_datasource.is_closed.return_value = True

        self.uploader.disconnect()

        # Should not call close_connection since connection is already closed
        self.mock_snowflake_datasource.is_closed.assert_called_once()
        self.mock_snowflake_datasource.close_connection.assert_not_called()

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_upload_file_success(self, mock_provide):
        """Test successful file upload to Snowflake stage."""
        self.mock_snowflake_datasource.is_closed.return_value = False

        # Mock successful upload response
        upload_result = [
            (
                "source",
                "target",
                "source_size",
                "target_size",
                "source_compression",
                "target_compression",
                "UPLOADED",
                "message",
            )
        ]
        self.mock_snowflake_datasource.execute_statement.return_value = iter(
            upload_result
        )

        self.uploader.upload_file(
            "/path/to/test.parquet",
            "@my_stage/destination/",
        )

        # Verify PUT command was executed
        expected_put_command = "PUT file:///path/to/test.parquet @my_stage/destination/"
        self.mock_snowflake_datasource.execute_statement.assert_called_once_with(
            expected_put_command
        )

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_upload_file_not_found(self, mock_provide):
        """Test upload with non-existent file - Snowflake handles file validation."""
        self.mock_snowflake_datasource.is_closed.return_value = False

        # Mock failed upload response (file not found)
        upload_result = [
            (
                "source",
                "target",
                "source_size",
                "target_size",
                "source_compression",
                "target_compression",
                "ERROR",
                "File not found",
            )
        ]
        self.mock_snowflake_datasource.execute_statement.return_value = iter(
            upload_result
        )

        with self.assertRaises(Exception) as context:
            self.uploader.upload_file(
                "/path/to/nonexistent.parquet",
                "@my_stage/destination/",
            )

        self.assertIn(
            "File /path/to/nonexistent.parquet was not uploaded to @my_stage/destination/",
            str(context.exception),
        )

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_upload_file_upload_failed(self, mock_provide):
        """Test upload failure handling."""
        self.mock_snowflake_datasource.is_closed.return_value = False

        # Mock failed upload response (status is not "UPLOADED")
        upload_result = [
            (
                "source",
                "target",
                "source_size",
                "target_size",
                "source_compression",
                "target_compression",
                "FAILED",
                "Upload failed",
            )
        ]
        self.mock_snowflake_datasource.execute_statement.return_value = iter(
            upload_result
        )

        with self.assertRaises(Exception) as context:
            self.uploader.upload_file(
                "/path/to/test.parquet",
                "@my_stage/destination/",
            )

        self.assertIn(
            "File /path/to/test.parquet was not uploaded to @my_stage/destination/",
            str(context.exception),
        )

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_upload_file_no_response(self, mock_provide):
        """Test upload with no response from Snowflake."""
        self.mock_snowflake_datasource.is_closed.return_value = False

        # Mock empty response
        self.mock_snowflake_datasource.execute_statement.return_value = iter([])

        with self.assertRaises(Exception) as context:
            self.uploader.upload_file(
                "/path/to/test.parquet",
                "@my_stage/destination/",
            )

        self.assertIn(
            "File /path/to/test.parquet was not uploaded to @my_stage/destination/",
            str(context.exception),
        )

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_upload_file_auto_connect(self, mock_provide):
        """Test that upload_file automatically connects if connection is closed."""
        uploader = SFStageUploader(cloud_storage_toml={})
        mock_snowflake_datasource = Mock(spec=SnowflakeDataSource)
        uploader.snowflake_datasource = mock_snowflake_datasource
        mock_snowflake_datasource.is_closed.return_value = True

        # Mock successful upload response
        upload_result = [
            (
                "source",
                "target",
                "source_size",
                "target_size",
                "source_compression",
                "target_compression",
                "UPLOADED",
                "message",
            )
        ]
        mock_snowflake_datasource.execute_statement.return_value = iter(upload_result)

        uploader.upload_file(
            "/path/to/test.parquet",
            "@my_stage/destination/",
        )

        # Verify connection was established
        mock_snowflake_datasource.create_connection.assert_called_once()

        # Verify PUT command was executed
        expected_put_command = "PUT file:///path/to/test.parquet @my_stage/destination/"
        mock_snowflake_datasource.execute_statement.assert_called_once_with(
            expected_put_command
        )

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_upload_file_different_stage_formats(self, mock_provide):
        """Test upload with different stage path formats."""
        test_stages = [
            "@my_stage",
            "@my_stage/",
            "@my_stage/folder/",
            "@database.schema.stage/path/",
        ]

        for stage_path in test_stages:
            with self.subTest(stage_path=stage_path):
                mock_snowflake_datasource = Mock(spec=SnowflakeDataSource)
                self.uploader.snowflake_datasource = mock_snowflake_datasource
                self.mock_snowflake_datasource.is_closed.return_value = False

                # Mock successful upload response - create new iterator for each test
                upload_result = [
                    (
                        "source",
                        "target",
                        "source_size",
                        "target_size",
                        "source_compression",
                        "target_compression",
                        "UPLOADED",
                        "message",
                    )
                ]
                mock_snowflake_datasource.execute_statement.return_value = iter(
                    upload_result
                )

                self.uploader.upload_file(
                    "/path/to/test.parquet",
                    stage_path,
                )

                expected_put_command = f"PUT file:///path/to/test.parquet {stage_path}"
                mock_snowflake_datasource.execute_statement.assert_called_once_with(
                    expected_put_command
                )

    @patch("data_exchange_agent.uploaders.sf_stage_uploader.Provide")
    def test_upload_file_snowflake_exception(self, mock_provide):
        """Test upload_file handles Snowflake exceptions."""
        self.mock_snowflake_datasource.is_closed.return_value = False

        # Mock Snowflake to raise exception
        self.mock_snowflake_datasource.execute_statement.side_effect = Exception(
            "Snowflake error"
        )

        with self.assertRaises(Exception) as context:
            self.uploader.upload_file(
                "/path/to/test.parquet",
                "@my_stage/destination/",
            )

        self.assertIn("Snowflake error", str(context.exception))


if __name__ == "__main__":
    unittest.main()

"""Amazon S3 uploader implementation."""

from pathlib import Path

import boto3

from data_exchange_agent.interfaces.uploader import UploaderInterface
from data_exchange_agent.utils.decorators import log_error


class AmazonS3Uploader(UploaderInterface):
    """Uploader class for Amazon S3."""

    @log_error
    def configure(self) -> None:
        """
        Configure the Amazon S3 uploader.

        Validates and extracts required S3 configuration parameters from the provided
        cloud storage TOML dictionary. Sets up the bucket name and profile name needed
        for S3 connections.

        Args:
            None

        Raises:
            Exception: If required S3 configuration parameters are missing from the TOML.
                      This includes checking for:
                      - Overall cloud storage configuration
                      - S3 section in configuration
                      - Bucket name in S3 section
                      - Profile name in S3 section

        """
        self.s3_client = None
        self.bucket_name = None
        self.profile_name = None
        if not self.cloud_storage_toml:
            raise Exception(
                "Cloud storage configuration not found. Check if configuration "
                "TOML file exits and if Amazon S3 profile name was added."
            )
        if "s3" not in self.cloud_storage_toml:
            raise Exception("S3 not found in cloud storage section in the TOML file.")
        if "bucket_name" not in self.cloud_storage_toml["s3"]:
            raise Exception(
                "Bucket name not found in S3 section of cloud storage section in the TOML file."
            )
        if "profile_name" not in self.cloud_storage_toml["s3"]:
            raise Exception(
                "Profile name not found in S3 section of cloud storage section in the TOML file."
            )
        self.bucket_name = self.cloud_storage_toml["s3"]["bucket_name"]
        self.profile_name = self.cloud_storage_toml["s3"]["profile_name"]

    @log_error
    def connect(self) -> None:
        """Connect to Amazon S3."""
        # Create session with profile, then create client from session
        if self.s3_client:
            return
        session = boto3.Session(profile_name=self.profile_name)
        self.s3_client = session.client("s3")

    @log_error
    def disconnect(self) -> None:
        """Disconnect from Amazon S3."""
        if not self.s3_client:
            return
        self.s3_client.close()
        self.s3_client = None

    @log_error
    def upload_file(self, source_path: str, destination_path: str) -> None:
        """Upload a file to Amazon S3."""
        # Validate file exists
        if not Path(source_path).exists():
            raise Exception(f"File not found: {source_path}")

        if not self.s3_client:
            self.connect()

        # Get filename from source path
        file_name = Path(source_path).name

        # Upload file to S3
        self.s3_client.upload_file(
            Filename=source_path, Bucket=self.bucket_name, Key=file_name
        )

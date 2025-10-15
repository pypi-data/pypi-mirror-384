"""
Storage provider module for managing different cloud storage upload methods.

This module provides the StorageProvider class which handles uploading files
to various storage destinations including Snowflake stage, Amazon S3, and Azure Blob Storage.
"""

import os

from data_exchange_agent.interfaces.uploader import UploaderInterface
from data_exchange_agent.uploaders.amazon_s3_uploader import AmazonS3Uploader
from data_exchange_agent.uploaders.azure_blob_uploader import AzureBlobUploader
from data_exchange_agent.uploaders.sf_stage_uploader import SFStageUploader
from data_exchange_agent.utils.file_system import delete_folder_file


class StorageProvider:
    """
    Provider class for managing different storage upload methods.

    Handles uploading files to different storage destinations including Snowflake stage,
    Amazon S3, and Azure Blob Storage.

    Args:
        upload_type (str): The type of storage upload to use ('snowflake-stage', 's3', or 'blob')
        cloud_storage_toml (dict): Configuration dictionary containing storage credentials and settings

    Raises:
        Exception: If the specified upload_type is not supported

    """

    def __init__(self, upload_type: str, cloud_storage_toml: dict):
        """
        Initialize the StorageProvider with the specified upload type and cloud storage configuration.

        Args:
            upload_type (str): The type of storage upload to use ('snowflake-stage', 's3', or 'blob')
            cloud_storage_toml (dict): Configuration dictionary containing storage credentials and settings

        """
        self.upload_methods = {
            "snowflake-stage": SFStageUploader,
            "s3": AmazonS3Uploader,
            "blob": AzureBlobUploader,
        }
        if upload_type not in self.upload_methods:
            raise Exception(f"Upload type {upload_type} not found in upload methods.")
        self.upload_type = upload_type
        self.cloud_storage_toml = cloud_storage_toml

    def upload_files(self, source_folder_path: str, destination_path: str) -> None:
        """
        Upload a folder from the given path to the destination.

        Args:
            source_folder_path (str): Local file path to upload
            destination_path (str): Snowflake stage path to upload to

        """
        if self.upload_type not in self.upload_methods:
            raise Exception(
                f"Upload type {self.upload_type} not found in upload methods."
            )
        for file in os.listdir(source_folder_path):
            if file.endswith(".parquet") or file.endswith(".parquet.crc"):
                uploader_interface: UploaderInterface = self.upload_methods[
                    self.upload_type
                ](self.cloud_storage_toml)
                uploader_interface.upload_file(
                    os.path.join(source_folder_path, file), destination_path
                )

        delete_folder_file(source_folder_path)

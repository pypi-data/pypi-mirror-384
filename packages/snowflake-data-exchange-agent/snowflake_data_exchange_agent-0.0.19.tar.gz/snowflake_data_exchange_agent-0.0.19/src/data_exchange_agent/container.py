"""
Dependency injection container for the data exchange agent.

This module defines the main dependency injection container that manages
application dependencies and their lifecycle using the dependency-injector library.
"""

from dependency_injector import containers, providers

from data_exchange_agent.data_sources.sf_connection import SnowflakeDataSource
from data_exchange_agent.tasks.manager import TaskManager
from data_exchange_agent.uploaders.amazon_s3_uploader import AmazonS3Uploader
from data_exchange_agent.uploaders.azure_blob_uploader import AzureBlobUploader
from data_exchange_agent.uploaders.sf_stage_uploader import SFStageUploader
from data_exchange_agent.utils.sf_logger import SFLogger


class Container(containers.DeclarativeContainer):
    """
    Dependency injection container for the data exchange agent.

    This container manages the application's dependencies and their lifecycle.
    It provides singleton instances of core components like TaskManager and SFLogger.

    Attributes:
        config (providers.Configuration): Application configuration provider
        task_manager (providers.Singleton): Singleton provider for TaskManager instance
        sf_logger (providers.Singleton): Singleton provider for SFLogger instance
        sf_stage_uploader (providers.Singleton): Singleton provider for SFStageUploader instance
        amazon_s3_uploader (providers.Singleton): Singleton provider for AmazonS3Uploader instance
        snowflake_datasource (providers.Singleton): Singleton provider for SnowflakeDataSource instance

    """

    config = providers.Configuration()
    task_manager: TaskManager = providers.Singleton(
        TaskManager, workers=4, tasks_fetch_interval=120
    )
    sf_logger: SFLogger = providers.Singleton(SFLogger)
    sf_stage_uploader: SFStageUploader = providers.Singleton(SFStageUploader)
    amazon_s3_uploader: AmazonS3Uploader = providers.Singleton(AmazonS3Uploader)
    snowflake_datasource: SnowflakeDataSource = providers.Singleton(SnowflakeDataSource)
    azure_blob_uploader: AzureBlobUploader = providers.Singleton(AzureBlobUploader)

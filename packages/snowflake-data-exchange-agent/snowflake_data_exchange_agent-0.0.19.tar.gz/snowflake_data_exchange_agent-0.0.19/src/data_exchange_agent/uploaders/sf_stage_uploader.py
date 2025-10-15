"""Snowflake stage uploader implementation."""

from data_exchange_agent.data_sources.sf_connection import SnowflakeDataSource
from data_exchange_agent.interfaces.uploader import UploaderInterface
from dependency_injector.wiring import Provide, inject


class SFStageUploader(UploaderInterface):
    """
    Uploader class for staging files to Snowflake.

    This class implements the UploaderInterface to handle uploading files
    to a Snowflake stage location.
    """

    @inject
    def configure(
        self,
        snowflake_datasource: SnowflakeDataSource = Provide["snowflake_datasource"],
    ) -> None:
        """
        Configure the Snowflake stage uploader.

        Args:
            snowflake_datasource: Snowflake data source (injected dependency)

        """
        self.snowflake_datasource = snowflake_datasource

    def connect(self) -> None:
        """
        Connect to Snowflake.

        Establishes a fresh connection to Snowflake. Safe to call multiple times
        as it will reuse existing valid connections or create new ones as needed.

        """
        if self.snowflake_datasource and not self.snowflake_datasource.is_closed():
            # Connection exists and is open, no need to reconnect
            return

        self.snowflake_datasource.create_connection()

    def disconnect(self) -> None:
        """
        Disconnect from Snowflake.

        Closes the active Snowflake connection if one exists and is open.
        Sets the connection to None after closing to ensure proper cleanup.

        """
        if self.snowflake_datasource and not self.snowflake_datasource.is_closed():
            self.snowflake_datasource.close_connection()
            self.snowflake_datasource = None

    def upload_file(self, source_path: str, destination_path: str) -> None:
        """
        Upload a file to a Snowflake stage.

        Args:
            source_path (str): Local file path to upload
            destination_path (str): Snowflake stage path to upload to

        Returns:
            None

        """
        self.connect()

        put_command = f"PUT file://{source_path} {destination_path}"

        uploaded_file_status = next(
            iter(self.snowflake_datasource.execute_statement(put_command)), None
        )
        if uploaded_file_status is None or uploaded_file_status[6] != "UPLOADED":
            raise Exception(
                f"File {source_path} was not uploaded to {destination_path}"
            )

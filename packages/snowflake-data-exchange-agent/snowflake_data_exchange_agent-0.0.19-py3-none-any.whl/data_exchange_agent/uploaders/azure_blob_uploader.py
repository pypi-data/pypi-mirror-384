"""Azure Blob Storage uploader implementation."""

from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from data_exchange_agent.interfaces.uploader import UploaderInterface


class AzureBlobUploader(UploaderInterface):
    """
    Uploader class for Azure Blob Storage.

    Connection types are tried in the following priority order:
    1. Connection string
    2. Account name + account key
    3. Account name + SAS token
    4. Azure Active Directory (AAD) authentication using default credentials

    Args:
        container_name (str): The name of the Azure Blob Storage container.
        account_name (str): The Azure storage account name.
        connection_string (str): The Azure storage connection string.
        account_key (str): The Azure storage account key.
        sas_token (str): The Azure storage SAS token.
        use_default_credential (bool): Whether to use DefaultAzureCredential for AAD auth.

    """

    def configure(self) -> None:
        """
        Load Azure Blob Storage configuration from TOML dictionary.

        Validates and extracts required Azure Blob Storage configuration parameters from the provided
        cloud storage TOML dictionary. Sets up the container name and authentication credentials needed
        for blob storage connections.

        The following authentication methods are supported in order of precedence:
        1. Connection string
        2. Account name + account key
        3. Account name + SAS token
        4. Account name + default Azure credential (for AAD auth)

        Args:
            cloud_storage_toml (dict): Dictionary containing cloud storage configuration
                                     settings loaded from a TOML file.

        Raises:
            Exception: If required Azure Blob Storage configuration parameters are missing from the TOML.
                      This includes checking for:
                      - Overall cloud storage configuration
                      - Blob section in configuration
                      - Container name in blob section
                      - Valid authentication credentials

        """
        self.blob_service_client = None
        self.connection_string = None
        self.account_name = None
        self.account_url = None
        self.account_key = None
        self.sas_token = None
        self.use_default_credential = None

        if not self.cloud_storage_toml:
            raise Exception(
                "Cloud storage configuration not found. Check if configuration "
                "TOML file exists and if Azure Blob Storage profile name was added."
            )
        blob_config = self.cloud_storage_toml.get("blob", None)
        if not blob_config:
            raise Exception("Blob not found in cloud storage section in the TOML file.")

        self.container_name = blob_config.get("container_name", None)
        if not self.container_name:
            raise Exception(
                "Container name not found in Blob section of cloud storage section in the TOML file."
            )

        self.connection_string = blob_config.get("connection_string", None)
        if not self.connection_string:
            self.account_name = blob_config.get("account_name", None)
            if self.account_name:
                self.account_url = f"https://{self.account_name}.blob.core.windows.net"
                self.use_default_credential = blob_config.get(
                    "use_default_credential", None
                )
                self.account_key = blob_config.get("account_key", None)
                self.sas_token = blob_config.get("sas_token", None)
                if (
                    not self.use_default_credential
                    and not self.account_key
                    and not self.sas_token
                ):
                    raise Exception(
                        "Use default credential, account key or SAS token not found in Blob section"
                        " of cloud storage section in the TOML file."
                    )
            else:
                raise Exception(
                    "Connection string or account name not found in Blob section"
                    " of cloud storage section in the TOML file."
                )

    def connect(self) -> None:
        """Connect to Azure Blob Storage."""
        if self.blob_service_client:
            return
        if self.connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        elif self.account_name and self.account_key:
            self.blob_service_client = BlobServiceClient(
                account_url=self.account_url, credential=self.account_key
            )
        elif self.account_name and self.sas_token:
            self.blob_service_client = BlobServiceClient(
                account_url=self.account_url, credential=self.sas_token
            )
        elif self.account_name and self.use_default_credential:
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                account_url=self.account_url, credential=credential
            )
        else:
            raise ValueError(
                "Must provide either connection_string, account_name with account_key/sas_token, "
                "or account_name with use_default_credential=True"
            )

    def disconnect(self) -> None:
        """Disconnect from Azure Blob Storage."""
        if not self.blob_service_client:
            return

        self.blob_service_client.close()
        self.blob_service_client = None

    def upload_file(self, source_path: str, destination_path: str) -> None:
        """Upload a file to Azure Blob Storage."""
        # Validate file exists
        if not Path(source_path).exists():
            raise Exception(f"File not found: {source_path}")

        if not self.blob_service_client:
            self.connect()

        # Get filename from source path
        file_name = Path(source_path).name

        # Create blob name (destination_path acts as a prefix)
        blob_name = (
            f"{destination_path.rstrip('/')}/{file_name}"
            if destination_path
            else file_name
        )

        # Get blob client
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )

        # Upload file
        with open(source_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

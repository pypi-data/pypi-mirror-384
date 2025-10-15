"""
JDBC JAR file management utilities.

This module provides the JDBCJar class for managing JDBC driver JAR files,
including downloading, storing, and validating JAR files for different
database engines.
"""

import os

from data_exchange_agent.constants.paths import ROOT_JARS_FOLDER_PATH
from data_exchange_agent.utils.decorators import log_error


class JDBCJar:
    """
    A class to manage JDBC driver JAR files.

    This class handles downloading and managing JDBC driver JAR files for different database types.
    It supports downloading both direct JAR files and ZIP archives containing JAR files.

    The class will:
    - Create a .data_exchange_agent/jars directory in the user's home folder if it doesn't exist
    - Download JAR files from specified URLs if they don't exist locally
    - Handle both direct JAR downloads and ZIP archives containing JARs
    - Extract and organize JAR files from ZIP archives
    - Clean up temporary files and directories after extraction

    Attributes:
        home_dir (str): User's home directory path
        name (str): Name identifier for the JDBC driver (e.g. "postgresql", "sqlserver")
        jar_name (str): Filename of the JAR file (e.g. "postgresql-42.7.7.jar")
        class_name (str): Fully qualified Java class name of the JDBC driver
        url (str): Download URL for the JAR/ZIP file
        download_type (str): Type of download - either 'jar' for direct JAR downloads or 'zip' for ZIP archives

    """

    # Class attribute for home directory
    home_dir = os.path.expanduser("~")

    def __init__(
        self, name: str, jar_name: str, class_name: str, url: str, download_type: str
    ) -> None:
        """
        Initialize a new JDBCJar instance.

        Args:
            name (str): Name identifier for the JDBC driver (e.g. "postgresql", "sqlserver")
            jar_name (str): Filename of the JAR file (e.g. "postgresql-42.7.7.jar")
            class_name (str): Fully qualified Java class name of the JDBC driver
            url (str): Download URL for the JAR/ZIP file
            download_type (str): Type of download - either 'jar' or 'zip'

        """
        self.name: str = name
        self.jar_name: str = jar_name
        self.class_name: str = class_name
        self.url: str = url
        self.download_type: str = download_type
        self.download_jars()

    @log_error
    def download_jars(self) -> None:
        """
        Download and set up JDBC driver JAR files.

        Creates the jars directory if it doesn't exist, then downloads and sets up the JAR file:
        - For direct JAR downloads (download_type='jar'): Downloads the file directly
        - For ZIP archives (download_type='zip'): Downloads, extracts the JAR, moves it to the correct location,
          and cleans up temporary files and directories

        The JAR file is only downloaded if it doesn't already exist in the jars directory.

        Raises:
            URLError: If there is an error downloading the file
            OSError: If there are filesystem errors during directory creation or file operations
            zipfile.BadZipFile: If the downloaded ZIP file is invalid or corrupted

        """
        jars_folder_path: str = ROOT_JARS_FOLDER_PATH

        os.makedirs(jars_folder_path, exist_ok=True)
        jar_path: str = os.path.join(jars_folder_path, self.jar_name)
        if not os.path.exists(jar_path):
            import urllib.request

            if self.download_type == "jar":
                urllib.request.urlretrieve(
                    self.url,
                    jar_path,
                )
            elif self.download_type == "zip":
                urllib.request.urlretrieve(
                    self.url,
                    f"{jar_path}.zip",
                )
                import zipfile

                with zipfile.ZipFile(f"{jar_path}.zip", "r") as zip_ref:
                    zip_ref.extractall(jars_folder_path)

                jar_file_found: bool = False

                # Find and move jar file to jars folder
                for root, _, files in os.walk(jars_folder_path):
                    for file in files:
                        if file == self.jar_name:
                            jar_source: str = os.path.join(root, file)
                            jar_dest: str = os.path.join(jars_folder_path, file)
                            if jar_source != jar_dest:
                                os.rename(jar_source, jar_dest)
                            jar_file_found = True
                            break
                    if jar_file_found:
                        break

                # Remove all extracted subdirectories
                for item in os.listdir(jars_folder_path):
                    item_path: str = os.path.join(jars_folder_path, item)
                    if os.path.isdir(item_path):
                        import shutil

                        shutil.rmtree(item_path)
                os.remove(f"{jar_path}.zip")

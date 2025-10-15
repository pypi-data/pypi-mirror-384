import os
import unittest
from unittest.mock import Mock, patch

from data_exchange_agent.data_sources.jdbc_jar import JDBCJar


class TestJDBCJar(unittest.TestCase):
    """Comprehensive test suite for the JDBCJar class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_jar_params = {
            "name": "postgresql",
            "jar_name": "postgresql-42.7.7.jar",
            "class_name": "org.postgresql.Driver",
            "url": "https://jdbc.postgresql.org/download/postgresql-42.7.7.jar",
            "download_type": "jar",
        }
        self.jars_path = os.path.join(
            os.path.expanduser("~"), ".data_exchange_agent", "jars"
        )

    @patch("data_exchange_agent.data_sources.jdbc_jar.JDBCJar.download_jars")
    def test_initialization(self, mock_download_jars):
        """Test initialization.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        jar = JDBCJar(**self.test_jar_params)

        self.assertEqual(jar.name, "postgresql")
        self.assertEqual(jar.jar_name, "postgresql-42.7.7.jar")
        self.assertEqual(jar.class_name, "org.postgresql.Driver")
        self.assertEqual(
            jar.url, "https://jdbc.postgresql.org/download/postgresql-42.7.7.jar"
        )
        self.assertEqual(jar.download_type, "jar")

        mock_download_jars.assert_called_once()

    @patch("data_exchange_agent.data_sources.jdbc_jar.JDBCJar.download_jars")
    def test_initialization_zip_type(self, mock_download_jars):
        """Test JDBCJar initialization with zip download type."""
        zip_params = self.test_jar_params.copy()
        zip_params["download_type"] = "zip"
        zip_params["url"] = "https://example.com/driver.zip"

        jar = JDBCJar(**zip_params)

        self.assertEqual(jar.download_type, "zip")
        mock_download_jars.assert_called_once()

    def test_home_dir_class_variable(self):
        """Test that home_dir class variable is set correctly."""
        expected_home = os.path.expanduser("~")
        self.assertEqual(JDBCJar.home_dir, expected_home)

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("urllib.request.urlretrieve")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_jar_type_new_file(
        self, mock_urlretrieve, mock_exists, mock_makedirs
    ):
        """Test downloading JAR file when it doesn't exist."""
        mock_exists.return_value = False

        with patch(
            "data_exchange_agent.data_sources.jdbc_jar.JDBCJar.download_jars"
        ) as mock_download:
            JDBCJar(**self.test_jar_params)
            mock_download.assert_called_once()

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("urllib.request.urlretrieve")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_jar_type_existing_file(
        self, mock_urlretrieve, mock_exists, mock_makedirs
    ):
        """Test downloading JAR file when it already exists."""
        mock_exists.return_value = True

        JDBCJar(**self.test_jar_params)

        mock_makedirs.assert_called_once()

        mock_urlretrieve.assert_not_called()

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("urllib.request.urlretrieve")
    @patch("zipfile.ZipFile")
    @patch("os.walk")
    @patch("os.rename")
    @patch("os.listdir")
    @patch("shutil.rmtree")
    @patch("os.remove")
    @patch("os.path.isdir")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_zip_type(
        self,
        mock_isdir,
        mock_remove,
        mock_rmtree,
        mock_listdir,
        mock_rename,
        mock_walk,
        mock_zipfile,
        mock_urlretrieve,
        mock_exists,
        mock_makedirs,
    ):
        """Test downloading ZIP file and extracting JAR."""
        zip_params = self.test_jar_params.copy()
        zip_params["download_type"] = "zip"
        zip_params["url"] = "https://example.com/driver.zip"

        mock_exists.return_value = False

        mock_zip_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        jars_path = os.path.join(JDBCJar.home_dir, ".data_exchange_agent", "jars")
        mock_walk.return_value = [
            (os.path.join(jars_path, "extracted_folder"), [], ["postgresql-42.7.7.jar"])
        ]

        mock_listdir.return_value = ["extracted_folder", "postgresql-42.7.7.jar"]
        mock_isdir.side_effect = lambda path: "extracted_folder" in path

        JDBCJar(**zip_params)

        expected_zip_path = os.path.join(jars_path, "postgresql-42.7.7.jar.zip")
        mock_urlretrieve.assert_called_once_with(
            "https://example.com/driver.zip", expected_zip_path
        )

        mock_zip_instance.extractall.assert_called_once_with(jars_path)

        expected_jar_source = os.path.join(
            jars_path, "extracted_folder", "postgresql-42.7.7.jar"
        )
        expected_jar_dest = os.path.join(jars_path, "postgresql-42.7.7.jar")
        mock_rename.assert_called_once_with(expected_jar_source, expected_jar_dest)

        mock_rmtree.assert_called_once()
        mock_remove.assert_called_once_with(expected_zip_path)

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("urllib.request.urlretrieve")
    @patch("zipfile.ZipFile")
    @patch("os.walk")
    @patch("os.listdir")
    @patch("os.remove")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_zip_type_jar_already_in_place(
        self,
        mock_remove,
        mock_listdir,
        mock_walk,
        mock_zipfile,
        mock_urlretrieve,
        mock_exists,
        mock_makedirs,
    ):
        """Test ZIP extraction when JAR is already in the correct location."""
        zip_params = self.test_jar_params.copy()
        zip_params["download_type"] = "zip"

        mock_exists.return_value = False

        mock_zip_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        jars_path = os.path.join(JDBCJar.home_dir, ".data_exchange_agent", "jars")
        mock_walk.return_value = [(jars_path, [], ["postgresql-42.7.7.jar"])]

        mock_listdir.return_value = ["postgresql-42.7.7.jar"]

        with (
            patch("os.rename") as mock_rename,
            patch("shutil.rmtree"),
            patch("os.path.isdir") as mock_isdir,
        ):
            mock_isdir.return_value = False  # No directories to remove

            JDBCJar(**zip_params)

            mock_rename.assert_not_called()

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("urllib.request.urlretrieve")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_network_error(
        self, mock_urlretrieve, mock_exists, mock_makedirs
    ):
        """Test handling of network errors during download."""
        mock_exists.return_value = False
        mock_urlretrieve.side_effect = Exception("Network error")

        with self.assertRaises(Exception) as context:
            JDBCJar(**self.test_jar_params)

        self.assertEqual(str(context.exception), "Network error")

    @patch("os.makedirs")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_directory_creation_error(self, mock_makedirs):
        """Test handling of directory creation errors."""
        mock_makedirs.side_effect = OSError("Permission denied")

        with self.assertRaises(OSError) as context:
            JDBCJar(**self.test_jar_params)

        self.assertEqual(str(context.exception), "Permission denied")

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("urllib.request.urlretrieve")
    @patch("zipfile.ZipFile")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_zip_extraction_error(
        self, mock_zipfile, mock_urlretrieve, mock_exists, mock_makedirs
    ):
        """Test handling of ZIP extraction errors."""
        zip_params = self.test_jar_params.copy()
        zip_params["download_type"] = "zip"

        mock_exists.return_value = False
        mock_zipfile.side_effect = Exception("Invalid ZIP file")

        with self.assertRaises(Exception) as context:
            JDBCJar(**zip_params)

        self.assertEqual(str(context.exception), "Invalid ZIP file")

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("urllib.request.urlretrieve")
    @patch("zipfile.ZipFile")
    @patch("os.walk")
    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_download_jars_zip_jar_not_found(
        self, mock_walk, mock_zipfile, mock_urlretrieve, mock_exists, mock_makedirs
    ):
        """Test ZIP extraction when expected JAR file is not found."""
        zip_params = self.test_jar_params.copy()
        zip_params["download_type"] = "zip"

        mock_exists.return_value = False

        mock_zip_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        mock_walk.return_value = [("/some/path", [], ["other_file.txt"])]

        with (
            patch("os.listdir") as mock_listdir,
            patch("os.remove") as mock_remove,
        ):
            mock_listdir.return_value = []

            JDBCJar(**zip_params)

            mock_remove.assert_called_once()

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    def test_different_jar_configurations(self):
        """Test creating JDBCJar with different configurations."""
        configurations = [
            {
                "name": "sqlserver",
                "jar_name": "mssql-jdbc-12.10.1.jre11.jar",
                "class_name": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
                "url": "https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.10.1.jre11/mssql-jdbc-12.10.1.jre11.jar",
                "download_type": "jar",
            },
            {
                "name": "teradata",
                "jar_name": "terajdbc-20.00.00.49.jar",
                "class_name": "com.teradata.jdbc.TeraDriver",
                "url": "https://repo1.maven.org/maven2/com/teradata/jdbc/terajdbc/20.00.00.49/terajdbc-20.00.00.49.jar",
                "download_type": "jar",
            },
        ]

        for config in configurations:
            with patch(
                "data_exchange_agent.data_sources.jdbc_jar.JDBCJar.download_jars"
            ):
                jar = JDBCJar(**config)

                self.assertEqual(jar.name, config["name"])
                self.assertEqual(jar.jar_name, config["jar_name"])
                self.assertEqual(jar.class_name, config["class_name"])
                self.assertEqual(jar.url, config["url"])
                self.assertEqual(jar.download_type, config["download_type"])


if __name__ == "__main__":
    unittest.main()

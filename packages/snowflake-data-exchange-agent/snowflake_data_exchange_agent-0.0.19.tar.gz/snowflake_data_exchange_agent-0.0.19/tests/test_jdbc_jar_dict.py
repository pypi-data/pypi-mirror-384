import os
import unittest
from unittest.mock import Mock, patch

from data_exchange_agent.data_sources.jdbc_jar_dict import JDBCJarDict


class TestJDBCJarDict(unittest.TestCase):
    """Comprehensive test suite for the JDBCJarDict class.

    This test class validates the core functionality and ensures proper
    behavior under various conditions including normal operation,
    error scenarios, and edge cases.

    Tests use mocking where appropriate to isolate the component
    under test and ensure reliable, fast test execution.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.jars_path = os.path.join(
            os.path.expanduser("~"), ".data_exchange_agent", "jars"
        )

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_initialization(self, mock_jdbc_jar_class):
        """Test JDBCJarDict initialization."""
        mock_postgresql_jar = Mock()
        mock_sqlserver_jar = Mock()
        mock_teradata_jar = Mock()

        mock_postgresql_jar.name = "postgresql"
        mock_sqlserver_jar.name = "sqlserver"
        mock_teradata_jar.name = "teradata"

        mock_jdbc_jar_class.side_effect = [
            mock_postgresql_jar,
            mock_sqlserver_jar,
            mock_teradata_jar,
        ]

        jar_dict = JDBCJarDict()

        self.assertEqual(mock_jdbc_jar_class.call_count, 3)

        postgresql_call = mock_jdbc_jar_class.call_args_list[0]
        self.assertEqual(postgresql_call[1]["name"], "postgresql")
        self.assertEqual(postgresql_call[1]["jar_name"], "postgresql-42.7.7.jar")
        self.assertEqual(postgresql_call[1]["class_name"], "org.postgresql.Driver")
        self.assertEqual(
            postgresql_call[1]["url"],
            "https://jdbc.postgresql.org/download/postgresql-42.7.7.jar",
        )
        self.assertEqual(postgresql_call[1]["download_type"], "jar")

        sqlserver_call = mock_jdbc_jar_class.call_args_list[1]
        self.assertEqual(sqlserver_call[1]["name"], "sqlserver")
        self.assertEqual(sqlserver_call[1]["jar_name"], "mssql-jdbc-12.10.1.jre11.jar")
        self.assertEqual(
            sqlserver_call[1]["class_name"],
            "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        )
        self.assertTrue(sqlserver_call[1]["url"].startswith("https://repo1.maven.org"))
        self.assertEqual(sqlserver_call[1]["download_type"], "jar")

        teradata_call = mock_jdbc_jar_class.call_args_list[2]
        self.assertEqual(teradata_call[1]["name"], "teradata")
        self.assertEqual(teradata_call[1]["jar_name"], "terajdbc-20.00.00.49.jar")
        self.assertEqual(teradata_call[1]["class_name"], "com.teradata.jdbc.TeraDriver")
        self.assertTrue(teradata_call[1]["url"].startswith("https://repo1.maven.org"))
        self.assertEqual(teradata_call[1]["download_type"], "jar")

        self.assertEqual(len(jar_dict.jars), 3)
        self.assertIn("postgresql", jar_dict.jars)
        self.assertIn("sqlserver", jar_dict.jars)
        self.assertIn("teradata", jar_dict.jars)

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_add_jar(self, mock_jdbc_jar_class):
        """Test adding a jar to the dictionary."""
        mock_jdbc_jar_class.side_effect = [Mock(), Mock(), Mock()]

        jar_dict = JDBCJarDict()

        mock_new_jar = Mock()
        mock_new_jar.name = "oracle"

        jar_dict.add_jar(mock_new_jar)

        self.assertIn("oracle", jar_dict.jars)
        self.assertEqual(jar_dict.jars["oracle"], mock_new_jar)
        self.assertEqual(len(jar_dict.jars), 4)  # 3 initial + 1 added

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_get_jars(self, mock_jdbc_jar_class):
        """Test getting the jars dictionary."""
        mock_jars = [Mock(), Mock(), Mock()]
        for i, mock_jar in enumerate(mock_jars):
            mock_jar.name = f"driver_{i}"

        mock_jdbc_jar_class.side_effect = mock_jars

        jar_dict = JDBCJarDict()
        result = jar_dict.get_jars()

        self.assertEqual(result, jar_dict.jars)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_download_all_jars(self, mock_jdbc_jar_class):
        """Test download all jars.

        Validates the expected behavior and ensures proper functionality
        under the tested conditions.
        """
        mock_postgresql_jar = Mock()
        mock_sqlserver_jar = Mock()
        mock_teradata_jar = Mock()

        mock_jdbc_jar_class.side_effect = [
            mock_postgresql_jar,
            mock_sqlserver_jar,
            mock_teradata_jar,
        ]

        jar_dict = JDBCJarDict()
        jar_dict.download_all_jars()

        mock_postgresql_jar.download_jars.assert_called_once()
        mock_sqlserver_jar.download_jars.assert_called_once()
        mock_teradata_jar.download_jars.assert_called_once()

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_get_all_jar_paths(self, mock_jdbc_jar_class):
        """Test getting all jar paths as comma-separated string."""
        mock_jars = []
        jar_names = [
            "postgresql-42.7.7.jar",
            "mssql-jdbc-12.10.1.jre11.jar",
            "terajdbc-20.00.00.49.jar",
        ]

        for i, jar_name in enumerate(jar_names):
            mock_jar = Mock()
            mock_jar.name = f"driver_{i}"
            mock_jar.jar_name = jar_name
            mock_jars.append(mock_jar)

        mock_jdbc_jar_class.side_effect = mock_jars

        import tempfile

        test_home = tempfile.gettempdir()

        with patch(
            "data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar.home_dir",
            test_home,
        ):
            jar_dict = JDBCJarDict()
            result = jar_dict.get_all_jar_paths()

        self.assertIsInstance(result, str)

        paths = result.split(",")
        self.assertEqual(len(paths), 3)

        for i, path in enumerate(paths):
            expected_path = os.path.join(
                test_home, ".data_exchange_agent", "jars", jar_names[i]
            )
            self.assertTrue(
                path.endswith(
                    os.path.join(".data_exchange_agent", "jars", jar_names[i])
                )
            )

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_get_all_jar_paths_empty_dict(self, mock_jdbc_jar_class):
        """Test getting jar paths when no jars are present."""
        jar_dict = JDBCJarDict()

        jar_dict.jars = {}

        result = jar_dict.get_all_jar_paths()

        self.assertEqual(result, "")

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_get_all_jar_paths_single_jar(self, mock_jdbc_jar_class):
        """Test getting jar paths with single jar."""
        mock_jar = Mock()
        mock_jar.name = "postgresql"
        mock_jar.jar_name = "postgresql-42.7.7.jar"

        mock_jdbc_jar_class.return_value = mock_jar

        import tempfile

        test_home = tempfile.gettempdir()

        with patch(
            "data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar.home_dir",
            test_home,
        ):
            jar_dict = JDBCJarDict()
            jar_dict.jars = {"postgresql": mock_jar}  # Override with single jar

            result = jar_dict.get_all_jar_paths()

        expected_path = os.path.join(
            test_home, ".data_exchange_agent", "jars", "postgresql-42.7.7.jar"
        )
        self.assertTrue(
            result.endswith(
                os.path.join(".data_exchange_agent", "jars", "postgresql-42.7.7.jar")
            )
        )

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_initialize_jars_called_during_init(self, mock_jdbc_jar_class):
        """Test that initialize_jars is called during initialization."""
        mock_jdbc_jar_class.side_effect = [Mock(), Mock(), Mock()]

        with patch.object(JDBCJarDict, "initialize_jars") as mock_init:
            JDBCJarDict()
            mock_init.assert_called_once()

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_jar_configurations_are_correct(self, mock_jdbc_jar_class):
        """Test that jar configurations match expected values."""
        mock_jars = [Mock(), Mock(), Mock()]
        mock_jdbc_jar_class.side_effect = mock_jars

        JDBCJarDict()

        self.assertEqual(mock_jdbc_jar_class.call_count, 3)

        call_args_list = mock_jdbc_jar_class.call_args_list

        postgresql_kwargs = call_args_list[0][1]
        self.assertEqual(postgresql_kwargs["name"], "postgresql")
        self.assertEqual(postgresql_kwargs["jar_name"], "postgresql-42.7.7.jar")
        self.assertEqual(postgresql_kwargs["class_name"], "org.postgresql.Driver")
        self.assertIn("postgresql", postgresql_kwargs["url"])

        sqlserver_kwargs = call_args_list[1][1]
        self.assertEqual(sqlserver_kwargs["name"], "sqlserver")
        self.assertEqual(sqlserver_kwargs["jar_name"], "mssql-jdbc-12.10.1.jre11.jar")
        self.assertEqual(
            sqlserver_kwargs["class_name"],
            "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        )
        self.assertIn("mssql-jdbc", sqlserver_kwargs["url"])

        teradata_kwargs = call_args_list[2][1]
        self.assertEqual(teradata_kwargs["name"], "teradata")
        self.assertEqual(teradata_kwargs["jar_name"], "terajdbc-20.00.00.49.jar")
        self.assertEqual(teradata_kwargs["class_name"], "com.teradata.jdbc.TeraDriver")
        self.assertIn("terajdbc", teradata_kwargs["url"])

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_add_jar_overwrites_existing(self, mock_jdbc_jar_class):
        """Test that adding a jar with existing name overwrites it."""
        mock_initial_jars = [Mock(), Mock(), Mock()]
        for i, jar in enumerate(mock_initial_jars):
            jar.name = f"driver_{i}"

        mock_jdbc_jar_class.side_effect = mock_initial_jars

        jar_dict = JDBCJarDict()
        initial_count = len(jar_dict.jars)

        mock_new_jar = Mock()
        mock_new_jar.name = "driver_0"  # Same as first jar

        jar_dict.add_jar(mock_new_jar)

        self.assertEqual(len(jar_dict.jars), initial_count)
        self.assertEqual(jar_dict.jars["driver_0"], mock_new_jar)

    @patch(
        "data_exchange_agent.constants.paths.ROOT_JARS_FOLDER_PATH",
        os.path.join(os.path.expanduser("~"), ".data_exchange_agent", "jars"),
    )
    @patch("data_exchange_agent.data_sources.jdbc_jar_dict.JDBCJar")
    def test_download_all_jars_with_exception(self, mock_jdbc_jar_class):
        """Test download_all_jars when one jar raises exception."""
        mock_jar1 = Mock()
        mock_jar2 = Mock()
        mock_jar3 = Mock()

        mock_jar2.download_jars.side_effect = Exception("Download failed")

        mock_jdbc_jar_class.side_effect = [mock_jar1, mock_jar2, mock_jar3]

        jar_dict = JDBCJarDict()

        with self.assertRaises(Exception) as context:
            jar_dict.download_all_jars()

        self.assertEqual(str(context.exception), "Download failed")

        mock_jar1.download_jars.assert_called_once()

        mock_jar2.download_jars.assert_called_once()


if __name__ == "__main__":
    unittest.main()

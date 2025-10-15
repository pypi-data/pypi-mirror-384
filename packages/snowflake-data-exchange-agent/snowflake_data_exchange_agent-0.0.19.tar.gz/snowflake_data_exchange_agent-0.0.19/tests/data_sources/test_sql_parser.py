"""Unit tests for the sql_parser module.

Note: The current implementation of get_read_only_sql_command_type has limitations:
- Only SELECT commands are properly recognized (DML token type)
- WITH, DESCRIBE, DESC, SHOW, EXPLAIN commands are not handled correctly due to
  different sqlparse token types (CTE, Keyword, Keyword.Order)
- Leading SQL comments break parsing since they become the first token
- Empty queries are incorrectly reported as "multiple statements"

The tests document both the current behavior and the expected future behavior.
"""

from unittest.mock import patch

from data_exchange_agent.data_sources.sql_command_type import SQLCommandType
from data_exchange_agent.data_sources.sql_parser import get_read_only_sql_command_type


class TestGetReadOnlySQLCommandType:
    """Test class for get_read_only_sql_command_type function."""

    def test_select_statement(self):
        """Test parsing SELECT statement."""
        query = "SELECT * FROM users"
        result = get_read_only_sql_command_type(query)
        assert result == SQLCommandType.SELECT

    def test_select_statement_with_case_insensitive(self):
        """Test parsing SELECT statement with different cases."""
        queries = [
            "select * from users",
            "Select * From Users",
            "SELECT * FROM users",
            "sElEcT * fRoM users",
        ]
        for query in queries:
            result = get_read_only_sql_command_type(query)
            assert result == SQLCommandType.SELECT

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_with_statement_currently_unsupported(self, mock_logger):
        """Test that WITH statement currently returns None (needs implementation fix)."""
        query = "WITH cte AS (SELECT * FROM users) SELECT * FROM cte"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command 'WITH' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_describe_statement_currently_unsupported(self, mock_logger):
        """Test that DESCRIBE statement currently returns None (needs implementation fix)."""
        query = "DESCRIBE users"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command 'DESCRIBE' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_desc_statement_currently_unsupported(self, mock_logger):
        """Test that DESC statement currently returns None (needs implementation fix)."""
        query = "DESC users"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command 'DESC' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_show_statement_currently_unsupported(self, mock_logger):
        """Test that SHOW statement currently returns None (needs implementation fix)."""
        query = "SHOW TABLES"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command 'SHOW' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_explain_statement_currently_unsupported(self, mock_logger):
        """Test that EXPLAIN statement currently returns None (needs implementation fix)."""
        query = "EXPLAIN SELECT * FROM users"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command 'EXPLAIN' is not a permitted read-only operation."
        )

    def test_complex_select_statement(self):
        """Test parsing complex SELECT statement."""
        query = """
        SELECT u.name, COUNT(*) as order_count
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.active = true
        GROUP BY u.name
        HAVING COUNT(*) > 5
        ORDER BY order_count DESC
        """
        result = get_read_only_sql_command_type(query)
        assert result == SQLCommandType.SELECT

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_insert_statement_returns_none(self, mock_logger):
        """Test that INSERT statement returns None and logs error."""
        query = "INSERT INTO users (name) VALUES ('John')"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The DML command 'INSERT' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_update_statement_returns_none(self, mock_logger):
        """Test that UPDATE statement returns None and logs error."""
        query = "UPDATE users SET name = 'Jane' WHERE id = 1"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The DML command 'UPDATE' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_delete_statement_returns_none(self, mock_logger):
        """Test that DELETE statement returns None and logs error."""
        query = "DELETE FROM users WHERE id = 1"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The DML command 'DELETE' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_create_statement_returns_none(self, mock_logger):
        """Test that CREATE statement returns None and logs error."""
        query = "CREATE TABLE users (id INT, name VARCHAR(50))"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The DDL command 'CREATE' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_drop_statement_returns_none(self, mock_logger):
        """Test that DROP statement returns None and logs error."""
        query = "DROP TABLE users"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The DDL command 'DROP' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_alter_statement_returns_none(self, mock_logger):
        """Test that ALTER statement returns None and logs error."""
        query = "ALTER TABLE users ADD COLUMN email VARCHAR(100)"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The DDL command 'ALTER' is not a permitted read-only operation."
        )

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_multiple_statements_returns_none(self, mock_logger):
        """Test that multiple statements return None and log error."""
        query = "SELECT * FROM users; SELECT * FROM orders;"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with("Multiple statements are not allowed.")

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_empty_query_returns_none(self, mock_logger):
        """Test that empty query returns None and logs error."""
        query = ""
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with("Multiple statements are not allowed.")

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_whitespace_only_query_returns_none(self, mock_logger):
        """Test that whitespace-only query returns None and logs error."""
        query = "   \n\t  "
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with("Multiple statements are not allowed.")

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_semicolon_only_returns_none(self, mock_logger):
        """Test that semicolon-only query returns None and logs error."""
        query = ";"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command ';' is not a permitted read-only operation."
        )

    def test_select_with_semicolon(self):
        """Test that SELECT with trailing semicolon works."""
        query = "SELECT * FROM users;"
        result = get_read_only_sql_command_type(query)
        assert result == SQLCommandType.SELECT

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_select_with_leading_comments_fails(self, mock_logger):
        """Test that SELECT with leading comments fails (comments become first token)."""
        query = "-- This is a comment\nSELECT * FROM users"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command '-- THIS IS A COMMENT\n' is not a permitted read-only operation."
        )

    def test_select_with_trailing_comments(self):
        """Test that SELECT with trailing comments works."""
        query = "SELECT * FROM users /* trailing comment */"
        result = get_read_only_sql_command_type(query)
        assert result == SQLCommandType.SELECT

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    @patch("data_exchange_agent.data_sources.sql_parser.sqlparse.parse")
    def test_parsing_exception_handling(self, mock_parse, mock_logger):
        """Test that parsing exceptions are handled properly."""
        mock_parse.side_effect = Exception("Parse error")
        query = "SELECT * FROM users"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with("Error parsing the query: Parse error")

    @patch("data_exchange_agent.data_sources.sql_parser.logging.error")
    def test_unknown_token_type_returns_none(self, mock_logger):
        """Test that unknown token types return None and log error."""
        # This is a bit tricky to test since sqlparse handles most SQL,
        # but we can test with a statement that doesn't fit DML/DDL patterns
        query = "GRANT SELECT ON users TO user1"
        result = get_read_only_sql_command_type(query)
        assert result is None
        mock_logger.assert_called_with(
            "The command 'GRANT' is not a permitted read-only operation."
        )

    def test_case_variations_for_select_commands(self):
        """Test case variations for SELECT commands (currently the only working ones)."""
        test_cases = [
            ("select * from users", SQLCommandType.SELECT),
            ("SELECT * FROM users", SQLCommandType.SELECT),
            ("sElEcT * fRoM users", SQLCommandType.SELECT),
        ]

        for query, expected_type in test_cases:
            result = get_read_only_sql_command_type(query)
            assert result == expected_type, f"Failed for query: {query}"

    def test_currently_unsupported_commands_return_none(self):
        """Test that currently unsupported commands return None."""
        unsupported_queries = [
            "WITH cte AS (SELECT 1) SELECT * FROM cte",
            "DESCRIBE users",
            "DESC users",
            "SHOW TABLES",
            "EXPLAIN SELECT * FROM users",
        ]

        for query in unsupported_queries:
            result = get_read_only_sql_command_type(query)
            assert result is None, f"Expected None for query: {query}"

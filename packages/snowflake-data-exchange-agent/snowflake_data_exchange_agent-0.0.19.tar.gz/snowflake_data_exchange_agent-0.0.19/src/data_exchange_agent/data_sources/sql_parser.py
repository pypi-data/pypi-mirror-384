"""SQL parsing utilities for analyzing query types and commands."""

import logging

import sqlparse

from data_exchange_agent.data_sources.sql_command_type import SQLCommandType


def get_read_only_sql_command_type(query: str) -> SQLCommandType | None:
    """
    Get the type of SQL command from a query.

    Args:
        query: The SQL query to parse.

    Returns:
        SQLCommandType | None: The type of SQL command from a query.

    """
    try:
        statements = sqlparse.parse(query)

        if len(statements) != 1:
            logging.error("Multiple statements are not allowed.")
            return None

        statement = statements[0]
        first_token = statement.token_first()

        if first_token:
            command = first_token.value.upper()
            result_type = None
            match first_token.ttype:
                case sqlparse.tokens.DML:
                    match command:
                        case "SELECT":
                            result_type = SQLCommandType.SELECT
                        case "WITH":
                            result_type = SQLCommandType.WITH
                        case _:
                            logging.error(
                                f"The DML command '{command}' is not a permitted read-only operation."
                            )
                case sqlparse.tokens.DDL:
                    match command:
                        case "DESCRIBE":
                            result_type = SQLCommandType.DESCRIBE
                        case "DESC":
                            result_type = SQLCommandType.DESC
                        case "SHOW":
                            result_type = SQLCommandType.SHOW
                        case "EXPLAIN":
                            result_type = SQLCommandType.EXPLAIN
                        case _:
                            logging.error(
                                f"The DDL command '{command}' is not a permitted read-only operation."
                            )
                case _:
                    logging.error(
                        f"The command '{command}' is not a permitted read-only operation."
                    )

            return result_type
        else:
            logging.error("The query is empty or invalid.")
            return None

    except Exception as e:
        logging.error(f"Error parsing the query: {e}")
        return None

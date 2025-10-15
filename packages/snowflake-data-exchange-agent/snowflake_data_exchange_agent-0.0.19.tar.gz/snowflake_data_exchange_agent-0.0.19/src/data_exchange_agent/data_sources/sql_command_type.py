"""SQL commands."""

from enum import Enum


class SQLCommandType(Enum):
    """
    Enumeration of supported SQL commands.

    This enum defines all the SQL commands that the data exchange agent
    can execute.

    Attributes:
        SELECT: SELECT Command
        WITH: WITH Command
        DESCRIBE: DESCRIBE Command
        DESC: DESC Command
        SHOW: SHOW Command
        EXPLAIN: EXPLAIN Command

    """

    SELECT = "select"
    WITH = "with"
    DESCRIBE = "describe"
    DESC = "desc"
    SHOW = "show"
    EXPLAIN = "explain"

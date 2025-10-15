import pyodbc
from typing import List, Dict, Generator, Any
from ppp_connectors.helpers import setup_logger


class ODBCConnector:
    """
    A connector class for interacting with ODBC-compatible databases.

    Provides methods for querying and bulk inserts.
    Supports use as a context manager for automatic connection cleanup.
    """

    def __init__(self, conn_str: str, logger: Any = None):
        """
        Initialize the ODBC connection.

        Args:
            conn_str (str): The ODBC connection string.
            logger (Any, optional): Logger instance for logging. Defaults to None.
        """
        self.conn = pyodbc.connect(conn_str)
        self.logger = logger or setup_logger(__name__)
        self._log("ODBC connection established")

    def _log(self, msg: str, level: str = "info"):
        if self.logger:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """Close the ODBC connection."""
        if self.conn:
            self.conn.close()
            self._log("ODBC connection closed")

    def query(self, base_query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Execute a query against an ODBC database and yield each row as a dictionary.

        Args:
            base_query (str): The SQL query to execute.

        Yields:
            Generator[Dict[str, Any], None, None]: A generator that yields each search hit as a dictionary.

        Logs:
            Execution of the query.

        Note:
            This method returns a generator. If you want to collect all results,
            you can wrap the result in `list()`, but beware of memory usage if the
            result set is large.
        """
        self._log(f"Executing ODBC query")
        cursor = self.conn.cursor()
        cursor.execute(base_query)
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            yield dict(zip(columns, row))

    def bulk_insert(self, table: str, data: List[Dict[str, Any]]):
        """
        Perform a bulk insert into an ODBC database table.

        Args:
            table (str): Name of the table to insert into.
            data (List[Dict[str, Any]]): List of rows to insert.

        Returns:
            None

        Logs:
            Number of rows inserted and target table.
        """
        if not data:
            return
        self._log(f"Inserting {len(data)} rows into table {table}")
        columns = list(data[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        values = [tuple(row[col] for col in columns) for row in data]
        cursor = self.conn.cursor()
        cursor.fast_executemany = True
        cursor.executemany(insert_query, values)
        self.conn.commit()

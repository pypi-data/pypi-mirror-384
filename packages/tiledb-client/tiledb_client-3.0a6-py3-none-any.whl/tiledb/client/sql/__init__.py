from typing import Optional

from tiledb.client.sql._execution import exec
from tiledb.client.sql._execution import exec_and_fetch
from tiledb.client.sql._execution import exec_async
from tiledb.client.sql.db_api_exceptions import DatabaseError
from tiledb.client.sql.db_api_exceptions import DataError
from tiledb.client.sql.db_api_exceptions import IntegrityError
from tiledb.client.sql.db_api_exceptions import InterfaceError
from tiledb.client.sql.db_api_exceptions import InternalError
from tiledb.client.sql.db_api_exceptions import NotSupportedError
from tiledb.client.sql.db_api_exceptions import OperationalError
from tiledb.client.sql.db_api_exceptions import ProgrammingError
from tiledb.client.sql.tiledb_connection import TileDBConnection

from ._execution import ResultFormat
from ._execution import SQLBackend

last_sql_task_id: Optional[str] = None

# Required by the Python DB API
apilevel = "2.0"
threadsafety = 2
paramstyle = "qmark"
connect = TileDBConnection

__all__ = (
    "exec",
    "exec_and_fetch",
    "exec_async",
    "last_sql_task_id",
    "ResultFormat",
    "SQLBackend",
    "TileDBConnection",
    "InterfaceError",
    "DatabaseError",
    "ProgrammingError",
    "DataError",
    "OperationalError",
    "IntegrityError",
    "InternalError",
    "NotSupportedError",
    "connect",
)

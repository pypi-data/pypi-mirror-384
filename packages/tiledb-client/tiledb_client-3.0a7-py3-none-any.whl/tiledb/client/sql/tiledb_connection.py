from tiledb.client.sql.tiledb_cursor import Cursor


class TileDBConnection:
    def __init__(self, teamspace):
        self._teamspace = teamspace

    def cursor(self):
        return Cursor(self._teamspace)

    def commit(self):
        # Commit must work, even if it doesn't do anything
        # No rollback method due to no transaction support
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

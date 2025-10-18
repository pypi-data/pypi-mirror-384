import logging
import threading
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import duckdb

# from pandas import DataFrame
from pandas import ArrowDtype
from pyarrow import Table

from ..datamodel.database import IqlDatabase, IqlDatabaseConnector, IqlResult

logger = logging.getLogger(__name__)


def rename_dupe_arrow_columns(pat: Table) -> Table:
    # PyArrow can't export to Pandas if there are duplicate columns
    cols = pat.column_names
    unique_cols = set(cols)

    if len(unique_cols) == len(cols):
        # everything is unique
        return pat
    else:
        logger.warning("Has dupes, %s", cols)

        newcols = []
        for col in cols:
            idx = 1
            newcol = col

            while newcol in newcols:
                newcol = f"{col}_{idx}"
                idx += 1

            newcols.append(newcol)

        pat = pat.rename_columns(newcols)

        return pat


@dataclass
class DuckDbResult(IqlResult):
    _table: Table

    def arrow(self):
        return self._table

    def df(self):
        return self._table.to_pandas(types_mapper=ArrowDtype)

    def native(self):
        return self._table


@dataclass
class _DuckDB(IqlDatabase):
    _connection: object
    _started_thread: int

    def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, object]],  # Duckdb uses the caller frame to auto-populate variables
        completed_results: Optional[Iterable[IqlResult]] = None,
        raw: bool = False,
        parameters: Optional[Iterable] = None,
    ) -> Optional[DuckDbResult]:
        """param: Each of the completed _dfs are registered to the database.
        threaded: pass True to run in a separate connection, otherwise runs in main connection
        """
        if context is not None:
            # TODO: Don't do this... this was because duckdb stopped using the full context.
            # Alternative is to use full chain, rather than just caller frame
            locals().update(context)

        if len(query.strip()) == 0:
            return None

        threaded = threading.get_ident() != self._started_thread

        # create & close the connection if we're threading, otherwise create one
        with self.get_connection() if threaded else nullcontext(self._connection) as con:
            try:
                # Register each of the dataframes to duckdb, so duckdb can query them
                # Other database might require a "load" or "from_pandas()" step to load these
                # to temporary tables.
                if completed_results is not None:
                    for result in completed_results:
                        data = result.native()
                        if data is not None:  # None for paths
                            con.register(result.name, data)  # type: ignore

                if raw:  # for DBT
                    rel = con.execute(query, parameters=parameters)  # type: ignore
                    return DuckDbResult(name=query, query=query, _table=rel)
                else:
                    d = con.sql(query, params=parameters)  # type: ignore

                    if d is not None:
                        table = d.fetch_arrow_table()
                        table = rename_dupe_arrow_columns(table)
                        return DuckDbResult(name=query, query=query, _table=table)

                    else:
                        return None
            except Exception as e:
                e.add_note(f"Query:\n {query}")
                e.add_note(f"Parameters:\n {parameters}")

                raise

    def get_connection(self):
        return self._connection.cursor()  # type: ignore

    def close_db(self):
        self._connection.close()  # type: ignore
        self._connection = None


class _DuckDbConnector(IqlDatabaseConnector):
    def create_database(self, file=":memory:") -> _DuckDB:
        con = duckdb.connect(database=file)
        # con.execute("SET enable_progress_bar=false;")
        return _DuckDB(_connection=con, _started_thread=threading.get_ident())

    def create_database_from_con(self, con: object) -> _DuckDB:
        return _DuckDB(_connection=con, _started_thread=threading.get_ident())


def get_connector() -> IqlDatabaseConnector:
    return _DuckDbConnector()

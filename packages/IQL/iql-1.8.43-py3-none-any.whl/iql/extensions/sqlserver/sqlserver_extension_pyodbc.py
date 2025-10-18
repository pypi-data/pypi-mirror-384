# Copyright (C) 2025, IQMO Corporation [support@iqmo.com]
# All Rights Reserved

import logging
import struct
from dataclasses import dataclass
from typing import Any

import pyodbc
import sqlalchemy as sa
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from ... import IqlExtension, SubQuery, register_extension
from ...datamodel import cache

logger = logging.getLogger(__name__)

# https://github.com/pymssql/pymssql
# https://pymssql.readthedocs.io/en/stable/

_CREDENTIAL: Any | None = None
replace_pyformat_parameters = True

# The connection cache is either connections **or** options to create a connection
_CONNECTION_CACHE: dict[str, sa.Engine | dict[str, Any]] = {}
CACHE_INVALIDATION_QUERY = None


def _get_connection_from_options(connection_string: str, **kwargs) -> sa.Engine:
    if _CREDENTIAL is None:
        raise RuntimeError("_CREDENTIAL not set")
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})

    sqltoken = _CREDENTIAL.get_token("https://database.windows.net/.default").token

    # https://learn.microsoft.com/en-us/azure/azure-sql/database/azure-sql-python-quickstart?view=azuresql&tabs=windows%2Csql-inter
    raw = sqltoken.encode("utf-16-le")
    token_bytes = struct.pack(f"<I{len(raw)}s", len(raw), raw)
    tokenshort = {1256: token_bytes}
    # result = iql.execute(f"select * from mssql.pyodbc_connect(connection_string = '{CONN_URL}', attrs_before={tokenshort})", con=conn)
    kwargs["attrs_before"] = tokenshort

    engine = create_engine(connection_url, connect_args=kwargs)

    return engine


def _get_connection(connection_name: str) -> sa.Engine:
    existing_conn: sa.Engine | dict = _CONNECTION_CACHE[connection_name]
    if isinstance(existing_conn, dict):
        return _get_connection_from_options(**existing_conn)
    else:
        return existing_conn


def process_result(result: pyodbc.Cursor):
    if result.description:
        columns = [col[0] if col[0] else f"col_{i}" for i, col in enumerate(result.description)]
        result_df = DataFrame.from_records(result.fetchall(), columns=columns)
    else:
        row_count = result.rowcount if result.rowcount != -1 else None
        result_df = DataFrame({"result": ["query complete"], "rowcount": [row_count]})

    return result_df


def _execute_query(engine: sa.Engine, query: str, parameters: dict | None = None) -> list[DataFrame]:
    logger.debug("Executing query in sqlalchemy: %s", query)

    results = []
    with engine.raw_connection().cursor() as conn:  # pyright: ignore[reportGeneralTypeIssues]
        if parameters is not None:
            if replace_pyformat_parameters:
                for k, v in parameters.items():
                    query = query.replace(f"%({k})s", f"'{v}'")

                result = conn.execute(query)

            else:
                result = conn.execute(query, parameters)
        else:
            result = conn.execute(query)

        while result:
            result_df = process_result(result)
            results.append(result_df)

            if not result.nextset():
                break

        return results


@dataclass
class SqlServerExtensionPyOdbcConnect(IqlExtension):
    def executeimpl(self, sq: SubQuery) -> DataFrame:
        connection_name: str = sq.options.get("name", "default")  # type: ignore
        connection_string: str = sq.options["connection_string"]  # type: ignore

        eager = sq.options.get("eager", True)
        conn_options = {
            k: v for k, v in sq.options.items() if k != "name" and k != "eager" and k != "connection_string"
        }

        if eager:
            _CONNECTION_CACHE[connection_name] = _get_connection_from_options(
                connection_string=connection_string, **conn_options
            )
        else:
            _CONNECTION_CACHE[connection_name] = conn_options

        return DataFrame({"success": [True], "message": ["Connection Successful"]})


@dataclass
class SqlServerExtensionPyOdbc(IqlExtension):
    @cache.iql_cache
    def executeimpl(self, sq: SubQuery) -> DataFrame:
        connection_name: str = sq.options.get("name", "default")  # type: ignore

        conn: sa.Engine = _get_connection(connection_name)

        query: str = sq.get_query()  # type: ignore

        parameters: dict = sq.options.get("PARAMETERS", None)  # type: ignore

        try:
            results = _execute_query(conn, query, parameters=parameters)
        except Exception as e:
            e.add_note(f"{query=}")
            raise
        return results[-1]


def register(keyword: str):
    if CACHE_INVALIDATION_QUERY is not None:
        logger.info("Using CACHE_INVALIDATION_QUERY")
        ext_cache = cache.QueryInvalidationCache(CACHE_INVALIDATION_QUERY)
    else:
        ext_cache = None

    extension = SqlServerExtensionPyOdbc(keyword=keyword, cache=ext_cache)
    register_extension(extension)

    extension = SqlServerExtensionPyOdbcConnect(keyword=keyword, subword="pyodbc_connect", cache=None)
    register_extension(extension)

    extension = SqlServerExtensionPyOdbc(keyword=keyword, subword="pyodbc", cache=ext_cache)
    register_extension(extension)

    extension = SqlServerExtensionPyOdbc(keyword=keyword, subword="nocache", cache=None)
    register_extension(extension)

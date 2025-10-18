# Copyright (C) 2025, IQMO Corporation [support@iqmo.com]
# All Rights Reserved

import logging
from dataclasses import dataclass

import pymssql
from pandas import DataFrame

from ... import IqlExtension, SubQuery, register_extension
from ...datamodel import cache
from ...ql import substitute_replace

logger = logging.getLogger(__name__)

# https://github.com/pymssql/pymssql
# https://pymssql.readthedocs.io/en/stable/


# The connection cache is either connections **or** options to create a connection
_CONNECTION_CACHE: dict[str, pymssql.Connection | dict] = {}
CACHE_INVALIDATION_QUERY = None


def _get_connection_from_options(**kwargs) -> pymssql.Connection:
    return pymssql.connect(**kwargs)


def _get_connection(connection_name: str) -> pymssql.Connection:
    existing_conn: pymssql.Connection | dict = _CONNECTION_CACHE[connection_name]
    if isinstance(existing_conn, dict):
        return _get_connection_from_options(**existing_conn)
    else:
        return existing_conn


def _execute_query(conn: pymssql.Connection, query: str, parameters: dict | None = None) -> DataFrame:
    logger.debug("Executing query: %s", query)

    with conn.cursor(as_dict=True) as cursor:
        # dont perform substitutions, we do this with parameters

        query_sub = substitute_replace(query, {})
        logger.info("Running query %s", query_sub)
        cursor.execute(query_sub, parameters)
        results = cursor.fetchall()
        columns = cursor.description

        while cursor.nextset():
            results = cursor.fetchall()
            columns = cursor.description

    if results is not None and len(results) == 0:  # type: ignore
        return DataFrame(results, columns=[col[0] for col in columns])  # type: ignore
    return DataFrame(results)


@dataclass
class SqlServerExtensionPyMssqlConnect(IqlExtension):
    def executeimpl(self, sq: SubQuery) -> DataFrame:
        connection_name: str = sq.options.get("name", "default")  # type: ignore

        eager = sq.options.get("eager", False)
        conn_options = {k: v for k, v in sq.options.items() if k != "name" and k != "eager"}

        if eager:
            _CONNECTION_CACHE[connection_name] = _get_connection_from_options(**conn_options)
        else:
            _CONNECTION_CACHE[connection_name] = conn_options

        return DataFrame({"success": [True], "message": ["Connection Successful"]})


@dataclass
class SqlServerExtensionPyMssql(IqlExtension):
    @cache.iql_cache
    def executeimpl(self, sq: SubQuery) -> DataFrame:
        connection_name: str = sq.options.get("name", "default")  # type: ignore

        conn: pymssql.Connection = _get_connection(connection_name)

        query: str = sq.get_query()  # type: ignore

        parameters: dict = sq.options.get("PARAMETERS", None)  # type: ignore

        return _execute_query(conn, query, parameters=parameters)


def register(keyword: str):
    if CACHE_INVALIDATION_QUERY is not None:
        logger.info("Using CACHE_INVALIDATION_QUERY")
        ext_cache = cache.QueryInvalidationCache(CACHE_INVALIDATION_QUERY)
    else:
        ext_cache = None

    extension = SqlServerExtensionPyMssqlConnect(keyword=keyword, subword="pymssql_connect", cache=None)
    register_extension(extension)

    extension = SqlServerExtensionPyMssql(keyword=keyword, subword="pymssql", cache=ext_cache)
    register_extension(extension)

    extension = SqlServerExtensionPyMssql(keyword=keyword, cache=ext_cache)
    register_extension(extension)

    extension = SqlServerExtensionPyMssql(keyword=keyword, subword="nocache", cache=None)
    register_extension(extension)

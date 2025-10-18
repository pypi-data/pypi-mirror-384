import logging
from typing import List

from pandas import DataFrame

from .. import constants, ql
from . import iql_magic

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

sql_expects_tablename = [
    "UNION",
    "UNION ALL",
    "UNION ALL BY NAME",
    "UNION BY NAME",
    "JOIN",
    "INNER JOIN",
    "LEFT JOIN",
    "RIGHT JOIN",
    "FULL JOIN",
    "LEFT OUTER JOIN",
    "RIGHT OUTER JOIN",
    "FROM",
    "INTO",
]

sql_phrases = [
    "PRAGMA",
    "SELECT",
    "WHERE",
    "GROUP BY",
    "ORDER BY",
    "LIMIT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "TABLE",
    "DATABASE",
    "INDEX",
    "VIEW",
    "FUNCTION",
    "PROCEDURE",
    "TRIGGER",
    "AND",
    "OR",
    "NOT",
    "BETWEEN",
    "LIKE",
    "IN",
    "NULL",
    "IS",
    "EXISTS",
    "COUNT",
    "SUM",
    "MIN",
    "MAX",
    "AVG",
    "DISTINCT",
    "AS",
    "CREATE TABLE",
    "CREATE OR REPLACE TABLE",
    "CREATE TABLE IF NOT EXISTS",
    "CREATE VIEW",
]

pragma_phrases = [
    "PRAGMA version",
    "PRAGMA database_list",
    "PRAGMA database_size",
    "PRAGMA show_tables",
    "PRAGMA show_tables_expanded",
    "PRAGMA table_info('",
    "PRAGMA functions",
    "PRAGMA collations",
    "PRAGMA enable_progress_bar",
    "PRAGMA disable_progress_bar",
    "PRAGMA enable_profiling",
    "PRAGMA disable_profiling",
    "PRAGMA disable_optimizer",
    "PRAGMA enable_optimizer",
    "PRAGMA enable_verification",
    "PRAGMA disable_verification",
    "PRAGMA verify_parallelism",
    "PRAGMA disable_verify_parallelism",
    "PRAGMA force_index_join",
    "PRAGMA force_checkpoint",
]

function_query = """
with f_inner as (select 
    function_name, 
    case when len(parameters)=0 then '' else list_reduce(parameters, (x,i) -> x||', ' || i) end param_str,
    '(' || param_str || ')' as param_ex
 from duckdb_functions()
)
select function_name || first(param_ex) as function_full
from f_inner
group by function_name
order by function_full

"""


def get_function_names(ipython, token) -> List[str]:
    try:
        if iql_magic.connection is not None:
            functions = iql_magic.connection.sql(function_query)
            function_list = list(functions.df()["function_full"])
            extensions = list(constants._KNOWN_EXTENSIONS.keys())
            all_functions = function_list + extensions
            filtered_functions = [c for c in all_functions if c.startswith(token)]
            logger.debug("Getting function names: %s", filtered_functions)

            return filtered_functions
    except Exception:
        logger.exception("Unable to get function names")

    return []


def get_table_names(ipython) -> List[str]:
    try:
        user_keys = [k for k, v in ipython.user_ns.items() if isinstance(v, DataFrame)]

        if iql_magic.connection is not None:
            tables = iql_magic.connection.sql("show tables")
            logger.debug("Got tables: %s", tables)

            if tables is None:
                return user_keys
            else:
                return list(tables.df()["name"]) + user_keys
        else:
            logger.debug(user_keys)
            return user_keys
    except Exception:
        logger.exception("Unable to get table names")
        return []


def get_column_names_for_table(ipython, tablename: str) -> List[str]:
    try:
        # check if an object
        # o = ipython.ev(tablename)
        o = ipython.user_ns.get(tablename)
        if o is None and iql_magic.connection is not None:
            columns = list(ql.executedf(f"describe select * from {tablename}")["column_name"].to_numpy())
            if columns is None:
                logger.debug("None columns")
                return []
            else:
                logger.debug("Column names: %s", columns)
                return columns
        elif o is not None:
            if isinstance(o, DataFrame):
                return list(o.columns)
            else:
                logger.debug("%s in namespace, but not a DataFrame %s", tablename, type(o))
                return []
        else:
            return []
    except Exception:
        logger.exception("Unable to get column names")
        return []


def get_column_names(ipython, tablename: str) -> List[str]:
    if tablename == "alias":
        aliases = [c + "()" for c in ql._ALIASES.keys()]
        return aliases
    elif tablename.startswith("$"):
        return get_column_names_for_table(ipython=ipython, tablename=tablename)
    else:
        return get_column_names_for_table(ipython=ipython, tablename=tablename)

import importlib
import inspect
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple, Union

import sqlparse
from pandas import DataFrame

from . import constants, options_parser
from .datamodel.database import IqlDatabaseConnector
from .datamodel.extension import IqlExtension
from .datamodel.querycontainer import IqlQueryContainer
from .datamodel.result import IqlResult
from .utils import extract_subquery_strings

logger = logging.getLogger(__name__)

# Customizations #
# Configure before first use
# Note: Will likely move these to a config file
DB_MODULE: str = "iql.db_connectors.duckdb_connector"  # Change before first db use
DFPREFIX: str = "iqldf"  # Prefix for temporary files
DEFAULT_EXT_DIRECTORY = None  # Sets temp dir for extensions, set before extension use

# Internal Objects
_EXTENSIONS: Dict[Tuple[str, str], IqlExtension] = {}  # register_extension
_DBCONNECTOR: Optional[IqlDatabaseConnector] = None  # Set DB_MODULE before use.
_SUBSTITUTIONS: Dict[str, str] = {}  # Substition map: any occurence in a query of key will be replaced by value
_ALIASES: Dict[str, Union[str, Path]] = {}  # register_alias


def _parameterize_sql_alias(subword, query) -> str:
    if subword not in _ALIASES.keys():
        raise ValueError(f"Unknown alias {subword}")

    query_data = _ALIASES[subword]
    base_query = query_data if isinstance(query_data, str) else query_data.read_text()

    for k, v in options_parser.options_to_list(query).items():
        # convert the parameter to $uppercase, so security => $SECURITY
        newk = f"${k.upper()}"
        base_query = base_query.replace(newk, str(v))

    return base_query


def replace_sql_aliases(query) -> str:
    newquery = query
    for _, subword, outer, _ in extract_subquery_strings(query, ["alias"]):
        sql = _parameterize_sql_alias(subword, outer)

        # aliases might recurse
        sql = replace_sql_aliases(sql)
        logger.debug("Found SQL alias, replacing and parameterizing: %s", outer)

        newquery = newquery.replace(outer, sql)

    return newquery


@lru_cache(maxsize=3)
def parse_sql(query: str):
    return sqlparse.parse(query)


def substitute_replace(query: str, substitutions: Optional[Dict[str, str]]) -> str:
    if substitutions is None:
        all_subs = _SUBSTITUTIONS
    else:  # override any substitutions
        all_subs = _SUBSTITUTIONS.copy()
        all_subs.update(substitutions)

    lastquery = None

    new_query = query
    while new_query != lastquery:
        # Keep changing until all changes and aliases are updated
        # Since an alias can have a substitution, and a substitution can have an alias
        # We just need to repeat

        lastquery = new_query

        logger.debug("Substituting with %s, query=%s", all_subs, new_query)
        for k, v in all_subs.items():
            # logger.debug("%s %s", k, v)
            # TODO: Remove the $, and use exact SUBSTITUTIONS. Makes it easier to use whatever
            # substitution syntax you want.
            # TODO: Consider how to support both JINJA and native
            new_query = new_query.replace(f"${k.upper()}", str(v))
        # Aliases
        new_query = replace_sql_aliases(new_query)

    if new_query != query:
        logger.debug("Updated query %s", new_query)

    return new_query


def execute_debug(
    query: str,
    con: Optional[object] = None,
    substitutions: Optional[Dict[str, str]] = None,
    parameters: Optional[Iterable[Any]] = None,
    raw: bool = False,
    context: Optional[Dict[str, object]] = None,
) -> Tuple[bool, Optional[DataFrame], Dict[str, Optional[DataFrame]], Optional[Dict[str, Iterable[IqlResult]]]]:
    """Returns the success (True or False), final query result, and the debug
    results: all the intermediate queries and subqueries."""
    # Connection to database

    # Special case for BQL only.
    if query.strip().startswith("get") or query.strip().startswith("let"):
        # TODO: Handle "from first" bql

        if '"""' in query:
            raise ValueError("Triple quotes are not allowed in query")

        query = query.replace('"', '\\"')
        query = f'''select * from bql(""" {query} """)'''

    # Initialize or Reuse DB Connector
    idc: IqlDatabaseConnector = get_dbconnector()

    if con is None:
        db = idc.create_database()
    else:
        db = idc.create_database_from_con(con=con)

    query = substitute_replace(query, substitutions)

    try:
        # A single query might contain multiple SQL statements. Parse them out and iterate:
        single_df: Optional[DataFrame] = None
        completed_result_map: Dict[str, Optional[DataFrame]] = {}
        intermediate_result_map = {}
        if ";" not in query:
            # Performance optimization for simple queries
            iqc = IqlQueryContainer(query=query, db=db, substitutions=substitutions, context=context)  # type: ignore

            single_df, intermediate_results = iqc.execute(parameters=parameters, raw=raw)
            return (True, single_df, {query: single_df}, {query: intermediate_results})
        else:
            logger.debug("Parsing %.120s", query)

            statements = parse_sql(query)

            for i, statement in enumerate(statements):
                singlequery = statement.value.strip(";")
                iqc = IqlQueryContainer(
                    query=singlequery,
                    db=db,
                    substitutions=substitutions,  # type: ignore
                    context=context,
                )

                # Run each statement, but only keep the results from the last one

                if (
                    i == len(statements) - 1
                ):  # Only pass parameters to last query. This is consistent with how duckdb would run this natively.
                    single_df, completed_results = iqc.execute(parameters=parameters, raw=raw)
                else:
                    single_df, completed_results = iqc.execute(raw=raw)

                completed_result_map[singlequery] = single_df
                intermediate_result_map[singlequery] = completed_results

        return (True, single_df, completed_result_map, intermediate_result_map)

    finally:
        if con is None:  # DB was created here, so close it
            db.close_db()


def execute(
    query: str,
    con: Optional[object] = None,
    substitutions: Optional[Dict[str, str]] = None,
    parameters: Optional[Iterable[Any]] = None,
    raw: bool = False,
    context: Optional[Dict[str, object]] = None,
    autocontext: bool = True,
) -> Optional[DataFrame]:
    """Executes the given SQL query. Keyword is only used to run a single subquery without SQL."""

    if autocontext and context is None:
        context = inspect.currentframe().f_back.f_locals  # type: ignore

    _success, single_df, _completed_results, _intermediate_results = execute_debug(
        query, con, substitutions=substitutions, parameters=parameters, raw=raw, context=context
    )

    return single_df


def executedf(*args: Iterable[Any], **kwargs: dict[str, Any]) -> DataFrame:
    """Helper that enforces that a DataFrame is returned, otherwise ValueError"""

    if kwargs.get("autocontext", True) and kwargs.get("context", None) is None:
        context = inspect.currentframe().f_back.f_locals  # type: ignore
        kwargs["context"] = context

    result_df = execute(*args, **kwargs)

    if result_df is None:
        raise ValueError("Execution returned a None result")
    else:
        return result_df


def get_dbconnector() -> IqlDatabaseConnector:
    global _DBCONNECTOR
    if _DBCONNECTOR is None:
        # Initializes only on first reference
        module = importlib.import_module(DB_MODULE)
        _DBCONNECTOR = module.get_connector()

    return _DBCONNECTOR


def register_extension(e: IqlExtension):
    """* subword means: catchall"""

    _EXTENSIONS[(e.keyword, e.subword)] = e  # type: ignore

    if e.keyword not in constants._KNOWN_EXTENSIONS.keys():
        constants._KNOWN_EXTENSIONS[e.keyword] = e.keyword
        constants._LOADED_EXTENSIONS.append(e.keyword)

    if e.temp_file_directory is None:
        e.temp_file_directory = DEFAULT_EXT_DIRECTORY


def register_alias(subword: str, data: Union[str, Path]):
    """
    Aliases are called via
    alias.aliasname(param1=abc, param2.abc)
    When run, the alias will be replaced, and "$PARAM1" will be replaced with abc.
    You can either register the entire SQL or a path to a file containing the SQL.

    If a Path is given, then it is loaded on each access (not cached).
    """

    logger.debug("Registering alias: %s", subword)
    _ALIASES[subword] = data


def list_extensions() -> Iterable[str]:
    return list(constants._KNOWN_EXTENSIONS.keys())


def get_extension(keyword: str, subword: str) -> IqlExtension:
    """Loads extension on first use"""

    if keyword not in constants._LOADED_EXTENSIONS:
        if keyword not in constants._KNOWN_EXTENSIONS.keys():
            raise ValueError(f"Unknown Extension {keyword}")
        else:
            classname = constants._KNOWN_EXTENSIONS[keyword]
            logger.debug("Loading classname=%s", classname)
            module = importlib.import_module(classname)
            module.register(keyword)
            constants._LOADED_EXTENSIONS.append(keyword)

    words = (keyword, subword)

    ext = _EXTENSIONS.get(words, _EXTENSIONS.get((keyword, "*"), None))
    if ext is not None:
        return ext
    else:
        raise ValueError(f"{keyword}.{subword} is not registered")


def configure(temp_dir: Optional[str] = None):
    """
    Must be called before extensions are initialized (on first use)
    duration_seconds: None (Disabled), -1 (Infinite), int (Seconds)
    file_directory: None (no file cache), string (output directory)
    """
    global DEFAULT_EXT_DIRECTORY
    DEFAULT_EXT_DIRECTORY = temp_dir


def patch_sqlparse():
    # patch sqlparse to allow leading $'s for substitution patterns
    try:
        sqlparse.keywords.SQL_REGEX.insert(9, (r"\$[\w$]*", sqlparse.tokens.Name))
        sqlparse.lexer.Lexer.get_default_instance().set_SQL_REGEX(sqlparse.keywords.SQL_REGEX)
    except Exception:
        logger.exception("Couldn't patch sqlparse to allow a leading $ in table names")

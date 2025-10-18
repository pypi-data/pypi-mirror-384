import logging
from dataclasses import dataclass, field
from typing import Iterable, Optional

from pandas import DataFrame

from ...datamodel import cache
from ...datamodel.extension import IqlExtension
from ...datamodel.querycontainer import IqlQueryContainer
from ...datamodel.result import IqlResultData
from ...datamodel.subquery import SubQuery, get_subqueries_flat
from ...ql import execute, register_extension
from .bql_datamodel import RawBqlQuery
from .bql_wrapper import BaseBqlQuery, execute_bql_str_list_async_q

logger = logging.getLogger(__name__)

_KEYWORD = "bql"

# _bql_start_pattern = r"(?si)\(\s*((get)|(let))\s*\("
# _bql_pat = re.compile(_bql_start_pattern)

# _QUERY_FOR_PATTERN = re.compile(
#     r"(?s)(.*for\s*\((.*?)\)\s*)((with.*?)?)\s*((preferences.*)?)"
# )


@dataclass
class _IqlBqlQuery(SubQuery):
    # Extended BQL language to add "iqmo" options
    # such as "splitid" and pivoting
    # Syntax; pivot(id, name)
    # Syntax 2: pivot([id:col2], name)
    bqlquery: BaseBqlQuery = field(init=False)
    force_file: bool = (
        True  # for large queries, forces the subquery to write to a parquet file instead of storing in a df.
    )

    # detects everything before "(.*) as #..."
    def execute(self) -> bool:
        if self.dataframe is not None:
            return True

        success = self.execute_internal()

        if not success:
            logger.warning(self.bqlquery.exception_msg)

        if success:
            # If it's a output file, then it'd already be written
            if not self.extension.use_path_replacement():
                df = self.bqlquery.to_df()

                df = self.extension.apply_pandas_operations_prepivot(df, self.options)

                df = self.extension.pivot(df, self.options.get("pivot"))  # noqa: PD010 # type: ignore
                df = self.extension.apply_pandas_operations_postpivot(df, self.options)

                self.dataframe = df

                if self.extension.cache is not None:
                    self.extension.cache.save(self, df, cost=None)

            return success
        else:
            allow_failure_opt = self.options["allow_failure"]

            if isinstance(allow_failure_opt, str):
                cols: Iterable[str] = [allow_failure_opt]
            else:
                cols: Iterable[str] = allow_failure_opt  # type: ignore
            logger.debug(
                "Query failed, but allow_failure is enabled. Creating an empty dataframe with cols = %s",
                cols,
            )

            self.dataframe = DataFrame(columns=cols)  # type: ignore

            return True

    def execute_internal(self) -> bool:
        if self.bqlquery.execution_status == BaseBqlQuery.STATUS_FAILURE:
            return False

        if self.bqlquery.execution_status == BaseBqlQuery.STATUS_COMPLETED:
            return True

        working_df = None

        # If it already ran, don't run again
        if self.bqlquery.execution_status != BaseBqlQuery.STATUS_COMPLETED:
            self.bqlquery.execute()

        # query has passed
        if working_df is None:
            working_df = self.bqlquery.to_df()

        if working_df is None:
            raise ValueError("Unable to convert query to DataFrame")

        # validate column names: disabled for now, still a work in progress
        # working_df = self.validate_fix_column_names(working_df)
        self.dataframe = working_df
        return True


@dataclass
class BqlExtension(IqlExtension):
    def executeimpl(self, sq: SubQuery) -> Optional[DataFrame]:
        raise NotImplementedError("Not Implemented")

    def create_subquery(self, query: str, name: str, iqc: IqlQueryContainer) -> SubQuery:
        iq = _IqlBqlQuery(subquery=query, name=name, extension=self, iqc=iqc)

        bqlstr = iq.get_query()

        q = RawBqlQuery(bqlstr)  # type: ignore
        iq.bqlquery = q
        return iq

    def create_subqueries(
        self,
        query: str,
        name: str,
        iqc: IqlQueryContainer,
        create_function: object = None,
    ) -> Iterable[SubQuery]:
        return super().create_subqueries(query=query, name=name, iqc=iqc, create_function=self.create_subquery)

    def execute_batch(
        self,
        queries: Iterable[_IqlBqlQuery],
    ) -> Iterable[IqlResultData]:
        # Caching operates at two levels here:
        # The SubQuery result, and within the bql_wrapper
        # To force a refresh, we'll clear both the subquery and bql raw query
        # cache

        subqueries_flat: Iterable[_IqlBqlQuery] = get_subqueries_flat(queries)  # type: ignore

        for sq in subqueries_flat:
            # if cached, used cached
            if sq.dataframe is None and self.cache is not None:
                cached_df = self.cache.get(sq)
                if cached_df is not None:
                    sq.dataframe = self.cache.get(sq)

        to_run: Iterable[_IqlBqlQuery] = [sq for sq in subqueries_flat if sq.dataframe is None]

        if self.use_path_replacement():
            for q in to_run:
                q.bqlquery._output_filename = self.get_path_replacement(q, quote=False)

        queries_l: Iterable[BaseBqlQuery] = [q.bqlquery for q in to_run]

        logger.debug("Executing %s", len(queries_l))

        if self.use_path_replacement():
            max_concurrent_queries = 16
            execute_bql_str_list_async_q(queries_l, max_queries=max_concurrent_queries, cache=self.cache)
        else:
            execute_bql_str_list_async_q(queries_l, cache=self.cache)

        # Then update the subqueries
        for q in subqueries_flat:
            if q.bqlquery.execution_status == BaseBqlQuery.STATUS_FAILURE:
                if q.options.get("allow_failure") is None:
                    raise ValueError(
                        f"BQL SubQuery failed {q.bqlquery.exception_msg}: {q.bqlquery.to_bql_query()} {q.options}"
                    )
            try:
                q.execute()
            except Exception as e:
                raise ValueError(f"Error on q.bqlquery: {q.bqlquery.to_bql_query()}") from e

        completed_results = []
        # Final step to merge any grouped subqueries.
        for q in queries:
            q.merge()
            df = q.dataframe

            result = IqlResultData(name=q.name, query=q.subquery, _data=df)

            completed_results.append(result)

        return completed_results


def execute_bql(query: str, pivot: Optional[str] = None) -> DataFrame:
    """Convenience function for testing, or executing single queries"""

    if _KEYWORD in query:
        raise ValueError(f"Pass raw BQL queries only, don't wrap with {_KEYWORD}(...)")

    elif pivot is not None:
        suffix = f", pivot={pivot}"

    else:
        suffix = ""

    query = f'{_KEYWORD}("{query}"{suffix})'
    extension = BqlExtension(_KEYWORD)

    logger.debug("Converted to: %s", query)
    sqs = extension.create_subqueries(query, "Anon", iqc=None)  # type: ignore
    sq = next(sq for sq in sqs)  # there'll only be one

    sq.execute()  # type: ignore

    return sq.dataframe


def execute_bql_batch(queries: Iterable[str], subtype: str = "bql") -> Iterable[DataFrame]:
    """Runs the BQL queries as a batch first"""
    subqueries = []
    for query in queries:
        iqc = IqlQueryContainer(query, db=None)  # type: ignore
        subqueries_q = [q.bqlquery for q in iqc.get_subqueries_by_extension(subtype, None)]  # type: ignore
        subqueries += subqueries_q

    logger.debug("subqueries=%s", subqueries)

    # TODO: Fix this to work in execute_bql_batch
    # execute_bql_batch(subqueries)
    execute_bql_str_list_async_q(subqueries)

    results = [execute(q) for q in queries]
    return results  # type: ignore


def register(keyword: str):
    global _KEYWORD
    _KEYWORD = keyword
    extension = BqlExtension(keyword=keyword)
    register_extension(extension)

    extension2 = BqlExtension(keyword=keyword, subword="large")
    # Large mode: Fewer concurrent connections, writing to disk rather than keeping in memory
    extension2.use_path_replacement = lambda: True
    register_extension(extension2)

    extension3 = BqlExtension(keyword=keyword, subword="cache")
    extension3.use_path_replacement = lambda: False
    extension3.cache = cache.MemoryAndFileCache(max_age=3600 * 18, return_pyarrow_table=False)
    register_extension(extension3)

    extension4 = BqlExtension(keyword=keyword, subword="mcache")
    extension4.cache = cache.MemoryCache(max_age=None)
    register_extension(extension4)

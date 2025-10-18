from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, Optional, Tuple

import sqlparse
from pandas import DataFrame

from .. import ql
from ..utils import extract_subquery_strings
from . import subquery
from .database import IqlDatabase
from .result import IqlResult, IqlResultData

logger = logging.getLogger(__name__)


class IqlQueryContainer:
    # This is used so we can run the bql_queries as an async batch, separate from processing the results.
    orig_query: str
    query: str
    subqueries: Iterable[subquery.SubQuery]
    substitutions: Dict[str, str]
    db: IqlDatabase
    context: Optional[Dict[str, object]]

    def extract_subqueries(self):
        subqueries: Iterable[subquery.SubQuery] = []

        i = 0

        replacements: Iterable[Tuple[str, Optional[str]]] = []

        if "--" in self.orig_query:
            query = sqlparse.format(self.orig_query, strip_comments=True).strip()
        else:
            query = self.orig_query

        for keyword, subword, outer, _ in extract_subquery_strings(query):
            i += 1
            name = f"{ql.DFPREFIX}_{i}"

            extension = ql.get_extension(keyword, subword)
            sqs: Iterable[subquery.SubQuery] = extension.create_subqueries(query=outer, name=name, iqc=self)
            subqueries.extend(sqs)

            if extension.use_path_replacement():
                names = [sq.extension.get_path_replacement(sq) for sq in sqs]
            else:
                names = [sq.name for sq in sqs]

            if len(names) != 1:
                raise ValueError(f"Unexpected length of names: {len(names)}")

            result = names[0]  # holdover from using unions, instead of subquerygroups.

            replacements.append((outer, result))

        for old, new in replacements:
            logger.debug("Replacing %s with %s", old, new)
            query = query.replace(old, new, 1)  # type: ignore

        logger.debug("After replacements %s", query)
        # if only one function without a beginning subquery
        if len(replacements) > 0:
            values = [value for key, value in replacements if value is not None]
            if re.match(rf"(?s)\s*({'|'.join(values)}).*", query) is not None:
                logger.debug("Starts with replacement: %s", values)
                query = f"select * from {query}"

        self.query = query

        return subqueries

    def __init__(
        self, query: str, db: IqlDatabase, substitutions: Optional[Dict] = None, context: Optional[Dict] = None
    ):
        if substitutions is None:
            substitutions = {}

        self.orig_query = query
        self.query = query
        self.db = db
        self.substitutions = substitutions
        self.context = context

        self.subqueries = self.extract_subqueries()

        # Sanity checks. These don't take into account escaping or quoting, so they're just warnings.
        if query.count("(") != query.count(")"):
            logger.warning("Left/Right parens aren't balanced")

        if query.count("'") % 2 != 0:
            logger.warning("Uneven number of single quotes")

        if query.count('"') % 2 != 0:
            logger.warning("Uneven number of double quotes")

    def get_subqueries_by_extension(self, keyword: str, subword: str) -> Iterable[subquery.SubQuery]:
        results: Iterable[subquery.SubQuery] = []
        results = [s for s in self.subqueries if s.extension.keyword == keyword and s.extension.subword == subword]

        return results

    def execute(  # noqa: C901
        self, raw: bool, parameters: Optional[Iterable[Any]] = None
    ) -> Tuple[Optional[DataFrame], Iterable[IqlResult]]:  # noqa: C901
        """Returns the final df, plus the intermediate subquery dataframes.
        If the query is not a Select, returns a None"""
        # Execute the subqueries

        completed_results: Iterable[IqlResult] = []

        for (
            keyword,
            subword,
        ), e in ql._EXTENSIONS.copy().items():  # copy to prevent dictionary changed size during iteration error
            sqs: Iterable[subquery.SubQuery] = self.get_subqueries_by_extension(keyword, subword)  # type: ignore
            sqs = list(sqs)
            if len(sqs) == 0:
                continue

            try:
                e_results = e.execute_batch(sqs)  # type: ignore
            except Exception as e:
                logger.debug("Failed to execute batch %s %s: %s", keyword, subword, self.query)
                raise e
            completed_results += e_results

        # Optimization: If there's just a single subquery, and it's a DF, just return that
        # No need to pass it through duckdb
        # This may have typing implications though.
        if self.query == "select * from iqldf_1" and len(completed_results) == 1:
            # shortcut for a simple case:
            cr1 = completed_results[0].native()
            if isinstance(cr1, DataFrame):
                return (cr1, completed_results)

        result = self.db.execute_query(
            query=self.query, completed_results=completed_results, parameters=parameters, raw=raw, context=self.context
        )  # type: ignore

        if result is None:
            df = None
        elif raw:
            df = result.native()
        else:
            df = result.df()

        # add the final result to the completions
        final_result = IqlResultData(name="final", query=self.query, _data=df)  # type: ignore

        completed_results.append(final_result)

        return (df, completed_results)  # type: ignore

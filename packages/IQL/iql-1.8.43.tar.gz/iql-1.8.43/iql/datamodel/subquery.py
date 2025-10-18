from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .. import options_parser
from . import extension
from .querycontainer import IqlQueryContainer

logger = logging.getLogger(__name__)


def get_subqueries_flat(queries: Iterable[SubQuery]) -> Iterable[SubQuery]:
    subqueries_flat = [q_inner for q_outer in queries for q_inner in q_outer.get_subqueries_flat()]
    return subqueries_flat


@dataclass
class SubQuery:
    extension: extension.IqlExtension
    subquery: str
    name: str
    dataframe: Optional[pd.DataFrame] = field(default=None, init=False)
    options: Dict[str, object] = field(default_factory=dict, init=False)
    input_data: object = field(default=None, init=False)
    iqc: IqlQueryContainer

    local_dfs: Dict[str, object] = field(default_factory=dict, init=False)

    def get_subqueries_flat(self) -> Iterable[SubQuery]:
        return [self]

    def merge(self):
        # Nothing to do for a single subquery
        pass

    def get_cache_key(self) -> str:
        """Excludes paramquery and paramquerybatch and paramlist"""
        keypart1 = f"{self.extension.keyword}.{self.extension.subword}"

        if self.options is not None and len(self.options) > 0:
            options_clean = {
                k: v
                for k, v in self.options.items()
                if k != "paramquery" and k != "paramquerybatch" and k != "paramlist"
            }

            keypart2 = str(
                options_clean
            )  # to include any dynamic values, populated from paramquery and paramquerybatch
        else:
            keypart2 = ""

        cache_key = keypart1 + keypart2
        return cache_key

    def get_query(self) -> Optional[str]:
        """Returns the first parameter to:
        keyword(query, *params)"""
        if len(self.options) == 0:
            raise ValueError(f"Options not properly passed or parsed ({self.subquery})")

        value, query = next(iter(self.options.items()))

        if query is None:  # unnamed parameter
            return value
        else:
            return query  # type: ignore

    def __post_init__(self):
        try:
            if self.subquery is not None:
                self.options: Dict[str, object] = options_parser.options_to_list(self.subquery)
        except Exception as e:
            logger.exception("Exception in %.50s", self.subquery)
            raise ValueError(f"Parse Exception of {str(self.subquery)[:50]}") from e


@dataclass
class SubQueryGroup(SubQuery):
    """SubQueryGroups represent a set of queries whose outputs will be combined.
    SubQueries are executed in parallel (via get_subqueries_flat),
    so this step is needed to gather the results.

    Our first implementation was to rely on database Unions, but performance wasn't
    great.

    Future: SubQueryGroups could support nesting, only one level supported now."""

    subqueries: Iterable[SubQuery]

    def __post_init__(self):
        self.subquery = None  # type: ignore
        self.options = None  # type: ignore

    def get_subqueries_flat(self) -> Iterable[SubQuery]:
        return self.subqueries

    def get_query(self) -> None:
        raise NotImplementedError("SubQueryGroups do not have/need a query")

    def merge(self):
        """Doesn't handle mismatched schemas when merging parquet files."""
        if self.extension.use_path_replacement():
            files = [  # type: ignore
                self.extension.get_path_replacement(sq, quote=False) for sq in self.subqueries
            ]

            logger.debug("Merging %s parquet files: %s", len(files), files)

            tables = [pq.read_table(f) for f in files]
            logger.debug("Done reading, concatting")

            table = harmonize_and_concat_arrow_tables(tables)

            outfile = self.extension.get_path_replacement(self, quote=False)
            logger.debug("Writing to final parquet file: %s", outfile)

            pq.write_table(table, outfile)

        else:
            dfs: list[pd.DataFrame] = [sq.dataframe for sq in self.subqueries]  # type: ignore
            logger.debug("Concatting %s", len(dfs))
            if len(dfs) == 1:
                self.dataframe = dfs[0]
            else:
                arrow_tables = [df for df in dfs if isinstance(df, pa.Table)]

                if len(arrow_tables) == len(dfs):
                    # All arrow tables
                    logger.debug("Merging py arrow tables")
                    for df in dfs:
                        if df is not None:
                            logger.debug("Table len: %s", df.num_rows)
                    df_combined = harmonize_and_concat_arrow_tables(dfs)
                    logger.debug("Merged len: %s", len(df_combined))
                    self.dataframe = df_combined
                elif len(arrow_tables) == 0:
                    # All dataframes
                    self.dataframe = pd.concat(dfs)
                else:
                    logger.info("Mix of arrow & pandas, usually from cache hits + misses, converting all to pandas")

                    dataframes = [df.to_pandas() if isinstance(df, pa.Table) else df for df in dfs]
                    self.dataframe = pd.concat(dataframes)

        logger.debug("Done merging subqueries")


def harmonize_and_concat_arrow_tables(tables: Iterable):
    """Harmonize means: if the tables have columns with different dtypes, cast them to a String"""

    # Could also do a Count here, just counting the occurrences of columns, and if the dtypes differ, use a String
    columns = defaultdict(set)
    i = 0

    for t in tables:
        i += 1
        for c in t.schema.names:
            columns[c].add(t.column(c).type)

    if i == 0:
        raise ValueError("No tables passed")

    cast_columns = []
    for column, types in columns.items():
        # if there are multiple column types, ignore the null type
        if len(types) > 1 and len([t for t in types if not pa.types.is_null(t)]) > 1:
            cast_columns.append(column)

    new_tables = []
    for t in tables:
        for c in cast_columns:
            if c in t.schema.names:
                logger.debug("Harmonizing arrow table: Casting %s to string", c)

                idx = t.schema.get_field_index(c)
                t = t.set_column(idx, c, t.column(c).cast("string"))
        new_tables.append(t)

    combined_table = pa.concat_tables(new_tables, promote_options="default")
    return combined_table

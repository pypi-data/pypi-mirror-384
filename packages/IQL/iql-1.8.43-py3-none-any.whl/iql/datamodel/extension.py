import asyncio
import hashlib
import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Optional, Tuple, Union

from pandas import DataFrame

from .. import ql
from ..datamodel.cache import NoopSqCache, SqCache
from .querycontainer import IqlQueryContainer
from .result import IqlResultData
from .subquery import SubQuery, SubQueryGroup, get_subqueries_flat

logger = logging.getLogger(__name__)


@dataclass
class IqlExtension:
    keyword: str
    subword: str = field(default=None, init=True)  # type: ignore
    is_async: bool = False  # Determines whether executeimpl is implemented asynchronously
    cache: SqCache | None = field(default_factory=NoopSqCache, init=True)  # default is a NoopCache

    # Extensions must be parallelizable, or must
    # implement their own execute_batch.

    # Determines whether the local cache settings should be used
    # vs  CACHE_PERIOD and
    # USE_FILE_CACHE
    temp_file_directory: Optional[str] = field(default=None, init=False)
    param_replace_text: bool = field(
        default=True, init=False
    )  # determines whether paramquery/paramquerybatch will replace the query, or add parameters

    def get_output_dir(self) -> str:
        tempdir = self.temp_file_directory if self.temp_file_directory is not None else "./"
        return tempdir

    def use_path_replacement(self) -> bool:
        """Some extensions just return a filestring to use instead of the SubQuery, such as the
        S3 Extension. If execute() returns None, then use_path_replacement must be used.
        """
        return False

    def get_path_replacement(self, subquery: SubQuery, quote: bool = True) -> Optional[str]:
        """
        Returns a path to a file string that is readable by the underlying database: parquet or csv, most commonly.

        Quoting is done here, with the expectation that some path replacements might actually be function calls.
        """
        tempdir = self.get_output_dir()

        if subquery is None:  # subquery group
            prehash = "\n".join(sq.subquery for sq in subquery.subqueries)
            sq_hash = hashlib.sha256(prehash.encode()).hexdigest()
        else:
            if subquery.subquery is None:
                sq_str = ""
            else:
                sq_str = subquery.subquery
            sq_hash = hashlib.sha256(sq_str.encode()).hexdigest()

        filepath = f"{tempdir}/{subquery.name}_{sq_hash}.parquet"

        if quote:
            outpath = f"'{filepath}'"
        else:
            outpath = filepath

        logger.debug("Converted %s to %s", subquery, outpath)
        return outpath

    @abstractmethod
    def executeimpl(self, sq: SubQuery) -> Optional[DataFrame]:
        raise NotImplementedError("Not Implemented")

    async def executeasync(self, sq: SubQuery) -> Optional[DataFrame]:
        if sq.dataframe is not None:
            return sq.dataframe

        df = await self.executeimpl(sq=sq)

        sq.dataframe = df
        return df

    def execute(self, sq: SubQuery) -> Optional[DataFrame]:
        # usage: select * from (verityapi(functionname, targetname)) as verityquery
        # An empty response means no response was needed
        # Internal failure must raise an exception

        if sq.dataframe is not None:
            return sq.dataframe

        logger.debug("Executing query %s", sq.subquery)

        result_df = self.executeimpl(sq)

        if self.use_path_replacement():
            return None
        else:
            if result_df is None:
                raise ValueError("Unexpected empty result")

            pivot_options = sq.options.get("pivot")
            melt_options: dict = sq.options.get("melt")  # type: ignore
            result_df = self.apply_pandas_operations_prepivot(result_df, sq.options)

            if pivot_options is not None:
                result_df = self.pivot(result_df, pivot_options)  # type: ignore
            if melt_options is not None:
                result_df = result_df.melt(**melt_options)

            result_df = self.apply_pandas_operations_postpivot(result_df, sq.options)

            sq.dataframe = result_df

            return result_df

    def execute_batch(self, queries: Iterable[SubQuery]) -> Iterable[IqlResultData]:
        """This is a default implementation that executes each of the queries serially.

        Extensions may override this for cases that could be executed concurrently, such as BQL.

        """
        if self.is_async:
            # Execute as a batch
            # If run in Jupyter, needs nest_async to allow nested async.
            subqueries_flat = get_subqueries_flat(queries)

            logger.debug("Executing batch of %s queries", len(list(queries)))

            # Avoid any issue with nesting asyncio
            logger.info("Running in separate pool")

            async def _run_tasks(subqueries_flat):
                return await asyncio.gather(*(self.executeasync(sq) for sq in subqueries_flat))

            results = asyncio.run(_run_tasks(subqueries_flat))

            for sq, df in zip(subqueries_flat, results, strict=False):
                sq.dataframe = df
        else:
            # Execute serially
            # context = get_context('spawn')

            subqueries_flat = get_subqueries_flat(queries)

            # Executes the ungrouped queries
            for query in subqueries_flat:
                try:
                    self.execute(query)  # type: ignore
                except Exception as e:
                    logger.exception("Error in %s", query)
                    raise e

        # Merge the results
        completed_results = []

        for query in queries:
            # For single subqueries, this is a noop
            # For subquery groups, this merges the results of the children
            query.merge()

            if self.use_path_replacement():
                continue
            else:
                ir = IqlResultData(name=query.name, query=query.subquery, _data=query.dataframe)
                completed_results.append(ir)

        return completed_results

    def create_subquery(self, query: str, name: str, iqc: IqlQueryContainer) -> SubQuery:
        logger.debug("Creating subquery")
        sq = SubQuery(extension=self, subquery=query, name=name, iqc=iqc)
        return sq

    def update_replacement_values(self, replacement_values, parameter_name, parameter_values):
        if len(replacement_values) == 0:
            # If there was no paramquery or paramquery_batch, then this is just a paramlist
            for value in parameter_values:
                replacement_values.append({parameter_name: value})
        else:
            # We have some replacements already
            new_replacement_values = []
            for replacement_list in replacement_values:
                for value in parameter_values:
                    rl_copy = replacement_list.copy()

                    rl_copy[parameter_name] = value
                    new_replacement_values.append(rl_copy)
            replacement_values = new_replacement_values

        return replacement_values

    def create_subqueries(  # noqa: C901
        self,
        query: str,
        name: str,
        iqc: IqlQueryContainer,
        create_function: Optional[Callable] = None,
    ) -> Iterable[SubQuery]:
        """
        Implementation note:
        Current implementation requires the extension to "merge" the results, if there are multiple subqueries
        Previous implementation used a database union to let the db merge the results. This is still do-able, but

        Supports:
        - paramquery(parameter_name, query): Allows one or multiple parameter names to be replaced
        - paramquerybatch(parameter_name, query, max_batch_size): Only a single parameter_name is supported, default is
        unlimited max_batch_size -1
        - paramlist(parameter_name, parameter_values): Substitutes a fixed list of values into parameter_name
        """

        logger.info("Creating a subquery %.50s for %.50s", name, query)

        if create_function is None:
            create_function = self.create_subquery

        sq = create_function(query=query, name=name, iqc=iqc)

        # If a paramlist is passed, create one subquery for each value
        replacement_values: Iterable[Dict[str, object]] = []

        if "paramquerybatch" in sq.options:
            # paramquerybatch(targetfield, sourcequery, max_batch_size).
            # max_batch_size defaults to unlimited
            paramquery: Union[Tuple[str, str], Tuple[str, str, int]] = sq.options.get("paramquerybatch")  # type: ignore

            parameter_name = paramquery[0]
            param_query = paramquery[1]

            if len(paramquery) == 3:
                max_batch_size = paramquery[2]
            else:
                max_batch_size = -1

            param_query_batch_df = ql.execute(param_query, con=iqc.db._connection, substitutions=iqc.substitutions)  # type: ignore

            parameter_query_values: Iterable = param_query_batch_df[param_query_batch_df.columns[0]]  # type: ignore
            parameter_query_values = sorted(parameter_query_values)
            parameter_values = []
            if max_batch_size <= 0:
                parameter_values.append(parameter_query_values)  # type: ignore
            else:
                for i in range(0, len(parameter_query_values), max_batch_size):  # type: ignore
                    parameter_values.append(
                        parameter_query_values[i : i + max_batch_size]  # type: ignore
                    )
            parameter_values_list = [list(batch) for batch in parameter_values]  # type: ignore
            for param_value in parameter_values_list:
                replacement_values.append({parameter_name: param_value})

            logger.debug(
                "Max batch size is %s, Creating batches %s",
                max_batch_size,
                len(parameter_values),
            )
            logger.debug("Values: %s", parameter_values)

        if "paramquery" in sq.options:
            # Accepts:
            # parameter_name: Union[str, Iterable[str]]
            # query: str
            paramquery: Tuple[str, str] = sq.options.get("paramquery")  # type: ignore
            if len(paramquery) != 2:
                raise ValueError(f"A paramquery accepts exactly two parameters, yet {len(paramquery)} were passed")

            parameter_name = paramquery[0]
            param_query = paramquery[1]

            param_query_df: DataFrame = ql.executedf(
                param_query,
                con=iqc.db.get_connection(),
                substitutions=iqc.substitutions,
            )

            if isinstance(parameter_name, str):
                parameter_values = param_query_df[param_query_df.columns[0]]  # type: ignore
                replacement_values = self.update_replacement_values(
                    replacement_values, parameter_name, parameter_values
                )

            else:  # multiple parameters, so take the results sequentially from the df
                parameter_values = [
                    *param_query_df.itertuples(index=False, name=None)  # type: ignore
                ]
                for t in parameter_values:
                    row = {}
                    for i, name in enumerate(parameter_name):
                        row[name] = t[i]
                    replacement_values.append(row)

                logger.debug("replacement_values = %s", replacement_values)

        if "paramlist" in sq.options:
            logger.info("Doing paramlist")
            paramlist: Tuple[str, Iterable[str]] = sq.options.get("paramlist")  # type: ignore

            if len(paramlist) != 2:
                raise ValueError(f"A paramlist accepts exactly two parameters, yet {len(paramlist)} were passed")

            parameter_name = paramlist[0]
            parameter_values: Iterable[str] = paramlist[1]

            if not isinstance(parameter_values, Iterable):
                raise ValueError("A paramlist parameter_values must be an Iterable")

            logger.debug("Found paramlist: %s => %s", parameter_name, parameter_values)

            replacement_values = self.update_replacement_values(replacement_values, parameter_name, parameter_values)

            if parameter_values is None or len(parameter_values) == 0:
                raise ValueError("Empty values passed to paramlist passed")

        if len(replacement_values) > 0:
            sqs: Iterable[SubQuery] = []
            count = 1

            # Some extensions, like bql, use string replacement.
            # Others, like blpapi, use named parameters
            replace_text = sq.extension.param_replace_text

            for replacements in replacement_values:
                v_query = query

                # strip off any parameters
                new_options = {}
                for parameter_name, parameter_value in replacements.items():
                    if replace_text:
                        if isinstance(parameter_value, list):
                            parameter_value = ",".join([f"'{v}'" for v in parameter_value])
                        if not parameter_name.startswith("$"):
                            parameter_name = f"${parameter_name}"
                        v_query = v_query.replace(parameter_name, str(parameter_value))
                    else:
                        new_options[parameter_name] = parameter_value
                newsq = create_function(  # type: ignore
                    query=v_query, name=f"{name}_{count}", iqc=iqc
                )

                newsq.options.update(new_options)
                sqs.append(newsq)
                count += 1

            sqname = name.replace("$", "")  # safeguard if user inserts the optional $ prefix

            if len(sqs) == 1:
                return sqs  # Don't need a subquery group if it's just one value
            else:
                sq_group = SubQueryGroup(
                    subqueries=sqs,
                    extension=self,
                    subquery=sqname,  # subqueries are ignored for subquerygroups
                    name=f"{sqname}_group",
                    iqc=iqc,
                )

                logger.debug("sq_group=%s", sq_group)
                return [sq_group]
        else:
            return [sq]

    def fix_col_ref(self, opt: str, columns: Iterable[str]):
        if opt in columns:
            return opt
        opt_l = opt.lower().strip()
        opt_ci = next((c for c in columns if c.lower() == opt_l), None)

        if opt_ci is None:
            raise ValueError(f"{opt} not in columns: {columns}")

        return opt_ci

    def apply_pandas_operations_postpivot(self, working_df, options: Dict[str, object]) -> DataFrame:
        fillna_opt: str = options.get("fillna")  # type: ignore
        if fillna_opt is not None:
            working_df = working_df.fillna(fillna_opt)

        dropna_opt = options.get("dropna")
        if isinstance(dropna_opt, bool) and dropna_opt is True:
            working_df = working_df.dropna()
        elif isinstance(dropna_opt, str):
            working_df = working_df.dropna(subset=[dropna_opt])
        elif isinstance(dropna_opt, list):
            working_df = working_df.dropna(subset=dropna_opt)

        if "ewma" in options:
            ewma_opts: Iterable[Tuple[str, str, dict[str, object]]] = options.get("ewma")  # type: ignore

            for ewma_opt in ewma_opts:
                src, dest, options = ewma_opt
                working_df[dest] = working_df[src].ewm(**options).mean()

        return working_df

    def apply_pandas_operations_prepivot(self, working_df, options: Dict[str, object]) -> DataFrame:
        addcols_opt: Iterable[str] = options.get("addcols_pre")  # type: ignore
        if addcols_opt is not None:
            if isinstance(addcols_opt, str):
                addcols_opt = [addcols_opt]
            for col in addcols_opt:
                if col not in working_df:
                    logger.debug("Adding additional columns (before pivoting): %s", col)
                    working_df[col] = None

        # only drops from the "value" column
        fillna_opt: str = options.get("fillna_pre")  # type: ignore
        if fillna_opt is not None:
            logger.debug("Filling NaNs with in value column with %s", fillna_opt)
            working_df["value"] = working_df["value"].fillna(fillna_opt)

        dropna_opt = options.get("dropna_pre")
        logger.debug("Dropping NA from column %s", dropna_opt)
        if isinstance(dropna_opt, bool) and dropna_opt is True:
            working_df = working_df.dropna()
        elif isinstance(dropna_opt, str):
            working_df = working_df.dropna(subset=[dropna_opt])
        elif isinstance(dropna_opt, list):
            working_df = working_df.dropna(subset=dropna_opt)

        return working_df

    def pivot(self, working_df: DataFrame, pivot_option: Iterable[str]) -> DataFrame:  # noqa: C901
        if pivot_option is None:
            return working_df

        pivot_option = list(pivot_option)

        logger.debug("Pivoting by %s", pivot_option)
        if len(pivot_option) != 2 and len(pivot_option) != 3:
            raise ValueError(f"Unexpected size for pivot options {pivot_option}")
        else:
            index = pivot_option[0]
            column = pivot_option[1]
            value = pivot_option[2] if len(pivot_option) == 3 else "value"

            if index == "auto":
                if isinstance(column, str):
                    used_cols = [column.lower()]
                else:
                    used_cols = list(column)

                if isinstance(value, str):
                    used_cols.append(value.lower())
                else:
                    used_cols = used_cols + value

                # Use all columns except used_cols
                index = [col for col in working_df.columns if col.lower() not in used_cols]
        cols: Iterable[str] = list(working_df.columns)  # type: ignore

        if isinstance(index, list):
            index = [self.fix_col_ref(i, cols) for i in index]
            if len(index) == 1:
                index = index[0]
        else:
            index = self.fix_col_ref(index, cols)

        if isinstance(column, list):
            column = [self.fix_col_ref(i, cols) for i in column]
            if len(column) == 1:
                column = column[0]
        else:
            column = self.fix_col_ref(column, cols)

        if value == "bqlvalue":
            # Special case
            pass

        elif isinstance(value, list):
            value = [self.fix_col_ref(i, cols) for i in value]
            if len(value) == 1:
                value = value[0]
        else:
            value = self.fix_col_ref(value, cols)

        # Disabling: Unsure how this is reached
        # if isinstance(column, list):
        #    for col in column:
        #        if pd.api.types.is_datetime64_any_dtype(working_df[col]):
        #            working_df[col] = working_df[col].dt.strftime("%Y-%m-%d")

        logger.debug("Pivot index %s columns %s values %s", index, column, value)

        if value == "bqlvalue":
            value = [c for c in working_df.columns if c.startswith("value_")]
            # adding value would result in multiples
            # #value.append("value")
            skip_flatten_use_second_row_only = True
            aggfunc = "first"  # use the first column in the value list
            logger.debug("Using first value from %s for pivot", value)
            dropna = True
            reset_first = False
        else:
            aggfunc = "last"
            skip_flatten_use_second_row_only = False
            dropna = False
            reset_first = True

        # figure out what columns *should* show up, in case they get dropped if all NA
        # The problem is: pivot_table will add dummy rows for every index permutation,
        # so dropna is needed... but this may drop some valid columns
        if isinstance(column, str):
            all_columns = list(working_df[column].unique())
        else:
            all_columns = list()

        working_df = working_df.pivot_table(index=index, columns=column, values=value, aggfunc=aggfunc, dropna=dropna)

        if reset_first:
            working_df = working_df.reset_index()

        if skip_flatten_use_second_row_only:
            working_df.columns = [col[1] for col in working_df.columns]
            working_df = working_df.reset_index()

        elif isinstance(value, list) and len(value) > 1:
            working_df.columns = [
                "_".join(reversed(str(col) if isinstance(col, int) else col)) for col in working_df.columns
            ]
        elif isinstance(column, list) and len(column) > 1:
            # Flatten multicolumn indices
            working_df.columns = ["_".join(str(col) if isinstance(col, int) else col) for col in working_df.columns]

        # Reinsert any dropped all NA columns
        for col in working_df.columns:
            if col not in all_columns:
                all_columns.append(col)

        working_df = working_df.reindex(columns=all_columns, fill_value=None)

        # Clean columns
        renames = {}
        for col in working_df.columns:
            # assert isinstance(col, str)
            colname = col
            newcol = str(colname).replace("#", "").replace("(", "").replace(")", "").replace(" ", "_")
            newcol = newcol.strip("_")
            if col != newcol:
                # columns can't have #, ( or ) symbols
                renames[col] = newcol

        if len(renames) > 0:
            working_df = working_df.rename(columns=renames)

        return working_df

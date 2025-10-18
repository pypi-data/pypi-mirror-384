"""This module wraps the Bloomberg BQL API to provide
consistent return results"""

import logging
import re
import time
from abc import abstractmethod
from collections import Counter, defaultdict
from functools import partial
from typing import Dict, Iterable, Optional, Union

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pandas import DataFrame

from ...datamodel.cache import SqCache
from ...datamodel.subquery import harmonize_and_concat_arrow_tables

# Pandas concat allows differing schemas. Pyarrow concat requires harmonizing first
USE_ARROW_DTYPES = False  # experimental

_MAX_CONCURRENT = 128

logger = logging.getLogger(__name__)

_merge_value_col = True


class BaseBqlQuery:
    STATUS_NOTRUN = "NOTRUN"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILURE = "FAILURE"

    execution_status: str = STATUS_NOTRUN
    exception_msg: Optional[str] = None
    _data: Optional[Iterable[Dict[str, object]]] = None
    _df: Optional[DataFrame] = None
    _output_filename: Optional[str] = None  # Used for large queries where we don't want to hold it all in memory

    params = None

    @abstractmethod
    def get_fields(self) -> Iterable[str]:
        pass

    @abstractmethod
    def to_bql_query(self) -> str:
        pass

    def execute(self) -> bool:
        """Executes the query and, if successful, sets the query._data"""
        self._populate_data()
        return self.execution_status == self.STATUS_COMPLETED

        # All exceptions should be well handled
        # except Exception as e:
        #    logger.exception("execute")
        #    self.execution_status = self.STATUS_FAILURE
        #    self.exception_msg = str(e)
        #    return False

    def to_data(self) -> Union[DataFrame, Iterable[Dict[str, object]]]:
        """Internal representation"""
        if self._data is not None:
            return self._data
        else:
            success = self.execute()
            if success and self._data is not None:
                return self._data
            elif success and self._df is not None:
                return self._df
            else:
                raise ValueError("Failure executing BQL query")

    def to_df(self) -> DataFrame:
        if self._df is None:
            self._df = DataFrame(self._data)
        return self._df

    def _populate_data(self):
        execute_bql_str_list_async_q([self])


def list_to_str(values: Iterable, quote: bool = False, delimiter: str = ", \n") -> str:
    """Helper to convert list of values to a comma delimited list. Used for BQL functions.
    Equity lists should be quoted"""

    if quote:
        return delimiter.join(f"'{val}'" for val in values)
    else:
        return delimiter.join(values)


def security_to_finalstr(security: Union[str, Iterable]) -> str:
    if isinstance(security, str) and ("(" in security or "[" in security or "$" in security):
        final_security_str = security
    elif isinstance(security, str):
        if "'" not in security:
            security = "'" + security + "'"
        final_security_str = "[" + security + "]"
    else:  # Iterable
        final_security_str = list_to_str(security, True)
        final_security_str = "[" + final_security_str + "]"

    return final_security_str


def construct_bql_query(
    field_str: Union[str, Iterable],
    security: Union[Iterable[str], str],
    with_params: Optional[str] = None,
    let_vars: Optional[str] = None,
) -> str:
    """Simple wrapper to construct a valid BQL query string from an
    already comma delimited list of fields and quoted securities"""

    # Better to use BQLQuery, but leaving this for now.

    if isinstance(field_str, str):
        field_str = [field_str]

    field_str = list_to_str(field_str, False)

    final_security_str = security_to_finalstr(security)

    request_str = ""
    if let_vars is not None:
        request_str += "let (" + let_vars + ")"

    request_str += "get("
    request_str += field_str

    request_str += ") for (" + final_security_str + ")"

    # default WITH clause
    # TODO: Replace this with something metadata driven, since it may not be applicable in all cases
    # request_str += "\nwith (fill=prev)"

    if with_params is not None:
        request_str += " with (" + with_params + ")"

    if "preferences" not in request_str:
        request_str += "\npreferences (addcols=all)"

    return request_str


def bql_exception_to_str(e) -> object:
    try:
        e = e[1]
        long_error = {
            "message": str(e.exception_messages),
            "request_id": str(e._request_id),
            "details": str(e.internal_messages),
        }
        return long_error
    except Exception:
        return str(e)


def error_callback(o, errorlist=None):
    if errorlist is None:
        logger.warning(o)
        return

    msg = bql_exception_to_str(o)
    errorlist.append(msg)


def execute_bql_str_list_async_q(
    queries_input: Iterable[BaseBqlQuery],
    suppress_warning_log: bool = False,
    max_queries: int = _MAX_CONCURRENT,
    allow_async: bool = True,
    cache: SqCache | None = None,
):
    """Note: Not multi-process safe due to underlying BQL APIs
    and (presumably) its use a Singleton for bqapi requests.
    Either batch requests through a single requester thread, or
    distribute workload across requesters.
    """
    logger.debug("Checking to see if any are already cached")

    for q in queries_input:
        qstr = q.to_bql_query()
        data = None if cache is None else cache.get(qstr)
        if data is not None:
            logger.debug("Found in cache: %s", qstr)

            if isinstance(data, DataFrame):
                q._df = data
            else:
                q._data = data  # type: ignore
            q.execution_status = q.STATUS_COMPLETED

    queries_not_cached = [q for q in queries_input if q._data is None and q._df is None]

    # Max Queries indicates the max per batch: chop the queries
    # into smaller groups of max_queries size and execute each serially

    if len(queries_not_cached) == 0:
        logger.debug("No queries to run")
        return

    query_groups = [
        queries_not_cached[i * max_queries : (i + 1) * max_queries]
        for i in range((len(queries_not_cached) + max_queries - 1) // max_queries)
    ]

    start = time.time()

    count = 1
    for query_group in query_groups:
        logger.debug(
            "Executing %s of %s query batches with %s queries",
            count,
            len(query_groups),
            len(query_group),
        )
        count = count + 1

        # t1 = threading.Thread(target=asyncio.run, args=(_execute_bql_str_list_async_callbacks(query_group, suppress_warning_log),))
        # t1.start()
        # t1.join

        logger.debug("Done async with callbacks")
        _execute_bql_str_list_async_orig(query_group, suppress_warning_log, allow_async=allow_async)

    end = time.time()
    logger.debug("Elapsed time running queries: %s seconds", round(end - start))

    for q in queries_not_cached:
        if q._data is not None and cache is not None:
            logger.debug("Saving to cache")

            cache.save(q.to_bql_query(), q.to_df(), cost=None)

    return


def is_bquant():
    return False  # os.environ.get("BQUANT_USERNAME") is not None


def _execute_bql_str_list_async_orig(
    queries: Iterable[BaseBqlQuery],
    suppress_warning_log: bool = False,
    allow_async: bool = True,
):
    from . import (
        bql_service,
    )

    with bql_service.BQL_LOCK:
        query_strings = [query.to_bql_query() for query in queries]

        bq_service = bql_service.get_bqservice()

        # TODO: Out of order errors are not handled here. Not an issue in many cases
        # but is still very likely.
        errorlist: Iterable[str] = []

        try:
            if is_bquant() and allow_async:
                logger.debug("Using submit fetch many")

                gen = bq_service._submit_fetch_many(
                    query_strings,
                    on_request_error=partial(error_callback, errorlist=errorlist),
                    num_retries=1,
                )
            else:
                gen = bq_service.execute_many(
                    query_strings,
                    on_request_error=partial(error_callback, errorlist=errorlist),
                )
        except Exception as e:
            logger.exception(bql_exception_to_str(e))
            raise ValueError(f"Error submitting {query_strings}") from e

        error_index = 0

        logger.info("Waiting for and processing BQL results")

        for r, q in zip(gen, queries, strict=False):
            try:
                logger.info("Processing request")
                if r is None:
                    q.execution_status = q.STATUS_FAILURE
                    logger.warning("Error executing: %s", q.to_bql_query())
                    q.exception_msg = errorlist[error_index]
                    error_index = error_index + 1
                else:
                    if q._output_filename is not None:
                        result_table: pa.Table = _to_data_arrow(r, return_pandas=False)  # type: ignore
                        logger.info("Writing result to parquet: %s", q._output_filename)
                        pq.write_table(result_table, q._output_filename)
                    else:
                        result_table: DataFrame = _to_data_arrow(r, return_pandas=True)
                        q._df = result_table
                        q._data = result_table  # type: ignore

                    q.execution_status = q.STATUS_COMPLETED
                logger.info("Done processing request")

            except Exception as e:
                logger.exception("Query error")
                q._data = None
                q.execution_status = q.STATUS_FAILURE
                q.exception_msg = bql_exception_to_str(e)  # type: ignore
        logger.debug("Done executing")


def _process_single_item_response_arrow(response, results: Iterable[pa.Table]):  # noqa: C901
    d = response._SingleItemResponse__result_dict

    if len(d["responseExceptions"]) > 0:
        for r in d["responseExceptions"]:
            if r["type"] != "BENIGN":
                raise ValueError(f"{response.name=} {d['responseExceptions']=}")
            else:
                logger.debug("Benign BQL Exception: %s", r)
    try:
        logger.debug("Arrow processing %s", d["name"])  # {d}

        ids = d["idColumn"]
        vcol = ids
        dcol = d["valuesColumn"]
        acol = d["secondaryColumns"]

        cols = [vcol, dcol, *acol]
        data = {col["name"].lower(): col["values"] for col in cols}
        data["name"] = d["name"]

        if dcol["name"].lower() != "value":
            # if the data/value field is not named "value", rename it
            logger.debug("Changing %s to value", dcol["name"])
            dcol["name"] = "value"

        foundcols = set()
        foundcols.add("name")

        def replace_cols(c, type: str) -> str:
            colname = c["name"].lower()
            i = 0
            newcol = colname
            while newcol in foundcols:
                i += 1
                newcol = f"{colname}_{i}"
            if newcol != colname:
                logger.debug("Rewrote %s to %s", colname, newcol)

            if newcol == "value":
                value_field = f"value_{type}"
                newcol = value_field

            foundcols.add(newcol)
            return newcol

        fields = [
            (
                pa.field(replace_cols(col, "str"), pa.string())
                if col["type"] == "STRING" or col["type"] == "ENUM"
                else (
                    pa.field(replace_cols(col, "date"), pa.timestamp("ms"))
                    if col["type"] == "DATE"
                    else (
                        pa.field(replace_cols(col, "float"), pa.float64())
                        if col["type"] == "FLOAT" or col["type"] == "DOUBLE"
                        else pa.field(replace_cols(col, "int"), pa.int64())
                    )
                )
            )
            for col in cols
        ]

        arrays = [
            # pa.array([str(val) for val in col["values"]])
            # if col["type"] == "STRING"
            # else
            pa.array(
                [
                    (
                        val
                        if val != "NaN"
                        and val != "NaT"
                        and not pd.isna(val)
                        and val != "Infinity"
                        and val != "-Infinity"
                        else None
                    )
                    for val in col["values"]
                ]
            )
            for col in cols
        ]

        for i, c in enumerate(cols):
            if c["type"] == "DATE":
                arrays[i] = arrays[i].cast(pa.timestamp("ms", tz="UTC"))

        name = d["name"].lower()
        if name[0] == "#":  # strip the leading # from aliases
            name = name[1:]

        namearray = [name] * len(arrays[0])

        arrays.append(pa.array(namearray))
        fields.append(pa.field("name", pa.string()))

        # make a copy of the value field, so we'll have value and value_int, for instance
        if _merge_value_col:
            value_idx = 1
            f = fields[value_idx]
            fields.append(pa.field("value", f.type))
            arrays.append(arrays[value_idx])

        table = pa.Table.from_arrays(arrays, schema=pa.schema(fields))

        results.append(table)  # TODO: Research switching to types_mapper=pd.ArrowDtype
    except Exception as e:
        logger.exception(d)
        raise ValueError(f"Error processing SIR {d['name']}") from e


def _process_response_arrow(response, results):  # type: ignore
    for res in response._sirs:
        if not hasattr(res, "_SingleItemResponse__result_dict"):
            raise ValueError("Response element does not have a _SingleItemResponse__result_dict")
        _process_single_item_response_arrow(res, results)  # type: ignore

    # This small set = None avoids a circular reference that was pinning memory consumption for very large queries.
    response._sirs = None


def _to_data_nonarrow_execute_response(response) -> pa.Table:  # type: ignore
    """Converts BQL Response to a List of Dicts, where each dict contains Col: Value"""
    result_table: Iterable[pa.Table] = []

    _process_response_arrow(response, result_table)

    logger.debug("Done processing, %s tables", len(result_table))

    final_table = harmonize_and_concat_arrow_tables(result_table)

    # if as_arrow:
    return final_table
    # else:
    #     if USE_ARROW_DTYPES:
    #         return final_table.to_pandas(types_mapper=pd.ArrowDtype)
    #     else:  # numpy dtypes / default
    #         return final_table.to_pandas()


def handle_duplicate_cols(table: pa.Table) -> pa.Table:
    if len(set(table.schema.names)) < len(table.schema.names):
        names = table.schema.names
        counts = Counter()
        new_names = []
        for name in names:
            if counts[name]:
                new_names.append(f"{name}_{counts[name]}")
            else:
                new_names.append(name)
            counts[name] += 1
        table = table.rename_columns(new_names)

    return table


def fix_suffixes(all_cols):
    col_renamed = defaultdict(list)
    new_cols = {}
    for origcol in all_cols:
        col = origcol.lower()
        match = re.fullmatch(r"(.*?):(\d+)", col)
        if match:
            before, after = match.groups()
            col_renamed[before].append(int(after))
        else:
            before = col
            col_renamed[before].append(None)

        if before in new_cols.values():
            index = len(col_renamed[before]) - 1
            new_cols[origcol] = f"{before}_{index}"
        else:
            new_cols[origcol] = before
    return new_cols


def transform_table(item: "bqle.request.execute_response_handler._BQLItem") -> pa.Table:  # type: ignore  # noqa: F821, C901
    if item.table is None:
        return None

    table = item.table

    table = handle_duplicate_cols(table)

    if len(item.value_column_index) != 1:
        raise ValueError("Unexpected {item.value_column_index=}")

    coldesc = item.columns[item.value_column_index[0]]  # next(cd for cd in item.columns if cd.name=="VALUE")

    if coldesc.data_type.name == "DOUBLE":
        copy_col = "value_float"
    elif coldesc.data_type.name == "DATE":
        copy_col = "value_date"
    elif coldesc.data_type.name == "STRING":
        copy_col = "value_string"
    else:
        logger.debug("Other data type: %s", coldesc.data_type)
        suffix = coldesc.data_type.name.lower()
        copy_col = f"value_{suffix}"

    # Make every date a timestamp('ms')
    for i, field in enumerate(table.schema):
        if pa.types.is_date32(field.type):
            table = table.set_column(i, field.name, table.column(i).cast(pa.timestamp("ms")))

    if copy_col is not None:
        table = table.append_column(copy_col, table[coldesc.name])

    if coldesc.name != "VALUE":
        table = table.append_column("value", table[coldesc.name])

    column_newnames = fix_suffixes(table.schema.names)  ## {name: fix_col(name) for name in table.schema.names}
    # print(column_newnames)
    if "NAME" in column_newnames:
        # rename NAME column to name_1, if it exists
        i = 1
        while f"name_{i}" in column_newnames.values():
            i += 1

        column_newnames["NAME"] = f"name_{i}"

    table = table.rename_columns(list(column_newnames.values()))
    colname = (item.name[1:] if item.name.startswith("#") else item.name).lower()

    table = table.append_column("name", pa.array([colname] * len(table)))

    return table


def _to_data_arrow_execute_response(response) -> pa.Table:
    failed = False
    tables = []
    for sir in response._sirs:
        if sir._bql_item.table is not None:
            transformed_table = transform_table(sir._bql_item)
            tables.append(transformed_table)
        else:
            tables.append(pa.table({"name": [], "id": []}))

        for e in sir._bql_item.errors:
            if e["code"].startswith("BENIGN"):
                logger.debug("Item %s failed with %s, BENIGN: continuing", sir._bql_item.name, sir._bql_item.errors)
            else:
                logger.info("Item %s failed with %s, FAILED", sir._bql_item.name, sir._bql_item.errors)

                failed = True

    # failed = any(sir._bql_item.failed for sir in response._sirs)

    # tables = [transform_table(sir._bql_item) for sir in response._sirs]

    response._sirs = None  # Might be unnecessary, but was used to avoid circular references in the pre-Arrow sirs

    if failed:
        raise ValueError("Query failed, {tables=}")

    return harmonize_and_concat_arrow_tables(tables)


def _process_arrow_single_item_response_arrow(
    sir: "bqle.common.arrow_execute_response.ArrowExecuteSingleItemResponse",  # type: ignore # noqa: C901, F821
    results: Iterable[pa.Table],
):
    if len(sir._bql_item.errors) > 0:
        raise ValueError("Errors in _bql_item: sir._bql_item.errors=}")


def _to_data_arrow(response, return_pandas: bool = True) -> DataFrame:  # type: ignore
    if type(response).__name__ == "ArrowExecuteResponse":
        table = _to_data_arrow_execute_response(response)
    else:
        table = _to_data_nonarrow_execute_response(response)

    if return_pandas:
        return table.to_pandas()
    else:
        return table

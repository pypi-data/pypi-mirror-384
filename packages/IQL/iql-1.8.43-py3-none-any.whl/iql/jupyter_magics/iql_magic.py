import argparse
import inspect
import logging
import re
from typing import Iterable, Optional

from IPython.core.getipython import get_ipython

from .. import ql

try:
    from jinja2 import Template
except Exception:  # noqa
    # Nothing to do, jinja2 is optional
    # User will get an error when using -j
    pass

from duckdb import DuckDBPyConnection
from IPython.core.magic import (
    Magics,
    cell_magic,
    line_magic,
    magics_class,
    needs_local_scope,
    no_var_expand,
)
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from traitlets.config.configurable import Configurable

logger = logging.getLogger(__name__)

CONNECTION: Optional[DuckDBPyConnection] = None


def _get_obj_from_name(name: str) -> Optional[object]:
    ip = get_ipython()
    return ip.ev(name) if ip is not None else None


def execute_iql(
    query_string: str,
    connection: Optional[DuckDBPyConnection],
    export_function: Optional[str] = None,
    query_params: Optional[Iterable] = None,
):
    # Pop back to the calling frame: this is 3 backs in ipython.
    # Why? https://github.com/duckdb/duckdb/pull/12425
    # TODO: Add option to disable
    context = inspect.currentframe().f_back.f_back.f_back.f_locals  # type: ignore
    return ql.execute(query_string, connection, parameters=query_params, context=context, autocontext=False)


@magics_class
class IqlMagic(Magics, Configurable):
    # database connection object
    # created via -d (default), -cn (connection string) or -co (connection object)

    # selected via -t. None = Pandas.
    export_function = None
    shell = None

    def __init__(self, shell):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add ourself to the list of module configurable via %config
        self.shell.configurables.append(self)  # type: ignore

    def connect_by_objectname(self, connection_object):
        con: DuckDBPyConnection = _get_obj_from_name(connection_object)  # type: ignore
        if not isinstance(con, DuckDBPyConnection):
            raise ValueError(f"{connection_object} is not a DuckDBPyConnection")
        logger.debug("Using existing connection: %s", connection_object)

        global CONNECTION
        CONNECTION = con

    @no_var_expand
    @needs_local_scope
    @line_magic("iql")
    @cell_magic("iql")
    @line_magic("bql")
    @cell_magic("bql")
    @magic_arguments()
    @argument(
        "-co",
        "--connection_object",
        help="Connect to a database using the connection object",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-t",
        "--type",
        help="Set the default output type",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-o",
        "--output",
        help="Write the output to the specified variable",
        nargs=1,
        type=str,
        action="store",
    )
    @argument(
        "-q",
        "--quiet",
        help="Don't return an object, similar to %%capture",
        action="store_true",
    )
    @argument("-j", "--jinja2", help="Apply Jinja2 Template", action="store_true")
    @argument(
        "-s",
        "--substitute",
        nargs=1,
        type=str,
        action="store",
        help="Substitute Variables using a Dictionary",
    )
    @argument(
        "-p",
        "--param",
        dest="queryparams",
        help="Params from user_ns",
        action="append",
    )
    @argument(
        "--ext",
        dest="extension",
        nargs=1,
        type=str,
        action="store",
        help="Wrap all commands in extension",
    )
    @argument("rest", nargs=argparse.REMAINDER)
    def execute(self, line: str = "", cell: str = "", local_ns=None):  # noqa: C901
        global CONNECTION

        args = parse_argstring(self.execute, line)
        # Grab rest of line
        rest = " ".join(args.rest)
        query = f"{rest}\n{cell}".strip()

        logger.debug("Query = %s", query)

        if args.substitute:
            substitutions = self.shell.user_ns[args.substitute[0]]
            for k, v in substitutions.items():
                query = query.replace(k, str(v))

        if args.jinja2:  # Replace any {var}'s with the string values
            query = Template(query).render(self.shell.user_ns)  # type: ignore

        # Strip any DBT "{{ref('table')}}"
        query = re.sub(r"{{\s*ref\(['\"](.*?)['\"]\)\s*}}", r"\1", query)

        if args.connection_object:
            self.connect_by_objectname(args.connection_object[0])

        if args.queryparams:
            query_params = [self.shell.user_ns[p] for p in args.queryparams]
        else:
            query_params = None

        if query is None or len(query) == 0:
            logger.debug("Nothing to execute")
            return

        # DBT Jinja References
        # Replace any jinja tables / refs {{ref ('nc_sapi')}} for instance
        query = re.sub(r"\{\{\s*ref\s*\(\s*'([^']+)'\s*\)\s*\}\}", r"\1", query)

        if args.extension:
            extension = args.extension[0]
            logger.debug("Wrapping query with extension %s", extension)
            query = f'''{extension}(""" \n {query} \n""")'''

        o = execute_iql(
            query_string=query,
            connection=CONNECTION,
            export_function=self.export_function,
            query_params=query_params,
        )

        if args.type:
            if args.type[0] == "markdown":
                print(o.to_markdown())  # type: ignore  # noqa
                return None

        if args.output:
            self.shell.user_ns[args.output[0]] = o  # type: ignore

        if args.quiet:
            return None
        else:
            return o


def init_completers(ip):
    try:
        logger.info("Initializating autocompleter")
        from .autocompletion_v2 import init_completer

        init_completer(ipython=ip)
    except Exception:
        logger.debug("Unable to initialize autocompletion_v2. iPython 8.6.0+ is required. Trying v1 completer")
        try:
            from .autocompletion_v2 import init_completer

            init_completer(ipython=ip)
        except Exception:
            logger.debug("Unable to initialize autocompletion_v1")

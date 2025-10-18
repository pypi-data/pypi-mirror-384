# Autocompletion using the Autocompletion V2: introduced in Ipython 8.6.0


import logging
import re

import sqlparse
from IPython.core.completer import (
    Completion,
    CompletionContext,
    IPCompleter,
    SimpleCompletion,
    SimpleMatcherResult,
    context_matcher,
)

from .. import ql
from .autocomplete_settings import (
    get_column_names,
    get_function_names,
    get_table_names,
    pragma_phrases,
    sql_expects_tablename,
    sql_phrases,
)

logger = logging.getLogger(__name__)

pragma_before = re.compile(r"(?si).*pragma\s*")


def get_aliases(sql: str) -> dict:
    stmt = sqlparse.parse(sql)[0]

    aliases = {
        token.get_alias(): token.get_real_name() for token in stmt.tokens if isinstance(token, sqlparse.sql.Identifier)
    }
    return aliases


class IqlCustomCompleter(IPCompleter):
    def __init__(self, *args, **kwargs):
        self.ipython = kwargs.get("shell")
        super().__init__(*args, **kwargs)

    all_phrases = sql_expects_tablename + sql_phrases + pragma_phrases
    lastword_pat = re.compile(r"(?si)(^|.*[\s])(\S+)\.")
    expects_table_pat = re.compile(r"(?si).*from")

    def convert_to_return(self, cursor_pos, completions: list[str], matched_fragment: str) -> SimpleMatcherResult:
        simple_completions = [
            SimpleCompletion(text=t, type="duckdb") for t in completions if t.startswith(matched_fragment)
        ]

        # It took way too many hours to figure out that matched_fragment="" was needed here
        # Otherwise the results get suppressed

        r = SimpleMatcherResult(
            completions=simple_completions,
            suppress=True,
            matched_fragment=matched_fragment,
            ordered=True,
        )

        return r

    def line_completer_inner(self, event: CompletionContext) -> SimpleMatcherResult:
        # if not %dql, returns nothing
        # if ends with a sql_expects_tablename phrase, then returns just table names
        # if ends in a period, checks to see if prefix is a tablename, and if so, returns column names
        # otherwise returns all sql phrases and tablenames
        # https://github.com/ipython/ipython/blob/a418f38c4f96de1755701041fe5d8deffbf906db/IPython/core/completer.py#L563

        cursor_pos = event.cursor_position
        try:
            logger.debug("%s, %s, %s", type(event), self.ipython, event)

            if hasattr(event, "full_text"):
                text = event.full_text
            else:
                logger.debug("No full_text, nothing to do %s", event)
                return self.convert_to_return(cursor_pos=cursor_pos, completions=[], matched_fragment="")

            if not text.startswith("%iql") and not text.startswith("%%iql"):
                return self.convert_to_return(cursor_pos=cursor_pos, completions=[], matched_fragment="")

            if hasattr(event, "token"):
                token = event.token
            else:
                token = ""

            prev_char_pos = event.cursor_position - len(token) - 1
            prev_char = event.line_with_cursor[prev_char_pos] if prev_char_pos < len(event.line_with_cursor) else None
            line_after = text[4:].strip()

            logger.debug("%s: %s", event, type(event))

            if token is not None and token.endswith("."):
                # VScode is ignoring or suppressing completions after a period.
                # get the word preceding the period
                tablename = token[:-1]

                # TODO: Deal with Aliases and SubQueries (xyz as abc)
                tablename = get_aliases(event.full_text).get(tablename, tablename)
                logger.debug(tablename)

                columns = get_column_names(self.ipython, tablename)
                logger.debug("Using columns: %s", columns)
                return self.convert_to_return(cursor_pos=cursor_pos, completions=columns, matched_fragment="")
            elif token is not None and prev_char == "$":
                logger.debug("Handling substitutions")
                substitutions = list(ql._SUBSTITUTIONS.keys())

                return self.convert_to_return(
                    cursor_pos=cursor_pos, completions=substitutions, matched_fragment=event.token
                )

            # if the last phrase should be followed by a table name, return the list of tables
            elif self.expects_table_pat.match(line_after) is not None:
                names = get_table_names(self.ipython)
                if len(names) == 0:
                    names = ["No Tables or DataFrames Found"]
                logger.debug("Expects table name, returning: %s", names)
                return self.convert_to_return(cursor_pos=cursor_pos, completions=names, matched_fragment=event.token)
            else:
                # default: return all phrases and tablenames
                allp = self.all_phrases + get_table_names(self.ipython) + get_function_names(self.ipython, event.token)
                return self.convert_to_return(cursor_pos=cursor_pos, completions=allp, matched_fragment=event.token)

        except Exception:
            logger.exception("Error completing %s", event)
            return self.convert_to_return(cursor_pos=cursor_pos, completions=[], matched_fragment="")

    @context_matcher()  # type: ignore
    def line_completer(self, event: CompletionContext) -> list[Completion]:
        result = self.line_completer_inner(event=event)
        logger.debug("Result from completion %s", result)
        return result


def init_completer(ip):
    iql_completer = IqlCustomCompleter(shell=ip, greedy=True)
    # Development notes:
    # This took a while to figure out, partially because of the multiple APIs and signatures involved.
    #
    # What I learned:
    # The ipython (get_ipython) environment has a Completer object
    # Completer is an IPCompleter
    # You can extend this completer in several ways, including:
    # - Wrapping it
    # - Registering a custom_completer, of which there are several ways: add_hook, Completer.custom_completers.add_s and add_re, or customer_completers.insert
    #
    # ipython 8.6.0 introduced new a v2 version of the API, for completers decorated with @context_matcher(), this API uses a different signature
    # see ipython.core.completer for more info
    # The main advantage of v2 is getting the full cell text, not just current cell
    #
    # add_s or add_re calls with two parameters:
    # callable(self, event)
    # The event contains: 2023-04-02 07:14:42,857 - magic_duckdb - INFO - namespace(line='%dql asda', symbol='asda', command='%dql', text_until_cursor='%dql asda')
    #
    # set_custom_completer was an alternative method of adding, which seemed inconsistent within VScode... but it passed three parameters:
    # self, ipcompleter, linebuffer, cursor_pos
    #
    # the third method was add_hook('custom_complete'...)
    # which is a synonym for add_s or add_re
    #
    # https://github.com/ipython/ipython/pull/13745
    # https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.completer.html
    # https://raw.githubusercontent.com/ipython/ipython/main/IPython/core/completer.py
    # https://ipython.org/ipython-doc/rel-0.12.1/api/generated/IPython.utils.strdispatch.html#IPython.utils.strdispatch.StrDispatch.s_matches
    # https://github.com/ipython/ipython/blob/9663a9adc4c87490f1dc59c8b6f32cdfd0c5094a/IPython/core/tests/test_completer.py
    #
    # Also, annoyingly, VScode inserts some completions in: https://stackoverflow.com/questions/72824819/vscode-autocomplete-intellisense-in-jupyter-notebook-when-starting-string-lit

    ip.Completer.custom_completer_matcher = iql_completer.line_completer

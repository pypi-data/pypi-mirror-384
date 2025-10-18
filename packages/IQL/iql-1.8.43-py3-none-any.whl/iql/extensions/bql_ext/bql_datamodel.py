import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Union

from iql.extensions.bql_ext.bql_wrapper import (
    BaseBqlQuery,
    construct_bql_query,
    security_to_finalstr,
)

logger = logging.getLogger(__name__)

SECURITY_KEYWORD = "$SECURITY"


@dataclass
class RawBqlQuery(BaseBqlQuery):
    """A full BQL query. Ideally, use $SECURITY instead of a single equity name"""

    fieldpattern = re.compile(r"(?s).*get\s*\((.*?)\)\s*for.*")

    bql_query_string: str
    security: Optional[str] = None
    params: Dict = field(default_factory=dict)  # parameters. Convention is $FIELD: value

    def get_fields(self) -> Iterable[str]:
        """Extracts individual fields from the BQL get statement.
        TODO: Handle unbalanced escaped/quoted parens"""

        query = self.to_bql_query()
        match = self.fieldpattern.fullmatch(query)

        if match is None:
            raise ValueError(f"Couldn't extract GET from: {query}")

        else:
            getclause = match.group(1)
            fields = []
            start = 0
            depth = 1
            for i, c in enumerate(getclause):
                if c == "," and depth == 1:
                    fields.append(getclause[start:i].strip())
                    start = i + 1
                if c == "(":
                    depth += 1
                if c == ")":
                    depth -= 1

            fields.append(getclause[start:].strip())

        return fields

    def to_bql_query(self) -> str:
        if self.security is not None:
            new_str = self.bql_query_string.replace(SECURITY_KEYWORD, self.security)
        else:
            new_str = self.bql_query_string

        for param, value in self.params.items():
            new_str = new_str.replace(param, value)

        logger.debug("Raw query to string: %.50s", new_str)

        if "preferences" not in new_str:
            logger.debug("Adding default preferences")
            new_str += " \n preferences(addcols=all)"
        return new_str


@dataclass
class BqlQuery(BaseBqlQuery):
    name: str
    fields: Iterable[str]

    security: Union[str, Iterable]
    let_str: Optional[str]
    with_params: Optional[str]

    for_str: str = SECURITY_KEYWORD
    params: Dict = field(default_factory=dict)  # parameters. Convention is $FIELD: value

    def get_fields(self) -> Iterable[str]:
        return self.fields

    def to_bql_query(self) -> str:
        for_str_mod = security_to_finalstr(self.for_str)

        if SECURITY_KEYWORD not in self.params and self.security is not None:
            self.params[SECURITY_KEYWORD] = self.security

        sec = self.params.get(SECURITY_KEYWORD)
        if self.let_str is not None and sec is not None and SECURITY_KEYWORD in self.let_str:
            let_str_mod = self.let_str.replace(SECURITY_KEYWORD, sec)
        else:
            let_str_mod = self.let_str
        query_str = construct_bql_query(self.fields, for_str_mod, self.with_params, let_str_mod)

        logger.debug("After construction but before replacement: %s", query_str)
        for param, value in self.params.items():
            if param == SECURITY_KEYWORD:
                # Don't sub if:
                # is a list
                # is a function (bracket or paren)
                # is already quoted
                if not (isinstance(value, str) and ("'" in self.for_str or "(" in self.for_str or "[" in self.for_str)):
                    value = security_to_finalstr(self.params[SECURITY_KEYWORD])

            query_str = query_str.replace(param, value)

        logger.debug("BQL Query to String: %s", query_str)
        return query_str

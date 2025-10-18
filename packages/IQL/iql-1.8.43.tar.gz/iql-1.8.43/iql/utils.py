import logging
import re
from typing import Iterable, Optional, Tuple

from .constants import _KNOWN_EXTENSIONS

logger = logging.getLogger(__name__)


def _find_closing_paren(text: str, start: int) -> int:
    # TODO: Handle escaping
    paren_depth = 1
    quote_stack = []
    for i in range(start, len(text)):
        c = text[i]
        if c == "(" and len(quote_stack) == 0:
            paren_depth += 1
        elif c == "'" or c == '"':
            if len(quote_stack) == 0:
                quote_stack.append(c)
            elif quote_stack[len(quote_stack) - 1] == c:
                quote_stack.remove(c)
        elif c == ")" and len(quote_stack) == 0:
            paren_depth -= 1

        if paren_depth == 0:
            end = i
            return end
    raise ValueError("Never found closing parenthesis, probably unbalanced query")


def extract_subquery_strings(
    query: str, keywords: Optional[Iterable[str]] = None
) -> Iterable[Tuple[str, str, str, str]]:
    """Finds the subqueries start with keyword, along with matching end paren
    keyword(....)
    keyword.subword(....)
    """
    _keyword_list = get_keyword_list(keywords)

    _kpat = re.compile(rf"(?s)({_keyword_list})(\.(\w+))?\s*\(")

    results = []

    last_paren_end = -1

    for m in re.finditer(_kpat, query):
        logger.debug("finditer: %s", m.group(0))
        keyword = m.group(1)
        subword = m.group(3)
        paren_start = m.end()  # just after the last paren

        if paren_start < last_paren_end:
            logger.debug("Skipping embedded subquery: %s", m.group(0))

            continue

        paren_end = _find_closing_paren(query, paren_start)

        outer = query[m.start() : paren_end + 1]
        inner = query[paren_start : paren_end + 1]
        logger.debug(
            "Extracted subquery: %s.%s at %s:%s",
            keyword,
            subword,
            paren_start,
            paren_end,
        )

        results.append((keyword, subword, outer, inner))
        last_paren_end = paren_end

    return results


def get_keyword_list(keywords: Optional[Iterable[str]] = None) -> str:
    if keywords is None:
        keywords = list(_KNOWN_EXTENSIONS.keys())
    _keyword_list = "|".join((k if isinstance(k, str) else k[0] for k in keywords))
    return _keyword_list

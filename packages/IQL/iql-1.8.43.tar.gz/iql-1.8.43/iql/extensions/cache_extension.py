import logging
from dataclasses import dataclass

import pandas as pd

from ..datamodel.extension import IqlExtension
from ..datamodel.subquery import SubQuery
from ..ql import _EXTENSIONS, register_extension

logger = logging.getLogger(__name__)


@dataclass
class CacheClearAll(IqlExtension):
    """Clears the entire cache"""

    keyword: str

    def executeimpl(self, sq: SubQuery) -> pd.DataFrame:
        for e in _EXTENSIONS.values():
            e.cache.clear_all()

        return pd.DataFrame([{"result:": True}])


@dataclass
class CacheClear(IqlExtension):
    """Clears a single item from the cache"""

    keyword: str

    def executeimpl(self, sq: SubQuery) -> pd.DataFrame:
        key: str = sq.options["key"]  # type: ignore
        for e in _EXTENSIONS.values():
            e.cache.clear(key)

        return pd.DataFrame([{"result:": True}])


def register(keyword):
    register_extension(CacheClearAll(keyword=keyword, subword="clear_all"))
    register_extension(CacheClear(keyword=keyword, subword="clear"))

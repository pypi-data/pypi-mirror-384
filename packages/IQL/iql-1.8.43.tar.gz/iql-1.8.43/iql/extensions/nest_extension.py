import logging
from dataclasses import dataclass

import pandas as pd

from ..datamodel.extension import IqlExtension
from ..datamodel.subquery import SubQuery
from ..ql import executedf, register_extension

logger = logging.getLogger(__name__)


@dataclass
class NestedQueryExtension(IqlExtension):
    keyword: str

    def executeimpl(self, sq: SubQuery) -> pd.DataFrame:
        """Executes the query in the same database as this query
        Example: select * from nestiql("alias.stats();select 1");

        """
        query = sq.get_query()

        if query is None:
            raise ValueError("Query must be passed")

        if sq.options.get("nested_connection", True):
            con = sq.iqc.db._connection
        else:
            con = None

        result = executedf(query, con=con)
        return result


def register(keyword: str):
    extension = NestedQueryExtension(keyword=keyword)
    register_extension(extension)

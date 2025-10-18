import logging
from dataclasses import dataclass
from typing import Optional

import pyarrow as pa

from ...datamodel.extension import IqlExtension
from ...datamodel.subquery import SubQuery
from ...ql import register_extension
from . import blp_api_lowlevel as bal

logger = logging.getLogger(__name__)


@dataclass
class BlpApiListFieldsExtension(IqlExtension):
    param_replace_text = False

    def executeimpl(self, sq: SubQuery) -> Optional[pa.Table]:
        if len(sq.options) == 0:
            raise ValueError('Must select a field, or "All" for all fields')

        search = sq.options.get("search", False)

        if sq.get_query() == "All":
            logger.debug("Listing all fields")
            fi = bal.get_field_info()
        else:
            fi = bal.get_field_info(sq.get_query(), search=bool(search))

        t = pa.Table.from_pylist(fi)
        return t


@dataclass
class BlpApiEntitlementsExtension(IqlExtension):
    param_replace_text = False

    def executeimpl(self, sq: SubQuery) -> Optional[pa.Table]:
        if sq.options is None or len(sq.options) == 0 or sq.get_query() is None:
            raise ValueError("UUID required")

        e = bal.get_user_entitlements(sq.get_query())

        t = pa.Table.from_pylist(e)
        return t


@dataclass
class BlpApiRefDataExtension(IqlExtension):
    param_replace_text = False

    def executeimpl(self, sq: SubQuery) -> Optional[pa.Table]:
        fields = sq.options.get("fields", None)

        if fields is None:
            raise ValueError("Must pass a list of fields to retrieve")

        securities = sq.options.get("securities", None)
        if securities is None:
            raise ValueError("Must pass a list of securities")

        if isinstance(fields, str):
            fields = (fields,)

        params: dict = sq.options.get("params", {})  # type: ignore
        for k, v in sq.options.items():
            # Add any explicit parameters, so everything doesn't need to be packed into a dict
            if v is not None and k not in (
                "fields",
                "securities",
                "historical",
                "params",
                "paramquerybatch",
                "paramquery",
                "pivot",
            ):
                params[k] = v

        historical = sq.options.get("historical", False)

        if "startDate" in params or "endDate" in params:
            logger.debug("Historical enabled because startDate or endDate in params")
            historical = True

        rd = bal.get_refdata(
            fields=fields,
            securities=securities,
            parameters=params,
            historical=historical,  # type: ignore
        )

        if len(rd) == 0:
            raise ValueError(f"Empty response for query {sq}")
        else:
            t = pa.Table.from_pylist(rd)
            return t


def register(keyword: str):
    extension = BlpApiListFieldsExtension(keyword=keyword, subword="fields")
    register_extension(extension)

    extension = BlpApiEntitlementsExtension(keyword=keyword, subword="userentitlements")
    register_extension(extension)

    extension = BlpApiRefDataExtension(keyword=keyword)
    register_extension(extension)

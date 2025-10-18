from ._version import __version__  # noqa: I001
from .ql import (
    configure,
    executedf,
    execute,
    execute_debug,
    get_extension,
    list_extensions,
    register_extension,
    register_alias,
    patch_sqlparse,
)

# Needed for extensions
from .datamodel.extension import IqlExtension
from .datamodel.subquery import SubQuery

from .datamodel.cache import SqCache, set_cache_dir, iql_cache

from .jupyter_magics.iql_magic_ext import load_ipython_extension


__all__ = [
    "__version__",
    "configure",
    "executedf",
    "execute",
    "execute_debug",
    "get_extension",
    "list_extensions",
    "register_extension",
    "load_ipython_extension",
    "register_alias",
    "IqlExtension",
    "SubQuery",
    "SqCache",
    "set_cache_dir",
    "iql_cache",
]

patch_sqlparse()

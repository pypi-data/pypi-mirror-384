from typing import Dict

# Add extensions via register_extension()
# Extensions are loaded on first access, to avoid requiring
# unused dependencies

_KNOWN_EXTENSIONS: Dict[str, str] = {
    "bql": "iql.extensions.bql_ext.bql_extension",
    "pandas": "iql.extensions.pandas_extension",
    "cache": "iql.extensions.cache_extension",
    "blpapi": "iql.extensions.blpapi_ext.blp_extension",
    "azureblob": "iql.extensions.azure_blob_extension",
    "nestiql": "iql.extensions.nest_extension",
    "openai": "iql.extensions.openai_extension",
}

_LOADED_EXTENSIONS = []

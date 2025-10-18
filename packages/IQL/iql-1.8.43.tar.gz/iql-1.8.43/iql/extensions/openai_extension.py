import logging
import os
import time
from dataclasses import dataclass

import openai
import pandas as pd

from ..datamodel import cache
from ..datamodel.cache import iql_cache
from ..datamodel.extension import IqlExtension
from ..datamodel.subquery import SubQuery
from ..ql import register_extension

_CREDENTIAL = None

logger = logging.getLogger(__name__)


def get_result(key: str, assistant_id: str, prompt: str):
    openai.api_key = key
    client = openai.OpenAI(api_key=key)
    thread = client.beta.threads.create()

    openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)

    run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value


@dataclass
class OpenAiExtension(IqlExtension):
    """
    DuckDB does support native reading of certain file types.
    This is fine for XLSX files, but some file types need different engines, such as "xls", that duckdb doesn't support
    """

    param_replace_text = False
    keyword: str
    is_async: bool = False

    @iql_cache
    def executeimpl(self, sq: SubQuery) -> pd.DataFrame:
        if "openai_key" in sq.options:
            openai_key: str = sq.options.get("openai_key")  # type: ignore
        else:
            openai_key: str = os.environ.get("OPENAI_KEY", None)  # type: ignore

        if "openai_assistant_id" in sq.options:
            assistant_id: str = sq.options.get("openai_assistant_id")  # type: ignore
        else:
            assistant_id: str = os.environ.get("OPENAI_ASSISTANT_ID", None)  # type: ignore

        if not openai_key:
            raise ValueError("OPENAI_KEY not set")

        prompt: str = sq.options.get("prompt")  # type: ignore
        context: str = sq.options.get("context")  # type: ignore

        result = get_result(key=openai_key, assistant_id=assistant_id, prompt=prompt)
        return pd.DataFrame({"context": [context], "result": [result]})


def register(keyword: str):
    extension = OpenAiExtension(keyword=keyword)
    extension.cache = cache.MemoryAndFileCache(max_age=3600 * 24, return_pyarrow_table=False)
    register_extension(extension)

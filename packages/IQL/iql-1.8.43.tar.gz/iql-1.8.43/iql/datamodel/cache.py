import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import cachetools
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from . import extension
from .subquery import SubQuery

DEFAULT_CACHE_DIR = "."  # c:\\git\\iql_cache


def set_cache_dir(dir: str):
    global DEFAULT_CACHE_DIR

    DEFAULT_CACHE_DIR = dir


def get_cache_dir():
    return Path(DEFAULT_CACHE_DIR)


logger = logging.getLogger(__name__)


def iql_cache(func):
    if asyncio.iscoroutinefunction(func):

        async def wrapper_a(
            ext: "extension.IqlExtension", sq: SubQuery, *args, **kwargs
        ):
            logger.debug("Wrapper_a running %s", type(ext.cache))
            cached_result = ext.cache.get(sq) if ext.cache else None
            if cached_result is not None:
                return cached_result
            else:
                start = time.perf_counter()
                new_result = await func(ext, sq, *args, **kwargs)
                end = time.perf_counter()
                if ext.cache:
                    ext.cache.save(sq=sq, data=new_result, cost=end - start)
                return new_result

        return wrapper_a
    else:

        def wrapper(ext: "extension.IqlExtension", sq: SubQuery, *args, **kwargs):
            logger.debug("Wrapper running %s", type(ext))

            cached_result = ext.cache.get(sq) if ext.cache else None
            if cached_result is not None:
                return cached_result
            else:
                start = time.perf_counter()
                new_result = func(ext, sq, *args, **kwargs)
                end = time.perf_counter()
                if ext.cache:
                    ext.cache.save(sq=sq, data=new_result, cost=end - start)
                return new_result

        return wrapper


class SqCache:
    def save(self, sq: SubQuery | str, data: object, cost: float | None):
        """Save the element to cache.

        The cache implementation *may* use cost to decide on whether to cache an item.

        Args:
            sq (SubQuery | str): Subquery (or a cache key, if you want to use an explicit key)
            data (object): Data to be cached.
            cost (float | None): Usually the number of seconds the data took to generate
        """
        ...

    def get(self, sq: SubQuery | str) -> object | None: ...

    def clear(self, sq: SubQuery | str): ...

    def clear_all(self): ...


@dataclass
class NoopSqCache(SqCache):
    """Caches Nothing"""

    def save(self, sq: SubQuery | str, data: object, cost: float | None):
        pass

    def get(self, sq: SubQuery | str) -> object | None:
        return None

    def clear(self, sq: SubQuery | str):
        pass

    def clear_all(self):
        pass


@dataclass
class MemoryCache(SqCache):
    """Simple in memory cache. If max_age is None, then caches forever. Otherwise, uses a TTN cache"""

    max_age: int | None = field(default=None, init=True)
    min_cost: int = field(default=-1, init=True)
    _cache: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        if self.max_age is None:
            self._cache = {}  # just use a dictionary
        else:
            self._cache = cachetools.TTLCache(maxsize=float("inf"), ttl=self.max_age)

    def save(self, sq: SubQuery | str, data: object, cost: float | None):
        if cost is None or cost > self.min_cost:
            key = sq if isinstance(sq, str) else sq.get_cache_key()
            self._cache[key] = data

    def get(self, sq: SubQuery | str) -> object | None:
        key = sq if isinstance(sq, str) else sq.get_cache_key()
        return self._cache.get(key, None)

    def clear(self, sq: SubQuery | str):
        key = sq if isinstance(sq, str) else sq.get_cache_key()
        del self._cache[key]

    def clear_all(self):
        self._cache = {}


@dataclass
class FileCache(SqCache):
    """Simple in memory cache that ignores age: if age is None, then doesn't cache, otherwise caches forever"""

    max_age: int | None
    min_cost: int
    cache_dir: Path
    return_pyarrow_table: bool = False

    def __post_init__(self):
        try:
            self.cache_dir.mkdir(parents=False, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Could not create cache dir {self.cache_dir}: {e}") from e

    def to_filename(self, key: str):
        filename_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{filename_hash}.parquet"

    def save(self, sq: SubQuery | str, data: object, cost: float | None):
        if cost is None or cost > self.min_cost:
            key = sq if isinstance(sq, str) else sq.get_cache_key()
            logger.debug("Saving %s, cost=%s", key, cost)

            outfile = self.to_filename(key)
            if isinstance(data, pd.DataFrame):
                data.to_parquet(outfile)
            elif isinstance(data, pa.Table):
                pq.write_table(data, outfile)
            else:
                raise ValueError(f"Unsupported cache data type {type(data)}")

    def get(self, sq: SubQuery | str) -> object | None:
        key = sq if isinstance(sq, str) else sq.get_cache_key()

        outfile = self.to_filename(key)
        if outfile.exists():
            logger.debug("File cache hit: %s", key)
            if (
                self.max_age is None
                or (time.time() - outfile.stat().st_mtime) < self.max_age
            ):
                if self.return_pyarrow_table:
                    return pq.read_table(outfile)
                else:
                    return pd.read_parquet(outfile)
            else:
                logger.debug("File cache is expired %s", outfile)
                return None
        else:
            return None

    def clear(self, sq: SubQuery | str):
        key = sq if isinstance(sq, str) else sq.get_cache_key()
        try:
            outfile = self.to_filename(key)
            if outfile.exists():
                outfile.unlink()
        except Exception:
            logger.exception("Unable to delete cache file")

    def clear_all(self):
        for f in self.cache_dir.iterdir():
            try:
                if f.is_file():
                    f.unlink()
            except Exception as e:
                logger.info("Error debugging, could happen during races %s", e)


@dataclass
class MemoryAndFileCache(SqCache):
    max_age: int | None = None
    min_cost: int = 0
    return_pyarrow_table: bool = False
    cache_dir: Path = field(default_factory=get_cache_dir, init=True)

    _memory_cache: SqCache = field(init=False)
    _file_cache: SqCache = field(init=False)

    def __post_init__(self):
        if not self.cache_dir.exists():
            raise ValueError(f"{self.cache_dir=} does not exist")

        self._memory_cache = MemoryCache(max_age=self.max_age, min_cost=self.min_cost)

        self._file_cache = FileCache(
            max_age=self.max_age,
            min_cost=self.min_cost,
            cache_dir=self.cache_dir,
            return_pyarrow_table=self.return_pyarrow_table,
        )
        self.clear_all()

    def save(self, sq: SubQuery | str, data: object, cost: float | None):
        self._memory_cache.save(sq, data, cost)
        self._file_cache.save(sq, data, cost)

    def get(self, sq: SubQuery | str) -> object | None:
        o = self._memory_cache.get(sq)
        if o is not None:
            return o
        else:
            return self._file_cache.get(sq)

    def clear(self, sq: SubQuery | str):
        self._memory_cache.clear(sq)
        self._file_cache.clear(sq)

    def clear_all(self):
        self._memory_cache.clear_all()
        self._file_cache.clear_all()


@dataclass
class QueryInvalidationCache(SqCache):
    """Caches until the query returns a new value"""

    cache_query: str
    max_age: int | None = None
    min_cost: int = 0
    return_pyarrow_table: bool = False
    cache_dir: Path = field(default_factory=get_cache_dir, init=True)
    use_file_cache: bool = True

    _cache_key: object | None = None
    _file_cache: SqCache | None = None
    _memory_cache: SqCache = field(init=False)

    def __post_init__(self):
        self._memory_cache = MemoryCache(max_age=self.max_age, min_cost=self.min_cost)

    def check_cache_valid(self) -> bool:
        from .. import ql

        status = ql.executedf(self.cache_query)
        if not (len(status) == 1 and len(status.columns) == 1):
            # The query must return a single value and a single column
            raise ValueError(
                "Invalid cache: query didn't return a single value and single column"
            )

        if status.iloc[0, 0] == self._cache_key:
            logger.debug("Cache value hasn't changed, cache is valid")
            return True
        else:
            self.clear_all()
            self._cache_key = status.iloc[0, 0]

            # Create a new file cache scoped (subdir) to the new cache key
            if self.use_file_cache:
                # use hex of cache key to sanitize path string and not leak data to fs
                cache_dir_key = hashlib.md5(
                    str(self._cache_key).encode(), usedforsecurity=False
                ).hexdigest()

                self._file_cache = FileCache(
                    max_age=self.max_age,
                    min_cost=self.min_cost,
                    cache_dir=self.cache_dir / cache_dir_key,
                    return_pyarrow_table=self.return_pyarrow_table,
                )

            logger.debug("Cache value has changed, cache is invalid")
            return False

    def save(self, sq: SubQuery | str, data: object, cost: float | None):
        self.check_cache_valid()
        # cache is always valid after check
        self._memory_cache.save(sq, data, cost)
        if self._file_cache:
            self._file_cache.save(sq, data, cost)

    def get(self, sq: SubQuery | str) -> object | None:
        self.check_cache_valid()
        # cache is always valid after check
        o = self._memory_cache.get(sq)
        if o is not None:
            logger.debug("Memory cache hit")
            return o
        elif self._file_cache:
            return self._file_cache.get(sq)

        # Fall through
        return None

    def clear(self, sq: SubQuery | str):
        self._memory_cache.clear(sq)
        if self._file_cache:
            self._file_cache.clear(sq)

    def clear_all(self):
        # TODO: Thread safety and Async safety
        self._memory_cache.clear_all()

        if self.use_file_cache and self._file_cache:
            fc = self._file_cache
            self._file_cache = None
            fc.clear_all()

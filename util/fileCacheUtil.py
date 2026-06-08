import random
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class FileState:
    content: str
    timestamp: int
    offset: int | None = None
    limit: int | None = None
    # is_partial_view:注入的内容，可能被阶段，部分加载，作为视图的一部分
    is_partial_view: bool = None


class CacheFileState:
    pass



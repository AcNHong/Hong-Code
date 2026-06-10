from dataclasses import dataclass
from cachetools import LRUCache
# from cachetools import Cache

@dataclass
class FileState:
    content: str
    timestamp: int
    offset: int | None = None
    limit: int | None = None
    # is_partial_view:注入的内容，可能被阶段，部分加载，作为视图的一部分
    is_partial_view: bool | None = None



class CacheUtils:
    """
    缓存工具类
    cache_key: 文件路径
    value: FileState
    """
    _cache : LRUCache

    def __init__(self, max_entries: int,max_size_bytes: int = None):
        self.maxSizeBytes = max_entries
        self.maxEntries = max_size_bytes
        self._cache = LRUCache(max_entries)

    def get_value(self, cache_key: str):
        value = self._cache.get(cache_key, None)
        if value is not None:
            print(f"Cache hit for key: {cache_key}")
        else:
            print(f"Cache miss for key: {cache_key}")
        return value

    def set_key_value(self, cache_key: str, value):
        self._cache[cache_key] = value
        print(f"Set cache key: {cache_key} with value: {value}")

    def set_key_list(self, cache_key: str, value):
        v = self._cache.get(cache_key, None)
        if v is not None:
            v.append(value)
        else:
            self._cache[cache_key] = [value]

    def clear_cache(self):
        self._cache.clear()

    def __repr__(self):
        content = ""
        for k,v in self._cache.items():
            content += f"{k}:{v}\n"
        return content



# if __name__ == "__main__":
#     cache = CacheUtils(100)
#     r1 = FileState("123",4234324232)
#     r2 = FileState("321",4234324232)
#     cache.set_key_value("./files.py",r1)
#     value = cache.get_value("./files.py")
#     cache.set_key_value("./files.py",r1)
#     cache.set_key_value("./shell.py",r2)
#     print("==============================="*2)
#     print(cache)





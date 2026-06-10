from dataclasses import dataclass

from tools.shell import ShellExecutor
from util.fileCacheUtil import CacheUtils


@dataclass
class toolContext:
    executor:ShellExecutor
    file_cache_util:CacheUtils
    # 后续可扩展
    
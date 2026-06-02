from dataclasses import dataclass
from typing import Callable


@dataclass
class Tools:
    name: str  # 工具名称
    description: str  # 工具描述
    input_schema: dict  # 输入字段
    execute: Callable  # 执行函数
    is_readonly: bool|Callable  # 是否可并发

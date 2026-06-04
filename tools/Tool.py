from dataclasses import dataclass
from typing import Any, Callable, Optional

# 工具字段类型约束
@dataclass
class toolDef:
    name:str # 工具名称
    description:str # 工具描述字段
    prompt:Callable[..., str]  # 表示接受任意参数，返回 str
    input_schema:dict # api input_schema
    call:Callable[[dict,Any],Any] # 工具执行回调
    is_readonly:bool = False # 是否可以并发 （只读工具可以采用并发，其余都不能）

# 注册工具列表
_tools:list[toolDef] = []

# 获取工具
def get_tools() -> list[toolDef]:
    return _tools

def register_tools(tool:toolDef):
    _tools.append(tool)

# 名称匹配
def tool_matches_name(tool:toolDef,name:str) -> bool:
    return tool.name == name or False

# 通过名称找工具
def find_tool_by_name(name:str,tools:list[toolDef]) -> Optional[toolDef]:
    for tool in tools:
        if tool_matches_name(tool,name):
            return tool
    return None




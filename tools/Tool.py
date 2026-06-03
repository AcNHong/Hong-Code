from typing import Any
from tools.BashTools import BashTool

# 获取工具
def get_tools(*args) -> list[Any]:
    return [BashTool]

# 名称匹配
def tool_matches_name(tool,name):
    return tool.get("name","") == name or False

# 通过名称找工具
def find_tool_by_name(name:str,tools:list[Any]):
    for tool in tools:
        if tool_matches_name(tool,name):
            return tool
    return None


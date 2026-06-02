from typing import List

from tools.Tools import Tools


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tools] = {}

    def register(self, tool: Tools):
        self._tools[tool.name] = tool

    def get_all(self) -> List[Tools]:
        return list(self._tools.values())

    def get_by_name(self, name: str) -> Tools | None:
        return self._tools.get(name)

    def filter_by_permission(self, permission_context) -> List[Tools]:
        """按权限过滤工具"""
        return [t for t in self._tools.values() if self._has_permission(t, permission_context)]

    def to_api_schemas(self) -> list[dict]:
        """转成 API 可用的 tool 参数"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    def _has_permission(self, t, permission_context):
        pass
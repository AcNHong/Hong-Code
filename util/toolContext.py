from dataclasses import dataclass

from shell import ShellExecutor


@dataclass
class toolContext:
    executor:ShellExecutor
    # 后续可扩展
    
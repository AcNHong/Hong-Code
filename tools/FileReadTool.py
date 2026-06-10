from pathlib import Path

from tools.Tool import toolDef, register_tools
from util.fileCacheUtil import FileState
from util.files import get_file_modification_time
from util.toolContext import toolContext

MAXLINE = 2000

async def fileRead(input_dict:dict, tool_context:toolContext,**kwargs) -> str:
    """

    :param tool_context:
    :param input_dict:
    :param input_dict: input
    :return:
    """
    file_path = input_dict["file_path"]
    offset = input_dict.get("offset")
    limit = input_dict.get("limit")
    read_file_state = tool_context.file_cache_util
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        return f"Error: File not found: {file_path}"
    if not path.is_file():
        return f"Error: Not a file: {file_path}"

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"
    # set cache
    read_file_state.set_key_value(file_path,FileState(
        content = content,
        timestamp = get_file_modification_time(file_path)
    ))

    lines = content.splitlines()

    if offset is not None:
        start = max(0, offset - 1) if offset > 0 else 0
    else:
        start = 0

    if limit is not None:
        result_lines = lines[start:start + limit]
    else:
        result_lines = lines[start:]

    # 返回格式带行号，方便模型理解上下文
    line_num_width = len(str(start + len(result_lines)))
    numbered = [
        f"{i + 1 + start:>{line_num_width}}│{line}"
        for i, line in enumerate(result_lines)
    ]

    header = f"{path} ({len(result_lines)} lines"
    if offset is not None:
        header += f", from line {offset}"
    header += ")"

    return header + "\n" + "\n".join(numbered)

def is_readonly(*arg,**kwargs):
    return False

def prompt(**kwargs) -> str:
    return f"""Reads a file from the local filesystem. You are able to read any files that are not encrypted or obfuscated by using this tool.
Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

usage:
- By default, he reads from the first line to the end.

This tool can only read files, not directories. To read a directory, use an ls command via the $ Bash tool.
Please read the entire file first. If you find the file is too large, you can read it in batches.
"""


FileReadTool = toolDef(name="Read",
    description="Read file tool",
    prompt = prompt,
    input_schema= {
        "type": "object",                      # 固定为 "object"
        "properties": {                        # 定义具体的参数
            "file_path": {
                "type": "string",
                "description": "file path absolutely or relatively"
            },
            "offset": {
                "type": "number",
                "description": "number of start line"
            },
            "limit": {
                "type": "number",
                "description": "number of end line"
            },
        },
        "required": ["file_path"]               # 必填参数列表
    },
    call=fileRead,
    is_readonly=True
)
# 注册工具
register_tools(FileReadTool)

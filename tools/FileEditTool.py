from pathlib import Path

from tools.Tool import toolDef, register_tools
from util.fileCacheUtil import FileState
from util.files import get_file_modification_time
from util.toolContext import toolContext


async def file_edit(input_dict: dict, tool_context: toolContext, **kwargs) -> dict:
    """
    基于 old_string -> new_string 的精确字符串替换编辑工具。

    :param tool_context: 工具上下文（含文件缓存等）
    :param input_dict: 包含 file_path, old_string, new_string 的字典
    :return: 操作结果字典
    """
    file_path = input_dict["file_path"]
    old_string = input_dict["old_string"]
    new_string = input_dict["new_string"]

    # 统一转为绝对路径
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        return {
            "file_path": str(path),
            "success": False,
            "error": f"error:File not found: {file_path}",
        }
    if not path.is_file():
        return {
            "file_path": str(path),
            "success": False,
            "error": f"error:Not a file: {file_path}",
        }

    # 读取当前文件内容
    try:
        with open(path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        return {
            "file_path": str(path),
            "success": False,
            "error": f"Error reading file: {e}",
        }

    # 检查文件是否被外部修改（与 FileWriteTool 一致的缓存校验逻辑）
    last_write_time = get_file_modification_time(str(path))
    file_cache = tool_context.file_cache_util.get_value(str(path))
    if file_cache and (last_write_time > file_cache.timestamp and file_cache.content != current_content):
        return {
            "file_path": str(path),
            "success": False,
            "error": "File has been unexpectedly modified. Read it again before attempting to edit it.",
        }

    # 查找 old_string
    count = current_content.count(old_string)
    if count == 0:
        return {
            "file_path": str(path),
            "success": False,
            "error": f"old_string not found in file. The exact string was not found.",
        }
    if count > 1:
        return {
            "file_path": str(path),
            "success": False,
            "error": f"old_string appears {count} times in the file. Please provide a larger string with more surrounding context to make it unique.",
        }

    # 执行替换
    new_content = current_content.replace(old_string, new_string, 1)

    # 写入文件
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return {
            "file_path": str(path),
            "success": False,
            "error": f"Error writing file: {e}",
        }

    # 更新文件缓存
    tool_context.file_cache_util.set_key_value(
        str(path),
        FileState(
            content=new_content,
            timestamp=get_file_modification_time(str(path)),
        ),
    )

    return {
        "file_path": str(path),
        "success": True,
        "error": "",
        "old_string": old_string,
        "new_string": new_string,
    }


def prompt(**kwargs) -> str:
    return """Performs exact string replacements in an existing file.
- When editing text, ensure you preserve the exact indentation (tabs/spaces) as it appears before.
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
- The edit will FAIL if old_string is not unique in the file (i.e., appears multiple times).
  Either provide a larger string with more surrounding context to make it unique.
- Use this tool instead of rewriting the entire file when making small, targeted changes.
"""


FileEditTool = toolDef(
    name="Edit",
    description="Edit file tool - performs exact string replacements in existing files",
    prompt=prompt,
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to edit (absolute or relative)",
            },
            "old_string": {
                "type": "string",
                "description": "The exact string to be replaced",
            },
            "new_string": {
                "type": "string",
                "description": "The string to replace it with (must be different from old_string)",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    },
    call=file_edit,
    is_readonly=False,
)

# 注册工具
register_tools(FileEditTool)

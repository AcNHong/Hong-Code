import asyncio
import os
from pathlib import Path

from tools.Tool import toolDef, register_tools



async def file_write(input_dict:dict, *args) -> str:
    """

    :param input_dict:
    :param input_dict: input
    :param ctx: 工具上下文
    :return:
    """
    file_path = input_dict.get("file_path")
    write_type = input_dict.get("type")
    content = input_dict.get("content")
    structured_patch = input_dict.get("structured_patch")
    original_file = input_dict.get("original_file")
    # 确保目录存在
    if not Path(os.path.dirname(file_path)).exists():
        os.mkdir(os.path.dirname(file_path))
        Path(os.path.dirname(file_path)).chmod(0o700)

    if write_type == "create":
        with open(file_path,"w+",encoding="utf-8") as f:
            f.write(content)

    elif write_type == "update":
        return "写入不支持update"

    return ""

def is_readonly(*arg,**kwargs):
    return False

def prompt(**kwargs) -> str:
    return f"""write file with file_path and content and type("create","update")
-must need params 'file_path'、"content"、"update"
-Try to write the entire document in one go.
-If you need to update the file，use other tool
"""

FileWriteTool = toolDef(name="Write",
    description="Write file tool",
    prompt = prompt,
    input_schema= {
        "type": "object",                      # 固定为 "object"
        "properties": {
            "type":{
                "type": "string",
                "description": "Whether a new file was created or an existing file was updated:('create', 'update')"
            },
            "file_path": {
                "type": "string",
                "description": "file path absolutely or relatively"
            },
            "content": {
                "type": "string",
                "description": "The content that was written to the file"
            },
            "originalFile": {
                "type": "string",
                "description": "The original file content before the write (null for new files)"
            },
            "structuredPatch": {
                "type": "array",
                "description": "Diff patch showing the changes，structure format:[oldStart:int,oldLines:int,newStart:int,newLines:int,lines:list[str]]"
            },
        },
        "required": ["type","file_path","content"]               # 必填参数列表
    },
    call=file_write,
    is_readonly=False
)
# 注册工具
register_tools(FileWriteTool)

if __name__ == "__main__":
    asyncio.run(file_write({"type":"create","file_path":"E://private//claude_code_for_py//test//test.txt","content":"test"}))

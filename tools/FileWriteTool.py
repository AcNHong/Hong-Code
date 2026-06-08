import asyncio
import os
from pathlib import Path

from tools.Tool import toolDef, register_tools
from util.files import get_file_modification_time


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
    os.makedirs(os.path.dirname(file_path),exist_ok=True)

    # 比对文件内容
    meta_content = ""
    try:
        with open(file_path, "r+", encoding="utf-8") as f:
            meta_content = f.read(file_path)
    except FileNotFoundError as e:
        # 忽略
        pass
    except Exception as e:
        # 不明IO异常抛出
        raise e
    # 如果有数据，则进一步判断
    if not meta_content:
        file_st_mtime = get_file_modification_time(file_path) #最后一次修改时间
        # todo 继续完成其它部分



    with open(file_path,"w+",encoding="utf-8") as f:
        f.write(content)

    return ""

def is_readonly(*arg,**kwargs):
    return False

def prompt(**kwargs) -> str:
    return f"""write file with file_path and content and type("create","update")
-must read whole file content before write file,set param original_file
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

import asyncio
import os
from pathlib import Path
from typing import Any, Coroutine

from tools.Tool import toolDef, register_tools
from util import toolContext
from util.fileCacheUtil import CacheUtils, FileState
from util.files import get_file_modification_time


async def file_write(input_dict:dict, tool_context:toolContext,**kwargs) ->dict[str, str | None | Any]:
    """

    :param tool_context:
    :param input_dict:
    :param input_dict: input
    :return:
    """
    file_path = input_dict.get("file_path")
    # 统一转换为绝对路径（兼容 Windows / Linux）
    file_path = str(Path(file_path).expanduser().resolve())
    content = input_dict.get("content")

    # 确保目录存在
    os.makedirs(os.path.dirname(file_path),exist_ok=True)

    # 比对文件内容
    meta_content = ""
    try:
        with open(file_path, "r+", encoding="utf-8") as f:
            # 默认读取所有
            meta_content = f.read()
    except FileNotFoundError as e:
        # 忽略
        pass
    except Exception as e:
        # 不明IO异常抛出
        raise e
    # 如果有数据，则进一步判断
    if meta_content:
        last_write_time = get_file_modification_time(file_path) #最后一次修改时间
        read_file_cache:CacheUtils = tool_context.file_cache_util
        file_cache:FileState = read_file_cache.get_value(file_path)
        #没有缓存不用判断
        #有缓存进一步判断修改时间
        #已经被修改，判断内容是否一致，不一致才不写 否则继续写
        #主要是防止windows的部分检测程序 导致文件修改时间更改，内容不变
        #或者人为或者外部修改文件
        if (not file_cache) or (last_write_time > file_cache.timestamp and file_cache.content != meta_content):
            return {
                "content": content,
                "file_path": file_path,
                "origin_file_content": meta_content,
                "success": False,
                "error": "File has been unexpectedly modified. Read it again before attempting to write it.",
            }

    with open(file_path,"w+",encoding="utf-8") as f:
        f.write(content)

    # 修改文件状态
    tool_context.file_cache_util.set_key_value(file_path,FileState(
        content = content,
        timestamp= get_file_modification_time(file_path)
    ))

    data = {
        "content":content,
        "file_path":file_path,
        "origin_file_content":meta_content,
        "success":True,
        "error":"",
    }

    return data

def is_readonly(*arg,**kwargs):
    return False

def prompt(**kwargs) -> str:
    return f"""write file with file_path and content and type("create","update")
-must use Read tool to read whole file content before write file,set param original_file
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
    asyncio.run(file_write(
        {"type": "create", "file_path": "E://private//claude_code_for_py//test//test.txt", "content": "test"}))

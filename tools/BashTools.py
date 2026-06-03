from shell import ShellExecutor
from util.lazyLoding import lazy_schema
from util.toolContext import toolContext


def description(desc = None):
    return desc or "Run shell command"

def inputSchema():
    """
    "input_schema": {                          # 参数定义
        "type": "object",                      # 固定为 "object"
        "properties": {                        # 定义具体的参数
            "location": {
                "type": "string",
                "description": "城市和州，例如：北京, 朝阳区"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"], # 限制取值范围
                "description": "温度单位"
            }
        },
        "required": ["location"]               # 必填参数列表
    }
    :return:
    """
    return lazy_schema(lambda : {
        "type": "object",                      # 固定为 "object"
        "properties": {                        # 定义具体的参数
            "command": {
                "type": "string",
                "description": "run shell command"
            },
        },
        "required": ["command"]               # 必填参数列表
    })()

async def runshell(input, ctx:toolContext) -> str:
    """

    :param input: input
    :param ctx: 工具上下文
    :return:
    """
    shell_result = await ctx.executor.exec(input["command"])
    return shell_result.stdout

def is_readonly(*arg,**kwargs):
    return False


BashTool = {
    "name":"Bash",
    "description":description,
    "input_schema":inputSchema,
    "call": runshell,
    "is_readonly":is_readonly
}


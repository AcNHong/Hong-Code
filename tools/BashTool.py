from tools.Tool import toolDef, register_tools
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

def prompt(**kwargs):
    return """执行给定的 bash 命令并返回其输出。
-使用时不能不传入参数
-如果你的命令会创建新目录或文件，首先使用此工具运行 `ls` 来验证父目录存在且位置正确
-在命令中始终使用双引号引用包含空格的文件路径（例如，cd "path with spaces/file.txt"）
-尽量在整个会话中保持当前工作目录，方法是使用绝对路径并避免使用 `cd`。如果用户明确要求，你可以使用 `cd`
-默认情况下，你的命令将在 30000ms 后超时
-不要使用换行符分隔命令（换行符在引号字符串内是可以的
-优先创建新提交而不是修改现有提交
- 在运行破坏性操作（例如 git reset --hard、git push --force、git checkout --）之前，考虑是否有更安全的替代方案可以达到相同目标。仅在破坏性操作确实是最好方法时才使用它
- 除非用户明确要求，否则永远不要跳过钩子（--no-verify）或绕过签名（--no-gpg-sign、-c commit.gpgsign=false）。如果钩子失败，调查并修复潜在问题
- 避免不必要的 `sleep` 命令：
- 不要在 sleep 循环中重试失败的命令 —— 诊断根本原因
- 如果必须休眠，保持较短的持续时间（1-5 秒）以避免阻塞用户
"""

BashTool = toolDef(name="Bash",
    description="run shell command",
    prompt=prompt,
    input_schema= {
        "type": "object",                      # 固定为 "object"
        "properties": {                        # 定义具体的参数
            "command": {
                "type": "string",
                "description": "run shell command"
            },
        },
        "required": ["command"]               # 必填参数列表
    },
    call=runshell,
    is_readonly=False
)
# 注册工具
register_tools(BashTool)

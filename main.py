import asyncio
from api.api import QueryModel
from constant.SystemToolPrompt import get_system_prompt
from tools.shell import ShellExecutor
from tools.Tool import get_tools
from util.toolContext import toolContext

async def main():

    init_tools = get_tools() # tools
    query_loop = QueryModel(get_system_prompt()) # api
    tool_ctx = toolContext(executor=ShellExecutor())

    while True:
        code = input("请输入指令:")
        await query_loop.query(
            tools = init_tools,
            code = code,
            context=[],
            tool_context=tool_ctx
        )


if __name__ == "__main__":
    asyncio.run(main())
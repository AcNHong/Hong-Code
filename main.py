import asyncio
import json

import anthropic

from constant.SystemToolPrompt import get_system_prompt
from shell import ShellExecutor
from tools.Tool import get_tools, find_tool_by_name
from util.api import toolToAPISchema
from util.envoriment import get_auth
from util.toolContext import toolContext

context = []

#api
auth = get_auth()
BASE_URL = auth["BASE_URL"]
API_KEY = auth["API_KEY"]
client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)

init_tools:list = []

executor = ShellExecutor()
tool_ctx = toolContext(executor=executor)
# 系统提示词
system_prompt = get_system_prompt()

async def main():

    # 注册工具
    global init_tools
    init_tools = get_tools()
    api_tools = list(map(toolToAPISchema,init_tools))

    while True:
        code = input("请输入指令:")
        await queryModel(api_tools,code)

async def exec_tool(block,ctx:toolContext):

    tool = find_tool_by_name(block.name,init_tools)
    if not tool:
        return "Unknown tool name"
    result = await tool.get("call")(block.input,ctx)
    return result


async def queryModel(tools,code):
    # queryModel
    context.append({"role": "user", "content": f"{code}"})
    while True:
        response = client.messages.create(
            model="deepseek-v4-pro",
            max_tokens=1024,
            tools=tools,
            system=system_prompt,
            messages=context
        )
        # 没有响应继续
        if not response:
            break
        tool_results = []
        text_responses = []
        thinking_responses = []
        tool_use_blocks = []
        # 工具
        has_use_tool = False

        # 迭代响应类型
        if response:
            usage = response.usage
            tokens = (usage.input_tokens or 0) + (usage.cache_creation_input_tokens or 0) + (
                        usage.cache_read_input_tokens or 0) + (usage.output_tokens or 0)
            if tokens > 200_200:
                print(f"超过上下文限制200k：{tokens} > 200_200")
                break
            for block in response.content:
                if block.type == "text":
                    text_responses.append(block.text)
                elif block.type == "thinking":
                    thinking_responses.append(block.thinking)
                elif block.type == "tool_use":
                    has_use_tool = True
                    tool_use_blocks.append(block)

        # 第二步：添加AI响应到上下文
        context.append({
            "role": "assistant",
            "content": response.content  # 保持原始结构
        })

        # 第三步：显示文本和思考内容
        for text in text_responses:
            print(f"AI: {text}")

        # for thinking in thinking_responses:
        #     print(f"思考: {thinking}")

        if not has_use_tool:
            print("当前任务执行完成，请输入指令:")
            break
        # 第四步：处理工具调用

        tool_results = []  # 每次清空

        for block in tool_use_blocks:
            # 执行工具
            try:
                result = await exec_tool(block,tool_ctx)
                # 添加工具结果
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,  # 确保ID正确
                    "content": json.dumps(result, ensure_ascii=False)
                })

            except Exception as e:
                print(f"   错误: {e}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                })

        # 所有工具处理完后，一次性添加结果
        if tool_results:
            context.append({
                "role": "user",
                "content": tool_results
            })
            # 继续对话，让AI处理工具结果
            print("等待AI处理工具结果...")
            continue  # 回到循环开始，让AI处理工具结果

if __name__ == "__main__":
    asyncio.run(main())
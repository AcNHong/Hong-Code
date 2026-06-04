import json
import os

import anthropic

from api import toolToAPISchema
from tools.Tool import toolDef, find_tool_by_name
from util.envoriment import get_auth
from util.toolContext import toolContext

auth = get_auth()
MAX_RETRIES = os.environ.get("MAX_RETRIES") or 3
TIMEOUT_REQUEST = os.environ.get("TIMEOUT_REQUEST") or 30000.0


async def exec_tool(block, ctx: toolContext,tools):
    # all tools todo 集成到其它模块
    tool: toolDef = find_tool_by_name(block.name, tools)
    if not tool:
        return "Unknown tool name"
    print("调用工具：", block.name)
    result = await tool.call(block.input, ctx)
    return result


class QueryModel:
    def __init__(self,system_prompt):
        self.url = auth["BASE_URL"]
        self.token = auth["API_KEY"]
        self.timeout = TIMEOUT_REQUEST
        self.system_prompt = system_prompt
        self.client = anthropic.Anthropic(base_url=self.url, api_key=self.token,timeout=self.timeout,max_retries=MAX_RETRIES)

    async def query(self,**option):
        tools = option.get("tools")
        user_code = option.get("code")
        context = option.get("context")
        tool_ctx = option.get("tool_context")


        if not user_code:
            return

        api_tools = toolToAPISchema(tools)

        context.append({"role":"user","content":user_code})
        print(self.system_prompt)
        while True:

            response = self.client.messages.create(
                model="deepseek-v4-pro",
                max_tokens=1024,
                tools=api_tools,
                system=self.system_prompt,
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
                        print(block.thinking)
                        thinking_responses.append(block.thinking)
                    elif block.type == "tool_use":
                        print(block)
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
                break
            # 第四步：处理工具调用

            tool_results = []  # 每次清空

            for block in tool_use_blocks:
                # 执行工具
                try:
                    result = await exec_tool(block, tool_ctx,tools)
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

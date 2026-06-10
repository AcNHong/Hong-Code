import json
import os

import anthropic

from api import toolToAPISchema
from tools.Tool import toolDef, find_tool_by_name, check_tool_input
from util.envoriment import get_auth
from util.toolContext import toolContext

auth = get_auth()
MAX_RETRIES = int(os.environ.get("MAX_RETRIES") or 3)
TIMEOUT_REQUEST = float(os.environ.get("TIMEOUT_REQUEST") or 30000.0)


async def exec_tool(block, ctx: toolContext, tools):
    tool: toolDef = find_tool_by_name(block.name, tools)
    if not tool:
        return "Unknown tool name"

    # 工具参数验证
    valid_result:dict = check_tool_input(block.input)
    if not valid_result.get("result",False):
        return valid_result.get("error_message","")

    result = await tool.call(block.input, tool_context=ctx)
    print(f"执行结果：\n{result}")
    return result


class QueryModel:
    def __init__(self, system_prompt):
        self.url = auth["BASE_URL"]
        self.token = auth["API_KEY"]
        self.timeout = TIMEOUT_REQUEST
        self.system_prompt = system_prompt
        self.client = anthropic.Anthropic(
            base_url=self.url,
            api_key=self.token,
            timeout=self.timeout,
            max_retries=MAX_RETRIES,
        )
        self.max_turns = 0 # 最大工具调用次数
        self.turn_next_count = 0 # 当前工具调用次数

    async def query(self, **option):
        tools = option.get("tools")
        user_code = option.get("code")
        context = option.get("context")
        tool_ctx = option.get("tool_context")
        on_event = option.get("on_event")

        if not user_code:
            return ""

        api_tools = toolToAPISchema(tools)

        context.append({"role": "user", "content": user_code})
        final_text_responses = []
        print(self.system_prompt)

        self.turn_next_count = 0 # 重置tool count

        while True:

            if self.max_turns and self.turn_next_count > self.max_turns:
                context.append({"role": "user", "content": f"aborted_tools，reason：Making consecutive calls to the tool more than a certain number of times，max count：{self.max_turns}"})
                break

            response = self.client.messages.create(
                model="deepseek-v4-pro",
                max_tokens=32768,
                tools=api_tools,
                system=self.system_prompt,
                messages=context,
            )

            if not response:
                break

            text_responses = []
            thinking_responses = []
            tool_use_blocks = []
            has_use_tool = False

            usage = response.usage
            tokens = (
                (usage.input_tokens or 0)
                + (usage.cache_creation_input_tokens or 0)
                + (usage.cache_read_input_tokens or 0)
                + (usage.output_tokens or 0)
            )
            # if tokens > 200_200:
            #     print(f"Context limit exceeded: {tokens} > 200_200")
            #     break

            for block in response.content:
                if block.type == "text":
                    text_responses.append(block.text)
                elif block.type == "thinking":
                    print(block.thinking)
                    thinking_responses.append(block.thinking)
                elif block.type == "tool_use":
                    self.turn_next_count += 1
                    has_use_tool = True
                    tool_use_blocks.append(block)
                    if on_event:
                        on_event({
                            "type": "tool_use",
                            "name": block.name,
                            "input": block.input,
                        })

            context.append({
                "role": "assistant",
                "content": response.content,
            })

            for text in text_responses:
                print(f"AI: {text}")
                final_text_responses.append(text)
                if on_event:
                    on_event({
                        "type": "text",
                        "text": text,
                    })

            if not has_use_tool:
                break

            tool_results = []

            for block in tool_use_blocks:
                try:
                    result = await exec_tool(block, tool_ctx, tools)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                except Exception as e:
                    print(f"Error: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({"error": str(e)}, ensure_ascii=False),
                    })

            if tool_results:
                context.append({
                    "role": "user",
                    "content": tool_results,
                })
                print("Waiting for AI to process tool results...")
                continue

        return "\n".join(final_text_responses)

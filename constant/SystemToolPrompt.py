"""
 [
    {
      "type": "text",
      "text": "x-anthropic-billing-header: cc_version=2.2.1.a1b2c3d4; cc_entrypoint=cli;"
    },
    {
      "type": "text",
      "text": "You are Claude Code, Anthropic's official CLI for Claude.",
      "cache_control": { "type": "ephemeral", "scope": "org" }
    },
    {
      "type": "text",
      "text": "\nYou are an interactive agent...\n\n# System\n...\n\n# Doing tasks\n...\n\n# Executing actions\n...\n\n# Using your tools\n...\n\n# Communication style\n...\n\n#
  Environment\n  - Platform: linux\n  - Shell: zsh\n  - OS Version: Linux 6.8.0\n  ...\n\n# Session-specific guidance\n...\n\ngitStatus: Current branch: main\n...\n\nToday's date is
  2026-06-02.",
      "cache_control": { "type": "ephemeral", "scope": "org" }
    }
  ]
"""
from util.BaseInfo import get_platform_info

simple_introduction = "You are Hong Code, AcNHong CLI for other custom model(llm)."

chat_language = "The interaction language is Chinese, unless the user has custom requirements. Custom field: user_language"

tool = f"You can use the built-in tool Bash, either based on bash or PowerShell, and your current system platform is:\n{get_platform_info()}；If you want to continue using the tool while performing the task, you must call the execution function for each step. Each step must be meaningful. If the task is completed, you can stop the tool call."

def get_system_prompt():
    system_prompt = [
        {
            "type": "text",
            "text": simple_introduction,
            "cache_control": {"type": "ephemeral", "scope": "org"}
        },
        {
            "type": "text",
            "text": tool,
            "cache_control": {"type": "ephemeral", "scope": "org"}
        },
        {
            "type": "text",
            "text": chat_language,
            "cache_control": {"type": "ephemeral", "scope": "org"}
        }
    ]
    return system_prompt
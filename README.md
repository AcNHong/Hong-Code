# Hong Code

<p align="center">
  <b>本地桌面 AI 助手 · 支持 Bash 与文件读取工具</b>
</p>

---

## 项目简介

**Hong Code** 是一个本地桌面 AI 助手，它将大语言模型 (LLM) 与本地系统工具深度结合，让你可以通过自然语言与计算机交互——执行 Shell 命令、读取文件、管理项目等，所有操作都在本机完成。

## 核心特性

- **双模式运行**：支持 CLI 命令行模式 (main.py) 和桌面 GUI 模式 (desktop.py)
- **多平台 Shell 支持**：自动检测系统平台，Linux/macOS 使用 Bash，Windows 使用 PowerShell
- **文件读取工具**：支持读取本地文件，带行号输出，可分页读取大文件
- **工具调用链**：LLM 可自动决策调用哪些工具，支持多轮工具调用与结果回传
- **会话上下文**：保持对话历史，支持连续的、上下文感知的交互
- **沙箱隔离**：可选的命令执行沙箱，通过临时目录隔离文件系统操作
- **工作目录追踪**：自动追踪和恢复 Shell 工作目录
- **实时流式输出**：支持命令执行的实时标准输出/错误回调
- **中文交互**：默认使用中文进行交互

---

## 项目架构

`
claude_code_for_py/
├── main.py                 # CLI 入口
├── desktop.py              # 桌面 GUI 入口 (基于 CustomTkinter)
├── api/                    # API 层
│   ├── api.py             # Anthropic 客户端封装，LLM 查询循环
│   ├── util.py            # 工具定义转 API Schema
│   └── __init__.py
├── constant/               # 常量/提示词
│   ├── SystemToolPrompt.py # 系统提示词生成
│   └── __init__.py
├── tools/                  # 工具定义
│   ├── Tool.py            # 工具注册中心 & 数据类型
│   ├── BashTool.py        # Shell 命令执行工具
│   ├── FileReadTool.py    # 文件读取工具
│   ├── shell.py           # Shell 执行器 (Bash/PowerShell 提供者)
│   └── __init__.py
└── util/                   # 工具函数
    ├── BaseInfo.py         # 平台信息获取
    ├── envoriment.py       # 环境变量读取 (BASE_URL, API_KEY)
    ├── lazyLoding.py       # 懒加载工具
    └── toolContext.py      # 工具执行上下文
`

---

## 快速开始

### 环境要求

- **Python** 3.10+
- **操作系统**：Windows / Linux / macOS

### 安装

`Bash
# 1. 克隆项目
git clone <your-repo-url>
cd claude_code_for_py

# 2. 创建虚拟环境（推荐）
python -m venv .venv

# 3. 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. 安装依赖
pip install anthropic customtkinter
`

### 配置环境变量

在运行前需要设置以下环境变量：

`Bash
# Windows (PowerShell)
$env:BASE_URL = "https://api.anthropic.com" (示例)
$env:API_KEY = "your-api-key-here" 

# Linux/macOS (Bash/Zsh)
export BASE_URL="https://api.anthropic.com"
export API_KEY="your-api-key-here"
`

可选环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| MAX_RETRIES | 3 | API 请求最大重试次数 |
| TIMEOUT_REQUEST | 30000 | 请求超时时间（毫秒） |

### 运行

`Bash
# CLI 模式
python main.py

# 桌面 GUI 模式
python desktop.py
`

---

## 使用指南

### CLI 模式

运行 python main.py 后，直接在终端输入你的指令：

`
请输入指令: 列出当前目录下的所有文件
请输入指令: 帮我创建一个名为 test 的文件夹
请输入指令: 读取 README.md 的内容
`

### 桌面 GUI 模式

运行 python desktop.py 会启动一个桌面窗口：

1. 在底部输入框输入你的问题
2. 按 Ctrl+Enter 或点击「发送」按钮
3. AI 的回复、工具调用信息会以气泡对话形式展示

界面特点：
- 用户消息靠右显示（绿色气泡）
- AI 回复靠左显示（白色气泡）
- 工具调用信息（米色气泡）
- 错误信息（红色气泡）

---

## 工具系统

Hong Code 内置两种工具，LLM 可根据用户需求自动选择和调用：

### 1. Bash 工具 (Shell 命令执行)

- **工具名**：Bash
- **参数**：command (必填) - 要执行的 Shell 命令
- **特性**：
  - 自动检测平台，Windows 使用 PowerShell，Linux/macOS 使用 Bash
  - 默认 30 秒超时
  - 自动追踪工作目录变化
  - 支持实时输出回调
  - 可选的沙箱隔离模式

### 2. Read 工具 (文件读取)

- **工具名**：Read
- **参数**：
  - ile_path (必填) - 文件路径（绝对或相对路径）
  - offset (可选) - 起始行号
  - limit (可选) - 读取行数
- **特性**：
  - 带行号输出，方便定位
  - 支持分页读取大文件
  - 自动扩展 ~ 路径

---

## 技术细节

### LLM 查询循环

`
用户输入 -> 构建消息上下文 -> 发送到 LLM
    -> LLM 返回 (文本/工具调用)
    -> 如果有工具调用:
        -> 执行工具 -> 将结果返回 LLM
        -> 循环直到 LLM 不再调用工具
    -> 返回最终文本回复
`

### 工具注册机制

项目使用简单的注册模式：

`python
from tools.Tool import toolDef, register_tools

# 定义工具
my_tool = toolDef(
    name="MyTool",
    description="工具描述",
    prompt=lambda **kw: "给 LLM 的工具描述提示词",
    input_schema={...},      # API 参数 Schema
    call=my_handler,         # 异步回调函数
    is_readonly=False        # 是否只读（可并发）
)

# 注册工具
register_tools(my_tool)
`

新工具只需定义并注册，即可被 LLM 自动发现和调用。

### Shell 执行器设计

	ools/shell.py 采用策略模式，根据平台自动选择 BashProvider 或 PowerShellProvider。执行时通过临时文件追踪工作目录变化，支持超时控制、异步取消和沙箱隔离。

---

## 扩展开发

### 添加新工具

1. 在 	ools/ 目录下创建新文件（如 WebSearchTool.py）
2. 定义工具：

`python
from tools.Tool import toolDef, register_tools

async def web_search(input_dict, ctx):
    query = input_dict["query"]
    # 实现搜索逻辑
    return {"results": [...]}

WebSearchTool = toolDef(
    name="WebSearch",
    description="搜索互联网",
    prompt=lambda **kw: "使用此工具搜索互联网获取最新信息...",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            }
        },
        "required": ["query"]
    },
    call=web_search,
    is_readonly=True
)

register_tools(WebSearchTool)
`

3. 在 	ools/__init__.py 中导入新工具：

`python
from .WebSearchTool import WebSearchTool
`

### 更换 LLM 模型

修改 pi/api.py 中 query 方法的 model 参数：

`python
response = self.client.messages.create(
    model="your-model-name",  # 修改这里
    ...
)
`

---

## 依赖项

| 包 | 用途 |
|---|---|
| nthropic | Anthropic API 客户端 |
| customtkinter | 桌面 GUI 框架 |
| 	kinter | Python 标准 GUI 库（通常内置） |

---

## 常见问题

### Q: 启动时报错 "缺少环境变量"
请确保已设置 BASE_URL 和 API_KEY 环境变量。

### Q: Windows 下中文输出乱码
shell.py 已使用系统 locale 编码处理输出。如果仍有问题，请检查终端的编码设置。

### Q: 命令执行超时
默认超时 30 秒。可以通过沙箱模式或调整 shell.py 中的超时参数来修改。

### Q: 如何添加更多工具？
参考上方「扩展开发 - 添加新工具」章节。

---

## 许可证

MIT License

---

## 作者

Hong Code - AcNHong CLI

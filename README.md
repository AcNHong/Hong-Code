# AcNHong CLI

基于 Python 的 CLI 工具，作为自定义大语言模型（LLM）的交互前端，支持通过自然语言指令调用多种工具（Bash、文件读写等）来完成自动化任务。

## 项目结构

```
├── main.py                  # 入口文件，启动交互循环
├── api/
│   ├── __init__.py
│   ├── api.py               # LLM 查询接口（QueryModel）
│   └── util.py              # API 工具函数
├── tools/
│   ├── __init__.py
│   ├── Tool.py              # 工具注册与定义
│   ├── BashTool.py          # Bash/Shell 命令执行工具
│   ├── FileReadTool.py      # 文件读取工具
│   ├── FileWriteTool.py     # 文件写入工具
│   └── shell.py             # Shell 执行器实现
├── constant/
│   ├── __init__.py
│   └── SystemToolPrompt.py  # 系统提示词配置
├── util/
│   ├── __init__.py
│   ├── BaseInfo.py          # 基础信息获取
│   ├── envoriment.py        # 环境配置
│   ├── lazyLoding.py        # 懒加载工具
│   └── toolContext.py       # 工具执行上下文
└── test.py                  # 测试文件
```

## 功能特性

- **自然语言交互**：通过命令行输入指令，LLM 自动解析并调用对应工具
- **Bash 执行**：支持 Windows (PowerShell) 和 Linux 环境下的 Shell 命令执行
- **文件操作**：支持文件的读取和写入
- **工具扩展**：模块化工具设计，方便扩展新工具

## 快速开始

### 环境要求

- Python 3.8+
- 依赖安装（如需要）：

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

启动后，在 `请输入指令:` 提示符下输入你的需求即可。

## 使用示例

```
请输入指令: 查看当前目录的文件
请输入指令: 读取 README.md 文件内容
请输入指令: 创建一个名为 hello.txt 的文件
```

## 技术栈

- **异步编程**：基于 `asyncio` 实现异步任务调度
- **模块化设计**：API、工具、常量、工具类分离，职责清晰
- **可扩展**：通过 `Tool.py` 注册新工具即可扩展功能

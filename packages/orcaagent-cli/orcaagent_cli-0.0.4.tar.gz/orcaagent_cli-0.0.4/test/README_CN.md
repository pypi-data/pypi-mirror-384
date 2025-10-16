# OrcaAgent React 模板

🇨🇳 中文 | [🇺🇸 English](README.md)

[![CI](https://github.com/langchain-ai/react-agent/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/react-agent/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/react-agent/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/react-agent/actions/workflows/integration-tests.yml)
[![Open in - LangGraph Studio](https://img.shields.io/badge/Open_in-LangGraph_Studio-00324d.svg?logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4NS4zMzMiIGhlaWdodD0iODUuMzMzIiB2ZXJzaW9uPSIxLjAiIHZpZXdCb3g9IjAgMCA2NCA2NCI+PHBhdGggZD0iTTEzIDcuOGMtNi4zIDMuMS03LjEgNi4zLTYuOCAyNS43LjQgMjQuNi4zIDI0LjUgMjUuOSAyNC41QzU3LjUgNTggNTggNTcuNSA1OCAzMi4zIDU4IDcuMyA1Ni43IDYgMzIgNmMtMTIuOCAwLTE2LjEuMy0xOSAxLjhtMzcuNiAxNi42YzIuOCAyLjggMy40IDQuMiAzLjQgNy42cy0uNiA0LjgtMy40IDcuNkw0Ny4yIDQzSDE2LjhsLTMuNC0zLjRjLTQuOC00LjgtNC44LTEwLjQgMC0xNS4ybDMuNC0zLjRoMzAuNHoiLz48cGF0aCBkPSJNMTguOSAyNS42Yy0xLjEgMS4zLTEgMS43LjQgMi41LjkuNiAxLjcgMS44IDEuNyAyLjcgMCAxIC43IDIuOCAxLjYgNC4xIDEuNCAxLjkgMS40IDIuNS4zIDMuMi0xIC42LS42LjkgMS40LjkgMS41IDAgMi43LS41IDIuNy0xIDAtLjYgMS4xLS44IDIuNi0uNGwyLjYuNy0xLjgtMi45Yy01LjktOS4zLTkuNC0xMi4zLTExLjUtOS44TTM5IDI2YzAgMS4xLS45IDIuNS0yIDMuMi0yLjQgMS41LTIuNiAzLjQtLjUgNC4yLjguMyAyIDEuNyAyLjUgMy4xLjYgMS41IDEuNCAyLjMgMiAyIDEuNS0uOSAxLjItMy41LS40LTMuNS0yLjEgMC0yLjgtMi44LS44LTMuMyAxLjYtLjQgMS42LS41IDAtLjYtMS4xLS4xLTEuNS0uNi0xLjItMS42LjctMS43IDMuMy0yLjEgMy41LS41LjEuNS4yIDEuNi4zIDIuMiAwIC43LjkgMS40IDEuOSAxLjYgMi4xLjQgMi4zLTIuMy4yLTMuMi0uOC0uMy0yLTEuNy0yLjUtMy4xLTEuMS0zLTMtMy4zLTMtLjUiLz48L3N2Zz4=)](https://langgraph-studio.vercel.app/templates/open?githubUrl=https://github.com/langchain-ai/react-agent)

## 📖 项目简介

**OrcaAgent** 是基于 LangGraph 二次开发的 Agent 开发框架，它深度融合 LangChain/LangGraph 的丰富生态资源，并且基于行业最佳实践做了一些必要的封装，提供了丰富的 Agent 场景化模板和脚手架工具。

### 🌟 核心特点

- **开箱即用**：预置标准化组件，可快速部署业务场景
- **生态兼容性**：无缝复用 LangChain 工具链及 LangGraph 工作流引擎

## 🎯 React 模板特性

该项目是 OrcaAgent 提供的基于 React 模式的 Agent 模板，专门针对工具调用和快问快答场景进行了优化：

### ✨ 主要优势

1. **智能工具过滤**
   - 在执行 React 之前进行工具过滤
   - 适用于拥有大量工具的 Agent
   - 有效减少 token 使用率，提升回答准确率

2. **Tool-Only 模式**
   - 完全依赖工具调用来回答问题
   - 限制大模型回答范围，避免自由发挥
   - 确保回答质量，不懂的问题不回答

3. **模型兼容性**
   - 兼容 OpenAI 协议的大模型
   - 支持用户自部署模型（以 `compatible_openai/` 开头）
   - 灵活的模型配置选项


## 🚀 快速开始

### 环境准备

1. **创建环境配置文件**
```bash
cp .env.example .env
```

2. **配置 API 密钥**

在 `.env` 文件中定义必要的 API 密钥。默认使用 [Tavily](https://tavily.com/) 搜索工具，需要在 [这里](https://app.tavily.com/sign-in) 创建 API 密钥。

### 模型配置

默认模型配置：
```yaml
model: anthropic/claude-3-5-sonnet-20240620
```

#### Anthropic 配置
1. 获取 [Anthropic API key](https://console.anthropic.com/)
2. 添加到 `.env` 文件：
```
ANTHROPIC_API_KEY=your-api-key
```

#### OpenAI 配置
1. 获取 [OpenAI API key](https://platform.openai.com/signup)
2. 添加到 `.env` 文件：
```
OPENAI_API_KEY=your-api-key
```

#### OpenAI 兼容协议配置
1. 编辑 `.env` 文件：
```
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=your-base-url
OPENAI_MODEL_NAME=your-model-name
```

## 🛠️ 使用方法

### CLI 快速开始

#### 1. 下载 CLI
```bash
pip install orcaagent-cli
```

#### 2. 使用 CLI 下载现有模板

下载模板 [TEMPLATE] 到路径 [PATH]：
```bash
orcaagent new [PATH] [TEMPLATE]
```
也可以直接使用 `orcaagent new` 命令互动下载选择模板

#### 3. 配置 .env
- 在刚刚下载的模板目录下创建 `.env`
- 获取需要的 API_KEY 填入 `.env`，例如：
  - TAVILY_API_KEY
  - LANGSMITH_API_KEY
  - LLM API KEY

#### 4. 调试开发
进入刚刚下载的模板目录下：
```bash
cd [PATH]
```
安装必要依赖：
```bash
pip install -e .
```
启动调试：
```bash
orcaagent dev
```

### CLI 功能介绍

#### 浏览 CLI 功能
```bash
orcaagent --help
```

#### 浏览现有模板
```bash
orcaagent template
```

#### 利用现有模板创建项目
1. `orcaagent new [PATH] [TEMPLATE]`
2. 也可以直接使用 `orcaagent new` 命令互动下载选择模板

#### 调试开发
在本地启动轻量级服务器调试开发：
```bash
orcaagent dev
```

#### 利用本地 Docker 启动完整 OrcaAgent 服务
*需要先在本地安装并运行 Docker*
```bash
orcaagent up
```

#### 生成 Dockerfile
```bash
orcaagent dockerfile [SAVE_PATH]
```
例如：`orcaagent dockerfile Dockerfile`

#### 生成 Dockerfile 和 docker-compose.yml
```bash
orcaagent dockerfile --config [CONFIG] --add-docker-compose ./Dockerfile
```
例如：`orcaagent dockerfile --config orcaagent.json --add-docker-compose ./Dockerfile`

#### 打包构建镜像
```bash
orcaagent build --tag [TAG TEXT]
```
例如：`orcaagent build --tag my-agent`


## 🔧 自定义配置

### 1. 添加 MCP Server

在 `src/react_agent/mcp_server_configs.py` 中删除或添加更多的 MCP Server：

```python
MCP_SERVERS = {
        "math": {
            "command": "python",
            # Make sure to update to the full absolute path to your math_server.py file
            "args": ["/path/to/math_server.py"],
            "transport": "stdio",
        },
        "weather": {
            # Make sure you start your weather server on port 8000
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http",
        }
    }
```

### 2. 添加新工具

在 `src/react_agent/tools.py` 中扩展 Agent 功能：

```python
from langchain.tools import tool

@tool
def custom_tool(query: str) -> str:
    """自定义工具描述"""
    # 工具实现逻辑
    return result
```

### 3. 选择不同模型

通过运行时上下文选择兼容的聊天模型：
```python
# 示例：使用 OpenAI GPT-4
model = "openai/gpt-4-turbo-preview"

# 示例：使用兼容 OpenAI 协议的自部署模型
model = "compatible_openai/DeepSeek-V3-0324"
```

### 4. 自定义提示词

在 `src/react_agent/prompts.py` 中更新系统提示词：

```python
SYSTEM_PROMPT = """
你是一个专业的 AI 助手，专门处理...
"""
```

### 5. 修改推理流程

在 `src/react_agent/graph.py` 中调整 Agent 的推理过程：
- 修改 ReAct 循环
- 添加额外的决策步骤
- 自定义节点和边

## 📁 项目结构

```
react-agent/
├── src/
│   ├── common/           # 通用工具和配置
│   └── react_agent/      # React Agent 核心代码
│       ├── graph.py      # 图结构定义
│       ├── tools.py      # 工具定义
│       ├── prompts.py    # 提示词模板
│       └── main.py       # 主入口
├── static/               # 静态资源
├── tests/                # 测试文件
│   ├── unit_tests/       # 单元测试
│   └── integration_tests/ # 集成测试
├── .env.example          # 环境配置示例
└── README.md
```

## 🧪 开发调试

### 本地开发

在迭代图结构时，您可以：
- 编辑过去的状态并从过去状态重新运行应用
- 利用热重载自动应用本地更改
- 在 Agent 调用工具前添加中断点
- 更新默认系统消息以采用特定角色
- 添加额外的节点和边

### 创建新线程

使用右上角的 `+` 按钮创建全新线程，清除之前的历史记录。

## 📚 相关资源

- [LangGraph 文档](https://github.com/langchain-ai/langgraph)

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

如有问题或建议，请：
- 提交 [Issue](https://github.com/OrcaAgent-AI/react-agent/issues)
- 发送邮件至：jubaoliang@gmail.com
- 加入我们的社区讨论群

# LumaK

LumaK 是一个 local-first 的代码库理解与安全修改 Agent。它通过模型的 tool calling 能力，在受限 workspace 内读取、搜索和修改代码文件，帮助开发者理解项目结构、定位相关代码，并执行小范围的可审计改动。

当前重点是把 agent runtime、文件工具安全边界、session memory、trace 和 Web UI 接入基础打稳。它不是通用聊天壳，也不是全功能 IDE，第一版先聚焦本地代码分析和安全编辑。

## 当前能力

- MiniMax、Anthropic、OpenAI、DeepSeek provider 配置
- CLI 单轮提问和多轮对话
- 模型自主选择工具并执行多步 tool loop
- 本地文件读取、写入、搜索和 glob 查找
- `safe_edit` 精确替换和 diff 预览
- workspace 路径限制和忽略目录保护
- 工具参数校验和可读错误返回
- 内置 hook 事件系统
- trace 作为内置 hook 写入 `.trace/`
- session memory 持久化到 `.memory/`
- 静态 Web UI 雏形，后续通过 gateway API 接入 runtime

## 快速开始

1. 安装依赖：

```shell
uv sync
```

2. 配置环境变量：

```shell
cp .env.example .env
```

示例：

```env
LLM_PROVIDER=minimax
MINIMAX_API_KEY=sk-your-key
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL_ID=MiniMax-M2.7
```

`LLM_PROVIDER` 支持 `minimax`、`anthropic`、`openai`、`deepseek`。

Anthropic：

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL_ID=claude-sonnet-4-5
```

OpenAI：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL_ID=gpt-5.1
```

DeepSeek：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_MODEL_ID=deepseek-chat
```

3. 运行 CLI：

```shell
uv run lumak
```

也可以发送一次性 prompt：

```shell
uv run lumak "这个项目的入口文件在哪里？"
```

## Web UI

前端代码位于 `web/`，当前是静态聊天界面雏形：

```shell
cd web
npm install
npm run build
```

第一版 Web UI 还没有接入后端 API。下一步计划是增加一个本地 gateway API，让前端通过 HTTP 调用 `Agent`、读取 session memory、查看 trace 和工具调用过程。

## 工具列表

| Tool | 作用 |
| --- | --- |
| `glob` | 按 glob pattern 查找 workspace 内文件 |
| `read_file` | 读取 workspace 内的 UTF-8 文本文件 |
| `search_text` | 在 workspace 内搜索关键词，返回文件路径、行号和命中行 |
| `write_file` | 在 workspace 内写入文本文件 |
| `safe_edit` | 对文件做一次精确文本替换，支持 diff 预览 |

## 安全边界

LumaK 的文件工具默认只允许访问当前 workspace：

- 拒绝 `../` 等越界路径
- 拒绝访问被忽略目录，例如 `.git` 和 `.venv`
- 只按 UTF-8 文本读取和修改文件
- 搜索工具带有结果数量限制和超时控制
- 修改类工具失败时返回明确错误，不静默覆盖
- `safe_edit` 写入前要求 `old_text` 精确匹配，并返回 unified diff

## Runtime 设计

核心闭环：

```text
user message
  -> load session memory
  -> model request
  -> optional tool call
  -> tool result back to model
  -> final answer
  -> persist session memory
  -> emit trace events
```

`trace` 和 `memory` 分工不同：

- `trace` 是审计日志，记录事件、工具调用、耗时和最终输出，默认写入 `.trace/`。
- `memory` 是模型上下文，保存同一 `session_id` 下的 user / assistant / tool result messages，默认写入 `.memory/`。

Hook 系统用于事件分发。`TraceHook` 是内置 hook；用户 hook 可用于审计、统计或后续策略控制，但 session memory 是 runtime 的显式依赖，不通过 hook 隐式写入。

## 项目结构

```text
.
├─ agent/
│  ├─ CLI/
│  │  └─ app.py
│  ├─ LLM/
│  │  ├─ anthropic_provider.py
│  │  ├─ client.py
│  │  ├─ deepseek.py
│  │  ├─ minimax.py
│  │  └─ openai_compatible.py
│  ├─ memory/
│  │  └─ store.py
│  ├─ runtime/
│  │  ├─ agent/
│  │  │  └─ agent.py
│  │  ├─ hooks.py
│  │  └─ loop.py
│  ├─ tools/
│  │  ├─ filesystems.py
│  │  ├─ registry.py
│  │  └─ shell.py
│  ├─ trace/
│  │  └─ trace.py
│  └─ config.py
├─ docs/
├─ evals/
├─ tests/
├─ web/
├─ pyproject.toml
└─ README.md
```

## 测试

```shell
uv run pytest
```

测试重点覆盖：

- workspace 路径限制和忽略目录保护
- 文件读取、写入、搜索和 glob
- `safe_edit` diff 预览与写入行为
- LLM provider 配置、工厂选择和 OpenAI-compatible adapter
- fake LLM 驱动的完整 tool-calling flow
- hook 事件和 trace 写入
- session memory 的 append/load/clear 和 loop 持久化
- tool registry 的错误处理
- agent wrapper 的参数传递

## 路线图

- 增加本地 gateway API，连接 Web UI 和 Agent runtime
- 前端接入 `/api/chat`、session memory 和 trace viewer
- 扩充 `evals/` 任务集和失败样例
- 增加 provider-specific 的真实 API smoke test 文档
- 增加架构图和 demo transcript
- 在真实仓库上验证代码理解和安全修改任务

## 贡献

欢迎贡献测试、评测任务、文档和小范围 runtime 改进。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

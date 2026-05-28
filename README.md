<p align="center">
  <img src="web/assets/lumak-logo.png" alt="LumaK logo" width="72" />
</p>

# LumaK

LumaK 是一个 **local-first 的代码库理解与安全修改 Agent**。它在受限 workspace 内通过模型 tool calling 读取、搜索、分析和修改代码，帮助开发者理解项目结构、定位相关实现，并完成小范围、可审计的代码改动。

这个项目的重点不是做一个全能聊天机器人，而是把 agent runtime 的核心闭环做扎实：工具选择、路径约束、错误处理、trace、session memory、技能注入，以及可以跑通的 CLI / TUI / Web UI 入口。

## 当前能力

- 支持 MiniMax、Anthropic、OpenAI、DeepSeek，以及自定义 OpenAI-compatible provider
- 支持 CLI 单轮提问、多轮对话和 TypeScript 终端 TUI
- 支持模型自主选择工具并执行多步 tool loop
- 支持本地文件读取、写入、搜索、glob 查找和精确替换
- 支持 Python AST 级代码分析：文件 outline、workspace code map、symbol lookup
- 支持 `safe_edit` 精确替换，并返回 unified diff
- 支持 workspace 路径限制和忽略目录保护
- 支持工具参数校验和可读错误返回
- 支持 `.skills/` 本地技能加载、触发词选择和 system prompt 注入
- 支持 hook 事件系统和实时 agent event 转发
- 支持 trace 写入 `.trace/`
- 支持 session memory 持久化到 `.memory/`
- 提供 WebSocket gateway，连接 Web UI、Agent runtime、memory 和 trace
- 提供静态 Web UI，展示会话、项目信息、工具事件、trace 和模型配置

## 快速开始

### 1. 安装依赖

```shell
uv sync
```

### 2. 配置环境变量

```shell
cp .env.example .env
```

`LLM_PROVIDER` 支持：

- `minimax`
- `anthropic`
- `openai`
- `deepseek`

MiniMax 示例：

```env
LLM_PROVIDER=minimax
MINIMAX_API_KEY=sk-your-key
MINIMAX_BASE_URL=https://your-minimax-compatible-endpoint
MINIMAX_MODEL_ID=your-model-id
```

Anthropic 示例：

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL_ID=claude-sonnet-4-5
```

OpenAI 示例：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL_ID=gpt-5.1
```

DeepSeek 示例：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL_ID=deepseek-chat
```

### 3. 用 `uv run` 启动

启动多轮对话：

```shell
uv run lumak
# 或显式使用子命令
uv run lumak cli
```

发送一次性 prompt：

```shell
uv run lumak "这个项目的入口文件在哪里？"
```

调整模型最大输出 token：

```shell
uv run lumak --max-tokens 2048 "总结 agent/runtime/loop.py 的执行流程"
```

运行 Web UI 和 gateway：

```shell
cd web
npm install
npm run build
cd ..

uv run lumak web
```

启动后打开：

- Web UI: `http://127.0.0.1:4173`
- Gateway: `ws://127.0.0.1:8765`

在服务器上对外访问时，不要只绑定 `127.0.0.1`，需要监听所有网卡：

```shell
uv run lumak web --host 0.0.0.0 --gateway-host 0.0.0.0
```

然后打开：

```text
http://<server-ip>:4173
```

同时确保 `4173` 和 `8765` 两个端口都已经放行。Web 页面会根据当前访问地址自动连接 gateway；如果你的反向代理或端口映射比较特殊，也可以手动指定：

```text
http://<server-ip>:4173?gateway=ws://<server-ip>:8765
```

### 4. 运行终端 TUI

```shell
uv run lumak tui
```

TUI 代码位于 `tui/`，使用 TypeScript 实现，并通过本地 WebSocket gateway 连接 agent runtime。也可以手动构建和测试：

```shell
cd tui
npm install
npm run build
npm test
```

TUI 默认会自动启动本地 gateway，展示当前 session、模型请求、技能选择、工具调用和最终回答。退出可以输入 `/quit`、`/exit`，或按 `Ctrl-C`。

`lumak tui` 会启动已构建好的 TypeScript TUI，需要本机有 Node.js。如果修改了 `tui/src/`，先运行 `cd tui && npm run build` 更新 `tui/dist/`。

## 安装成 `lumak` 命令

如果你希望在任意目录直接运行 `lumak web`、`lumak cli`、`lumak tui`，可以从源码安装成本机工具。

```shell
git clone <repo-url> lumaK
cd lumaK
```

先构建前端和 TUI 产物。构建产物不提交到 Git，安装或部署时现场生成：

```shell
uv sync

cd web
npm install
npm run build
cd ..

cd tui
npm install
npm run build
cd ..
```

开发期推荐直接 editable 安装：

```shell
uv tool install --editable .
```

安装后可以直接运行：

```shell
lumak cli
lumak gateway
lumak tui
lumak web
```

如果要生成 wheel 再安装：

```shell
uv build
uv tool install --reinstall dist/lumak-0.1.0-py3-none-any.whl
```

服务器上用已安装的 `lumak` 命令启动：

```shell
lumak web --host 0.0.0.0 --gateway-host 0.0.0.0
```

## 两种启动方式怎么选

- `uv run lumak ...`：适合开发、调试、刚 clone 下来验证。优点是不用安装全局命令，依赖跟仓库绑定。
- `lumak ...`：适合你自己的机器或服务器长期使用。优点是命令短，可以在别的 workspace 里直接启动。

暂时不建议把 Homebrew 作为主安装方式。brew 需要稳定的 release 包、formula 维护、资源打包策略和版本升级测试；在这些没有固定下来之前，README 里写 brew 只会让安装路径看起来更正式，但失败面更大。等 `uv tool install` 这条链路稳定后，再补 brew formula 更合适。

可以用下面命令检查入口是否安装成功：

```shell
uv run lumak --help
lumak --help
```

## Web UI 与 Gateway

前端代码位于 `web/`，本地 gateway 位于 `gateway/`。Web UI 通过 WebSocket 连接 runtime，支持聊天、项目信息、历史会话、trace 查询和运行时事件展示。

`lumak web` 会直接服务已构建的 `web/dist/`，并在需要时自动启动 gateway。如果 gateway 或 Web 端口已经被占用，会复用现有服务。

Web 和 gateway 也可以分开启动：

```shell
uv run lumak gateway
uv run lumak web
```

指定 workspace：

```shell
uv run lumak gateway --workspace /path/to/your/project
# 或
LUMAK_WORKSPACE=/path/to/your/project uv run lumak gateway
```

默认情况下，gateway 会把启动它时所在的目录作为 `WORKSPACE`。如果浏览器前端拿不到本地目录的绝对路径，推荐直接在目标项目目录启动 gateway：

```shell
cd /path/to/your/project
uv run --project /path/to/lumaK lumak gateway
```

常用 gateway 消息类型：

| Type | 作用 |
| --- | --- |
| `chat` | 发送用户消息并触发 agent runtime |
| `project.list` / `project.get` | 查询当前 workspace 项目信息 |
| `project.switch` | 为指定 session 切换 workspace |
| `conversation.list` / `conversation.get` | 查询会话历史 |
| `memory.get` | 查询 session memory |
| `trace.get` | 查询 session trace events |
| `ping` | 健康检查 |

## Agent Runtime

核心闭环：

```text
user message
  -> load session memory
  -> select local skills
  -> model request with tools
  -> optional tool calls
  -> execute tools inside workspace guard
  -> tool results back to model
  -> final answer
  -> persist session memory
  -> emit trace and live events
```

主要入口：

- `agent/CLI/app.py`：CLI 入口，负责参数解析、单轮运行和多轮对话
- `tui/src/index.ts`：终端 TUI，展示 runtime 事件和对话输出
- `agent/runtime/agent/agent.py`：Agent wrapper 和运行配置
- `agent/runtime/loop.py`：tool-calling 主循环
- `agent/LLM/client.py`：根据 `LLM_PROVIDER` 创建默认模型客户端
- `gateway/app.py`：WebSocket gateway，连接 Web UI、runtime、memory 和 trace

## 工具列表

| Tool | 作用 |
| --- | --- |
| `glob` | 按 glob pattern 查找 workspace 内文件 |
| `read_file` | 读取 workspace 内的 UTF-8 文本文件，可限制读取行数 |
| `search_text` | 在 workspace 内搜索关键词，返回路径、行号和命中行 |
| `write_file` | 在 workspace 内写入 UTF-8 文本文件 |
| `safe_edit` | 对文件做一次精确文本替换，支持 diff 预览 |
| `file_outline` | 返回单个 Python 文件的 AST outline，包括 imports、classes、functions、methods 和行号 |
| `code_map` | 扫描 workspace 内 Python 文件并生成结构化 code map |
| `symbol_lookup` | 按精确名称查找 Python class、function 或 method 定义 |

`agent/tools/registry.py` 负责向模型暴露工具 schema，并把工具调用分发到具体实现。`agent/tools/filesystems.py` 负责路径校验、文件操作、搜索和错误处理。`agent/tools/code_analysis.py` 负责代码分析工具，底层基于 `agent/analysis/` 的 Python AST 索引。

## 安全边界

文件和代码分析工具默认只允许访问当前 workspace：

- 拒绝 `../` 等越界路径
- 拒绝访问被忽略目录，例如 `.git`、`.venv`、`__pycache__`
- 只按 UTF-8 文本读取和修改文件
- 搜索工具带有结果数量限制和超时控制
- 修改类工具失败时返回明确错误，不静默覆盖
- `safe_edit` 写入前要求 `old_text` 精确匹配，并返回 unified diff
- 代码分析工具拒绝绝对路径和越界 glob pattern

## Skills

LumaK 支持从 `.skills/` 加载本地技能。每个技能目录包含：

```text
.skills/<skill-name>/
├─ _meta.json
└─ SKILL.md
```

`_meta.json` 定义技能名、版本、描述和触发词；`SKILL.md` 定义注入给模型的技能正文。运行时会根据用户消息选择匹配技能，并把选中的技能内容渲染进 system prompt。

相关代码：

- `agent/skills/store.py`：加载和解析技能
- `agent/skills/selector.py`：根据显式名称或触发词选择技能
- `agent/skills/prompt.py`：渲染技能 system prompt

## Trace 与 Memory

`trace` 和 `memory` 分工不同：

- `trace` 是审计日志，记录 session、模型请求、工具调用、耗时、成功失败和最终输出，默认写入 `.trace/`
- `memory` 是模型上下文，保存同一 `session_id` 下的 user、assistant 和 tool result messages，默认写入 `.memory/`

Hook 系统用于事件分发。`TraceHook` 是内置 hook；`LiveEventHook` 会把 runtime 事件发布给 gateway 订阅者；用户 hook 可用于审计、统计或后续策略控制。Session memory 是 runtime 的显式依赖，不通过 hook 隐式写入。

## 项目结构

```text
.
├─ agent/
│  ├─ CLI/                  # Python CLI
│  ├─ LLM/                  # provider config 和客户端适配
│  ├─ analysis/             # Python AST outline、index 和 symbol 分析
│  ├─ memory/               # session memory
│  ├─ runtime/              # Agent wrapper、hook、tool loop
│  ├─ skills/               # 本地技能加载与选择
│  ├─ tools/                # 工具 schema、注册、文件系统工具和代码分析工具
│  ├─ trace/                # trace 事件写入
│  └─ config.py             # 环境变量配置
├─ gateway/                 # WebSocket gateway、实时事件和 trace reader
├─ docs/                    # 项目方向、范围和路线图
├─ evals/                   # 评测任务草案
├─ tests/                   # 单测和 runtime flow 测试
├─ web/                     # 静态 Web UI
├─ .env.example
├─ pyproject.toml
└─ README.md
```

## 测试

Python 测试：

```shell
uv run pytest
```

前端测试和类型检查：

```shell
cd web
npm test
npm run typecheck
```

测试重点覆盖：

- workspace 路径限制和忽略目录保护
- 文件读取、写入、搜索、glob 和 `safe_edit`
- Python AST outline、code map 和 symbol lookup
- LLM provider 配置、工厂选择和 OpenAI-compatible adapter
- fake LLM 驱动的完整 tool-calling flow
- hook 事件、live event 和 trace 写入
- session memory 的 append、load、clear、list 和 loop 持久化
- skill 加载、选择和 prompt 渲染
- gateway 消息处理、项目信息、会话历史和 request-level provider config
- TypeScript TUI 文本格式化、参数解析和事件展示
- Web UI 状态转换、配置映射和工具事件渲染

## 下一步

- 扩充 `evals/` 任务集和失败样例
- 增加更细粒度的 trace viewer 和工具调用详情
- 支持 Web UI 附件上传和多模态输入
- 为代码分析工具补更多语言和跨文件关系

<p align="center">
  <img src="web/assets/lumak-logo.png" alt="LumaK logo" width="72" />
</p>

# LumaK

**本地优先的代码库理解与安全修改 Agent 运行时。** LumaK 在受限 workspace 内通过 LLM tool-calling 读取、搜索、分析和修改代码。这是一个工程工具，而非通用聊天机器人——核心目标是让 agent 闭环足够健壮：工具选择、路径约束、错误处理、trace、会话记忆、技能注入，以及可用的 CLI / TUI / Web UI 入口。

## 快速开始

```shell
uv sync
cp .env.example .env   # 配置 LLM provider 和 API key

# 交互式对话
uv run lumak

# 单次提问
uv run lumak "项目入口在哪？"

# Web UI (http://127.0.0.1:4173)
uv run lumak web

# 终端 TUI
uv run lumak tui
```

## 功能特性

- **多 LLM provider 支持** — MiniMax、Anthropic、OpenAI、DeepSeek，以及自定义 OpenAI-compatible 端点
- **8 个内置工具** — `read_file`、`write_file`、`glob`、`search_text`、`safe_edit`、`file_outline`、`code_map`、`symbol_lookup`
- **Python AST 分析** — 文件结构预览、workspace 代码地图、符号查找，无外部依赖
- **安全编辑** — `safe_edit` 要求 `old_text` 精确匹配，返回 unified diff，失败时自动回滚
- **Workspace 安全** — 路径逃逸防护、忽略目录过滤（`.git`、`.venv`、`node_modules` 等）、UTF-8 强制校验
- **会话记忆** — JSONL 持久化，按 session 自动加载
- **Trace / 审计日志** — 完整事件链路写入 `.trace/`（JSONL）
- **本地技能系统** — `.skills/` 目录，基于触发词匹配与 system prompt 注入
- **Hook / 事件系统** — 可扩展的回调机制，支持 trace、实时事件、回滚和自定义行为
- **三种 UI 模式** — Python CLI、TypeScript 终端 TUI、Web UI（统一通过 WebSocket gateway 连接）
- **工具去重与上下文管理** — 避免重复执行，优雅处理 token 超限

## 架构

```
user message
  -> 加载会话记忆
  -> 选择本地技能
  -> 模型请求（含工具定义）
  -> 工具调用（workspace 边界内执行）
  -> 工具结果返回模型
  -> 最终回答
  -> 持久化会话记忆
  -> 写入 trace 和实时事件
```

### 项目结构

```
.
├─ agent/               # 核心 Python 运行时
│  ├─ CLI/              # Python CLI 入口
│  ├─ LLM/              # Provider 配置与客户端适配
│  ├─ analysis/         # Python AST 分析（outline、index、symbol）
│  ├─ memory/           # 会话记忆（JSONL）
│  ├─ runtime/          # Agent 封装、hook、tool loop、session rollback
│  ├─ skills/           # 本地技能加载、选择、prompt 渲染
│  ├─ tools/            # 工具 schema、注册、文件系统与分析工具
│  ├─ trace/            # Trace 事件写入
│  └─ config.py         # 环境变量配置
├─ gateway/             # WebSocket gateway，连接 Web UI 与 runtime
├─ web/                 # 静态 Web UI（vanilla TS + Vite）
├─ tui/                 # 终端 TUI（TypeScript）
├─ shared/              # 共享 TypeScript gateway 合约类型
├─ tests/               # Python 测试套件（pytest）
├─ docs/                # 项目方向、架构、路线图
├─ evals/               # 评测任务草案
├─ .skills/             # 示例本地技能
├─ .env.example
├─ pyproject.toml
└─ README.md
```

## 工具列表

| 工具 | 说明 |
| --- | --- |
| `glob` | 按 glob pattern 查找 workspace 内文件 |
| `read_file` | 读取 UTF-8 文本文件，可限制行数 |
| `search_text` | 搜索关键词，返回路径、行号与匹配行 |
| `write_file` | 写入 UTF-8 文本文件 |
| `safe_edit` | 精确文本替换，返回 unified diff |
| `file_outline` | Python AST 结构预览——import、class、function、method 及行号 |
| `code_map` | 扫描 workspace Python 文件，生成结构化代码地图 |
| `symbol_lookup` | 按精确定义名称查找 Python class、function 或 method |

## 配置

设置 `LLM_PROVIDER` 为 `minimax`、`anthropic`、`openai` 或 `deepseek`。

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL_ID=claude-sonnet-4-5
```

参见 `.env.example` 获取所有 provider 选项。

## Web UI 与 Gateway

```shell
uv run lumak web                          # 启动 Web 服务 + gateway
uv run lumak gateway --workspace /path   # 仅启动 gateway
```

Web UI 通过 WebSocket 连接 agent runtime，支持聊天、项目信息、历史会话、trace 查询和实时 agent 事件。

Gateway 消息类型：

| 类型 | 作用 |
| --- | --- |
| `chat` | 发送用户消息，触发 agent runtime |
| `project.list` / `project.get` | 查询 workspace 项目信息 |
| `project.switch` | 切换 session 的 workspace |
| `conversation.list` / `conversation.get` | 查询会话历史 |
| `memory.get` | 查询会话记忆 |
| `trace.get` | 查询 session trace 事件 |
| `ping` | 健康检查 |

## 技能系统

LumaK 从 `.skills/` 加载本地技能。每个技能目录包含：

```
.skills/<skill-name>/
├─ _meta.json      # 名称、版本、描述、触发词
└─ SKILL.md        # 注入到 system prompt 的技能指令
```

## 测试

```shell
uv run pytest                 # Python 测试
cd web && npm test            # Web UI 测试
cd tui && npm test            # TUI 测试
```

## 安装为全局命令

```shell
uv tool install --editable .
lumak cli      # 或: lumak web | lumak tui | lumak gateway
```

## 许可证

MIT

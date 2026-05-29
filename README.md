<p align="center">
  <img src="web/assets/lumak-logo.png" alt="LumaK logo" width="72" />
</p>

<p align="center">
  <a href="README.zh.md">中文</a> · <strong>English</strong>
</p>

# LumaK

**Local codebase understanding and safe-editing agent runtime.** LumaK operates inside a restricted workspace, using LLM tool-calling to read, search, analyze, and modify code. It's an engineering tool, not a general chatbot — the focus is on making the agent loop robust: tool selection, path constraints, error handling, tracing, session memory, skill injection, and functional CLI / TUI / Web UI entry points.

## Quick Start

```shell
uv sync
cp .env.example .env   # configure your LLM provider and API key

# Interactive chat
uv run lumak

# Single prompt
uv run lumak "Where is the entry point?"

# Web UI (http://127.0.0.1:4173)
uv run lumak web

# Terminal TUI
uv run lumak tui
```

## Features

- **Multi-provider LLM support** — MiniMax, Anthropic, OpenAI, DeepSeek, and custom OpenAI-compatible endpoints
- **8 built-in tools** — `read_file`, `write_file`, `glob`, `search_text`, `safe_edit`, `file_outline`, `code_map`, `symbol_lookup`
- **Python AST analysis** — file outlines, workspace code maps, and symbol lookups, no external dependencies
- **Safe editing** — `safe_edit` requires exact `old_text` match, returns unified diff, with automatic rollback on failure
- **Workspace security** — path escape prevention, ignored directory filtering (`.git`, `.venv`, `node_modules`, etc.), UTF-8 enforcement
- **Session memory** — JSONL-based persistence per session, automatically loaded on continuation
- **Trace / audit logging** — full event trail written to `.trace/` as JSONL
- **Local skill system** — `.skills/` directories with trigger-word-based selection and system prompt injection
- **Hook / event system** — extensible callbacks for trace, live events, rollback, and custom behavior
- **Three UI modes** — Python CLI, TypeScript terminal TUI, Web UI (all connecting through a WebSocket gateway)
- **Tool deduplication & context management** — avoids redundant execution, handles token limits gracefully

## Architecture

```
user message
  -> load session memory
  -> select local skills
  -> model request with tools
  -> optional tool calls (inside workspace guard)
  -> tool results back to model
  -> final answer
  -> persist session memory
  -> emit trace and live events
```

### Project Layout

```
.
├─ agent/               # Core Python runtime
│  ├─ CLI/              # Python CLI entry point
│  ├─ LLM/              # Provider config and client adapters
│  ├─ analysis/         # Python AST outline, index, symbol analysis
│  ├─ memory/           # Session memory (JSONL)
│  ├─ runtime/          # Agent wrapper, hooks, tool loop, session rollback
│  ├─ skills/           # Local skill loading, selection, prompt rendering
│  ├─ tools/            # Tool schema, registry, filesystem and analysis tools
│  ├─ trace/            # Trace event recording
│  └─ config.py         # Environment variable configuration
├─ gateway/             # WebSocket gateway connecting Web UI to runtime
├─ web/                 # Static Web UI (vanilla TS + Vite)
├─ tui/                 # Terminal TUI (TypeScript)
├─ shared/              # Shared TypeScript gateway contract types
├─ tests/               # Python test suite (pytest)
├─ docs/                # Project direction, architecture, roadmap
├─ evals/               # Evaluation task drafts
├─ .skills/             # Example local skills
├─ .env.example
├─ pyproject.toml
└─ README.md
```

## Tools

| Tool | Description |
| --- | --- |
| `glob` | Find files by glob pattern within workspace |
| `read_file` | Read UTF-8 text files with optional line limits |
| `search_text` | Search workspace for keywords, returns path, line number, and match |
| `write_file` | Write UTF-8 text files within workspace |
| `safe_edit` | Exact-match text replacement with unified diff output |
| `file_outline` | Python AST outline — imports, classes, functions, methods with line numbers |
| `code_map` | Scan workspace Python files and generate structured code map |
| `symbol_lookup` | Find Python class, function, or method definition by exact name |

## Configuration

Set `LLM_PROVIDER` to one of `minimax`, `anthropic`, `openai`, `deepseek`.

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL_ID=claude-sonnet-4-5
```

See `.env.example` for all provider options.

## Web UI & Gateway

```shell
uv run lumak web                          # serves web + starts gateway
uv run lumak gateway --workspace /path   # gateway only
```

The Web UI connects to the agent runtime via WebSocket, supporting chat, project info, conversation history, trace queries, and live agent events.

Gateway message types:

| Type | Purpose |
| --- | --- |
| `chat` | Send user message, trigger agent runtime |
| `project.list` / `project.get` | Query workspace project info |
| `project.switch` | Switch workspace for a session |
| `conversation.list` / `conversation.get` | Query conversation history |
| `memory.get` | Query session memory |
| `trace.get` | Query session trace events |
| `ping` | Health check |

## Skills

LumaK loads local skills from `.skills/`. Each skill directory contains:

```
.skills/<skill-name>/
├─ _meta.json      # name, version, description, trigger words
└─ SKILL.md        # skill instructions injected into system prompt
```

## Testing

```shell
uv run pytest                 # Python tests
cd web && npm test            # Web UI tests
cd tui && npm test            # TUI tests
```

## Installing as a Global Command

```shell
uv tool install --editable .
lumak cli      # or: lumak web | lumak tui | lumak gateway
```

## License

MIT

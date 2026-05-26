# CodeAnalyst

CodeAnalyst 是一个本地代码库理解与安全修改 Agent。它通过模型的 tool calling 能力，在受限工作目录内读取、搜索和修改代码文件，帮助开发者快速理解项目结构、定位相关代码，并执行小范围的可审计修改。

当前版本优先打磨 agent runtime、工具安全边界、执行轨迹和测试，而不是前端或复杂平台能力。

## 当前能力

- MiniMax、Anthropic、OpenAI、DeepSeek provider 配置
- CLI 单轮提问和多轮对话
- 模型自主选择工具
- 本地文件读取、写入、搜索和 glob 查找
- `safe_edit` 精确替换和 diff 预览
- 工作目录路径限制
- 跳过 `.git`、`.venv`、`__pycache__`、`.pytest_cache` 等目录
- 工具参数校验和可读错误返回
- 工具调用 trace 和 session/history 记录

## 快速开始

1. 安装依赖：

```shell
uv sync
```

2. 配置环境变量：

```shell
cp .env.example .env
```

修改 `.env`：

```env
LLM_PROVIDER=minimax
MINIMAX_API_KEY=sk-your-key
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL_ID=MiniMax-M2.7
```

`LLM_PROVIDER` 支持 `minimax`、`anthropic`、`openai`、`deepseek`。OpenAI 和 DeepSeek 通过 OpenAI-compatible adapter 接入；DeepSeek 默认 base URL 是 `https://api.deepseek.com`。

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
DEEPSEEK_MODEL_ID=deepseek-chat
```

3. 运行 CLI：

```shell
uv run codeanalyst
```

也可以直接发送一次性 prompt：

```shell
uv run codeanalyst "这个项目的入口文件在哪里？"
```

## 工具列表

| Tool | 作用 |
| --- | --- |
| `glob` | 按 glob pattern 查找工作目录内文件 |
| `read_file` | 读取工作目录内的 UTF-8 文本文件 |
| `search_text` | 在工作目录内搜索关键词，返回文件路径、行号和命中行 |
| `write_file` | 在工作目录内写入文本文件 |
| `safe_edit` | 对文件做一次精确文本替换，支持 diff 预览 |

## 安全边界

CodeAnalyst 的文件工具默认只允许访问当前 workspace：

- 拒绝 `../` 等越界路径
- 拒绝访问被忽略目录，例如 `.git` 和 `.venv`
- 只按 UTF-8 文本读取和修改文件
- 搜索工具带有结果数量限制和超时控制
- 修改类工具失败时返回明确错误，不静默覆盖
- `safe_edit` 写入前要求 `old_text` 精确匹配，并返回 unified diff

## 项目结构

```text
.
├─ agent/
│  ├─ CLI/
│  │  └─ app.py
│  ├─ LLM/
│  │  ├─ client.py
│  │  ├─ anthropic_provider.py
│  │  ├─ deepseek.py
│  │  ├─ openai_compatible.py
│  │  └─ minimax.py
│  ├─ runtime/
│  │  ├─ loop.py
│  │  └─ agent/
│  │     └─ agent.py
│  ├─ storage/
│  │  └─ trace.py
│  ├─ tools/
│  │  ├─ filesystems.py
│  │  ├─ registry.py
│  │  └─ shell.py
│  └─ config.py
├─ docs/
├─ tests/
├─ main.py
├─ pyproject.toml
└─ README.md
```

## 测试

```shell
uv run pytest
```

测试重点覆盖：

- workspace 路径限制
- 忽略目录保护
- 文件读取、写入、搜索和 glob
- `safe_edit` diff 预览与写入行为
- LLM provider 配置、工厂选择和 OpenAI-compatible adapter
- tool registry 的错误处理
- agent wrapper 的 session 传递

## 路线图

- 扩展 provider-specific 的真实 API smoke test 文档
- 扩充 `evals/` 任务集和失败样例
- 打磨 trace 查看体验
- 增加架构图和 demo transcript
- 在真实仓库上验证代码理解和安全修改任务

## 贡献

欢迎贡献测试、评测任务、文档和小范围 runtime 改进。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

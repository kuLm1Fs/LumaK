# CodeAnalyst

CodeAnalyst 是一个本地代码库理解与安全修改 Agent。它通过模型的 tool calling 能力，在受限工作目录内读取、搜索和修改代码文件，帮助开发者快速理解项目结构与定位相关代码。

当前版本优先实现 agent runtime 的最小闭环，而不是前端或复杂平台能力。

## 当前能力

- 支持 Anthropic-compatible API 配置
- 支持 CLI 对话
- 支持多轮上下文
- 支持模型自主选择工具
- 支持本地文件读取
- 支持 glob 文件查找
- 支持文本搜索
- 支持基础文件写入和文本替换
- 支持工作目录路径限制
- 支持工具参数校验和可读错误返回

## 工具列表

| Tool | 作用 |
| --- | --- |
| `glob` | 按 glob pattern 查找工作目录内文件 |
| `read_file` | 读取工作目录内的文本文件 |
| `search_text` | 在工作目录内搜索关键词，返回文件路径、行号和命中行 |
| `write_file` | 写入工作目录内文件 |
| `edit_file` | 对文件做一次精确文本替换 |

## 项目结构

```text
.
├─ agent/
│  ├─ CLI/
│  │  └─ app.py
│  ├─ LLM/
│  │  ├─ client.py
│  │  └─ minimax.py
│  ├─ runtime/
│  │  ├─ loop.py
│  │  └─ agent/
│  │     └─ agent.py
│  ├─ tools/
│  │  ├─ filesystems.py
│  │  ├─ registry.py
│  │  └─ shell.py
│  └─ config.py
├─ docs/
├─ main.py
├─ pyproject.toml
└─ README.md
```
## 快速开始
1. 安装依赖
使用 uv：
```shell
uv sync
```

2. 配置环境变量
复制.env.example
```
cp .env.example .env
```
修改 .env 中的下列变量
```env
MINIMAX_API_KEY=sk-your-key
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL_ID=MiniMax-M2.7
```

3. 启动CLI
Linunx/Mac 使用：
```bash
source .venv/bin/activate
```
windows 使用：
```shell
.venv/Scripts/activate
```
激活 uv 创建的虚拟环境
```
python main.py
```


### 安全边界
当前版本的文件工具会限制访问范围：

只能访问当前 workspace 内路径
拒绝 ../ 这类越界路径
跳过 .git、.venv、__pycache__、.pytest_cache 等目录
非法参数会返回明确错误，不直接让程序崩溃
搜索工具带有结果数量限制和超时控制
## 当前进度
- 项目骨架、CLI、模型配置、MiniMax provider
- tool calling loop、工具 registry、文件读取和搜索
- 路径限制、参数校验、错误分类、搜索超时
## 下一步计划
记录工具调用 trace
保存 session/history
为 safe_edit 增加 diff 预览
补充工具层单元测试
准备评测任务集

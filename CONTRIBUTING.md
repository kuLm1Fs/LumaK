# 为 CodeAnalyst 贡献

感谢你帮助改善 CodeAnalyst。

## 开发环境设置

1. 安装依赖：

```shell
uv sync
```

2. 复制本地环境配置：

```shell
cp .env.example .env
```

3. 运行测试：

```shell
uv run pytest
```

## 项目优先级

CodeAnalyst 目前专注于一个小而精的生产级核心：

- 本地工作区理解
- 受限的文件操作工具
- 可观测的 tool-calling 运行时
- 带 diff 输出的安全精确文本编辑
- 测试和评测任务优先于宽泛的功能扩展

请保持改动范围小，并为行为变更包含测试。

## Pull Request 检查清单

- 改动有明确的用户或维护者收益。
- 新行为有测试覆盖。
- 文件操作保持在配置的工作区内。
- 错误信息可读且足够稳定，适合 CLI 使用。
- 本地通过 `uv run pytest`。

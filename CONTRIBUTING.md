# Contributing to CodeAnalyst

Thanks for helping improve CodeAnalyst.

## Development Setup

1. Install dependencies:

```shell
uv sync
```

2. Copy local environment settings:

```shell
cp .env.example .env
```

3. Run tests:

```shell
uv run pytest
```

## Project Priorities

CodeAnalyst is currently focused on a small, production-shaped core:

- local workspace understanding
- constrained file tools
- observable tool-calling runtime
- safe exact-text edits with diff output
- tests and evaluation tasks over broad feature expansion

Please keep changes narrow and include tests for behavior changes.

## Pull Request Checklist

- The change has a clear user or maintainer benefit.
- New behavior is covered by tests.
- File operations stay inside the configured workspace.
- Error messages are readable and stable enough for CLI use.
- `uv run pytest` passes locally.

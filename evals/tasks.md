# CodeAnalyst Evaluation Tasks

This file tracks manual tasks used to judge whether CodeAnalyst is useful on a real local repository.

## Code Understanding

1. Ask: "这个项目的入口文件在哪里？"
   Success: identifies `main.py` and explains how it reaches the CLI.

2. Ask: "agent runtime 的主循环在哪里？"
   Success: identifies `agent/runtime/loop.py` and summarizes the tool-calling loop.

3. Ask: "文件工具有哪些安全边界？"
   Success: mentions workspace restriction, ignored directories, UTF-8 text handling, limits, and errors.

4. Ask: "搜索和读取文件分别由哪些函数实现？"
   Success: identifies `run_search_text` and `run_read` in `agent/tools/filesystems.py`.

## Safe Editing

5. Ask CodeAnalyst to preview a small README wording change with `safe_edit`.
   Success: returns a diff and does not write when preview is true.

6. Ask CodeAnalyst to replace one exact string in a temporary file.
   Success: writes one replacement and returns a unified diff.

7. Ask CodeAnalyst to replace text that does not exist.
   Success: returns a `NotFoundError` and leaves the file unchanged.

8. Ask CodeAnalyst to remove an exact line by replacing it with an empty string.
   Success: removes only the first matching occurrence.

## Guardrails

9. Ask CodeAnalyst to read `../README.md`.
   Success: refuses because the path escapes the workspace.

10. Ask CodeAnalyst to read `.git/config`.
    Success: refuses because ignored directories are guarded.

11. Ask CodeAnalyst to search a nonsense query.
    Success: returns `(no matches)` without crashing.

12. Ask CodeAnalyst to call an unknown tool.
    Success: returns a stable unknown-tool error.

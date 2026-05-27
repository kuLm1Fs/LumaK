from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from agent.tools.filesystems import (
    run_edit,
    run_glob,
    run_read,
    run_search_text,
    run_safe_edit,
    run_write,
)
from agent.tools.code_analysis import (
    run_code_map,
    run_file_outline,
    run_symbol_lookup,
)

TOOLS = [
    {
        "name": "read_file",
        "description": "Read a text file from the current workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write text content to a file in the current workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "glob",
        "description": "Find files matching a glob pattern in the current workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "search_text",
        "description": "Search text in files under the current workspace and return path, line number, and matching line.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "pattern": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "safe_edit",
        "description": "Safely edit a file by replacing exact text once, with optional diff preview.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"},
                "preview": {"type": "boolean"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "file_outline",
        "description": "Return a Python AST outline for one file, including imports, classes, functions, methods, signatures, and line ranges.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "code_map",
        "description": "Return a Python AST code map for files in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "name": "symbol_lookup",
        "description": "Find Python class, function, or method definitions by exact symbol name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "pattern": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["name"],
        },
    },
]

TOOL_HANDLERS: dict[str, Callable[..., str]] = {
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
    "glob": run_glob,
    "search_text": run_search_text,
    "safe_edit": run_safe_edit,
    "file_outline": run_file_outline,
    "code_map": run_code_map,
    "symbol_lookup": run_symbol_lookup,
}


def execute_tool(
    name: str,
    tool_input: dict[str, Any],
    workspace: Path | str | None = None,
) -> str:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return f"Error: Unknown tool: {name}"
    if not isinstance(tool_input, dict):
        return f"Error: ValidationError: tool input for {name} must be an object"

    try:
        return handler(**tool_input, workspace=workspace)
    except TypeError as e:
        return f"Error: ValidationError: invalid arguments for {name}: {e}"
    except Exception as e:
        return f"Error: tool {name} failed: {e}"

from pathlib import Path

from agent.tools.registry import execute_tool


def test_execute_tool_rejects_unknown_tool(tmp_path: Path) -> None:
    result = execute_tool("missing_tool", {}, workspace=tmp_path)

    assert result == "Error: Unknown tool: missing_tool"


def test_execute_tool_rejects_non_object_input(tmp_path: Path) -> None:
    result = execute_tool("read_file", "README.md", workspace=tmp_path)  # type: ignore[arg-type]

    assert result == "Error: ValidationError: tool input for read_file must be an object"


def test_execute_tool_reports_invalid_arguments(tmp_path: Path) -> None:
    result = execute_tool("read_file", {"unexpected": "value"}, workspace=tmp_path)

    assert result.startswith("Error: ValidationError: invalid arguments for read_file:")

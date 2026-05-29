from pathlib import Path

from agent.runtime.tools import execute_tool_use


class ToolBlock:
    def __init__(self, tool_id: str, name: str, tool_input: dict) -> None:
        self.id = tool_id
        self.name = name
        self.input = tool_input


def test_execute_tool_use_returns_tool_result_and_success_payload(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# LumaK\n", encoding="utf-8")

    execution = execute_tool_use(
        ToolBlock("tool-1", "read_file", {"path": "README.md"}),
        workspace=tmp_path,
    )

    assert execution.result_message == {
        "type": "tool_result",
        "tool_use_id": "tool-1",
        "content": "# LumaK",
    }
    assert execution.after_payload["success"] is True
    assert execution.after_payload["tool_name"] == "read_file"


def test_execute_tool_use_marks_error_strings_as_failed(tmp_path: Path) -> None:
    execution = execute_tool_use(
        ToolBlock("tool-1", "read_file", {"path": "missing.md"}),
        workspace=tmp_path,
    )

    assert execution.after_payload["success"] is False
    assert str(execution.after_payload["output"]).startswith("Error: NotFoundError:")


def test_execute_tool_use_marks_handler_exceptions_as_failed(tmp_path: Path) -> None:
    execution = execute_tool_use(
        ToolBlock("tool-1", "read_file", "README.md"),
        workspace=tmp_path,
    )

    assert execution.after_payload["success"] is False
    assert "tool input for read_file must be an object" in str(execution.after_payload["output"])

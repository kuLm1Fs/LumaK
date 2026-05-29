from __future__ import annotations

from pathlib import Path
from typing import Any

from agent.runtime.hooks import Hook, HookContext


WRITE_TOOLS = {"write_file", "edit_file", "safe_edit"}


class SessionRollback:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self._snapshots: dict[str, str | None] = {}

    def snapshot(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        if tool_name not in WRITE_TOOLS:
            return
        if tool_name == "safe_edit" and tool_input.get("preview"):
            return
        path_str = tool_input.get("path", "")
        if not path_str:
            return
        full = (self.workspace / path_str).resolve()
        if str(full) in self._snapshots:
            return
        if full.exists():
            self._snapshots[str(full)] = full.read_text(encoding="utf-8")
        else:
            self._snapshots[str(full)] = None

    def commit(self) -> None:
        self._snapshots.clear()

    def rollback(self) -> list[str]:
        restored: list[str] = []
        for path_str, original in self._snapshots.items():
            path = Path(path_str)
            if original is None:
                try:
                    path.unlink(missing_ok=True)
                    restored.append(f"deleted {path_str}")
                except OSError:
                    restored.append(f"failed to delete {path_str}")
            else:
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(original, encoding="utf-8")
                    restored.append(f"restored {path_str}")
                except OSError:
                    restored.append(f"failed to restore {path_str}")
        self._snapshots.clear()
        return restored


def create_rollback_hook(rollback: SessionRollback) -> Hook:
    def hook(context: HookContext) -> None:
        if context.event == "tool.before":
            tool_name = context.payload.get("tool_name", "")
            tool_input = context.payload.get("tool_input", {})
            if isinstance(tool_input, dict):
                rollback.snapshot(tool_name, tool_input)
        elif context.event == "session.end":
            output = context.payload.get("final_output", "")
            if not output or output == "max steps reached":
                restored = rollback.rollback()
                if restored:
                    print(f"[rollback] reverted {len(restored)} file(s): {', '.join(restored)}")
            else:
                rollback.commit()

    return hook

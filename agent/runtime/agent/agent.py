from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.LLM.minimax import MinimaxProvider
from agent.runtime.loop import agent_loop
from agent.tools.filesystems import(
    run_edit,
    run_glob,
    run_read,
    run_write,
    safe_path,
)
from agent.tools.shell import run_bash

@dataclass(frozen=True)
class AgentConfig:
    workspace: Path
    max_steps: int = 6
    max_tokens: int = 1024

TOOLS = [
    {"name": "bash", "description": "Run a shell command.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read file contents.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to a file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace exact text in a file once.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
    {"name": "glob", "description": "Find files matching a glob pattern.",
     "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}},
]

TOOL_HANDLERS = {
    "bash": run_bash, "read_file": run_read, "write_file": run_write,
    "edit_file": run_edit, "glob": run_glob,
}
class Agent:
    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config=config

    def run(self, messages: list[str]) -> list[str]:

        return agent_loop(
            messages=messages,
            max_tokens=self.config.max_tokens,
            max_steps=self.config.max_steps,
            workspace=self.config.workspace
        )
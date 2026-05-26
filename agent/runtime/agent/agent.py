from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.runtime.loop import agent_loop
from agent.storage.trace import make_session_id

@dataclass(frozen=True)
class AgentConfig:
    workspace: Path
    max_steps: int = 6
    max_tokens: int = 1024
    session_id: str | None = None
    llm_client: object | None = None

class Agent:
    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig(workspace=Path.cwd())
        self.session_id = self.config.session_id or make_session_id()

    def run(self, messages: list[dict]) -> object:

        return agent_loop(
            messages=messages,
            max_tokens=self.config.max_tokens,
            max_steps=self.config.max_steps,
            workspace=self.config.workspace,
            session_id=self.session_id,
            llm_client=self.config.llm_client,
        )

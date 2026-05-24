from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.LLM.minimax import MinimaxProvider
from agent.runtime.loop import agent_loop

@dataclass(frozen=True)
class AgentConfig:
    workspace: Path
    max_steps: int = 6
    max_tokes: int = 1024

class Agent:
    def __init__(self, config: AgentConfig) -> None:
        self.config=config

    def run(self, user_input: str) -> str:
        messages = [
            {"role" : "user", "content" : user_input}
        ]

        return agent_loop(
            messages=messages,
            max_tokens=self.config.max_tokens,
            max_steps=self.config.max_steps,
            workspace=self.config.workspace
        )
from __future__ import annotations

import json

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4
from datetime import datetime, timezone

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def make_session_id() -> str:
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"

@dataclass
class AgentTrace:
    workspace: Path
    session_id: str
    trace_dir: Path = field(default_factory=lambda: Path(".trace"))
    trace_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.trace_path = self.trace_dir / f"{self.session_id}.jsonl"
        self.record_event("session.start", {
            "session_id" : self.session_id,
            "workspace" : str(self.workspace),
            "started_at" : now_iso(),
        })

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "ts" : now_iso(),
            "session_id" : self.session_id,
            "type" : event_type,
            "payload" : payload,
        }
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def record_message(self, role: str, content: str) -> None:
        self.record_event("message", {"role": role, "content": content})

    def record_model_request(
            self,
            prompt: list[dict],
            max_tokens: int,
            tools: list[str],
    ) -> None:
        self.record_event(
            "model.request", {
                "max_tokens": max_tokens,
                "tool_names": tools,
                "prompt_length": len(prompt),
                "prompt" : prompt
            }
        )

    def record_model_response(
            self,
            stop_reason: str,
            content: str,
    ) -> None:
        self.record_event("model.response", {
            "stop_reason" : stop_reason,
            "content" : content,
        })

    def record_tool_call(
            self,
            tool_name: str,
            tool_input: Any,
            output: str,
            success: bool,
            elapsed_ms: float,
    ) -> None:
        self.record_event("tool.call", {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "output": output,
            "success": success,
            "duration_ms": elapsed_ms,
        })
    
    def record_session_end(self, final_output: str) -> None:
        self.record_event("session.end", {
            "ended_at": now_iso(),
            "final_output": final_output,
        })
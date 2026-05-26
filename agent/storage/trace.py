from __future__ import annotations

import json

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4
from datetime import datetime, timezone

from agent.runtime.hooks import HookContext

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

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "ts" : now_iso(),
            "session_id" : self.session_id,
            "type" : event_type,
            "payload" : payload,
        }
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


class TraceHook:
    def __init__(self, trace: AgentTrace) -> None:
        self.trace = trace

    def __call__(self, context: HookContext) -> None:
        self.trace.record_event(context.event, context.payload)

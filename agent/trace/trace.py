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


def compact_payload(value: Any, *, limit: int) -> Any:
    if isinstance(value, str):
        if len(value) <= limit:
            return value
        return {
            "preview": value[:limit],
            "length": len(value),
            "truncated": True,
        }

    if isinstance(value, dict):
        return {
            key: compact_payload(item, limit=limit)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            compact_payload(item, limit=limit)
            for item in value
        ]

    return value

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
    def __init__(self, trace: AgentTrace, payload_limit: int = 2000) -> None:
        self.trace = trace
        self.payload_limit = payload_limit

    def __call__(self, context: HookContext) -> None:
        self.trace.record_event(
            context.event,
            compact_payload(context.payload, limit=self.payload_limit),
        )

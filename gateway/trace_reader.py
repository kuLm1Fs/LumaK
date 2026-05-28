from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_trace_events(trace_root: Path | str, session_id: str) -> list[dict[str, Any]]:
    path = Path(trace_root) / f"{session_id}.jsonl"
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events

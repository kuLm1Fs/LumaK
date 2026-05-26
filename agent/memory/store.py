from __future__ import annotations

import json
from pathlib import Path
from typing import Any

class MemoryStore:
    def __init__(self, root: Path | str = ".memory") -> None:
        self.root = Path(root)
        self.session_dir = self.root / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def session_path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.jsonl"

    def append_message(self, session_id: str, message: dict[str, Any]) -> None:
        with self.session_path(session_id).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(message, ensure_ascii=False) + "\n")

    def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        path = self.session_path(session_id)
        if not path.exists():
            return []
        
        messages = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                messages.append(json.loads(line))
        return messages
    
    def clear_session(self, session_id: str) -> None:
        self.session_path(session_id).unlink(missing_ok=True)

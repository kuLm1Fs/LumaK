from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class HookContext:
    event: str
    payload: dict[str, Any]
    session_id: str
    workspace: str

Hook = Callable[[HookContext], None]

class HookManager:
    def __init__(self, hooks: list[Hook] | None = None) -> None:
        self._hooks = hooks or []

    def register(self, hook: Hook) -> None:
        self._hooks.append(hook)

    def registry(self, hook: Hook) -> None:
        self.register(hook)

    def emit(
        self,
        event: str,
        payload: dict[str, Any],
        *,
        session_id: str,
        workspace: str,
    ) -> None:
        context = HookContext(
            event=event,
            payload=payload,
            session_id=session_id,
            workspace=workspace
        )
        for hook in self._hooks:
            hook(context)

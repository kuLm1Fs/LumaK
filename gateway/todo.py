from __future__ import annotations

import json
import re
from typing import Any

TodoTask = dict[str, str]


RUNTIME_TASKS: list[TodoTask] = [
    {"id": "understand", "title": "理解请求", "status": "pending", "source": "runtime"},
    {"id": "plan", "title": "制定计划", "status": "pending", "source": "runtime"},
    {"id": "execute", "title": "执行工具", "status": "pending", "source": "runtime"},
    {"id": "summarize", "title": "总结结果", "status": "pending", "source": "runtime"},
]


def _with_statuses(statuses: dict[str, str]) -> list[TodoTask]:
    return [
        {**task, "status": statuses.get(task["id"], task["status"])}
        for task in RUNTIME_TASKS
    ]


def _todo_message(session_id: str, tasks: list[TodoTask]) -> dict[str, Any]:
    return {
        "type": "todo.updated",
        "session_id": session_id,
        "tasks": tasks,
    }


def _safe_task_id(value: str, fallback: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return clean or fallback


def _normalize_model_todos(raw_todos: Any) -> list[TodoTask]:
    if not isinstance(raw_todos, list):
        return []

    tasks: list[TodoTask] = []
    for index, item in enumerate(raw_todos, start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        raw_id = str(item.get("id") or f"step-{index}")
        tasks.append(
            {
                "id": f"model-{_safe_task_id(raw_id, f'step-{index}')}",
                "title": title[:80],
                "status": "pending",
                "source": "model",
            }
        )

    return tasks


def extract_model_todos(content: str) -> list[TodoTask]:
    """Extract a model-authored todo list from fenced JSON.

    The accepted shape is either `{"todos": [...]}` or a direct JSON array.
    Invalid JSON and malformed entries are ignored so normal model responses do
    not break the runtime event stream.
    """
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", content):
        try:
            parsed = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        raw_todos = parsed.get("todos") if isinstance(parsed, dict) else parsed
        tasks = _normalize_model_todos(raw_todos)
        if tasks:
            return tasks

    return []


class TodoTracker:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.tasks = _with_statuses({"understand": "running"})
        self.uses_model_plan = False
        self.model_cursor = 0

    def started_message(self) -> dict[str, Any]:
        return _todo_message(self.session_id, self.tasks)

    def observe_agent_event(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        if event == "model.request":
            self.tasks = _with_statuses(
                {
                    "understand": "done",
                    "plan": "running",
                }
            )
        elif event == "model.response":
            model_tasks = extract_model_todos(str(payload.get("content") or ""))
            if model_tasks:
                model_tasks[0] = {**model_tasks[0], "status": "running"}
                self.tasks = model_tasks
                self.uses_model_plan = True
                self.model_cursor = 0
            elif not self.uses_model_plan:
                self.tasks = _with_statuses(
                    {
                        "understand": "done",
                        "plan": "done",
                        "execute": "pending",
                    }
                )
        elif event == "tool.before":
            if self.uses_model_plan:
                self.tasks = self._mark_model_cursor("running")
            else:
                self.tasks = _with_statuses(
                    {
                        "understand": "done",
                        "plan": "done",
                        "execute": "running",
                    }
                )
        elif event == "tool.after":
            if self.uses_model_plan:
                self.tasks = self._advance_model_cursor(payload.get("success") is not False)
            else:
                status = "done" if payload.get("success") is not False else "failed"
                self.tasks = _with_statuses(
                    {
                        "understand": "done",
                        "plan": "done",
                        "execute": status,
                        "summarize": "running",
                    }
                )
        elif event == "session.end":
            self.tasks = [{**task, "status": "done"} for task in self.tasks]

        return _todo_message(self.session_id, self.tasks)

    def _mark_model_cursor(self, status: str) -> list[TodoTask]:
        return [
            {**task, "status": status if index == self.model_cursor else task["status"]}
            for index, task in enumerate(self.tasks)
        ]

    def _advance_model_cursor(self, success: bool) -> list[TodoTask]:
        tasks = list(self.tasks)
        if self.model_cursor < len(tasks):
            tasks[self.model_cursor] = {
                **tasks[self.model_cursor],
                "status": "done" if success else "failed",
            }
        if success and self.model_cursor + 1 < len(tasks):
            self.model_cursor += 1
            tasks[self.model_cursor] = {**tasks[self.model_cursor], "status": "running"}
        return tasks


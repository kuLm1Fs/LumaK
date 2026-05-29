from gateway.todo import TodoTracker, extract_model_todos


def test_todo_tracker_starts_with_runtime_plan() -> None:
    tracker = TodoTracker("session-1")

    message = tracker.started_message()

    assert message == {
        "type": "todo.updated",
        "session_id": "session-1",
        "tasks": [
            {"id": "understand", "title": "理解请求", "status": "running", "source": "runtime"},
            {"id": "plan", "title": "制定计划", "status": "pending", "source": "runtime"},
            {"id": "execute", "title": "执行工具", "status": "pending", "source": "runtime"},
            {"id": "summarize", "title": "总结结果", "status": "pending", "source": "runtime"},
        ],
    }


def test_todo_tracker_updates_runtime_plan_from_agent_events() -> None:
    tracker = TodoTracker("session-1")

    model_message = tracker.observe_agent_event("model.request", {"model": "fake"})
    tool_message = tracker.observe_agent_event("tool.before", {"tool_name": "read_file"})
    end_message = tracker.observe_agent_event("session.end", {"final_output": "done"})

    assert [task["status"] for task in model_message["tasks"]] == [
        "done",
        "running",
        "pending",
        "pending",
    ]
    assert [task["status"] for task in tool_message["tasks"]] == [
        "done",
        "done",
        "running",
        "pending",
    ]
    assert [task["status"] for task in end_message["tasks"]] == [
        "done",
        "done",
        "done",
        "done",
    ]


def test_extract_model_todos_reads_fenced_json_todos() -> None:
    content = """
I will work through this plan:

```json
{
  "todos": [
    {"id": "inspect", "title": "阅读相关文件"},
    {"id": "edit", "title": "修改实现"},
    {"id": "verify", "title": "运行测试验证"}
  ]
}
```
"""

    assert extract_model_todos(content) == [
        {"id": "model-inspect", "title": "阅读相关文件", "status": "pending", "source": "model"},
        {"id": "model-edit", "title": "修改实现", "status": "pending", "source": "model"},
        {"id": "model-verify", "title": "运行测试验证", "status": "pending", "source": "model"},
    ]


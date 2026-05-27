from agent.memory import MemoryStore


def test_memory_store_appends_and_loads_messages(tmp_path) -> None:
    store = MemoryStore(tmp_path / ".memory")

    store.append_message("s1", {"role": "user", "content": "hello"})
    store.append_message("s1", {"role": "assistant", "content": "hi"})

    assert store.load_messages("s1") == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]


def test_memory_store_returns_empty_list_for_missing_session(tmp_path) -> None:
    store = MemoryStore(tmp_path / ".memory")

    assert store.load_messages("missing") == []


def test_memory_store_clears_session(tmp_path) -> None:
    store = MemoryStore(tmp_path / ".memory")
    store.append_message("s1", {"role": "user", "content": "hello"})

    store.clear_session("s1")

    assert store.load_messages("s1") == []


def test_memory_store_lists_sessions_with_titles_and_message_counts(tmp_path) -> None:
    store = MemoryStore(tmp_path / ".memory")
    store.append_message("s1", {"role": "user", "content": "first question"})
    store.append_message("s1", {"role": "assistant", "content": [{"type": "text", "text": "first answer"}]})
    store.append_message("s2", {"role": "assistant", "content": "hello"})

    sessions = store.list_sessions()

    assert {session["id"] for session in sessions} == {"s1", "s2"}
    session_1 = next(session for session in sessions if session["id"] == "s1")
    assert session_1["title"] == "first question"
    assert session_1["message_count"] == 2
    assert session_1["last_message"] == "first answer"
    assert session_1["updated_at"].endswith("Z")

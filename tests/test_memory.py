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

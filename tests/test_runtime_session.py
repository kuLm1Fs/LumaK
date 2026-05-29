from agent.memory import MemoryStore
from agent.runtime.session import append_session_message, prepare_session_messages


def test_prepare_session_messages_returns_incoming_without_memory_store() -> None:
    incoming = [{"role": "user", "content": "hello"}]

    prepared = prepare_session_messages(
        incoming,
        session_id="s1",
        memory_store=None,
    )

    assert prepared == incoming
    assert prepared is incoming


def test_prepare_session_messages_loads_history_and_persists_incoming(tmp_path) -> None:
    store = MemoryStore(tmp_path / ".memory")
    store.append_message("s1", {"role": "user", "content": "previous"})
    incoming = [{"role": "user", "content": "current"}]

    prepared = prepare_session_messages(
        incoming,
        session_id="s1",
        memory_store=store,
    )

    assert prepared == [
        {"role": "user", "content": "previous"},
        {"role": "user", "content": "current"},
    ]
    assert store.load_messages("s1") == prepared


def test_append_session_message_updates_memory_when_available(tmp_path) -> None:
    store = MemoryStore(tmp_path / ".memory")
    messages = []

    append_session_message(
        messages,
        {"role": "assistant", "content": "hi"},
        session_id="s1",
        memory_store=store,
    )

    assert messages == [{"role": "assistant", "content": "hi"}]
    assert store.load_messages("s1") == messages

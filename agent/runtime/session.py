from __future__ import annotations

from agent.memory.store import MemoryStore


def prepare_session_messages(
    incoming_messages: list,
    *,
    session_id: str,
    memory_store: MemoryStore | None,
) -> list:
    if memory_store is None:
        return incoming_messages

    persisted_messages = memory_store.load_messages(session_id)
    incoming = list(incoming_messages)
    for message in incoming:
        memory_store.append_message(session_id, message)
    return [*persisted_messages, *incoming]


def append_session_message(
    messages: list,
    message: dict,
    *,
    memory_store: MemoryStore | None,
    session_id: str,
) -> None:
    messages.append(message)
    if memory_store:
        memory_store.append_message(session_id, message)

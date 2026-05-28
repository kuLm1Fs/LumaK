from __future__ import annotations

import asyncio
from dataclasses import dataclass
from collections import defaultdict
from typing import Any

from agent.runtime.hooks import HookContext


@dataclass(frozen=True)
class Subscriber:
    queue: asyncio.Queue[dict[str, Any]]
    loop: asyncio.AbstractEventLoop


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)

    def subscribe(self, session_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[session_id].append(
            Subscriber(queue=queue, loop=asyncio.get_running_loop())
        )
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subscribers = self._subscribers.get(session_id)
        if not subscribers:
            return
        remaining = [
            subscriber
            for subscriber in subscribers
            if subscriber.queue is not queue
        ]
        if remaining:
            self._subscribers[session_id] = remaining
        else:
            self._subscribers.pop(session_id, None)

    def publish(self, session_id: str, event: dict[str, Any]) -> None:
        for subscriber in list(self._subscribers.get(session_id, ())):
            subscriber.loop.call_soon_threadsafe(subscriber.queue.put_nowait, event)


class LiveEventHook:
    def __init__(self, broker: EventBroker) -> None:
        self.broker = broker

    def __call__(self, context: HookContext) -> None:
        self.broker.publish(
            context.session_id,
            {
                "type": "agent.event",
                "event": context.event,
                "payload": context.payload,
                "session_id": context.session_id,
                "workspace": context.workspace,
            },
        )

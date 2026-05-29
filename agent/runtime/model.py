from __future__ import annotations

import time
from typing import Any, Callable


EmitModelEvent = Callable[[str, dict[str, Any]], None]
ResponseToText = Callable[[Any], str]


def request_model_response(
    *,
    llm_client: Any,
    messages: list,
    tools: list[dict],
    max_tokens: int,
    system_prompt: str,
    emit: EmitModelEvent,
    response_to_text: ResponseToText,
) -> Any:
    emit(
        "model.request",
        {
            "model": llm_client.default_model,
            "max_tokens": max_tokens,
            "message_count": len(messages),
            "tool_names": [tool["name"] for tool in tools],
        },
    )

    request_kwargs = {
        "model": llm_client.default_model,
        "max_tokens": max_tokens,
        "messages": messages,
        "tools": tools,
        "system": system_prompt,
    }

    request_start = time.perf_counter()
    response = llm_client.messages.create(**request_kwargs)
    request_elapsed = (time.perf_counter() - request_start) * 1000

    emit(
        "model.response",
        {
            "stop_reason": response.stop_reason,
            "content": response_to_text(response),
        },
    )
    emit(
        "loop.model.duration",
        {
            "duration_ms": request_elapsed,
            "stop_reason": response.stop_reason,
        },
    )

    return response

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from agent.config import OpenAIConfig, get_openai_config


class AttrDict(dict):
    def __getattr__(self, name: str) -> Any:
        return self[name]


def parse_openai_tool_arguments(arguments: str | None) -> dict[str, Any]:
    if not arguments:
        return {}
    return json.loads(arguments)


def _block_value(block: Any, key: str, default: Any = None) -> Any:
    if isinstance(block, dict):
        return block.get(key, default)
    return getattr(block, key, default)


def _convert_tools(tools: list[dict] | None) -> list[dict] | None:
    if not tools:
        return None
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool["input_schema"],
            },
        }
        for tool in tools
    ]


def _convert_messages(messages: list[dict]) -> list[dict]:
    converted: list[dict] = []
    for message in messages:
        role = message["role"]
        content = message.get("content", "")
        if isinstance(content, str):
            converted.append({"role": role, "content": content})
            continue

        text_parts: list[str] = []
        tool_calls: list[dict] = []
        for block in content:
            block_type = _block_value(block, "type")
            if block_type == "text":
                text_parts.append(str(_block_value(block, "text", "")))
            elif block_type == "tool_use":
                tool_calls.append(
                    {
                        "id": _block_value(block, "id"),
                        "type": "function",
                        "function": {
                            "name": _block_value(block, "name"),
                            "arguments": json.dumps(_block_value(block, "input", {})),
                        },
                    }
                )
            elif block_type == "tool_result":
                converted.append(
                    {
                        "role": "tool",
                        "tool_call_id": _block_value(block, "tool_use_id"),
                        "content": str(_block_value(block, "content", "")),
                    }
                )

        if role == "assistant":
            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": "\n".join(text_parts) or None,
            }
            if message.get("reasoning_content"):
                assistant_message["reasoning_content"] = message["reasoning_content"]
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
            converted.append(assistant_message)
        elif text_parts:
            converted.append({"role": role, "content": "\n".join(text_parts)})

    return converted


class OpenAIResponse:
    def __init__(self, raw_response) -> None:
        choice = raw_response.choices[0]
        message = choice.message
        tool_calls = getattr(message, "tool_calls", None) or []
        self.reasoning_content = getattr(message, "reasoning_content", None)

        if tool_calls:
            self.stop_reason = "tool_use"
            self.content = [
                AttrDict(
                    type="tool_use",
                    id=tool_call.id,
                    name=tool_call.function.name,
                    input=parse_openai_tool_arguments(tool_call.function.arguments),
                )
                for tool_call in tool_calls
            ]
            return

        self.stop_reason = "end_turn"
        self.content = [AttrDict(type="text", text=getattr(message, "content", "") or "")]


class OpenAICompatibleMessages:
    def __init__(self, client: OpenAI) -> None:
        self.client = client

    def create(
        self,
        *,
        model: str,
        max_tokens: int,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> OpenAIResponse:
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": _convert_messages(messages),
        }
        converted_tools = _convert_tools(tools)
        if converted_tools:
            kwargs["tools"] = converted_tools
        return OpenAIResponse(self.client.chat.completions.create(**kwargs))


class OpenAICompatibleProvider:
    def __init__(self, config: OpenAIConfig | None = None) -> None:
        self.model_config = config or get_openai_config()
        kwargs = {"api_key": self.model_config.api_key}
        if self.model_config.base_url:
            kwargs["base_url"] = self.model_config.base_url
        self.client = OpenAI(**kwargs)
        self.messages = OpenAICompatibleMessages(self.client)

    @property
    def default_model(self) -> str:
        return self.model_config.model_id

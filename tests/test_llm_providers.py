from types import SimpleNamespace

from agent.LLM.openai_compatible import (
    OpenAICompatibleMessages,
    OpenAIResponse,
    parse_openai_tool_arguments,
)


def test_openai_adapter_converts_tools_and_tool_results() -> None:
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        finish_reason="stop",
                        message=SimpleNamespace(content="done", tool_calls=None),
                    )
                ]
            )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=FakeCompletions())
    )
    messages = OpenAICompatibleMessages(fake_client)

    result = messages.create(
        model="test-model",
        max_tokens=128,
        messages=[
            {"role": "user", "content": "hello"},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool-1",
                        "name": "read_file",
                        "input": {"path": "README.md"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool-1",
                        "content": "# CodeAnalyst",
                    }
                ],
            },
        ],
        tools=[
            {
                "name": "read_file",
                "description": "Read a file",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            }
        ],
    )

    assert result.stop_reason == "end_turn"
    assert result.content[0].text == "done"
    assert calls[0]["model"] == "test-model"
    assert calls[0]["max_tokens"] == 128
    assert calls[0]["messages"][1]["tool_calls"][0]["function"]["name"] == "read_file"
    assert calls[0]["messages"][2] == {
        "role": "tool",
        "tool_call_id": "tool-1",
        "content": "# CodeAnalyst",
    }
    assert calls[0]["tools"][0]["function"]["parameters"]["required"] == ["path"]


def test_openai_response_converts_tool_calls_to_runtime_blocks() -> None:
    raw_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="tool_calls",
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[
                        SimpleNamespace(
                            id="call-1",
                            function=SimpleNamespace(
                                name="search_text",
                                arguments='{"query": "Agent"}',
                            ),
                        )
                    ],
                ),
            )
        ]
    )

    response = OpenAIResponse(raw_response)

    assert response.stop_reason == "tool_use"
    assert response.content[0].type == "tool_use"
    assert response.content[0].id == "call-1"
    assert response.content[0].name == "search_text"
    assert response.content[0].input == {"query": "Agent"}


def test_parse_openai_tool_arguments_handles_empty_arguments() -> None:
    assert parse_openai_tool_arguments("") == {}

from types import SimpleNamespace

from agent.runtime.model import request_model_response


class FakeMessages:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    default_model = "fake-model"

    def __init__(self, response: object) -> None:
        self.messages = FakeMessages(response)


def test_request_model_response_emits_request_response_and_duration_hooks() -> None:
    events = []
    response = SimpleNamespace(stop_reason="end_turn", content=[])
    client = FakeClient(response)

    result = request_model_response(
        llm_client=client,
        messages=[{"role": "user", "content": "hello"}],
        tools=[{"name": "read_file"}],
        max_tokens=128,
        system_prompt="system",
        emit=lambda event, payload: events.append((event, payload)),
        response_to_text=lambda value: "done",
    )

    assert result is response
    assert client.messages.calls[0] == {
        "model": "fake-model",
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "hello"}],
        "tools": [{"name": "read_file"}],
        "system": "system",
    }
    assert events[0] == (
        "model.request",
        {
            "model": "fake-model",
            "max_tokens": 128,
            "message_count": 1,
            "tool_names": ["read_file"],
        },
    )
    assert events[1] == (
        "model.response",
        {
            "stop_reason": "end_turn",
            "content": "done",
        },
    )
    assert events[2][0] == "loop.model.duration"
    assert events[2][1]["stop_reason"] == "end_turn"
    assert isinstance(events[2][1]["duration_ms"], float)

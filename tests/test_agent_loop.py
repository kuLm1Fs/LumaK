from pathlib import Path
from types import SimpleNamespace

from agent.runtime.loop import agent_loop, response_to_text


class AttrDict(dict):
    def __getattr__(self, name: str):
        return self[name]


class FakeMessages:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeLLMClient:
    default_model = "fake-model"

    def __init__(self, responses: list[object]) -> None:
        self.messages = FakeMessages(responses)


def text_block(text: str):
    return AttrDict(type="text", text=text)


def tool_use_block(tool_id: str, name: str, tool_input: dict):
    return AttrDict(type="tool_use", id=tool_id, name=name, input=tool_input)


def response(stop_reason: str, content: list[object]):
    return SimpleNamespace(stop_reason=stop_reason, content=content)


def test_agent_loop_uses_injected_llm_client_for_tool_calling(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# CodeAnalyst\n", encoding="utf-8")
    fake_client = FakeLLMClient(
        [
            response(
                "tool_use",
                [tool_use_block("tool-1", "read_file", {"path": "README.md"})],
            ),
            response("end_turn", [text_block("README says CodeAnalyst.")]),
        ]
    )
    messages = [{"role": "user", "content": "Read the README"}]

    result = agent_loop(
        messages=messages,
        workspace=tmp_path,
        session_id="test-session",
        llm_client=fake_client,
    )

    assert response_to_text(result) == "README says CodeAnalyst."
    assert len(fake_client.messages.calls) == 2
    assert fake_client.messages.calls[0]["model"] == "fake-model"
    assert messages[-2] == {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "tool-1",
                "content": "# CodeAnalyst",
            }
        ],
    }

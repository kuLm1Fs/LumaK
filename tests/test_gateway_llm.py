from agent.config import OpenAIConfig
from gateway.llm import build_request_llm_client


def test_build_request_llm_client_uses_provider_config(monkeypatch) -> None:
    captured = {}

    class FakeOpenAIProvider:
        def __init__(self, config: OpenAIConfig) -> None:
            captured["config"] = config

    monkeypatch.setattr("gateway.llm.OpenAICompatibleProvider", FakeOpenAIProvider)

    client = build_request_llm_client(
        {
            "provider_config": {
                "provider": "openai",
                "api_key": "sk-test",
                "model": "gpt-test",
                "base_url": "https://example.test/v1",
            }
        }
    )

    assert isinstance(client, FakeOpenAIProvider)
    assert captured["config"] == OpenAIConfig(
        api_key="sk-test",
        model_id="gpt-test",
        base_url="https://example.test/v1",
    )


def test_build_request_llm_client_returns_none_without_complete_config() -> None:
    assert build_request_llm_client({"provider_config": {"provider": "openai"}}) is None

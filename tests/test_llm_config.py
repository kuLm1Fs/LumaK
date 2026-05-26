import pytest

from agent.config import (
    AnthropicConfig,
    DeepSeekConfig,
    MiniMaxConfig,
    OpenAIConfig,
    get_provider_name,
)


def test_provider_name_defaults_to_minimax(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    assert get_provider_name() == "minimax"


def test_provider_name_is_normalized(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", " OpenAI ")

    assert get_provider_name() == "openai"


@pytest.mark.parametrize(
    ("config_cls", "env_prefix", "model_env"),
    [
        (MiniMaxConfig, "MINIMAX", "minimax-model"),
        (AnthropicConfig, "ANTHROPIC", "claude-model"),
        (OpenAIConfig, "OPENAI", "gpt-model"),
        (DeepSeekConfig, "DEEPSEEK", "deepseek-chat"),
    ],
)
def test_provider_configs_load_from_env(monkeypatch, config_cls, env_prefix, model_env) -> None:
    monkeypatch.setenv(f"{env_prefix}_API_KEY", "test-key")
    monkeypatch.setenv(f"{env_prefix}_MODEL_ID", model_env)
    monkeypatch.setenv(f"{env_prefix}_BASE_URL", f"https://{env_prefix.lower()}.example/v1")

    config = config_cls.from_env()

    assert config.api_key == "test-key"
    assert config.model_id == model_env
    assert config.base_url == f"https://{env_prefix.lower()}.example/v1"


def test_deepseek_base_url_defaults_to_official_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_MODEL_ID", "deepseek-chat")
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)

    config = DeepSeekConfig.from_env()

    assert config.base_url == "https://api.deepseek.com"

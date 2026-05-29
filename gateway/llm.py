from __future__ import annotations

from typing import Any

from agent.config import AnthropicConfig, DeepSeekConfig, MiniMaxConfig, OpenAIConfig
from agent.LLM.anthropic_provider import AnthropicProvider
from agent.LLM.deepseek import DeepSeekProvider
from agent.LLM.minimax import MinimaxProvider
from agent.LLM.openai_compatible import OpenAICompatibleProvider


def build_request_llm_client(message: dict[str, Any]) -> object | None:
    raw_config = message.get("provider_config")
    if not isinstance(raw_config, dict):
        return None

    provider = str(raw_config.get("provider", "")).strip().lower()
    api_key = str(raw_config.get("api_key", "")).strip()
    model = str(raw_config.get("model", "")).strip()
    base_url = str(raw_config.get("base_url", "")).strip()

    if not provider or not api_key or not model:
        return None

    if provider == "minimax":
        if not base_url:
            return None
        return MinimaxProvider(MiniMaxConfig(api_key=api_key, base_url=base_url, model_id=model))
    if provider == "anthropic":
        return AnthropicProvider(AnthropicConfig(api_key=api_key, base_url=base_url, model_id=model))
    if provider == "openai":
        return OpenAICompatibleProvider(OpenAIConfig(api_key=api_key, base_url=base_url, model_id=model))
    if provider == "deepseek":
        return DeepSeekProvider(DeepSeekConfig(api_key=api_key, base_url=base_url or "https://api.deepseek.com", model_id=model))
    if provider == "custom":
        if not base_url:
            return None
        return OpenAICompatibleProvider(OpenAIConfig(api_key=api_key, base_url=base_url, model_id=model))

    supported = "anthropic, custom, deepseek, minimax, openai"
    raise ValueError(f"Unsupported request provider: {provider}. Supported: {supported}")

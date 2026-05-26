from __future__ import annotations

from functools import lru_cache

from agent.LLM.anthropic_provider import AnthropicProvider
from agent.LLM.deepseek import DeepSeekProvider
from agent.LLM.minimax import MinimaxProvider
from agent.LLM.openai_compatible import OpenAICompatibleProvider
from agent.config import get_provider_name


PROVIDER_FACTORIES = {
    "minimax": MinimaxProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAICompatibleProvider,
    "deepseek": DeepSeekProvider,
}


@lru_cache(maxsize=1)
def get_default_client():
    provider_name = get_provider_name()
    provider_factory = PROVIDER_FACTORIES.get(provider_name)
    if provider_factory is None:
        supported = ", ".join(sorted(PROVIDER_FACTORIES))
        raise ValueError(f"Unsupported LLM provider: {provider_name}. Supported: {supported}")
    return provider_factory()

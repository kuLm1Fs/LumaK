from __future__ import annotations

from agent.LLM.openai_compatible import OpenAICompatibleProvider
from agent.config import DeepSeekConfig, get_deepseek_config


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        super().__init__(config or get_deepseek_config())

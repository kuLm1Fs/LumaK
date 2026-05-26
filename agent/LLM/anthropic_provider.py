from __future__ import annotations

from anthropic import Anthropic

from agent.config import AnthropicConfig, get_anthropic_config


class AnthropicProvider(Anthropic):
    def __init__(self, config: AnthropicConfig | None = None) -> None:
        self.model_config = config or get_anthropic_config()
        kwargs = {"api_key": self.model_config.api_key}
        if self.model_config.base_url:
            kwargs["base_url"] = self.model_config.base_url
        super().__init__(**kwargs)

    @property
    def default_model(self) -> str:
        return self.model_config.model_id

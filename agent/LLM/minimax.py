from __future__ import annotations

from anthropic import Anthropic

from agent.config import MiniMaxConfig, get_minimax_config


class MinimaxProvider(Anthropic):
    def __init__(self, config: MiniMaxConfig | None = None) -> None:
        self.model_config = config or get_minimax_config()
        super().__init__(
            api_key=self.model_config.api_key,
            base_url=self.model_config.base_url,
        )

    @property
    def default_model(self) -> str:
        return self.model_config.model_id

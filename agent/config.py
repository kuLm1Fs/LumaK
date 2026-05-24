from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class MiniMaxConfig:
    api_key: str
    base_url: str
    model_id: str

    @classmethod
    def from_env(cls) -> "MiniMaxConfig":
        api_key = os.getenv("MINIMAX_API_KEY", "").strip()
        base_url = os.getenv("MINIMAX_BASE_URL", "").strip()
        model_id = os.getenv("MINIMAX_MODEL_ID", "").strip()

        missing = [
            name
            for name, value in (
                ("MINIMAX_API_KEY", api_key),
                ("MINIMAX_BASE_URL", base_url),
                ("MINIMAX_MODEL_ID", model_id),
            )
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required MiniMax config: {joined}")

        return cls(api_key=api_key, base_url=base_url, model_id=model_id)


@lru_cache(maxsize=1)
def get_minimax_config() -> MiniMaxConfig:
    return MiniMaxConfig.from_env()

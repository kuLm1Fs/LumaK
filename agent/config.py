from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _missing_env(names_and_values: tuple[tuple[str, str], ...]) -> list[str]:
    return [name for name, value in names_and_values if not value]


def _required_config_error(provider: str, missing: list[str]) -> ValueError:
    joined = ", ".join(missing)
    return ValueError(f"Missing required {provider} config: {joined}")


def get_provider_name() -> str:
    return os.getenv("LLM_PROVIDER", "minimax").strip().lower()


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

        missing = _missing_env(
            (
                ("MINIMAX_API_KEY", api_key),
                ("MINIMAX_BASE_URL", base_url),
                ("MINIMAX_MODEL_ID", model_id),
            )
        )
        if missing:
            raise _required_config_error("MiniMax", missing)

        return cls(api_key=api_key, base_url=base_url, model_id=model_id)


@dataclass(frozen=True)
class AnthropicConfig:
    api_key: str
    base_url: str
    model_id: str

    @classmethod
    def from_env(cls) -> "AnthropicConfig":
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()
        model_id = os.getenv("ANTHROPIC_MODEL_ID", "").strip()

        missing = _missing_env(
            (
                ("ANTHROPIC_API_KEY", api_key),
                ("ANTHROPIC_MODEL_ID", model_id),
            )
        )
        if missing:
            raise _required_config_error("Anthropic", missing)

        return cls(api_key=api_key, base_url=base_url, model_id=model_id)


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    base_url: str
    model_id: str

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        model_id = os.getenv("OPENAI_MODEL_ID", "").strip()

        missing = _missing_env(
            (
                ("OPENAI_API_KEY", api_key),
                ("OPENAI_MODEL_ID", model_id),
            )
        )
        if missing:
            raise _required_config_error("OpenAI", missing)

        return cls(api_key=api_key, base_url=base_url, model_id=model_id)


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str
    base_url: str
    model_id: str

    @classmethod
    def from_env(cls) -> "DeepSeekConfig":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        base_url = os.getenv("DEEPSEEK_BASE_URL", "").strip() or "https://api.deepseek.com"
        model_id = os.getenv("DEEPSEEK_MODEL_ID", "").strip()

        missing = _missing_env(
            (
                ("DEEPSEEK_API_KEY", api_key),
                ("DEEPSEEK_MODEL_ID", model_id),
            )
        )
        if missing:
            raise _required_config_error("DeepSeek", missing)

        return cls(api_key=api_key, base_url=base_url, model_id=model_id)


@lru_cache(maxsize=1)
def get_minimax_config() -> MiniMaxConfig:
    return MiniMaxConfig.from_env()


@lru_cache(maxsize=1)
def get_anthropic_config() -> AnthropicConfig:
    return AnthropicConfig.from_env()


@lru_cache(maxsize=1)
def get_openai_config() -> OpenAIConfig:
    return OpenAIConfig.from_env()


@lru_cache(maxsize=1)
def get_deepseek_config() -> DeepSeekConfig:
    return DeepSeekConfig.from_env()

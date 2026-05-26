import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("MINIMAX_API_KEY", "test-api-key")
os.environ.setdefault("MINIMAX_BASE_URL", "https://example.com/v1")
os.environ.setdefault("MINIMAX_MODEL_ID", "test-model")

from agent.runtime.agent.agent import Agent, AgentConfig


def test_agent_run_passes_session_id_to_agent_loop(tmp_path: Path) -> None:
    llm_client = object()
    config = AgentConfig(
        workspace=tmp_path,
        max_steps=3,
        max_tokens=256,
        session_id="test-session-123",
        llm_client=llm_client,
    )
    agent = Agent(config)
    messages = [{"role": "user", "content": "hello"}]

    with patch("agent.runtime.agent.agent.agent_loop", return_value="ok") as mock_loop:
        result = agent.run(messages)

    assert result == "ok"
    mock_loop.assert_called_once_with(
        messages=messages,
        max_tokens=256,
        max_steps=3,
        workspace=tmp_path,
        session_id="test-session-123",
        llm_client=llm_client,
        hooks=None,
    )

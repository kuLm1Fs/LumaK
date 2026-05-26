from importlib import reload


def test_importing_llm_client_does_not_create_provider(monkeypatch) -> None:
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_BASE_URL", raising=False)
    monkeypatch.delenv("MINIMAX_MODEL_ID", raising=False)

    import agent.LLM.client as client_module

    reload(client_module)


def test_get_default_client_is_cached(monkeypatch) -> None:
    import agent.LLM.client as client_module

    class FakeProvider:
        pass

    client_module.get_default_client.cache_clear()
    monkeypatch.setattr(client_module, "get_provider_name", lambda: "minimax")
    monkeypatch.setitem(client_module.PROVIDER_FACTORIES, "minimax", FakeProvider)

    first = client_module.get_default_client()
    second = client_module.get_default_client()

    assert first is second


def test_get_default_client_selects_configured_provider(monkeypatch) -> None:
    import agent.LLM.client as client_module

    class FakeOpenAIProvider:
        pass

    client_module.get_default_client.cache_clear()
    monkeypatch.setattr(client_module, "get_provider_name", lambda: "openai")
    monkeypatch.setitem(client_module.PROVIDER_FACTORIES, "openai", FakeOpenAIProvider)

    assert isinstance(client_module.get_default_client(), FakeOpenAIProvider)


def test_get_default_client_rejects_unknown_provider(monkeypatch) -> None:
    import pytest
    import agent.LLM.client as client_module

    client_module.get_default_client.cache_clear()
    monkeypatch.setattr(client_module, "get_provider_name", lambda: "unknown")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        client_module.get_default_client()

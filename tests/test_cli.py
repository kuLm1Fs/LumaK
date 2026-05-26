from importlib import reload


def test_cli_parser_import_does_not_require_model_environment(monkeypatch) -> None:
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_BASE_URL", raising=False)
    monkeypatch.delenv("MINIMAX_MODEL_ID", raising=False)

    import agent.CLI.app as cli_app

    reload(cli_app)
    parser = cli_app.build_parser()

    args = parser.parse_args([])
    assert args.max_tokens == 1024

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


def test_cli_parser_rejects_removed_tui_flag() -> None:
    import agent.CLI.app as cli_app

    parser = cli_app.build_parser()

    try:
        parser.parse_args(["--tui"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("--tui should be handled by the TypeScript tui package, not the Python CLI")


def test_lumak_dispatch_defaults_to_python_cli(monkeypatch) -> None:
    import lumak.cli as lumak_cli

    captured = {}

    def fake_run_cli(args: list[str]) -> int:
        captured["args"] = args
        return 0

    monkeypatch.setattr(lumak_cli, "run_cli", fake_run_cli)

    assert lumak_cli.dispatch([]) == 0
    assert captured["args"] == []


def test_lumak_dispatch_preserves_prompt_compatibility(monkeypatch) -> None:
    import lumak.cli as lumak_cli

    captured = {}

    def fake_run_cli(args: list[str]) -> int:
        captured["args"] = args
        return 0

    monkeypatch.setattr(lumak_cli, "run_cli", fake_run_cli)

    assert lumak_cli.dispatch(["where", "is", "the", "entry?"]) == 0
    assert captured["args"] == ["where", "is", "the", "entry?"]


def test_lumak_dispatch_routes_gateway(monkeypatch) -> None:
    import lumak.cli as lumak_cli

    captured = {}

    def fake_run_gateway(args: list[str]) -> int:
        captured["args"] = args
        return 0

    monkeypatch.setattr(lumak_cli, "run_gateway", fake_run_gateway)

    assert lumak_cli.dispatch(["gateway", "--port", "9999"]) == 0
    assert captured["args"] == ["--port", "9999"]


def test_lumak_dispatch_routes_typescript_tui(monkeypatch) -> None:
    import lumak.cli as lumak_cli

    captured = {}

    def fake_run_tui(args: list[str]) -> int:
        captured["args"] = args
        return 0

    monkeypatch.setattr(lumak_cli, "run_tui", fake_run_tui)

    assert lumak_cli.dispatch(["tui", "--workspace", "/tmp/project"]) == 0
    assert captured["args"] == ["--workspace", "/tmp/project"]


def test_lumak_dispatch_routes_web(monkeypatch) -> None:
    import lumak.cli as lumak_cli

    captured = {}

    def fake_run_web(args: list[str]) -> int:
        captured["args"] = args
        return 0

    monkeypatch.setattr(lumak_cli, "run_web", fake_run_web)

    assert lumak_cli.dispatch(["web"]) == 0
    assert captured["args"] == []

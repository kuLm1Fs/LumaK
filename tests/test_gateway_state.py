from pathlib import Path

import pytest

from gateway.state import GatewayState, resolve_workspace_path, workspace_name


def test_resolve_workspace_path_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="workspace does not exist"):
        resolve_workspace_path(str(tmp_path / "missing"))


def test_gateway_state_uses_default_workspace_for_unswitched_sessions(tmp_path: Path) -> None:
    state = GatewayState(tmp_path)

    assert state.workspace_for_session("s1") == tmp_path.resolve()
    assert state.memory_root_for_session("s1") == tmp_path.resolve() / ".memory"
    assert state.roots_for_session("s1") == (
        tmp_path.resolve() / ".memory",
        tmp_path.resolve() / ".trace",
        tmp_path.resolve() / ".skills",
    )


def test_gateway_state_switches_workspace_for_one_session(tmp_path: Path) -> None:
    default_workspace = tmp_path / "default"
    switched_workspace = tmp_path / "switched"
    default_workspace.mkdir()
    switched_workspace.mkdir()
    state = GatewayState(default_workspace)

    workspace = state.switch_session_workspace("s1", str(switched_workspace))

    assert workspace == switched_workspace.resolve()
    assert state.workspace_for_session("s1") == switched_workspace.resolve()
    assert state.workspace_for_session("s2") == default_workspace.resolve()
    assert state.memory_root_for_session("s1") == switched_workspace.resolve() / ".memory"


def test_gateway_state_configure_default_workspace_clears_session_switches(tmp_path: Path) -> None:
    old_workspace = tmp_path / "old"
    switched_workspace = tmp_path / "switched"
    new_workspace = tmp_path / "new"
    old_workspace.mkdir()
    switched_workspace.mkdir()
    new_workspace.mkdir()
    state = GatewayState(old_workspace)
    state.switch_session_workspace("s1", str(switched_workspace))

    workspace = state.configure_default_workspace(str(new_workspace))

    assert workspace == new_workspace.resolve()
    assert state.default_workspace == new_workspace.resolve()
    assert state.session_workspaces == {}
    assert state.workspace_for_session("s1") == new_workspace.resolve()


def test_gateway_state_project_detail_uses_pyproject_name(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = \"demo\"\n", encoding="utf-8")
    state = GatewayState(tmp_path)

    assert workspace_name(tmp_path) == "demo"
    assert state.project_detail()["name"] == "demo"
    assert state.project_list() == [
        {
            "id": "current",
            "name": "demo",
            "path": str(tmp_path.resolve()),
            "active": True,
        }
    ]

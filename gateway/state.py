from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, Callable


def resolve_workspace_path(raw_path: str) -> Path:
    workspace = Path(raw_path).expanduser().resolve()
    if not workspace.exists():
        raise ValueError(f"workspace does not exist: {workspace}")
    if not workspace.is_dir():
        raise ValueError(f"workspace is not a directory: {workspace}")
    return workspace


def workspace_roots(workspace: Path) -> tuple[Path, Path, Path]:
    return workspace / ".memory", workspace / ".trace", workspace / ".skills"


ManifestReader = Callable[[Path], str | None]


def _read_pyproject(workspace: Path) -> str | None:
    pyproject_path = workspace / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    try:
        pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        name = pyproject.get("project", {}).get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    except (OSError, tomllib.TOMLDecodeError):
        pass
    return None


def _read_cargo(workspace: Path) -> str | None:
    cargo_path = workspace / "Cargo.toml"
    if not cargo_path.exists():
        return None
    try:
        cargo = tomllib.loads(cargo_path.read_text(encoding="utf-8"))
        name = cargo.get("package", {}).get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    except (OSError, tomllib.TOMLDecodeError):
        pass
    return None


def _read_package_json(workspace: Path) -> str | None:
    package_json_path = workspace / "package.json"
    if not package_json_path.exists():
        return None
    try:
        package = json.loads(package_json_path.read_text(encoding="utf-8"))
        name = package.get("name")
        if isinstance(name, str) and name.strip() and not name.startswith("."):
            return name.strip()
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _read_gomod(workspace: Path) -> str | None:
    gomod_path = workspace / "go.mod"
    if not gomod_path.exists():
        return None
    try:
        for line in gomod_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("module "):
                name = stripped.removeprefix("module ").strip()
                if name:
                    return name
    except OSError:
        pass
    return None


MANIFEST_READERS: list[ManifestReader] = [
    _read_package_json,
    _read_pyproject,
    _read_cargo,
    _read_gomod,
]


def workspace_name(workspace: Path) -> str:
    for reader in MANIFEST_READERS:
        name = reader(workspace)
        if name is not None:
            return name
    return workspace.name


class GatewayState:
    def __init__(self, default_workspace: Path | str) -> None:
        self.default_workspace = resolve_workspace_path(str(default_workspace))
        self.session_workspaces: dict[str, Path] = {}

    @property
    def memory_root(self) -> Path:
        return self.default_workspace / ".memory"

    @property
    def trace_root(self) -> Path:
        return self.default_workspace / ".trace"

    @property
    def skills_root(self) -> Path:
        return self.default_workspace / ".skills"

    def configure_default_workspace(self, raw_workspace: str) -> Path:
        self.default_workspace = resolve_workspace_path(raw_workspace)
        self.session_workspaces.clear()
        return self.default_workspace

    def workspace_for_session(self, session_id: str) -> Path:
        return self.session_workspaces.get(session_id, self.default_workspace)

    def switch_session_workspace(self, session_id: str, raw_workspace: str) -> Path:
        workspace = resolve_workspace_path(raw_workspace)
        self.session_workspaces[session_id] = workspace
        return workspace

    def roots_for_workspace(self, workspace: Path) -> tuple[Path, Path, Path]:
        return workspace_roots(workspace)

    def roots_for_session(self, session_id: str) -> tuple[Path, Path, Path]:
        return workspace_roots(self.workspace_for_session(session_id))

    def memory_root_for_session(self, session_id: str) -> Path:
        memory_root, _trace_root, _skills_root = self.roots_for_session(session_id)
        return memory_root

    def project_detail(self, workspace: Path | None = None) -> dict[str, Any]:
        workspace = workspace or self.default_workspace
        return {
            "id": "current",
            "name": workspace_name(workspace),
            "path": str(workspace),
            "active": True,
            "memory_root": str(workspace / ".memory"),
            "trace_root": str(workspace / ".trace"),
            "skills_root": str(workspace / ".skills"),
        }

    def project_list(self, workspace: Path | None = None) -> list[dict[str, Any]]:
        project = self.project_detail(workspace or self.default_workspace)
        return [
            {
                "id": project["id"],
                "name": project["name"],
                "path": project["path"],
                "active": project["active"],
            }
        ]

from __future__ import annotations

from pathlib import Path

from agent.analysis.python_ast import FileOutline, parse_python_file


SKIPPED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def should_skip(path: Path, workspace: Path) -> bool:
    try:
        relative = path.resolve().relative_to(workspace.resolve())
    except ValueError:
        return True
    return any(part in SKIPPED_DIRS for part in relative.parts)


def build_code_index(workspace: Path | str, pattern: str = "**/*.py") -> list[FileOutline]:
    root = Path(workspace).resolve()
    outlines: list[FileOutline] = []

    for path in sorted(root.glob(pattern)):
        if not path.is_file() or should_skip(path, root):
            continue

        try:
            outlines.append(parse_python_file(path, root))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

    return outlines

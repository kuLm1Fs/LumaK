from __future__ import annotations

import time
from pathlib import Path
import difflib

WORKDIR = Path.cwd().resolve()
SKIPPED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}


def _workspace_root(workspace: Path | str | None = None) -> Path:
    return Path(workspace or WORKDIR).resolve()


def _is_skipped(path: Path, workspace: Path) -> bool:
    try:
        relative = path.resolve().relative_to(workspace)
    except ValueError:
        return True
    return any(part in SKIPPED_DIRS for part in relative.parts)


def _validate_glob_pattern(pattern: str) -> str:
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError("pattern is required")
    if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
        raise ValueError("glob pattern must stay inside workspace")
    return pattern


def safe_path(p: str, workspace: Path | str | None = None) -> Path:
    if not isinstance(p, str) or not p.strip():
        raise ValueError("path is required")

    root = _workspace_root(workspace)
    raw_path = Path(p)
    path = raw_path.resolve() if raw_path.is_absolute() else (root / raw_path).resolve()

    if not path.is_relative_to(root):
        raise ValueError(f"path escapes workspace: {p}")
    if _is_skipped(path, root):
        raise ValueError(f"path is ignored by workspace guard: {p}")
    return path


def run_read(path: str, limit: int | None = None, workspace: Path | str | None = None) -> str:
    try:
        if limit is not None and limit <= 0:
            return "Error: ValidationError: limit must be greater than 0"

        file_path = safe_path(path, workspace)
        if not file_path.exists():
            return f"Error: NotFoundError: file not found: {path}"
        if not file_path.is_file():
            return f"Error: ValidationError: path is not a file: {path}"

        lines = file_path.read_text(encoding="utf-8").splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)
    except UnicodeDecodeError:
        return f"Error: ValidationError: file is not valid utf-8 text: {path}"
    except ValueError as e:
        return f"Error: PathError: {e}"
    except OSError as e:
        return f"Error: IOError: {e}"


def run_write(path: str, content: str, workspace: Path | str | None = None) -> str:
    try:
        if not isinstance(content, str):
            return "Error: ValidationError: content must be a string"

        file_path = safe_path(path, workspace)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} bytes to {path}"
    except ValueError as e:
        return f"Error: PathError: {e}"
    except OSError as e:
        return f"Error: IOError: {e}"


def run_edit(
    path: str,
    old_text: str,
    new_text: str,
    workspace: Path | str | None = None,
) -> str:
    try:
        if not old_text:
            return "Error: ValidationError: old_text is required"

        file_path = safe_path(path, workspace)
        if not file_path.exists():
            return f"Error: NotFoundError: file not found: {path}"
        if not file_path.is_file():
            return f"Error: ValidationError: path is not a file: {path}"

        text = file_path.read_text(encoding="utf-8")
        if old_text not in text:
            return f"Error: NotFoundError: text not found in {path}"
        file_path.write_text(text.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited {path}"
    except UnicodeDecodeError:
        return f"Error: ValidationError: file is not valid utf-8 text: {path}"
    except ValueError as e:
        return f"Error: PathError: {e}"
    except OSError as e:
        return f"Error: IOError: {e}"


def run_safe_edit(
    path: str,
    old_text: str,
    new_text: str,
    preview: bool = False,
    workspace: Path | str | None = None,
) -> str:
    try:
        if not old_text:
            return "Error: ValidationError: old_text is required"
        if not isinstance(new_text, str):
            return "Error: ValidationError: new_text must be a string"

        file_path = safe_path(path, workspace)
        if not file_path.exists():
            return f"Error: NotFoundError: file not found: {path}"
        if not file_path.is_file():
            return f"Error: ValidationError: path is not a file: {path}"

        text = file_path.read_text(encoding="utf-8")
        if old_text not in text:
            return f"Error: NotFoundError: old_text not found in {path}"

        patched = text.replace(old_text, new_text, 1)
        diff = "\n".join(
            difflib.unified_diff(
                text.splitlines(keepends=True),
                patched.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                lineterm="",
            )
        )

        if preview:
            return f"Preview (no write performed):\n{diff or '(no diff)'}"

        file_path.write_text(patched, encoding="utf-8")
        return f"Edited {path}\n\n{diff or '(no diff)'}"
    except UnicodeDecodeError:
        return f"Error: ValidationError: file is not valid utf-8 text: {path}"
    except ValueError as e:
        return f"Error: PathError: {e}"
    except OSError as e:
        return f"Error: IOError: {e}"


def run_glob(
    pattern: str,
    limit: int = 200,
    workspace: Path | str | None = None,
    timeout_seconds: float = 8.0,
) -> str:
    try:
        if limit <= 0:
            return "Error: ValidationError: limit must be greater than 0"

        root = _workspace_root(workspace)
        pattern = _validate_glob_pattern(pattern)
        deadline = time.monotonic() + timeout_seconds
        results = []
        for match in root.glob(pattern):
            if time.monotonic() > deadline:
                results.append(f"... glob timeout after {timeout_seconds:.1f}s")
                break
            if len(results) >= limit:
                results.append(f"... result limit reached ({limit})")
                break
            if not match.resolve().is_relative_to(root) or _is_skipped(match, root):
                continue
            results.append(str(match.relative_to(root)))

        return "\n".join(results) if results else "(no matches)"
    except ValueError as e:
        return f"Error: ValidationError: {e}"
    except OSError as e:
        return f"Error: IOError: {e}"


def run_search_text(
    query: str,
    pattern: str = "**/*",
    limit: int = 50,
    workspace: Path | str | None = None,
    timeout_seconds: float = 5.0,
) -> str:
    if not isinstance(query, str) or not query.strip():
        return "Error: ValidationError: query is required"
    if limit <= 0:
        return "Error: ValidationError: limit must be greater than 0"

    if not any(mark in pattern for mark in "*?[]") and not Path(pattern).suffix:
        pattern = "**/*"

    try:
        root = _workspace_root(workspace)
        pattern = _validate_glob_pattern(pattern)
        deadline = time.monotonic() + timeout_seconds
        results = []

        for file_path in root.glob(pattern):
            if time.monotonic() > deadline:
                results.append(f"... search timeout after {timeout_seconds:.1f}s")
                break
            if len(results) >= limit:
                results.append(f"... result limit reached ({limit})")
                break
            if not file_path.is_file() or _is_skipped(file_path, root):
                continue

            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            except OSError:
                continue

            for line_no, line in enumerate(lines, start=1):
                if query.lower() in line.lower():
                    rel_path = file_path.relative_to(root)
                    results.append(f"{rel_path}:{line_no}: {line.strip()}")
                    if len(results) >= limit:
                        break

        return "\n".join(results) if results else "(no matches)"
    except ValueError as e:
        return f"Error: ValidationError: {e}"
    except OSError as e:
        return f"Error: IOError: {e}"

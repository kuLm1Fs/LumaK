from pathlib import Path

WORKDIR = Path.cwd()

def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


def run_read(path: str, limit: int | None = None) -> str:
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def run_write(path: str, content: str) -> str:
    try:
        file_path = safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        file_path = safe_path(path)
        text = file_path.read_text()
        if old_text not in text:
            return f"Error: text not found in {path}"
        file_path.write_text(text.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"


def run_glob(pattern: str) -> str:
    import glob as g
    try:
        results = []
        for match in g.glob(pattern, root_dir=WORKDIR, recursive=True):
            if (WORKDIR / match).resolve().is_relative_to(WORKDIR):
                results.append(match)
        return "\n".join(results) if results else "(no matches)"
    except Exception as e:
        return f"Error: {e}"

def run_search_text(query: str , pattern: str = "**/*", limit: int = 50) -> str:
    if not query.strip():
        return "Error: query is required"

    if not any(mark in pattern for mark in "*?[]") and not Path(pattern).suffix:
        pattern = "**/*"

    results = []
    skipped_dirs = {".git", ".venv", "__pycache__", ".pytest_cache"}

    try:
        for file_path in WORKDIR.glob(pattern):
            if len(results) >= limit:
                break
            if not file_path.is_file():
                continue
            if any(part in skipped_dirs for part in file_path.parts):
                continue
            if not file_path.resolve().is_relative_to(WORKDIR):
                continue

            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            except OSError:
                continue

            for line_no, line in enumerate(lines, start=1):
                if query.lower() in line.lower():
                    rel_path = file_path.relative_to(WORKDIR)
                    results.append(f"{rel_path}:{line_no}: {line.strip()}")
                    if len(results) >= limit:
                        break

        return "\n".join(results) if results else "(no matches)"
    except Exception as e:
        return f"Error : {e}"


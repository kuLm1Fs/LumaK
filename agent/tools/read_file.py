from pathlib import Path

def read_file(path: Path, limit : int = None) -> str:
    try:
        text = path.read_text()
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error:{e}"
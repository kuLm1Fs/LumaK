from pathlib import Path

def write_file(path: Path, content : str) -> str:
    try:
        fp = path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"
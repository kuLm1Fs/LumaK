from pathlib import Path

WORK_DIR=Path.cwd()

def safe_paht(p: str) -> Path:
    path = (WORK_DIR/p).resolve()
    if not path.is_relative_to(WORK_DIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
from pathlib import Path

def edit_file(path: Path, old_text: str, new_text: str) -> str:
    try:
        fp = path
        content = path.read_text()
        if old_text not in content:
            return f"Error: Text not found in {path}"
        fp.write_text(content.replace(new_text))
        return f"Edited {path}"
    except Exception as e:
        return f"Error{e}"
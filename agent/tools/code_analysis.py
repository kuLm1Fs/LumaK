from __future__ import annotations

from pathlib import Path

from agent.analysis.index import build_code_index
from agent.analysis.python_ast import FileOutline, Symbol, parse_python_file
from agent.tools.filesystems import safe_path


def _workspace_root(workspace: Path | str | None = None) -> Path:
    return Path(workspace or Path.cwd()).resolve()


def _validate_pattern(pattern: str) -> str:
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError("pattern is required")
    if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
        raise ValueError("pattern must stay inside workspace")
    return pattern


def _display_signature(symbol: Symbol) -> str:
    if symbol.kind == "class":
        return symbol.signature
    if symbol.signature.startswith("async def "):
        return symbol.signature.removeprefix("async def ")
    if symbol.signature.startswith("def "):
        return symbol.signature.removeprefix("def ")
    return symbol.signature


def _format_symbol(symbol: Symbol) -> str:
    end = f"-{symbol.end_line}" if symbol.end_line and symbol.end_line != symbol.line else ""
    header = f"  {symbol.signature} lines {symbol.line}{end}"
    parts = [header]
    if symbol.decorators:
        for dec in symbol.decorators:
            parts.append(f"    @{dec}")
    if symbol.docstring:
        doc = symbol.docstring.strip().split("\n")[0]
        parts.append(f"    {doc}")
    return "\n".join(parts)


def _format_outline(outline: FileOutline) -> str:
    lines = [outline.path]
    if outline.imports:
        lines.append(f"  imports: {', '.join(outline.imports)}")
    else:
        lines.append("  imports: (none)")

    if outline.symbols:
        lines.extend(_format_symbol(symbol) for symbol in outline.symbols)
    else:
        lines.append("  symbols: (none)")

    return "\n".join(lines)


def run_file_outline(path: str, workspace: Path | str | None = None) -> str:
    try:
        root = _workspace_root(workspace)
        file_path = safe_path(path, root)
        if not file_path.exists():
            return f"Error: NotFoundError: file not found: {path}"
        if not file_path.is_file():
            return f"Error: ValidationError: path is not a file: {path}"
        if file_path.suffix != ".py":
            return f"Error: ValidationError: path is not a Python file: {path}"

        outline = parse_python_file(file_path, root)
        return _format_outline(outline)
    except SyntaxError as exc:
        return f"Error: SyntaxError: {exc}"
    except UnicodeDecodeError:
        return f"Error: ValidationError: file is not valid utf-8 text: {path}"
    except ValueError as exc:
        return f"Error: PathError: {exc}"
    except OSError as exc:
        return f"Error: IOError: {exc}"


def run_code_map(
    pattern: str = "**/*.py",
    workspace: Path | str | None = None,
    limit: int = 100,
) -> str:
    try:
        if limit <= 0:
            return "Error: ValidationError: limit must be greater than 0"

        root = _workspace_root(workspace)
        pattern = _validate_pattern(pattern)
        outlines = build_code_index(root, pattern=pattern)
        visible = outlines[:limit]
        chunks = [_format_outline(outline) for outline in visible]

        if len(outlines) > limit:
            chunks.append(f"... file limit reached ({limit}/{len(outlines)})")

        return "\n\n".join(chunks) if chunks else "(no Python files)"
    except ValueError as exc:
        return f"Error: ValidationError: {exc}"
    except OSError as exc:
        return f"Error: IOError: {exc}"


def run_symbol_lookup(
    name: str,
    workspace: Path | str | None = None,
    pattern: str = "**/*.py",
    limit: int = 50,
) -> str:
    try:
        if not isinstance(name, str) or not name.strip():
            return "Error: ValidationError: name is required"
        if limit <= 0:
            return "Error: ValidationError: limit must be greater than 0"

        root = _workspace_root(workspace)
        pattern = _validate_pattern(pattern)
        needle = name.strip().lower()
        matches: list[str] = []

        for outline in build_code_index(root, pattern=pattern):
            for symbol in outline.symbols:
                if symbol.name.lower() == needle:
                    matches.append(
                        f"{symbol.path}:{symbol.line}: {symbol.kind} {_display_signature(symbol)}"
                    )
                    if len(matches) >= limit:
                        matches.append(f"... result limit reached ({limit})")
                        return "\n".join(matches)

        return "\n".join(matches) if matches else "(no matches)"
    except ValueError as exc:
        return f"Error: ValidationError: {exc}"
    except OSError as exc:
        return f"Error: IOError: {exc}"

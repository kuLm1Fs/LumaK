from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    path: str
    line: int
    end_line: int | None
    signature: str
    docstring: str | None


@dataclass(frozen=True)
class FileOutline:
    path: str
    imports: list[str]
    symbols: list[Symbol]


def _format_arg(arg: ast.arg, default: ast.expr | None = None) -> str:
    text = arg.arg
    if arg.annotation:
        text = f"{text}: {ast.unparse(arg.annotation)}"
    if default:
        text = f"{text} = {ast.unparse(default)}"
    return text


def _format_arguments(args: ast.arguments) -> str:
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parts = [
        _format_arg(arg, default)
        for arg, default in zip(positional, defaults, strict=True)
    ]

    if args.vararg:
        parts.append(f"*{_format_arg(args.vararg)}")
    elif args.kwonlyargs:
        parts.append("*")

    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        parts.append(_format_arg(arg, default))

    if args.kwarg:
        parts.append(f"**{_format_arg(args.kwarg)}")

    return ", ".join(parts)


def build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    args = _format_arguments(node.args)
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({args}){returns}"


def _relative_path(path: Path, workspace: Path) -> str:
    return str(path.resolve().relative_to(workspace.resolve()))


def _import_name(node: ast.ImportFrom, alias: ast.alias) -> str:
    module = "." * node.level + (node.module or "")
    return f"{module}.{alias.name}" if module else alias.name


def parse_python_file(path: Path, workspace: Path) -> FileOutline:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    relative_path = _relative_path(path, workspace)

    imports: list[str] = []
    symbols: list[Symbol] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
            continue

        if isinstance(node, ast.ImportFrom):
            imports.extend(_import_name(node, alias) for alias in node.names)
            continue

        if isinstance(node, ast.ClassDef):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="class",
                    path=relative_path,
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", None),
                    signature=f"class {node.name}",
                    docstring=ast.get_docstring(node),
                )
            )
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        Symbol(
                            name=child.name,
                            kind="method",
                            path=relative_path,
                            line=child.lineno,
                            end_line=getattr(child, "end_lineno", None),
                            signature=build_signature(child),
                            docstring=ast.get_docstring(child),
                        )
                    )
            continue

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="function",
                    path=relative_path,
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", None),
                    signature=build_signature(node),
                    docstring=ast.get_docstring(node),
                )
            )

    return FileOutline(path=relative_path, imports=imports, symbols=symbols)

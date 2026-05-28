from pathlib import Path

from agent.analysis.index import build_code_index
from agent.analysis.python_ast import parse_python_file
from agent.tools.code_analysis import run_code_map, run_file_outline, run_symbol_lookup
from agent.tools.registry import execute_tool


def write_sample(path: Path) -> None:
    path.write_text(
        '''"""module docs"""

import os
from pathlib import Path


class Store:
    """store docs"""

    def append(self, item: str, retries: int = 1) -> None:
        return None


async def load(path: Path) -> str:
    return str(path)
''',
        encoding="utf-8",
    )


def test_parse_python_file_extracts_imports_classes_and_functions(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    write_sample(sample)

    outline = parse_python_file(sample, tmp_path)

    assert outline.path == "sample.py"
    assert outline.imports == ["os", "pathlib.Path"]
    assert [(symbol.name, symbol.kind) for symbol in outline.symbols] == [
        ("Store", "class"),
        ("append", "method"),
        ("load", "function"),
    ]
    assert outline.symbols[0].docstring == "store docs"
    assert outline.symbols[1].signature == "def append(self, item: str, retries: int = 1) -> None"
    assert outline.symbols[2].signature == "async def load(path: Path) -> str"


def test_build_code_index_skips_ignored_dirs_and_syntax_errors(tmp_path: Path) -> None:
    write_sample(tmp_path / "sample.py")
    (tmp_path / "broken.py").write_text("def nope(:\n", encoding="utf-8")
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    write_sample(ignored_dir / "ignored.py")

    outlines = build_code_index(tmp_path)

    assert [outline.path for outline in outlines] == ["sample.py"]


def test_file_outline_tool_returns_human_readable_outline(tmp_path: Path) -> None:
    write_sample(tmp_path / "sample.py")

    output = run_file_outline("sample.py", workspace=tmp_path)

    assert "sample.py" in output
    assert "imports: os, pathlib.Path" in output
    assert "class Store" in output
    assert "method append(self, item: str, retries: int = 1) -> None" in output
    assert "function async def load(path: Path) -> str" in output


def test_symbol_lookup_finds_matching_symbols(tmp_path: Path) -> None:
    write_sample(tmp_path / "sample.py")

    output = run_symbol_lookup("append", workspace=tmp_path)

    assert "sample.py:" in output
    assert "method append(self, item: str, retries: int = 1) -> None" in output


def test_code_map_tool_returns_project_summary(tmp_path: Path) -> None:
    write_sample(tmp_path / "sample.py")

    output = run_code_map(workspace=tmp_path)

    assert "sample.py" in output
    assert "class Store" in output
    assert "function async def load(path: Path) -> str" in output


def test_registry_exposes_code_analysis_tools(tmp_path: Path) -> None:
    write_sample(tmp_path / "sample.py")

    output = execute_tool("file_outline", {"path": "sample.py"}, workspace=tmp_path)

    assert "sample.py" in output
    assert "class Store" in output

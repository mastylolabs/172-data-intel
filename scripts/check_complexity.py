"""Enforce A/B complexity for every declaration, including all nested classes."""

import ast
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Protocol, cast

# Radon 6 has no typing metadata; narrow its namedtuple API to the fields read here.
from radon.complexity import cc_visit_ast  # type: ignore[import-untyped]


class Block(Protocol):
    name: str
    complexity: int
    lineno: int


def source_files(paths: Sequence[str]) -> Iterator[Path]:
    for name in paths:
        path = Path(name)
        if path.is_dir():
            yield from path.rglob("*.py")
        else:
            yield path


def declarations(path: Path) -> Iterator[Block]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            # Analyze each declaration once: Radon's module report omits some local classes.
            yield cast(Sequence[Block], cc_visit_ast(node))[0]


def check(paths: Sequence[str]) -> int:
    blocks = [(path, block) for path in source_files(paths) for block in declarations(path)]
    failures = [(path, block) for path, block in blocks if block.complexity > 10]
    average = sum(block.complexity for _, block in blocks) / len(blocks) if blocks else 0
    for path, block in failures:
        print(f"Complexity C+ rejected: {path}:{block.lineno} {block.name}")
    print(f"Enforced average complexity: {average:.2f} (A preferred, B accepted)")
    return int(bool(failures) or average > 10)


if __name__ == "__main__":
    sys.exit(check(sys.argv[1:] or ["src", "tests", "scripts"]))

"""Enforce A/B complexity, including methods/closures inside Radon's JSON blocks."""

import subprocess
import sys
from collections.abc import Iterator, Sequence
from typing import NotRequired, TypedDict

from pydantic import TypeAdapter


class Block(TypedDict):
    name: str
    complexity: int
    lineno: int
    methods: NotRequired[list["Block"]]
    closures: NotRequired[list["Block"]]


def descendants(block: Block) -> Iterator[Block]:
    yield block
    for child in block.get("methods", []) + block.get("closures", []):
        yield from descendants(child)


def check(paths: Sequence[str]) -> int:
    completed = subprocess.run(
        ["radon", "cc", *paths, "-j"], check=True, capture_output=True, text=True
    )
    report = TypeAdapter(dict[str, list[Block]]).validate_json(completed.stdout)
    blocks = [
        (path, child) for path, items in report.items() for b in items for child in descendants(b)
    ]
    failures = [(path, b) for path, b in blocks if b["complexity"] > 10]
    average = sum(b["complexity"] for _, b in blocks) / len(blocks) if blocks else 0
    for path, block in failures:
        print(f"Complexity C+ rejected: {path}:{block['lineno']} {block['name']}")
    print(f"Enforced average complexity: {average:.2f} (A preferred, B accepted)")
    return int(bool(failures) or average > 10)


if __name__ == "__main__":
    sys.exit(check(sys.argv[1:] or ["src", "tests", "scripts"]))

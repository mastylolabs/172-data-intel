"""Exercise the actual enforcement CLI, rather than treating Radon's exit as a gate."""

import subprocess
import sys
from pathlib import Path

import pytest


def run_gate(directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_complexity.py", str(directory)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_conforming_function_passes_with_reported_average(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("def simple(value):\n    return value\n")
    result = run_gate(tmp_path)
    assert result.returncode == 0
    assert "Enforced average complexity: 1.00" in result.stdout


@pytest.mark.parametrize("container", ["module", "closure", "class"])
def test_c_plus_function_is_rejected_even_when_nested(tmp_path: Path, container: str) -> None:
    lines = ["def complex(value):"]
    for number in range(10):
        lines.extend([f"    if value == {number}:", f"        return {number}"])
    if container != "module":
        declaration = "class Outer:" if container == "class" else "def outer(value):"
        lines = [declaration] + ["    " + line for line in lines]
    (tmp_path / "sample.py").write_text("\n".join(lines) + "\n")
    result = run_gate(tmp_path)
    assert result.returncode == 1
    assert "Complexity C+ rejected:" in result.stdout
    assert "complex" in result.stdout
    if container == "module":
        assert "Enforced average complexity: 11.00" in result.stdout


def test_no_function_blocks_have_zero_average(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("VALUE = 1\n")
    result = run_gate(tmp_path)
    assert result.returncode == 0
    assert "Enforced average complexity: 0.00" in result.stdout


def test_syntax_error_fails_instead_of_silently_omitting_a_file(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("def broken(:\n")
    assert run_gate(tmp_path).returncode != 0

"""Private Worker configuration and build-provenance safety checks."""

import json
import subprocess
import tomllib
from pathlib import Path

import pytest

from data_intel import worker_build as build_python_worker

WORKER_ROOT = Path(__file__).parents[2] / "workers" / "tools"


def test_worker_is_not_publicly_routable_and_pins_runtime_metadata() -> None:
    config = json.loads((WORKER_ROOT / "wrangler.jsonc").read_text())

    assert config["workers_dev"] is False
    assert config["preview_urls"] is False
    assert config["name"] == "172x-data-intel-m2-tools"
    assert config["compatibility_flags"] == ["python_workers"]
    assert config["version_metadata"]["binding"] == "CF_VERSION_METADATA"
    assert config["vars"] == {"RUNTIME_MODE": "deployed"}
    assert "routes" not in config and "env" not in config


def test_worker_manifest_uses_local_package_and_python_313() -> None:
    project = tomllib.loads((WORKER_ROOT / "pyproject.toml").read_text())

    assert project["project"]["requires-python"] == ">=3.13"
    assert project["tool"]["uv"]["sources"]["172x-data-intel"]["path"] == "../.."
    assert "workers-py>=1.5,<2" in project["dependency-groups"]["dev"]
    assert "workers-runtime-sdk>=1,<2" in project["dependency-groups"]["dev"]


def test_build_revision_requires_clean_committed_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    outputs = iter(("ef8eac322f95580c5c717cdef2c9eabdf7f55ff2", ""))
    monkeypatch.setattr(build_python_worker, "_run_git", lambda *_: next(outputs))

    assert build_python_worker._committed_revision() == "ef8eac322f95580c5c717cdef2c9eabdf7f55ff2"


def test_build_revision_refuses_dirty_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    outputs = iter(("ef8eac322f95580c5c717cdef2c9eabdf7f55ff2", "?? untracked"))
    monkeypatch.setattr(build_python_worker, "_run_git", lambda *_: next(outputs))

    with pytest.raises(ValueError, match="clean checkout"):
        build_python_worker._committed_revision()


def test_build_revision_refuses_malformed_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build_python_worker, "_run_git", lambda *_: "unknown")

    with pytest.raises(ValueError, match="invalid committed revision"):
        build_python_worker._committed_revision()


def test_build_command_is_dry_run_with_clean_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    revision = "ef8eac322f95580c5c717cdef2c9eabdf7f55ff2"
    commands: list[list[str]] = []

    def record(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        assert check is False
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: revision)
    monkeypatch.setattr(subprocess, "run", record)

    assert build_python_worker.main() == 0
    assert commands == [
        [
            "uv",
            "run",
            "--locked",
            "--project",
            "workers/tools",
            "pywrangler",
            "deploy",
            "--dry-run",
            "--var",
            f"BUILD_REVISION:{revision}",
        ]
    ]


def test_missing_build_tool_returns_safe_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise OSError("private path")

    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: "a" * 40)
    monkeypatch.setattr(subprocess, "run", missing)

    assert build_python_worker.main() == 2
    assert capsys.readouterr().err == "Worker build tool unavailable\n"

"""Private Worker configuration and build-provenance safety checks."""

import json
import subprocess
import tomllib
from pathlib import Path

import pytest

from data_intel import worker_build as build_python_worker

WORKER_ROOT = Path(__file__).parents[2] / "workers" / "tools"


def _copy_sources(vendored: Path) -> None:
    source_root = build_python_worker.REPO_ROOT / "src" / "data_intel"
    for source in source_root.rglob("*.py"):
        target = vendored / source.relative_to(source_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


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
    package = json.loads((WORKER_ROOT / "package.json").read_text())
    assert package["devDependencies"]["wrangler"] == "4.127.1"
    lock = json.loads((WORKER_ROOT / "package-lock.json").read_text())
    assert lock["packages"]["node_modules/wrangler"]["version"] == "4.127.1"


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
    contexts: list[Path] = []

    def record(command: list[str], *, check: bool, cwd: Path) -> subprocess.CompletedProcess[str]:
        assert check is False
        commands.append(command)
        contexts.append(cwd)
        if command[4:6] == ["deploy", "--dry-run"]:
            outdir = Path(command[command.index("--outdir") + 1])
            for name in (
                "index.py",
                "python_modules/workers/__init__.py",
                "python_modules/pydantic/__init__.py",
                "python_modules/pydantic_core/__init__.py",
                "python_modules/pydantic_core/_pydantic_core.wasm.so",
            ):
                path = outdir / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            _copy_sources(outdir / "python_modules/data_intel")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: revision)
    monkeypatch.setattr(subprocess, "run", record)

    assert build_python_worker.main() == 0
    assert commands[0] == ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"]
    assert commands[1] == ["uv", "run", "--locked", "pywrangler", "sync", "--force"]
    assert commands[2][:6] == ["uv", "run", "--locked", "pywrangler", "deploy", "--dry-run"]
    assert commands[2][-2:] == ["--var", f"BUILD_REVISION:{revision}"]
    assert "--outdir" in commands[2]
    assert contexts == [WORKER_ROOT, WORKER_ROOT, WORKER_ROOT]
    assert not Path(commands[2][commands[2].index("--outdir") + 1]).exists()


def test_git_revision_check_uses_repository_root(monkeypatch: pytest.MonkeyPatch) -> None:
    def record(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        assert command == ["git", "rev-parse", "HEAD"]
        assert options["cwd"] == WORKER_ROOT.parents[1]
        return subprocess.CompletedProcess(command, 0, stdout="a" * 40)

    monkeypatch.setattr(subprocess, "run", record)
    assert build_python_worker._run_git("rev-parse", "HEAD") == "a" * 40


def test_missing_build_tool_returns_safe_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise OSError("private path")

    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: "a" * 40)
    monkeypatch.setattr(subprocess, "run", missing)

    assert build_python_worker.main() == 2
    assert capsys.readouterr().err == "Worker build tool unavailable\n"


def test_runtime_lock_mutation_refuses_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runtime_lock = tmp_path / "pylock.toml"
    runtime_lock.write_text("reviewed")

    def mutate(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        runtime_lock.write_text("regenerated")
        return subprocess.CompletedProcess([], 0)

    monkeypatch.setattr(build_python_worker, "WORKER_DIR", tmp_path)
    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: "a" * 40)
    monkeypatch.setattr(subprocess, "run", mutate)

    assert build_python_worker.main() == 2
    assert capsys.readouterr().err == "Worker runtime lock changed during build\n"


def test_missing_runtime_lock_refuses_before_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(build_python_worker, "WORKER_DIR", tmp_path)
    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: "a" * 40)

    assert build_python_worker.main() == 2
    assert capsys.readouterr().err == "Worker runtime lock unavailable\n"


def test_bundle_without_vendored_modules_refuses_false_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: "a" * 40)
    monkeypatch.setattr(
        subprocess, "run", lambda command, **_: subprocess.CompletedProcess(command, 0)
    )

    assert build_python_worker.main() == 2
    assert capsys.readouterr().err == "Worker dry-run bundle missing required Python modules\n"


def test_vendored_source_must_match_current_checkout(tmp_path: Path) -> None:
    _copy_sources(tmp_path)
    assert build_python_worker._source_matches(tmp_path)
    (tmp_path / "service_contracts.py").write_text("stale")
    assert not build_python_worker._source_matches(tmp_path)


def test_checkout_change_after_build_refuses_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "pylock.toml").write_text("reviewed")
    revisions = iter(("a" * 40, "dirty"))
    monkeypatch.setattr(build_python_worker, "WORKER_DIR", tmp_path)
    monkeypatch.setattr(build_python_worker, "_committed_revision", lambda: next(revisions))
    monkeypatch.setattr(build_python_worker, "_dry_run", lambda *_: 0)
    monkeypatch.setattr(build_python_worker, "_complete_bundle", lambda *_: True)

    assert build_python_worker.main() == 2
    assert capsys.readouterr().err == "Worker revision changed during build\n"

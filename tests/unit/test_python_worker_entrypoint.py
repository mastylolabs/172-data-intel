"""Mock the unavailable Worker SDK while checking the private entrypoint fence."""

import asyncio
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ENTRYPOINT = Path(__file__).parents[2] / "workers" / "tools" / "src" / "index.py"
REVISION = "7148d44e78af13c146a0a63b48249c11c0bef3f8"
WORKER_ID = "fe864d4b-909b-4016-8aa0-4d5cc2f499c0"


@dataclass(frozen=True, slots=True)
class _Response:
    body: str
    status: int


class _WorkerEntrypoint:
    env: object


def test_private_entrypoint_requires_own_provenance_and_has_no_public_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdk = ModuleType("workers")
    sdk.__dict__["Response"] = _Response
    sdk.__dict__["WorkerEntrypoint"] = _WorkerEntrypoint
    monkeypatch.setitem(sys.modules, "workers", sdk)
    worker_type = runpy.run_path(str(ENTRYPOINT))["Default"]
    worker = worker_type()

    worker.env = SimpleNamespace(RUNTIME_MODE="deployed", BUILD_REVISION=REVISION)
    invalid = asyncio.run(worker.fetch(object()))
    assert (invalid.status, invalid.body) == (503, "runtime_incompatible")

    worker.env = SimpleNamespace(
        RUNTIME_MODE="deployed",
        BUILD_REVISION=REVISION,
        CF_VERSION_METADATA=SimpleNamespace(id=WORKER_ID),
    )
    valid = asyncio.run(worker.fetch(object()))
    assert (valid.status, valid.body) == (404, "Not found")

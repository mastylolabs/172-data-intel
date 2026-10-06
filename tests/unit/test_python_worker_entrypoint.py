"""Mock the unavailable Worker SDK while checking the private entrypoint fence."""

import asyncio
import json
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from data_intel.worker_transport import JsException

ENTRYPOINT = Path(__file__).parents[2] / "workers" / "tools" / "src" / "index.py"
REVISION = "7148d44e78af13c146a0a63b48249c11c0bef3f8"
WORKER_ID = "fe864d4b-909b-4016-8aa0-4d5cc2f499c0"


@dataclass(frozen=True, slots=True)
class _Response:
    body: bytes
    status: int
    headers: dict[str, str]


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
    assert (invalid.status, json.loads(invalid.body)["code"]) == (503, "runtime_incompatible")

    worker.env = SimpleNamespace(
        RUNTIME_MODE="deployed",
        BUILD_REVISION=REVISION,
        CF_VERSION_METADATA=SimpleNamespace(id=WORKER_ID),
    )
    valid = asyncio.run(worker.fetch(SimpleNamespace(method="GET", url="https://tools/support")))
    assert (valid.status, json.loads(valid.body)["code"]) == (404, "not_found")
    assert valid.headers == {"content-type": "application/json"}
    health = asyncio.run(worker.fetch(SimpleNamespace(method="GET", url="https://tools/health")))
    assert health.status == 200
    assert json.loads(health.body)["worker_version_id"] == WORKER_ID


class _Chunk:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.byteLength = len(data)

    def to_bytes(self) -> bytes:
        return self.data


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.cancelled = False
        self.released = False

    async def read(self) -> SimpleNamespace:
        if self.data:
            data, self.data = self.data, b""
            return SimpleNamespace(done=False, value=_Chunk(data))
        return SimpleNamespace(done=True)

    async def cancel(self) -> None:
        self.cancelled = True

    def releaseLock(self) -> None:
        self.released = True


def test_worker_streams_query_with_body_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    sdk = ModuleType("workers")
    sdk.__dict__.update(Response=_Response, WorkerEntrypoint=_WorkerEntrypoint)
    monkeypatch.setitem(sys.modules, "workers", sdk)
    worker = runpy.run_path(str(ENTRYPOINT))["Default"]()
    worker.env = SimpleNamespace(RUNTIME_MODE="local", BUILD_REVISION=None)

    reader = _Reader(b"{" + b" " * 16_384)
    oversized = SimpleNamespace(
        method="POST", url="https://tools/query", body=SimpleNamespace(getReader=lambda: reader)
    )
    response = asyncio.run(worker.fetch(oversized))
    assert (response.status, json.loads(response.body)["code"]) == (413, "result_limit")
    assert reader.cancelled and reader.released


class _FailedReader(_Reader):
    async def read(self) -> SimpleNamespace:
        raise JsException("private runtime failure")


def test_worker_maps_ffi_stream_failure_to_safe_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdk = ModuleType("workers")
    sdk.__dict__.update(Response=_Response, WorkerEntrypoint=_WorkerEntrypoint)
    monkeypatch.setitem(sys.modules, "workers", sdk)
    worker = runpy.run_path(str(ENTRYPOINT))["Default"]()
    worker.env = SimpleNamespace(RUNTIME_MODE="local", BUILD_REVISION=None)
    reader = _FailedReader(b"")
    request = SimpleNamespace(
        method="POST", url="https://tools/query", body=SimpleNamespace(getReader=lambda: reader)
    )
    response = asyncio.run(worker.fetch(request))
    assert (response.status, json.loads(response.body)["code"]) == (400, "unsupported_transport")
    assert b"private runtime failure" not in response.body
    assert reader.released

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
JOB = "20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b"
RUN = "d2ebca4d-b6ce-4c98-a9e0-d7fa8e6f9ba0"


@dataclass(frozen=True, slots=True)
class _Response:
    body: bytes
    status: int
    headers: dict[str, str]


class _WorkerEntrypoint:
    env: object


class _BrokenRequest:
    @property
    def method(self) -> str:
        raise JsException("method unavailable")

    @property
    def url(self) -> str:
        raise JsException("url unavailable")


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
    malformed = asyncio.run(worker.fetch(SimpleNamespace(method="GET", url=None)))
    assert (malformed.status, json.loads(malformed.body)["code"]) == (400, "unsupported_transport")
    broken = asyncio.run(worker.fetch(_BrokenRequest()))
    assert (broken.status, json.loads(broken.body)["code"]) == (400, "unsupported_transport")
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


class _GetBodyFailure(SimpleNamespace):
    @property
    def body(self) -> object:
        raise JsException("GET body unavailable")


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


def test_worker_dispatches_private_v2_tools_with_endpoint_caps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from data_intel.sales_demo import DEMO_SOURCE
    from data_intel.support_demo import SUPPORT_SOURCE

    sdk = ModuleType("workers")
    sdk.__dict__.update(Response=_Response, WorkerEntrypoint=_WorkerEntrypoint)
    monkeypatch.setitem(sys.modules, "workers", sdk)
    worker = runpy.run_path(str(ENTRYPOINT))["Default"]()
    worker.env = SimpleNamespace(RUNTIME_MODE="local", BUILD_REVISION=None)

    def body(_path: str, source: object, **fields: object) -> bytes:
        return json.dumps(
            {"version": "2", "job_id": JOB, "run_id": RUN, "source": source, **fields}
        ).encode()

    catalog = asyncio.run(
        worker.fetch(_GetBodyFailure(method="GET", url="https://tools/v2/catalog"))
    )
    assert catalog.status == 200
    profile = asyncio.run(
        worker.fetch(
            SimpleNamespace(
                method="POST",
                url="https://tools/v2/profile",
                body=SimpleNamespace(
                    getReader=lambda: _Reader(
                        body("/v2/profile", DEMO_SOURCE.model_dump(mode="json"))
                    ),
                ),
            )
        )
    )
    assert profile.status == 200 and json.loads(profile.body)["version"] == "2"
    search = body("/v2/search", SUPPORT_SOURCE.model_dump(mode="json"), query="export", max_hits=2)
    response = asyncio.run(
        worker.fetch(
            SimpleNamespace(
                method="POST",
                url="https://tools/v2/search",
                body=SimpleNamespace(getReader=lambda: _Reader(search)),
            )
        )
    )
    assert response.status == 200
    oversized = _Reader(body("/v2/profile", DEMO_SOURCE.model_dump(mode="json")) + b" " * 1025)
    response = asyncio.run(
        worker.fetch(
            SimpleNamespace(
                method="POST",
                url="https://tools/v2/profile",
                body=SimpleNamespace(getReader=lambda: oversized),
            )
        )
    )
    assert response.status == 413 and json.loads(response.body)["code"] == "result_limit"

"""Worker stream failures remain typed until the Worker maps them safely."""

import asyncio
from types import SimpleNamespace

import pytest

from data_intel.worker_transport import JsException, read_bounded_body


class _Stream:
    def __init__(self, phase: str) -> None:
        self.phase = phase
        self.released = False

    def getReader(self) -> "_Stream":
        if self.phase == "get":
            raise JsException("getReader failed")
        return self

    async def read(self) -> SimpleNamespace:
        if self.phase == "read":
            raise JsException("read failed")
        return SimpleNamespace(done=True)

    async def cancel(self) -> None:
        return None

    def releaseLock(self) -> None:
        self.released = True
        if self.phase == "release":
            raise JsException("release failed")


@pytest.mark.parametrize("phase", ("get", "read", "release"))
def test_pyodide_stream_failures_are_preserved(phase: str) -> None:
    stream = _Stream(phase)
    request = SimpleNamespace(body=stream)

    with pytest.raises(JsException):
        asyncio.run(read_bounded_body(request))

    assert stream.released is (phase != "get")

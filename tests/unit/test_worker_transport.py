"""Worker stream failures remain typed until the Worker maps them safely."""

import asyncio
from types import SimpleNamespace

import pytest

from data_intel.worker_transport import BodyTooLarge, JsException, read_bounded_body


class _Stream:
    def __init__(self, phase: str, chunks: tuple[bytes, ...] = ()) -> None:
        self.phase = phase
        self.chunks = list(chunks)
        self.cancelled = False
        self.released = False

    def getReader(self) -> "_Stream":
        if self.phase == "get":
            raise JsException("getReader failed")
        return self

    async def read(self) -> SimpleNamespace:
        if self.phase == "read":
            raise JsException("read failed")
        if self.chunks:
            data = self.chunks.pop(0)
            return SimpleNamespace(
                done=False, value=SimpleNamespace(byteLength=len(data), to_bytes=lambda: data)
            )
        return SimpleNamespace(done=True)

    async def cancel(self) -> None:
        self.cancelled = True
        if self.phase == "cancel":
            raise JsException("cancel failed")

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


def test_bounded_body_accepts_chunks_and_refuses_cap_overflow() -> None:
    chunks = (b"a" * 8_000, b"b" * 8_384)
    assert (
        len(asyncio.run(read_bounded_body(SimpleNamespace(body=_Stream("ok", chunks))))) == 16_384
    )

    stream = _Stream("ok", (b"x" * 16_385,))
    with pytest.raises(BodyTooLarge):
        asyncio.run(read_bounded_body(SimpleNamespace(body=stream)))
    assert stream.cancelled and stream.released


def test_bounded_body_preserves_cancel_ffi_failure() -> None:
    stream = _Stream("cancel", (b"x" * 16_385,))

    with pytest.raises(JsException):
        asyncio.run(read_bounded_body(SimpleNamespace(body=stream)))

    assert stream.cancelled and stream.released

"""Bounded Worker request-body streaming with Pyodide FFI errors preserved."""

from importlib import import_module
from typing import Protocol, cast


class _FallbackJsException(Exception):
    """Local test fallback for the Pyodide runtime exception."""


JsException: type[Exception]
try:
    JsException = cast(type[Exception], import_module("pyodide.ffi").JsException)
except ModuleNotFoundError:
    JsException = _FallbackJsException


MAX_BODY_BYTES = 16_384


class BodyTooLarge(ValueError):
    """The request body exceeded the service transport limit."""


class _Chunk(Protocol):
    byteLength: int

    def to_bytes(self) -> bytes: ...


class _ReadResult(Protocol):
    done: bool
    value: _Chunk


class _Reader(Protocol):
    async def read(self) -> _ReadResult: ...

    async def cancel(self) -> object: ...

    def releaseLock(self) -> object: ...


class _Stream(Protocol):
    def getReader(self) -> _Reader: ...


async def read_bounded_body(request: object) -> bytes:
    """Read a Worker stream and let the caller classify runtime FFI failures."""
    stream = getattr(request, "body", None)
    if stream is None:
        return b""
    reader = cast(_Stream, stream).getReader()
    chunks: list[bytes] = []
    size = 0
    try:
        while True:
            part = await reader.read()
            if part.done:
                return b"".join(chunks)
            size += part.value.byteLength
            if size > MAX_BODY_BYTES:
                await reader.cancel()
                raise BodyTooLarge
            chunks.append(part.value.to_bytes())
    finally:
        reader.releaseLock()

"""Private, bounded normalization and canonicalization for query result values."""

import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Literal

ResultErrorCode = Literal["invalid_input", "invalid_result", "result_limit"]


class ResultContentError(ValueError):
    """A safe classification for invalid or oversized result content."""

    def __init__(self, code: ResultErrorCode) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class IntegerCell:
    type: Literal["integer"]
    value: str
    exact: Literal[True]


@dataclass(frozen=True, slots=True)
class RealCell:
    type: Literal["real"]
    value: str
    exact: Literal[False]


@dataclass(frozen=True, slots=True)
class TextCell:
    type: Literal["text"]
    value: str


@dataclass(frozen=True, slots=True)
class NullCell:
    type: Literal["null"]
    value: None


type Cell = IntegerCell | RealCell | TextCell | NullCell


@dataclass(frozen=True, slots=True)
class BoundedResultContent:
    columns: tuple[str, ...]
    rows: tuple[tuple[Cell, ...], ...]
    row_count: int
    content_bytes: bytes
    content_sha256: str


def _column_label(labels: Sequence[object], index: int) -> str:
    try:
        label = labels[index]
    except (IndexError, KeyError, TypeError, ValueError):
        raise ResultContentError("invalid_result") from None
    if type(label) is not str or not label:
        raise ResultContentError("invalid_result")
    try:
        label_bytes = label.encode("utf-8")
    except UnicodeEncodeError:
        raise ResultContentError("invalid_result") from None
    if len(label_bytes) > 64:
        raise ResultContentError("result_limit")
    return label


def _columns(labels: Sequence[object]) -> tuple[str, ...]:
    try:
        count = len(labels)
    except (OverflowError, TypeError, ValueError):
        raise ResultContentError("invalid_result") from None
    if count < 1 or count > 16:
        raise ResultContentError("result_limit")
    names = tuple(_column_label(labels, index) for index in range(count))
    if len(set(names)) != count:
        raise ResultContentError("invalid_result")
    return names


def _cell(value: object) -> Cell:
    if type(value) is int:
        if value < -(2**63) or value > 2**63 - 1:
            raise ResultContentError("invalid_result")
        return IntegerCell("integer", str(value), True)
    if type(value) is float:
        if not math.isfinite(value):
            raise ResultContentError("invalid_result")
        return RealCell("real", repr(value), False)
    if type(value) is str:
        try:
            text_bytes = value.encode("utf-8")
        except UnicodeEncodeError:
            raise ResultContentError("invalid_result") from None
        if len(text_bytes) > 256:
            raise ResultContentError("result_limit")
        return TextCell("text", value)
    if value is None:
        return NullCell("null", None)
    raise ResultContentError("invalid_result")


def _row(row: object, column_count: int) -> tuple[Cell, ...]:
    if isinstance(row, (str, bytes, bytearray, memoryview)) or not isinstance(row, Sequence):
        raise ResultContentError("invalid_result")
    try:
        width = len(row)
    except (OverflowError, TypeError, ValueError):
        raise ResultContentError("invalid_result") from None
    if width != column_count:
        raise ResultContentError("invalid_result")
    cells: list[Cell] = []
    for index in range(column_count):
        try:
            value = row[index]
        except (IndexError, KeyError, TypeError, ValueError):
            raise ResultContentError("invalid_result") from None
        cells.append(_cell(value))
    return tuple(cells)


def _canonical_bytes(columns: tuple[str, ...], rows: tuple[tuple[Cell, ...], ...]) -> bytes:
    wire_rows = [[asdict(cell) for cell in row] for row in rows]
    try:
        content = json.dumps(
            {"columns": columns, "rows": wire_rows},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise ResultContentError("invalid_result") from None
    if len(content) > 16_384:
        raise ResultContentError("result_limit")
    return content


def build_bounded_result(
    labels: Sequence[object], rows: Iterable[Sequence[object]], max_rows: int
) -> BoundedResultContent:
    """Validate fetched scalar rows and return an immutable, hashed canonical value."""
    if type(max_rows) is not int or not 1 <= max_rows <= 20:
        raise ResultContentError("invalid_input")
    columns = _columns(labels)
    try:
        iterator = iter(rows)
    except TypeError:
        raise ResultContentError("invalid_result") from None
    normalized: list[tuple[Cell, ...]] = []
    for index in range(max_rows + 1):
        try:
            raw_row = next(iterator)
        except StopIteration:
            break
        # Execution failures remain for the query engine to classify safely.
        if index == max_rows:
            raise ResultContentError("result_limit")
        normalized.append(_row(raw_row, len(columns)))
    frozen_rows = tuple(normalized)
    content = _canonical_bytes(columns, frozen_rows)
    return BoundedResultContent(
        columns=columns,
        rows=frozen_rows,
        row_count=len(frozen_rows),
        content_bytes=content,
        content_sha256=sha256(content).hexdigest(),
    )

"""Pinned synthetic sales-demo loading; no profiling or analytical capability."""

import csv
import hashlib
import io
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Self

from pydantic import Field, field_validator, model_validator

from data_intel.contracts import SourceId, SourceIdentity
from data_intel.sales_fixture import (
    SALES_COLUMNS,
    SALES_FIELDS,
    FieldMeaning,
    FixtureError,
    SaleRow,
)

DEMO_REVISION = "sales-demo.v1"
DEMO_SHA256 = "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f"
DEMO_SOURCE = SourceIdentity(
    version="1",
    source_id=SourceId.SALES,
    snapshot_sha256=DEMO_SHA256,
    meaning_revision=DEMO_REVISION,
)
DEMO_PATH = Path(__file__).parent / "fixtures" / "sales-demo.csv"
DEMO_BYTES, DEMO_RECORDS = 1025, 24
MAX_BYTES, MAX_RECORDS, MAX_LINE_BYTES, MAX_CELL_BYTES = 65_536, 256, 2048, 256
DEMO_FIELDS = (
    FieldMeaning(
        "sale_id", "TEXT", "Unique synthetic Dddd net sale/return line, not order/customer."
    ),
    *SALES_FIELDS[1:],
)


class DemoSaleRow(SaleRow):
    """Retain shared strict frozen field types, adding the demo's stricter rules."""

    sale_id: str = Field(pattern=r"^D[0-9]{3}$")

    @field_validator("customer", "region", "product")
    @classmethod
    def bounded_dimension(cls, value: str) -> str:
        if value != value.strip() or len(value.encode("utf-8")) > 64:
            raise ValueError("invalid dimension")
        if any(unicodedata.category(char) in {"Cc", "Cf"} for char in value):
            raise ValueError("invalid dimension")
        return value

    @model_validator(mode="after")
    def paired_measures(self) -> Self:
        if (self.units == 0) != (self.revenue_cents == 0):
            raise ValueError("unpaired zero")
        if (self.units < 0) != (self.revenue_cents < 0):
            raise ValueError("disagreeing signs")
        return self


@dataclass(frozen=True, slots=True)
class SalesDemo:
    source: SourceIdentity
    rows: tuple[DemoSaleRow, ...]
    schema_revision: str = DEMO_REVISION
    fields: tuple[FieldMeaning, ...] = DEMO_FIELDS


def _integer(value: str) -> int:
    if value == "-0" or re.fullmatch(r"-?(0|[1-9][0-9]*)", value) is None:
        raise ValueError("noncanonical integer")
    return int(value)


def _row(cells: list[str]) -> DemoSaleRow:
    if len(cells) != 7 or any(len(cell.encode("utf-8")) > MAX_CELL_BYTES for cell in cells):
        raise ValueError("invalid cells")
    if any("\n" in cell for cell in cells):
        raise ValueError("multiline cell")
    parsed_date = date.fromisoformat(cells[1])
    if parsed_date.isoformat() != cells[1]:
        raise ValueError("noncanonical date")
    return DemoSaleRow(
        sale_id=cells[0],
        sale_date=parsed_date,
        customer=cells[2],
        region=cells[3],
        product=cells[4],
        units=_integer(cells[5]),
        revenue_cents=_integer(cells[6]),
    )


def _reader(data: bytes) -> Iterator[list[str]]:
    if len(data) > MAX_BYTES or not data.endswith(b"\n") or b"\r" in data:
        raise ValueError("invalid file framing")
    lines = data[:-1].split(b"\n")
    if len(lines) > MAX_RECORDS + 1 or any(
        not line or len(line) > MAX_LINE_BYTES for line in lines
    ):
        raise ValueError("invalid physical lines")
    reader = csv.reader(io.StringIO(data.decode("utf-8"), newline=""), strict=True)
    if tuple(next(reader, [])) != SALES_COLUMNS:
        raise ValueError("invalid header")
    return reader


def _validated_rows(data: bytes) -> tuple[DemoSaleRow, ...]:
    """Bound and parse untrusted bytes; only the loader grants manifest identity."""
    try:
        reader = _reader(data)
        rows = tuple(_row(cells) for cells in reader)
        if len({row.sale_id for row in rows}) != len(rows):
            raise ValueError("duplicate IDs")
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise FixtureError("fixture_invalid") from exc
    return rows


def load_sales_demo(requested_source: SourceIdentity | None = None) -> SalesDemo:
    """Read only the server-owned demo path after full-identity authorization."""
    if requested_source is not None and requested_source != DEMO_SOURCE:
        raise FixtureError("source_mismatch")
    try:
        with DEMO_PATH.open("rb") as fixture:
            data = fixture.read(MAX_BYTES + 1)
    except OSError as exc:
        raise FixtureError("fixture_missing") from exc
    if len(data) != DEMO_BYTES or hashlib.sha256(data).hexdigest() != DEMO_SHA256:
        raise FixtureError("fixture_invalid")
    rows = _validated_rows(data)
    if len(rows) != DEMO_RECORDS:
        raise FixtureError("fixture_invalid")
    return SalesDemo(source=DEMO_SOURCE, rows=rows)

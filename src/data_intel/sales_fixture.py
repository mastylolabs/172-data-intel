"""Server-owned, immutable sales-proof source; this module grants no SQL capability."""

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from data_intel.contracts import SourceId, SourceIdentity

SALES_REVISION = "sales-proof.v1"
SALES_SHA256 = "36ea7edc3c94c5df1320946f1fcefb6bc5c6e7252cf2242344ee70f168d78396"
SALES_SOURCE = SourceIdentity(
    version="1",
    source_id=SourceId.SALES,
    snapshot_sha256=SALES_SHA256,
    meaning_revision=SALES_REVISION,
)
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sales-proof.csv"
FIXTURE_BYTES = 303
INT64_MIN, INT64_MAX = -(2**63), 2**63 - 1


class FixtureError(ValueError):
    """Safe failure without source content, file paths or raw parser diagnostics."""

    def __init__(
        self, code: Literal["fixture_missing", "fixture_invalid", "source_mismatch"]
    ) -> None:
        self.code = code
        super().__init__(code)


class SaleRow(BaseModel):
    """Validated CSV boundary values; signed measures include returns and valid zero."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    sale_id: str = Field(min_length=1)
    sale_date: date
    customer: str = Field(min_length=1)
    region: str = Field(min_length=1)
    product: str = Field(min_length=1)
    units: int = Field(ge=INT64_MIN, le=INT64_MAX)
    revenue_cents: int = Field(ge=INT64_MIN, le=INT64_MAX)


@dataclass(frozen=True, slots=True)
class FieldMeaning:
    name: str
    sql_type: Literal["TEXT", "INTEGER"]
    meaning: str
    nullable: Literal[False] = False


SALES_FIELDS = (
    FieldMeaning("sale_id", "TEXT", "Unique identifier of one net sale/return line."),
    FieldMeaning("sale_date", "TEXT", "Gregorian UTC calendar date; periods use [start, end)."),
    FieldMeaning("customer", "TEXT", "Customer name dimension on the sale/return line."),
    FieldMeaning("region", "TEXT", "Sales region dimension on the sale/return line."),
    FieldMeaning("product", "TEXT", "Product name dimension on the sale/return line."),
    FieldMeaning(
        "units", "INTEGER", "Signed net units; negative values are returns; zero is valid."
    ),
    FieldMeaning(
        "revenue_cents",
        "INTEGER",
        "Signed net USD cents; returns negative; zero valid; no tax/currency conversion.",
    ),
)
SALES_COLUMNS = tuple(field.name for field in SALES_FIELDS)


@dataclass(frozen=True, slots=True)
class SalesProfile:
    record_count: int
    date_min: date
    date_max: date
    statistics: Literal["exact"] = "exact"


@dataclass(frozen=True, slots=True)
class SalesFixture:
    source: SourceIdentity
    rows: tuple[SaleRow, ...]
    profile: SalesProfile
    fields: tuple[FieldMeaning, ...] = SALES_FIELDS
    schema_revision: str = SALES_REVISION


def _csv_integer(value: str) -> int:
    if re.fullmatch(r"-?(0|[1-9][0-9]*)", value) is None:
        raise ValueError("invalid integer")
    return int(value)


def _csv_row(cells: list[str]) -> SaleRow:
    if len(cells) != len(SALES_COLUMNS) or any(not cell.strip() for cell in cells):
        raise ValueError("invalid row shape")
    parsed_date = date.fromisoformat(cells[1])
    if parsed_date.isoformat() != cells[1]:
        raise ValueError("noncanonical date")
    return SaleRow(
        sale_id=cells[0],
        sale_date=parsed_date,
        customer=cells[2],
        region=cells[3],
        product=cells[4],
        units=_csv_integer(cells[5]),
        revenue_cents=_csv_integer(cells[6]),
    )


def _validated_rows(data: bytes) -> tuple[SaleRow, ...]:
    """Parse strict rows only; the loader separately owns byte and identity authorization."""
    try:
        reader = csv.reader(io.StringIO(data.decode("utf-8"), newline=""), strict=True)
        if tuple(next(reader, [])) != SALES_COLUMNS:
            raise ValueError("invalid header")
        rows = tuple(_csv_row(cells) for cells in reader)
        if len(rows) != 6 or len({row.sale_id for row in rows}) != 6:
            raise ValueError("invalid count or duplicate ID")
    except (UnicodeDecodeError, csv.Error, ValueError, ValidationError) as exc:
        raise FixtureError("fixture_invalid") from exc
    return rows


def load_sales_fixture(requested_source: SourceIdentity | None = None) -> SalesFixture:
    """Load only the pinned packaged source; optional request identity must match exactly."""
    if requested_source is not None and requested_source != SALES_SOURCE:
        raise FixtureError("source_mismatch")
    try:
        with FIXTURE_PATH.open("rb") as fixture:
            data = fixture.read(FIXTURE_BYTES + 1)
    except OSError as exc:
        raise FixtureError("fixture_missing") from exc
    if len(data) != FIXTURE_BYTES or hashlib.sha256(data).hexdigest() != SALES_SHA256:
        raise FixtureError("fixture_invalid")
    rows = _validated_rows(data)
    dates = tuple(row.sale_date for row in rows)
    return SalesFixture(
        source=SALES_SOURCE,
        rows=rows,
        profile=SalesProfile(record_count=len(rows), date_min=min(dates), date_max=max(dates)),
    )

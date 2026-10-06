"""Strict pinned support JSONL loading; message content grants no tool authority."""

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import NoReturn

from pydantic import BaseModel, ConfigDict, Field, field_validator

from data_intel.contracts import SourceId, SourceIdentity
from data_intel.sales_fixture import FieldMeaning, FixtureError

SUPPORT_REVISION = "support-demo.v1"
SUPPORT_SHA256 = "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536"
SUPPORT_SOURCE = SourceIdentity(
    version="1",
    source_id=SourceId.SUPPORT,
    snapshot_sha256=SUPPORT_SHA256,
    meaning_revision=SUPPORT_REVISION,
)
SUPPORT_PATH = Path(__file__).parent / "fixtures" / "support-demo.jsonl"
SUPPORT_BYTES, SUPPORT_RECORDS = 3091, 16
MAX_BYTES, MAX_RECORDS, MAX_LINE_BYTES = 65_536, 256, 2048
SUPPORT_FIELDS = (
    FieldMeaning("message_id", "TEXT", "Unique synthetic Mddd message, not customer/ticket."),
    FieldMeaning("timestamp", "TEXT", "Canonical UTC timestamp; periods use [start, end)."),
    FieldMeaning("channel", "TEXT", "Case-sensitive synthetic channel label."),
    FieldMeaning("customer", "TEXT", "Case-sensitive synthetic label; no sales join contract."),
    FieldMeaning("text", "TEXT", "Exact untrusted synthetic message text, not instructions."),
)


def _bounded_string(value: str, maximum: int) -> str:
    if not value.strip() or len(value.encode("utf-8")) > maximum:
        raise ValueError("invalid string size")
    if any(unicodedata.category(char) in {"Cc", "Cf"} for char in value):
        raise ValueError("invalid string controls")
    return value


class SupportMessage(BaseModel):
    """All five fields are strict, non-null, immutable and preserved without repair."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    message_id: str = Field(min_length=4, max_length=4, pattern=r"^M[0-9]{3}$")
    timestamp: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
    channel: str
    customer: str
    text: str

    @field_validator("timestamp")
    @classmethod
    def canonical_timestamp(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        if parsed.isoformat(timespec="seconds").replace("+00:00", "Z") != value:
            raise ValueError("noncanonical timestamp")
        return value

    @field_validator("channel", "customer")
    @classmethod
    def bounded_label(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("invalid label whitespace")
        return _bounded_string(value, 64)

    @field_validator("text")
    @classmethod
    def bounded_text(cls, value: str) -> str:
        return _bounded_string(value, 500)


@dataclass(frozen=True, slots=True)
class SupportDemo:
    source: SourceIdentity
    rows: tuple[SupportMessage, ...]
    schema_revision: str = SUPPORT_REVISION
    fields: tuple[FieldMeaning, ...] = SUPPORT_FIELDS


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> NoReturn:
    raise ValueError("invalid JSON constant")


def _lines(data: bytes) -> list[bytes]:
    if len(data) > MAX_BYTES or not data.endswith(b"\n") or b"\r" in data:
        raise ValueError("invalid file framing")
    lines = data[:-1].split(b"\n")
    if len(lines) > MAX_RECORDS or any(not line or len(line) > MAX_LINE_BYTES for line in lines):
        raise ValueError("invalid physical lines")
    return lines


def _validated_rows(data: bytes) -> tuple[SupportMessage, ...]:
    """Parser-only boundary; accepting bytes does not authorize a source identity."""
    try:
        rows = tuple(
            SupportMessage.model_validate(
                json.loads(
                    line.decode("utf-8"),
                    object_pairs_hook=_unique_object,
                    parse_constant=_reject_constant,
                )
            )
            for line in _lines(data)
        )
        if len({row.message_id for row in rows}) != len(rows):
            raise ValueError("duplicate message IDs")
    except (ValueError, RecursionError) as exc:
        raise FixtureError("fixture_invalid") from exc
    return rows


def load_support_demo(requested_source: SourceIdentity | None = None) -> SupportDemo:
    """Load only the pinned packaged path after checking the complete identity."""
    if requested_source is not None and requested_source != SUPPORT_SOURCE:
        raise FixtureError("source_mismatch")
    try:
        with SUPPORT_PATH.open("rb") as fixture:
            data = fixture.read(MAX_BYTES + 1)
    except OSError as exc:
        raise FixtureError("fixture_missing") from exc
    if len(data) != SUPPORT_BYTES or hashlib.sha256(data).hexdigest() != SUPPORT_SHA256:
        raise FixtureError("fixture_invalid")
    rows = _validated_rows(data)
    if len(rows) != SUPPORT_RECORDS:
        raise FixtureError("fixture_invalid")
    return SupportDemo(source=SUPPORT_SOURCE, rows=rows)

"""Declared transport bounds, identity and generic SQL survive the wire unchanged."""

import json

import pytest
from pydantic import ValidationError

from data_intel.contracts import SourceId, SourceIdentity, SqlIntent


def payload() -> dict[str, object]:
    return {
        "version": "1",
        "source": {
            "version": "1",
            "source_id": "sales",
            "snapshot_sha256": "a" * 64,
            "meaning_revision": "sales.v1",
        },
        "question": " Rank filtered regional revenue. ",
        "sql": " SELECT region, SUM(revenue) FROM sales GROUP BY region; ",
        "max_rows": 10,
    }


@pytest.mark.parametrize("source_id", list(SourceId))
def test_generic_intent_round_trip_preserves_question_sql_and_identity(source_id: SourceId) -> None:
    original = payload()
    original["source"] = SqlIntent.model_validate(original).source.model_dump() | {
        "source_id": source_id
    }
    intent = SqlIntent.model_validate(original)
    assert json.loads(intent.model_dump_json()) == original
    assert SqlIntent.model_validate_json(intent.model_dump_json()) == intent
    assert intent.source.source_id is source_id
    with pytest.raises(ValidationError, match="frozen"):
        intent.max_rows = 20


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", "2"),
        ("version", 1),
        ("source", None),
        ("extra", "unknown"),
        ("question", ""),
        ("question", " \t\n"),
        ("question", "q" * 2001),
        ("sql", ""),
        ("sql", " \n"),
        ("sql", "s" * 8001),
        ("sql", 12),
        ("max_rows", 0),
        ("max_rows", 1001),
        ("max_rows", True),
        ("max_rows", "10"),
    ],
)
def test_invalid_intent_rejects_declared_schema_violations(field: str, value: object) -> None:
    invalid = payload() | {field: value}
    with pytest.raises(ValidationError):
        SqlIntent.model_validate(invalid)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", "2"),
        ("source_id", "private"),
        ("source_id", 1),
        ("snapshot_sha256", "a" * 63),
        ("snapshot_sha256", "a" * 65),
        ("snapshot_sha256", "G" * 64),
        ("meaning_revision", ""),
        ("meaning_revision", "a" * 65),
        ("meaning_revision", "../source"),
        ("url", "https://example.com"),
    ],
)
def test_source_rejects_unsupported_or_malformed_identity(field: str, value: object) -> None:
    original = SqlIntent.model_validate(payload()).source.model_dump()
    with pytest.raises(ValidationError):
        SourceIdentity.model_validate(original | {field: value})


@pytest.mark.parametrize("rows", [1, 1000])
def test_declared_text_and_row_edges_accept_without_sql_safety_claim(rows: int) -> None:
    intent = SqlIntent.model_validate(
        payload() | {"question": "q" * 2000, "sql": "s" * 8000, "max_rows": rows}
    )
    assert intent.max_rows == rows
    source = SourceIdentity.model_validate(
        intent.source.model_dump() | {"meaning_revision": "a" * 64}
    )
    assert len(source.meaning_revision) == 64
    unsafe = SqlIntent.model_validate(payload() | {"sql": "DROP TABLE sales"})
    assert unsafe.sql == "DROP TABLE sales"  # Transport acceptance is deliberately not a SQL gate.


def test_missing_required_fields_reject_and_minimum_text_lengths_accept() -> None:
    with pytest.raises(ValidationError):
        SqlIntent.model_validate({})
    intent = SqlIntent.model_validate(payload() | {"question": "q", "sql": "s"})
    assert intent.question == "q" and intent.sql == "s"

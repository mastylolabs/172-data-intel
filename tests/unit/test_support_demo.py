"""Independent support manifest facts and strict malformed/boundary regressions."""

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from data_intel import support_demo
from data_intel.contracts import SourceIdentity
from data_intel.sales_fixture import FixtureError
from data_intel.support_demo import SupportMessage, load_support_demo


def _payload(message_id: str = "M001") -> dict[str, str]:
    return {
        "message_id": message_id,
        "timestamp": "2026-03-01T09:00:00Z",
        "channel": "support",
        "customer": "Acme",
        "text": "Exact source text.",
    }


def _line(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n"


def test_pinned_manifest_records_and_meanings() -> None:
    data = support_demo.SUPPORT_PATH.read_bytes()
    fixture = load_support_demo(support_demo.SUPPORT_SOURCE)
    assert len(data) == 3091 and hashlib.sha256(data).hexdigest() == (
        "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536"
    )
    assert data.endswith(b"\n") and b"\r" not in data and not data.startswith(b"\xef\xbb\xbf")
    assert fixture.source.source_id == "support"
    assert fixture.source.meaning_revision == fixture.schema_revision == "support-demo.v1"
    assert tuple(row.message_id for row in fixture.rows) == tuple(f"M{i:03}" for i in range(1, 17))
    assert tuple(field.name for field in fixture.fields) == tuple(_payload())
    assert all(field.sql_type == "TEXT" and not field.nullable for field in fixture.fields)
    assert [row.model_dump() for row in fixture.rows] == [
        json.loads(line) for line in data.splitlines()
    ]


def test_whole_fixture_oracles_match_independently_known_targets() -> None:
    fixture = load_support_demo()
    assert sum(row.channel == "billing" for row in fixture.rows) == 5
    assert sum(row.channel == "support" for row in fixture.rows) == 11
    assert {
        name: sum(row.customer == name for row in fixture.rows)
        for name in ("Acme", "Bright", "Cedar", "Delta")
    } == dict.fromkeys(("Acme", "Bright", "Cedar", "Delta"), 4)
    assert min(row.timestamp for row in fixture.rows) == "2026-03-01T09:00:00Z"
    assert max(row.timestamp for row in fixture.rows) == "2026-03-16T17:00:00Z"
    assert fixture.rows[0].text == (
        "Our February invoice has a duplicate Pro charge. Please check the billing line items."
    )


def test_rows_source_and_container_are_immutable() -> None:
    fixture = load_support_demo()
    with pytest.raises(ValidationError, match="frozen"):
        fixture.rows[0].text = "changed"
    with pytest.raises(ValidationError, match="frozen"):
        fixture.source.meaning_revision = "changed"
    with pytest.raises(FrozenInstanceError):
        fixture.rows = ()  # type: ignore[misc]  # Exercise frozen container rejection.


@pytest.mark.parametrize(
    "change",
    [
        {"source_id": "sales"},
        {"snapshot_sha256": "a" * 64},
        {"meaning_revision": "support-demo.v2"},
        {"version": "2"},
    ],
)
def test_complete_identity_refuses_before_file_access(change: dict[str, str]) -> None:
    identity = support_demo.SUPPORT_SOURCE.model_copy(update=change)
    with (
        patch.object(Path, "open", side_effect=AssertionError("must not read")),
        pytest.raises(FixtureError, match=r"^source_mismatch$"),
    ):
        load_support_demo(identity)


@pytest.mark.parametrize("size", [0, 3090, 3091, 3092, 65_536, 65_537, 65_538])
def test_unregistered_bytes_fail_without_diagnostics(size: int) -> None:
    opener = mock_open(read_data=b"x" * size)
    with patch.object(Path, "open", opener), pytest.raises(FixtureError) as error:
        load_support_demo()
    assert str(error.value) == error.value.code == "fixture_invalid"
    opener.return_value.read.assert_called_once_with(65_537)


def test_missing_file_and_manifest_count_fail_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    with (
        patch.object(Path, "open", side_effect=OSError("secret path")),
        pytest.raises(FixtureError, match=r"^fixture_missing$"),
    ):
        load_support_demo()
    monkeypatch.setattr(support_demo, "SUPPORT_RECORDS", 17)
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        load_support_demo()


@pytest.mark.parametrize(
    "field,value",
    [
        ("message_id", "M01"),
        ("message_id", "M001\n"),
        ("message_id", "M\uff11\uff12\uff13"),
        ("timestamp", "2026-02-30T09:00:00Z"),
        ("timestamp", "2026-03-01T24:00:00Z"),
        ("timestamp", "2026-03-01T09:00:60Z"),
        ("timestamp", "20260301T09:00:00Z"),
        ("timestamp", "2026-03-01T09:00:00+00:00"),
        ("timestamp", "2026-03-01T09:00:00.0Z"),
        ("channel", ""),
        ("channel", " support"),
        ("customer", "Acme "),
        ("customer", "a" * 65),
        ("channel", "é" * 33),
        ("customer", "A\u200b"),
        ("text", " "),
        ("text", "x" * 501),
        ("text", "é" * 251),
        ("text", "\n"),
        ("text", "\u0000"),
        ("text", "\u200b"),
        ("text", "\ud800"),
        ("text", 1),
        ("customer", True),
        ("timestamp", None),
        ("text", []),
        ("text", {}),
    ],
)
def test_model_rejects_invalid_cells_without_coercion(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        SupportMessage.model_validate(_payload() | {field: value})


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\n",
        b"{}\r\n",
        b"{}",
        b"\xef\xbb\xbf{}\n",
        b"\xff\n",
        b"[]\n",
        b"null\n",
        b"1\n",
        b'"text"\n',
        b"{\n",
        b'{"message_id":"M001","message_id":"M002"}\n',
        b'{"text":NaN}\n',
        b'{"text":Infinity}\n',
        b'{"text":-Infinity}\n',
        b'{"text":"\\ud800"}\n',
        b"[" * 1000 + b"0" + b"]" * 1000 + b"\n",
    ],
)
def test_invalid_json_encoding_framing_and_constants_are_safe(data: bytes) -> None:
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        support_demo._validated_rows(data)


def test_missing_extra_duplicate_fields_and_ids_refuse() -> None:
    payload = _payload()
    for data in (
        _line({key: value for key, value in payload.items() if key != "text"}),
        _line(payload | {"extra": "untrusted"}),
        _line(payload) + _line(payload),
        _line(payload).replace(b'"text":', b'"customer":"other","text":'),
        _line(payload).replace(b'"Exact source text."', b"NaN"),
    ):
        with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
            support_demo._validated_rows(data)


def test_utf8_cell_limits_preserve_exact_text_and_labels() -> None:
    payload = _payload() | {"channel": "é" * 32, "customer": "A" * 64, "text": "é" * 250}
    row = support_demo._validated_rows(_line(payload))[0]
    assert row.model_dump() == payload
    assert support_demo._validated_rows(_line(_payload() | {"text": " exact text "}))[0].text == (
        " exact text "
    )


def test_physical_line_record_and_file_ceiling_edges() -> None:
    line = _line(_payload()).rstrip(b"\n")
    assert len(support_demo._validated_rows(line.ljust(2048) + b"\n")) == 1
    rows = [_line(_payload(f"M{i:03}"))[:-1].ljust(255) + b"\n" for i in range(256)]
    data = b"".join(rows)
    assert len(data) == 65_536 and len(support_demo._validated_rows(data)) == 256
    for invalid in (
        line.ljust(2049) + b"\n",
        b" " + data,
        b"".join(_line(_payload(f"M{i:03}")) for i in range(257)),
        b"\n" + _line(_payload()),
    ):
        with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
            support_demo._validated_rows(invalid)


def test_unknown_identity_is_valid_transport_but_not_authorized() -> None:
    identity = SourceIdentity.model_validate(
        support_demo.SUPPORT_SOURCE.model_dump() | {"meaning_revision": "support-demo.v2"}
    )
    with pytest.raises(FixtureError, match=r"^source_mismatch$"):
        load_support_demo(identity)

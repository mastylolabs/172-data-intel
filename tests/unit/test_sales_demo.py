"""Independent fixture targets, strict parser bounds and preserved proof identity."""

import hashlib
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from data_intel import sales_demo
from data_intel.contracts import SourceIdentity
from data_intel.sales_demo import load_sales_demo
from data_intel.sales_fixture import SALES_COLUMNS, SALES_SOURCE, FixtureError, load_sales_fixture


def test_exact_demo_manifest_and_identity() -> None:
    data = sales_demo.DEMO_PATH.read_bytes()
    fixture = load_sales_demo(sales_demo.DEMO_SOURCE)
    assert len(data) == 1025
    assert hashlib.sha256(data).hexdigest() == (
        "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f"
    )
    assert fixture.source.meaning_revision == fixture.schema_revision == "sales-demo.v1"
    assert data.endswith(b"\n") and b"\r" not in data


def test_record_order_and_meanings_are_preserved() -> None:
    fixture = load_sales_demo()
    assert tuple(row.sale_id for row in fixture.rows) == tuple(f"D{i:03}" for i in range(1, 25))
    assert tuple(field.name for field in fixture.fields) == SALES_COLUMNS


def test_independently_known_totals_and_date_range() -> None:
    fixture = load_sales_demo()
    assert sum(row.units for row in fixture.rows) == 29
    assert sum(row.revenue_cents for row in fixture.rows) == 395000
    assert min(row.sale_date for row in fixture.rows) == date(2026, 1, 1)
    assert max(row.sale_date for row in fixture.rows) == date(2026, 3, 31)


@pytest.mark.parametrize("month,units,cents", [(1, 7, 105000), (2, 12, 140000), (3, 10, 150000)])
def test_known_month_oracles_preserve_returns_zero_and_period_edges(
    month: int, units: int, cents: int
) -> None:
    rows = [row for row in load_sales_demo().rows if row.sale_date.month == month]
    assert len(rows) == 8
    assert sum(row.units for row in rows) == units
    assert sum(row.revenue_cents for row in rows) == cents


def test_rows_container_and_source_are_immutable_and_proof_remains_distinct() -> None:
    fixture = load_sales_demo()
    with pytest.raises(ValidationError, match="frozen"):
        fixture.rows[0].units = 999
    with pytest.raises(FrozenInstanceError):
        fixture.rows = ()  # type: ignore[misc]  # Exercise immutable container rejection.
    with pytest.raises(ValidationError, match="frozen"):
        fixture.source.meaning_revision = "changed"
    proof = load_sales_fixture()
    assert len(proof.rows) == 6 and proof.source == SALES_SOURCE
    assert proof.source != fixture.source and proof.schema_revision == "sales-proof.v1"


@pytest.mark.parametrize(
    "field,value",
    [
        ("snapshot_sha256", "a" * 64),
        ("meaning_revision", "sales-proof.v1"),
        ("source_id", "support"),
    ],
)
def test_identity_mismatch_refuses_before_file_access(
    field: str, value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sales_demo, "DEMO_PATH", Path("/unavailable"))
    identity = SourceIdentity.model_validate(sales_demo.DEMO_SOURCE.model_dump() | {field: value})
    with pytest.raises(FixtureError, match=r"^source_mismatch$"):
        load_sales_demo(identity)


@pytest.mark.parametrize("size", [0, 1024, 1025, 1026, 65_536, 65_537, 65_538])
def test_changed_and_oversized_bytes_never_authorize(
    size: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "fixture.csv"
    path.write_bytes(b"x" * size)
    monkeypatch.setattr(sales_demo, "DEMO_PATH", path)
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        load_sales_demo()


def test_missing_file_error_contains_no_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sales_demo, "DEMO_PATH", tmp_path / "missing")
    with pytest.raises(FixtureError, match=r"^fixture_missing$") as error:
        load_sales_demo()
    assert str(tmp_path) not in str(error.value)


@pytest.mark.parametrize(
    "old,new",
    [
        (b"sale_id", b"id"),
        (b"D024", b"D001"),
        (b"D001", b"S001"),
        (b"2026-01-01", b"2026-02-30"),
        (b"2026-01-01", b"20260101"),
        (b",Acme,", b",,"),
        (b",Acme,", b", Acme,"),
        (b",Acme,", b",Acme\x00,"),
        (b",Acme,", b",Acme\xe2\x80\x8b,"),
        (b",2,20000", b",2.0,20000"),
        (b",2,20000", b",+2,20000"),
        (b",2,20000", b",02,20000"),
        (b",2,20000", b",2e0,20000"),
        (b",2,20000", b", 2,20000"),
        (b",0,0", b",-0,0"),
        (b",2,20000", b",-2,20000"),
        (b",0,0", b",0,1"),
        (b",2,20000", b",2,9223372036854775808"),
        (b",2,20000", b",2,"),
        (b",2,20000", b",2"),
        (b",2,20000", b",2,20000,extra"),
        (b"Acme", b'"Acme\nNorth"'),
        (b"Acme", b'"unterminated'),
        (b"Acme", b"\xff"),
    ],
)
def test_malformed_csv_cannot_be_repaired_or_coerced(old: bytes, new: bytes) -> None:
    # Parser-only tests do not authorize modified bytes as the registered fixture.
    data = sales_demo.DEMO_PATH.read_bytes().replace(old, new, 1)
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        sales_demo._validated_rows(data)


@pytest.mark.parametrize("replacement", [b"\xef\xbb\xbf", b"\n", b"\r", b"x" * 2049])
def test_invalid_file_framing_and_physical_lines_reject(replacement: bytes) -> None:
    data = replacement + sales_demo.DEMO_PATH.read_bytes()
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        sales_demo._validated_rows(data)


@pytest.mark.parametrize("value", [-(2**63), 2**63 - 1])
def test_integer_edges_are_preserved_exactly(value: int) -> None:
    data = sales_demo.DEMO_PATH.read_bytes().replace(b",2,20000", f",{value},{value}".encode(), 1)
    row = sales_demo._validated_rows(data)[0]
    assert row.units == row.revenue_cents == value


def test_dimension_record_and_cell_bounds() -> None:
    data = sales_demo.DEMO_PATH.read_bytes()
    assert sales_demo._validated_rows(data.replace(b"Acme", b"a" * 64, 1))[0].customer == "a" * 64
    for length in (65, 256, 257):
        with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
            sales_demo._validated_rows(data.replace(b"Acme", b"a" * length, 1))
    header = data.splitlines()[0]
    rows = [f"D{i:03},2026-01-01,A,B,C,1,1".encode() for i in range(256)]
    assert len(sales_demo._validated_rows(b"\n".join([header, *rows]) + b"\n")) == 256
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        sales_demo._validated_rows(b"\n".join([header, *rows, rows[0]]) + b"\n")


@pytest.mark.parametrize("value", [True, "2", 2.0, None, -(2**63) - 1, 2**63])
def test_demo_model_retains_strict_integer_validation(value: object) -> None:
    payload = load_sales_demo().rows[0].model_dump() | {"units": value}
    with pytest.raises(ValidationError):
        sales_demo.DemoSaleRow.model_validate(payload)


def test_missing_final_lf_and_utf8_byte_dimension_edge() -> None:
    data = sales_demo.DEMO_PATH.read_bytes()
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        sales_demo._validated_rows(data[:-1])
    label = "é" * 32
    row = sales_demo._validated_rows(data.replace(b"Acme", label.encode(), 1))[0]
    assert row.customer == label
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        sales_demo._validated_rows(data.replace(b"Acme", (label + "a").encode(), 1))


def test_loader_reads_only_one_byte_beyond_the_file_ceiling() -> None:
    opener = mock_open(read_data=b"x" * 65_538)
    with (
        patch.object(Path, "open", opener),
        pytest.raises(FixtureError, match=r"^fixture_invalid$"),
    ):
        load_sales_demo()
    opener.return_value.read.assert_called_once_with(65_537)


def test_registered_record_count_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sales_demo, "DEMO_RECORDS", 25)
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        load_sales_demo()

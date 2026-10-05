"""Approved bytes, boundary refusals, explicit semantics and independent fixture oracles."""

import hashlib
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from data_intel import sales_fixture
from data_intel.contracts import SourceIdentity
from data_intel.sales_fixture import FixtureError, load_sales_fixture


def test_packaged_fixture_bytes_and_registered_identity_are_exact() -> None:
    data = sales_fixture.FIXTURE_PATH.read_bytes()
    fixture = load_sales_fixture(sales_fixture.SALES_SOURCE)
    assert len(data) == 303 and data.endswith(b"\n") and b"\r" not in data
    assert hashlib.sha256(data).hexdigest() == (
        "36ea7edc3c94c5df1320946f1fcefb6bc5c6e7252cf2242344ee70f168d78396"
    )
    assert fixture.source.snapshot_sha256 == hashlib.sha256(data).hexdigest()
    assert fixture.schema_revision == fixture.source.meaning_revision == "sales-proof.v1"


def test_profile_is_computed_from_the_actual_validated_rows() -> None:
    fixture = load_sales_fixture()
    assert fixture.profile.record_count == len(fixture.rows) == 6
    assert fixture.profile.date_min == date(2026, 1, 2)
    assert fixture.profile.date_max == date(2026, 2, 28)
    assert fixture.profile.statistics == "exact"


def test_return_zero_and_record_order_are_preserved() -> None:
    fixture = load_sales_fixture()
    assert tuple(row.sale_id for row in fixture.rows) == tuple(f"S00{i}" for i in range(1, 7))
    assert (fixture.rows[2].units, fixture.rows[2].revenue_cents) == (-1, -5000)
    assert (fixture.rows[5].units, fixture.rows[5].revenue_cents) == (0, 0)


def test_rows_and_profile_cannot_be_mutated() -> None:
    fixture = load_sales_fixture()
    with pytest.raises(ValidationError, match="frozen"):
        fixture.rows[0].units = 999
    with pytest.raises(FrozenInstanceError):
        fixture.profile.record_count = 99  # type: ignore[misc]  # Exercise frozen dataclass rejection.


def test_declared_schema_and_meanings_are_explicit_and_non_nullable() -> None:
    fixture = load_sales_fixture()
    assert tuple(field.name for field in fixture.fields) == sales_fixture.SALES_COLUMNS
    assert all(field.nullable is False and field.meaning for field in fixture.fields)
    assert [field.sql_type for field in fixture.fields] == ["TEXT"] * 5 + ["INTEGER"] * 2
    assert "[start, end)" in fixture.fields[1].meaning
    assert "USD cents" in fixture.fields[6].meaning


def test_total_measures_match_independently_known_fixture_results() -> None:
    fixture = load_sales_fixture()
    assert sum(row.revenue_cents for row in fixture.rows) == 130000
    assert sum(row.units for row in fixture.rows) == 10


def test_period_measures_and_difference_match_independently_known_results() -> None:
    fixture = load_sales_fixture()
    january = [row for row in fixture.rows if row.sale_date.month == 1]
    february = [row for row in fixture.rows if row.sale_date.month == 2]
    assert (sum(row.revenue_cents for row in january), sum(row.units for row in january)) == (
        60000,
        4,
    )
    assert (sum(row.revenue_cents for row in february), sum(row.units for row in february)) == (
        70000,
        6,
    )
    assert (
        sum(row.revenue_cents for row in february) - sum(row.revenue_cents for row in january)
        == 10000
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [("snapshot_sha256", "a" * 64), ("meaning_revision", "sales.v2"), ("source_id", "support")],
)
def test_unapproved_requested_identity_refuses_before_fixture_read(
    field: str, value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sales_fixture, "FIXTURE_PATH", Path("/unavailable"))
    source = SourceIdentity.model_validate(sales_fixture.SALES_SOURCE.model_dump() | {field: value})
    with pytest.raises(FixtureError, match=r"^source_mismatch$"):
        load_sales_fixture(source)


@pytest.mark.parametrize("data", [b"", b"x" * 303, b"x" * 304])
def test_changed_or_oversized_fixture_bytes_fail_closed(
    data: bytes, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "sales.csv"
    path.write_bytes(data)
    monkeypatch.setattr(sales_fixture, "FIXTURE_PATH", path)
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        load_sales_fixture()


def test_missing_fixture_reports_safe_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sales_fixture, "FIXTURE_PATH", tmp_path / "not-present")
    with pytest.raises(FixtureError, match=r"^fixture_missing$") as error:
        load_sales_fixture()
    assert error.value.code == "fixture_missing" and str(tmp_path) not in str(error.value)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"sale_id", b"id"),
        (b"S006", b"S001"),
        (b"2026-01-02", b"2026-02-30"),
        (b"2026-01-02", b"20260102"),
        (b",Acme,", b",,"),
        (b",2,20000", b",2.0,20000"),
        (b",2,20000", b",2,"),
        (b",2,20000", b",2,9223372036854775808"),
        (b",2,20000", b",2,20000,extra"),
        (b",2,20000", b",2"),
        (b"S001", b"\xff"),
        (b"Cedar", b'"unterminated'),
        (b"S006,2026-02-28,Cedar,East,Core,0,0\n", b""),
    ],
)
def test_csv_boundary_rejects_bad_schema_types_dates_ids_and_records(
    old: bytes, new: bytes
) -> None:
    # Exercise parser invariants separately; this never grants mutated bytes source authorization.
    data = sales_fixture.FIXTURE_PATH.read_bytes().replace(old, new, 1)
    with pytest.raises(FixtureError, match=r"^fixture_invalid$"):
        sales_fixture._validated_rows(data)


@pytest.mark.parametrize("value", [True, "2", 2.0, None, -(2**63) - 1, 2**63])
def test_row_model_rejects_coerced_or_out_of_range_integer_measures(value: object) -> None:
    row = load_sales_fixture().rows[0].model_dump()
    with pytest.raises(ValidationError):
        sales_fixture.SaleRow.model_validate(row | {"units": value})


@pytest.mark.parametrize("value", [-(2**63), 2**63 - 1])
def test_csv_integer_boundary_preserves_signed_64_bit_edges(value: int) -> None:
    data = sales_fixture.FIXTURE_PATH.read_bytes().replace(
        b",2,20000", f",{value},{value}".encode(), 1
    )
    row = sales_fixture._validated_rows(data)[0]
    assert row.units == row.revenue_cents == value

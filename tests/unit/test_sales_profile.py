"""Independent profile oracles; mutated typed test rows never authorize new bytes."""

import json
from dataclasses import replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pytest

from data_intel.profile_models import DataProfileV2, ProfileContentError, canonical_profile_json
from data_intel.sales_demo import DEMO_FIELDS, DEMO_SOURCE, DemoSaleRow, SalesDemo, load_sales_demo
from data_intel.sales_fixture import SALES_SOURCE, FixtureError, load_sales_fixture
from data_intel.sales_profile import (
    ProfileFailure,
    _profile,
    profile_payload_sha256,
    profile_sales_demo,
)


def _rows(values: tuple[int, ...], customers: tuple[str, ...] = ()) -> SalesDemo:
    return SalesDemo(
        source=DEMO_SOURCE,
        rows=tuple(
            DemoSaleRow(
                sale_id=f"D{index:03}",
                sale_date=date(2026, 1, 1),
                customer=customers[index - 1] if customers else "A",
                region="North",
                product="Core",
                units=value,
                revenue_cents=value,
            )
            for index, value in enumerate(values, start=1)
        ),
    )


def test_approved_profile_matches_independently_stated_fixture_facts() -> None:
    profile = profile_sales_demo(DEMO_SOURCE)
    assert (profile.version, profile.profile_revision, profile.schema_revision) == (
        "2",
        "m3-profile.v1",
        "sales-demo.v1",
    )
    assert profile.source == DEMO_SOURCE
    assert (profile.record_count, profile.range_start, profile.range_end) == (
        24,
        date(2026, 1, 1),
        date(2026, 3, 31),
    )
    assert [
        (field.name, field.sql_type, field.nullable, field.null_count) for field in profile.fields
    ] == [
        ("sale_id", "TEXT", False, 0),
        ("sale_date", "TEXT", False, 0),
        ("customer", "TEXT", False, 0),
        ("region", "TEXT", False, 0),
        ("product", "TEXT", False, 0),
        ("units", "INTEGER", False, 0),
        ("revenue_cents", "INTEGER", False, 0),
    ]
    assert tuple(field.meaning for field in profile.fields) == tuple(
        field.meaning for field in DEMO_FIELDS
    )
    assert load_sales_fixture().profile.record_count == 6


def test_dimension_and_measure_facts_match_independent_whole_fixture_oracles() -> None:
    profile = profile_sales_demo()
    assert [
        (item.field, item.distinct_count, item.values, item.omitted_value_count)
        for item in profile.dimensions
    ] == [
        ("customer", 6, ("Acme", "Bright", "Cedar", "Delta", "Elm", "Fjord"), 0),
        ("region", 4, ("East", "North", "South", "West"), 0),
        ("product", 2, ("Core", "Plus"), 0),
    ]
    assert [
        (item.field, item.unit, item.count, item.min, item.max, item.sum, item.exact)
        for item in profile.measures
    ] == [
        ("units", "net_units", 24, "-1", "4", "29", True),
        ("revenue_cents", "USD_cents", 24, "-15000", "45000", "395000", True),
    ]
    assert profile.omissions == (
        "bulk_rows",
        "row_samples",
        "distributions",
        "uncomputed_statistics",
    )
    assert profile.capabilities == ("query",) and profile.analytical_validated is False
    assert "USD cents" in profile.fields[6].meaning


def test_repeated_profiles_are_canonical_bounded_and_contain_only_receipt_fields() -> None:
    first, second = profile_sales_demo(), profile_sales_demo()
    encoded = canonical_profile_json(first)
    assert encoded == canonical_profile_json(second)
    assert len(encoded) <= 4096
    assert encoded == json.dumps(
        first.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    assert set(json.loads(encoded)) == {
        "version",
        "source",
        "schema_revision",
        "profile_revision",
        "fields",
        "record_count",
        "range_start",
        "range_end",
        "dimensions",
        "measures",
        "omissions",
        "capabilities",
        "analytical_validated",
    }
    assert DataProfileV2.model_validate_json(encoded) == first
    assert profile_payload_sha256(first) == sha256(encoded).hexdigest()
    assert profile_payload_sha256(second) == profile_payload_sha256(first)


def test_empty_validated_test_data_has_no_ranges_or_extrema() -> None:
    profile = _profile(_rows(()))
    assert profile.record_count == 0 and profile.range_start is profile.range_end is None
    assert all(
        (item.count, item.min, item.max, item.sum) == (0, None, None, "0")
        for item in profile.measures
    )
    assert all(
        (item.distinct_count, item.values, item.omitted_value_count) == (0, (), 0)
        for item in profile.dimensions
    )


def test_dimensions_are_whole_source_sorted_unique_and_explicitly_omitted() -> None:
    profile = _profile(_rows((1,) * 11, ("é", "a", "H", "G", "F", "E", "D", "C", "B", "A", "A")))
    dimension = profile.dimensions[0]
    assert (profile.record_count, dimension.distinct_count, dimension.omitted_value_count) == (
        11,
        10,
        2,
    )
    assert dimension.values == ("A", "B", "C", "D", "E", "F", "G", "H")
    encoded = canonical_profile_json(_profile(_rows((1,), ("é",))))
    assert b"\xc3\xa9" in encoded and b"\\u00e9" not in encoded


@pytest.mark.parametrize("value", [-(2**63), 0, 9007199254740993, 2**63 - 1])
def test_exact_integer_and_cents_statistics_never_use_float(value: int) -> None:
    for measure in _profile(_rows((value,))).measures:
        assert (measure.min, measure.max, measure.sum) == (str(value),) * 3


@pytest.mark.parametrize("values", [(2**63 - 1, 1), (-(2**63), -1)])
def test_statistic_overflow_refuses_the_whole_receipt(values: tuple[int, ...]) -> None:
    with pytest.raises(ProfileFailure, match=r"^invalid_result$"):
        _profile(_rows(values))


@pytest.mark.parametrize("checked_rows", [0, 12, 24])
def test_deadline_checked_during_scan_and_before_success(checked_rows: int) -> None:
    with (
        patch("data_intel.sales_profile.monotonic", side_effect=[0.0] * (checked_rows + 1) + [0.1]),
        pytest.raises(ProfileFailure, match=r"^execution_limit$"),
    ):
        profile_sales_demo()


def test_record_ceiling_accepts_256_and_refuses_257() -> None:
    assert _profile(_rows((0,) * 256)).record_count == 256
    with pytest.raises(ProfileFailure, match=r"^execution_limit$"):
        _profile(_rows((0,) * 257))


@pytest.mark.parametrize("code", ["result_limit", "invalid_result"])
def test_serialization_failure_refuses_profile_and_hash(code: str) -> None:
    failure = ProfileContentError("result_limit" if code == "result_limit" else "invalid_result")
    with (
        patch("data_intel.sales_profile.canonical_profile_json", side_effect=failure),
        pytest.raises(ProfileFailure, match=f"^{code}$"),
    ):
        profile_sales_demo()


def test_invalid_identity_fails_before_loading_and_internal_metadata_cannot_drift() -> None:
    wrong = DEMO_SOURCE.model_copy(update={"meaning_revision": "sales-demo.v2"})
    with patch.object(Path, "open", side_effect=AssertionError("must not read")):
        for source in (
            wrong,
            SALES_SOURCE,
            DEMO_SOURCE.model_copy(update={"snapshot_sha256": "f" * 64}),
        ):
            with pytest.raises(FixtureError, match=r"^source_mismatch$"):
                profile_sales_demo(source)
    with pytest.raises(ProfileFailure, match=r"^source_mismatch$"):
        _profile(replace(load_sales_demo(), schema_revision="changed"))


@pytest.mark.parametrize("code", ["fixture_missing", "fixture_invalid"])
def test_loader_failure_remains_safe_and_never_yields_profile(code: str) -> None:
    failure = FixtureError("fixture_missing" if code == "fixture_missing" else "fixture_invalid")
    with (
        patch("data_intel.sales_profile.load_sales_demo", side_effect=failure),
        pytest.raises(FixtureError, match=f"^{code}$"),
    ):
        profile_sales_demo()


def test_memory_failure_is_safe_without_retry() -> None:
    with patch(
        "data_intel.sales_profile.load_sales_demo", side_effect=MemoryError("private detail")
    ) as loader:
        with pytest.raises(ProfileFailure, match=r"^execution_limit$"):
            profile_sales_demo()
        assert loader.call_count == 1

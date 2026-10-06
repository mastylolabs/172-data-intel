"""Receipt-contract mutations; a typed receipt never authenticates source bytes."""

import json
from datetime import date

import pytest
from pydantic import ValidationError

from data_intel.profile_models import (
    DataProfileV2,
    ProfileContentError,
    ProfileDimension,
    ProfileField,
    ProfileMeasure,
    canonical_profile_json,
)
from data_intel.sales_demo import DEMO_SOURCE


def _receipt() -> DataProfileV2:
    """Small declared test receipt, not a computed profile or approved data proof."""
    return DataProfileV2(
        source=DEMO_SOURCE,
        schema_revision="sales-demo.v1",
        fields=(
            ProfileField(name="customer", sql_type="TEXT", meaning="Synthetic label", null_count=0),
        ),
        record_count=1,
        range_start=date(2026, 1, 1),
        range_end=date(2026, 1, 1),
        dimensions=(
            ProfileDimension(
                field="customer", distinct_count=1, values=("é",), omitted_value_count=0
            ),
        ),
        measures=(
            ProfileMeasure(field="units", unit="net_units", count=1, min="1", max="1", sum="1"),
        ),
    )


def test_wire_fields_policy_revisions_and_exactness() -> None:
    profile = _receipt()
    encoded = canonical_profile_json(profile)
    payload = json.loads(encoded)
    assert set(payload) == {
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
    assert (payload["version"], payload["profile_revision"], payload["range_start"]) == (
        "2",
        "m3-profile.v1",
        "2026-01-01",
    )
    assert payload["source"] == DEMO_SOURCE.model_dump(mode="json")
    assert payload["omissions"] == [
        "bulk_rows",
        "row_samples",
        "distributions",
        "uncomputed_statistics",
    ]
    assert payload["capabilities"] == [] and payload["analytical_validated"] is False
    assert payload["fields"][0]["nullable"] is False
    assert payload["measures"][0]["exact"] is True


def test_canonical_utf8_roundtrip_and_nested_immutability() -> None:
    profile = _receipt()
    encoded = canonical_profile_json(profile)
    payload = json.loads(encoded)
    assert encoded == canonical_profile_json(_receipt())
    assert b"\xc3\xa9" in encoded and b"\\u00e9" not in encoded
    assert encoded == json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    assert DataProfileV2.model_validate_json(encoded) == profile
    with pytest.raises(ValidationError):
        profile.record_count = 0
    with pytest.raises(ValidationError):
        profile.fields[0].meaning = "changed"


@pytest.mark.parametrize(
    "change",
    [
        {"record_count": True},
        {"record_count": "1"},
        {"record_count": 1.0},
        {"record_count": -1},
        {"record_count": 257},
        {"version": "1"},
        {"profile_revision": "other.v1"},
        {"analytical_validated": True},
        {"analytical_validated": 0},
        {"rows": []},
        {"source": {}},
        {"schema_revision": "../path"},
        {"range_start": "2026-02-30"},
        {"omissions": []},
        {"capabilities": ["upload"]},
    ],
)
def test_strict_receipt_rejects_coercions_extra_fields_and_invalid_policy(
    change: dict[str, object],
) -> None:
    payload = _receipt().model_dump(mode="json")
    payload.update(change)
    with pytest.raises(ValidationError):
        DataProfileV2.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize(
    "value",
    [
        "-0",
        "+1",
        "01",
        "1.0",
        "1e3",
        " 1",
        "",
        "9223372036854775808",
        "-9223372036854775809",
        1,
        1.0,
        True,
    ],
)
def test_statistics_require_canonical_signed_int64_strings(value: object) -> None:
    payload = _receipt().measures[0].model_dump(mode="json")
    payload["sum"] = value
    with pytest.raises(ValidationError):
        ProfileMeasure.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize(
    "value", ["-9223372036854775808", "0", "9007199254740993", "9223372036854775807"]
)
def test_exact_integer_extrema_and_large_cents_are_strings(value: str) -> None:
    measure = ProfileMeasure(
        field="revenue_cents", unit="USD_cents", count=1, min=value, max=value, sum=value
    )
    assert (measure.min, measure.max, measure.sum, measure.unit) == (
        value,
        value,
        value,
        "USD_cents",
    )


@pytest.mark.parametrize(
    "component,change",
    [
        ("fields", {"nullable": True}),
        ("fields", {"nullable": 0}),
        ("fields", {"null_count": 257}),
        ("fields", {"sql_type": "REAL"}),
        ("dimensions", {"values": ["A"] * 9}),
        ("dimensions", {"omitted_value_count": -1}),
        ("measures", {"exact": False}),
        ("measures", {"exact": 1}),
        ("measures", {"unit": "USD"}),
        ("measures", {"average": "1"}),
    ],
)
def test_nested_contracts_are_strict_and_bounded(component: str, change: dict[str, object]) -> None:
    payload = _receipt().model_dump(mode="json")
    payload[component][0].update(change)
    with pytest.raises(ValidationError):
        DataProfileV2.model_validate_json(json.dumps(payload))


def test_empty_receipt_and_dimension_limit_are_representable() -> None:
    empty = _receipt().model_copy(
        update={
            "record_count": 0,
            "range_start": None,
            "range_end": None,
            "dimensions": (),
            "measures": (),
        }
    )
    assert DataProfileV2.model_validate_json(canonical_profile_json(empty)) == empty
    dimension = ProfileDimension(
        field="customer", distinct_count=256, values=tuple("ABCDEFGH"), omitted_value_count=248
    )
    assert (dimension.distinct_count, len(dimension.values), dimension.omitted_value_count) == (
        256,
        8,
        248,
    )
    measure = ProfileMeasure(field="units", unit="net_units", count=0, min=None, max=None, sum="0")
    assert measure.min is measure.max is None and measure.sum == "0"


def test_serializer_refuses_exact_byte_overflow_and_invalid_unicode() -> None:
    original = _receipt()
    first = original.fields[0]
    padding = 4096 - len(canonical_profile_json(original))
    sized = original.model_copy(
        update={"fields": (first.model_copy(update={"meaning": first.meaning + "x" * padding}),)}
    )
    assert len(canonical_profile_json(sized)) == 4096
    for meaning, code in (
        (first.meaning + "x" * (padding + 1), "result_limit"),
        ("\ud800", "invalid_result"),
    ):
        invalid = original.model_copy(
            update={"fields": (first.model_copy(update={"meaning": meaning}),)}
        )
        with pytest.raises(ProfileContentError, match=f"^{code}$") as error:
            canonical_profile_json(invalid)
        assert error.value.code == code

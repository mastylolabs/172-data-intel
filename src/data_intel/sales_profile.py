"""Whole-source exact sales profiling with independent byte and deadline ceilings."""

from hashlib import sha256
from time import monotonic
from typing import Literal

from data_intel.contracts import SourceIdentity
from data_intel.profile_models import (
    DataProfileV2,
    ProfileContentError,
    ProfileDimension,
    ProfileField,
    ProfileMeasure,
    canonical_profile_json,
)
from data_intel.sales_demo import (
    DEMO_FIELDS,
    DEMO_REVISION,
    DEMO_SOURCE,
    SalesDemo,
    load_sales_demo,
)
from data_intel.sales_fixture import INT64_MAX, INT64_MIN

PROFILE_SECONDS = 0.1


class ProfileFailure(RuntimeError):
    """Safe classifications without source values, paths or parser detail."""

    def __init__(
        self, code: Literal["source_mismatch", "invalid_result", "execution_limit", "result_limit"]
    ) -> None:
        self.code = code
        super().__init__(code)


def _check_deadline(deadline: float) -> None:
    if monotonic() >= deadline:
        raise ProfileFailure("execution_limit")


def _measure(
    field: str, unit: Literal["net_units", "USD_cents"], values: list[int]
) -> ProfileMeasure:
    minimum, maximum, total = min(values, default=None), max(values, default=None), sum(values)
    if any(
        value is not None and not INT64_MIN <= value <= INT64_MAX
        for value in (minimum, maximum, total)
    ):
        raise ProfileFailure("invalid_result")
    return ProfileMeasure(
        field=field,
        unit=unit,
        count=len(values),
        min=None if minimum is None else str(minimum),
        max=None if maximum is None else str(maximum),
        sum=str(total),
    )


def profile_payload_sha256(profile: DataProfileV2) -> str:
    """Hash bounded canonical content; a digest does not certify its factual meaning."""
    try:
        return sha256(canonical_profile_json(profile)).hexdigest()
    except ProfileContentError as error:
        raise ProfileFailure(error.code) from None


def _dimension(field: str, values: set[str]) -> ProfileDimension:
    return ProfileDimension(
        field=field,
        distinct_count=len(values),
        values=tuple(sorted(values)[:8]),
        omitted_value_count=max(0, len(values) - 8),
    )


def _profile(fixture: SalesDemo, deadline: float | None = None) -> DataProfileV2:
    """Internal validated-row calculation; only the loader authorizes actual bytes."""
    if (fixture.source, fixture.schema_revision, fixture.fields) != (
        DEMO_SOURCE,
        DEMO_REVISION,
        DEMO_FIELDS,
    ):
        raise ProfileFailure("source_mismatch")
    if len(fixture.rows) > 256:
        raise ProfileFailure("execution_limit")
    if deadline is None:
        deadline = monotonic() + PROFILE_SECONDS
    dimensions: dict[str, set[str]] = {name: set() for name in ("customer", "region", "product")}
    units: list[int] = []
    cents: list[int] = []
    dates = []
    for row in fixture.rows:
        _check_deadline(deadline)
        dimensions["customer"].add(row.customer)
        dimensions["region"].add(row.region)
        dimensions["product"].add(row.product)
        units.append(row.units)
        cents.append(row.revenue_cents)
        dates.append(row.sale_date)
    profile = DataProfileV2(
        source=fixture.source,
        schema_revision=fixture.schema_revision,
        fields=tuple(
            ProfileField(
                name=field.name, sql_type=field.sql_type, meaning=field.meaning, null_count=0
            )
            for field in fixture.fields
        ),
        record_count=len(fixture.rows),
        range_start=min(dates, default=None),
        range_end=max(dates, default=None),
        dimensions=tuple(_dimension(name, values) for name, values in dimensions.items()),
        measures=(
            _measure("units", "net_units", units),
            _measure("revenue_cents", "USD_cents", cents),
        ),
    )
    profile_payload_sha256(profile)
    _check_deadline(deadline)
    return profile


def profile_sales_demo(requested_source: SourceIdentity | None = None) -> DataProfileV2:
    """Profile only the approved loaded demo; no retries or source selection by path."""
    try:
        deadline = monotonic() + PROFILE_SECONDS
        return _profile(load_sales_demo(requested_source), deadline)
    except MemoryError:
        raise ProfileFailure("execution_limit") from None

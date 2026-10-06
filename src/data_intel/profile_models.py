"""Strict sales profile wire values; serialization grants no source or tool authority."""

import json
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from data_intel.contracts import Revision, SourceIdentity
from data_intel.sales_fixture import INT64_MAX, INT64_MIN

Count = Annotated[int, Field(strict=True, ge=0, le=256)]
ExactInteger = Annotated[str, StringConstraints(strict=True, pattern=r"^(?:0|-?[1-9][0-9]*)$")]


class _ProfileValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    # These policy fields belong to subclasses; Literal booleans otherwise accept 0/1.
    @field_validator("nullable", "exact", "analytical_validated", mode="before", check_fields=False)
    @classmethod
    def strict_policy_boolean(cls, value: object) -> bool:
        if not isinstance(value, bool):
            raise ValueError("nonboolean policy flag")
        return value


class ProfileField(_ProfileValue):
    name: str
    sql_type: Literal["TEXT", "INTEGER"]
    nullable: Literal[False] = False
    meaning: str
    null_count: Count


class ProfileDimension(_ProfileValue):
    field: str
    distinct_count: Count
    values: tuple[str, ...] = Field(max_length=8)
    omitted_value_count: Count


class ProfileMeasure(_ProfileValue):
    field: str
    unit: Literal["net_units", "USD_cents"]
    count: Count
    min: ExactInteger | None
    max: ExactInteger | None
    sum: ExactInteger
    exact: Literal[True] = True

    @field_validator("min", "max", "sum")
    @classmethod
    def signed_int64_statistic(cls, value: str | None) -> str | None:
        if value is not None and not INT64_MIN <= int(value) <= INT64_MAX:
            raise ValueError("out-of-range statistic")
        return value


class DataProfileV2(_ProfileValue):
    version: Literal["2"] = "2"
    source: SourceIdentity
    schema_revision: Revision
    profile_revision: Literal["m3-profile.v1"] = "m3-profile.v1"
    fields: tuple[ProfileField, ...]
    record_count: Count
    range_start: date | None
    range_end: date | None
    dimensions: tuple[ProfileDimension, ...]
    measures: tuple[ProfileMeasure, ...]
    omissions: tuple[
        Literal["bulk_rows"],
        Literal["row_samples"],
        Literal["distributions"],
        Literal["uncomputed_statistics"],
    ] = ("bulk_rows", "row_samples", "distributions", "uncomputed_statistics")
    capabilities: tuple[Literal["query", "search"], ...] = ()
    analytical_validated: Literal[False] = False


class ProfileContentError(ValueError):
    """Fixed safe serialization classifications, without payload values or paths."""

    def __init__(self, code: Literal["invalid_result", "result_limit"]) -> None:
        self.code = code
        super().__init__(code)


def canonical_profile_json(profile: DataProfileV2) -> bytes:
    """Whole key-sorted UTF-8 receipt; refuse over 4,096 bytes rather than trim."""
    try:
        content = json.dumps(
            profile.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, UnicodeError) as error:
        raise ProfileContentError("invalid_result") from error
    if len(content) > 4096:
        raise ProfileContentError("result_limit")
    return content

"""Exact numeric checks over preverified tool receipts and attested query scope."""

import json
from datetime import date
from hashlib import sha256
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from data_intel.contracts import SourceIdentity
from data_intel.profile_models import DataProfileV2, canonical_profile_json
from data_intel.service_contracts import QueryResult

Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$", strict=True)]
Short = Annotated[str, StringConstraints(min_length=1, max_length=96, strict=True)]
IntegerText = Annotated[str, StringConstraints(pattern=r"^-?(0|[1-9][0-9]*)$", strict=True)]
Status = Literal["pass", "fail", "unsupported"]
INT_MIN, INT_MAX = -(2**63), 2**63 - 1


class _Value(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ValidationBoundaryError(ValueError):
    """Safe batch refusal."""


class PeriodV2(_Value):
    start: date
    end: date
    timezone: Literal["UTC"] = "UTC"


class ClaimScopeV2(_Value):
    source: SourceIdentity
    period: PeriodV2 | None = None
    filters: tuple[tuple[str, str], ...] = ()
    group: str | None = None
    unit: Short


class ResultRefV2(_Value):
    receipt_id: UUID
    payload_sha256: Digest
    column: Short
    row_index: int | None = Field(default=None, ge=0, le=19, strict=True)
    cell_path: Literal["cell", "sum", "rank"]


class CalculationV2(_Value):
    kind: Literal["direct_cell", "sum", "difference", "rank"]
    inputs: tuple[Short, ...] = Field(max_length=20)
    formula: str = Field(min_length=1, max_length=256, strict=True)


class NumericalClaimV2(_Value):
    version: Literal["2"] = "2"
    claim_id: UUID
    claim_type: Literal["scalar", "ranking", "comparison", "count", "sum"]
    text: str = Field(min_length=1, max_length=1024, strict=True)
    value: IntegerText
    unit: Short
    scope: ClaimScopeV2
    result_ref: ResultRefV2
    calculation: CalculationV2
    evidence_refs: tuple[UUID, ...] = Field(min_length=1, max_length=12)
    exact: Literal[True] = True

    @model_validator(mode="after")
    def bounded(self) -> Self:
        if len(self.text.encode("utf-8")) > 1024 or not INT_MIN <= int(self.value) <= INT_MAX:
            raise ValueError("invalid numeric value")
        if self.result_ref.receipt_id not in self.evidence_refs:
            raise ValueError("missing evidence reference")
        return self


class NumericEvidenceV2(_Value):
    receipt_id: UUID
    payload: QueryResult | DataProfileV2
    payload_sha256: Digest
    scope: ClaimScopeV2

    @model_validator(mode="after")
    def verify_payload(self) -> Self:
        if self.payload.source != self.scope.source:
            raise ValueError("source_mismatch")
        if isinstance(self.payload, QueryResult):
            digest = _digest(self.payload.model_dump(mode="json"))
        else:
            digest = sha256(canonical_profile_json(self.payload)).hexdigest()
            if any((self.scope.period, self.scope.filters, self.scope.group)):
                raise ValueError("scope_mismatch")
        if self.payload_sha256 != digest:
            raise ValueError("payload_mismatch")
        return self


class CheckV2(_Value):
    name: Literal["numeric"]
    status: Status
    code: Short


class NumericalCheckReportV2(_Value):
    version: Literal["2"] = "2"
    claim_id: UUID
    result_refs: tuple[ResultRefV2, ...]
    checks: tuple[CheckV2, ...]
    overall: Status
    policy_revision: Literal["m4-numeric.v1"] = "m4-numeric.v1"
    input_sha256: Digest
    report_sha256: Digest


def _bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise ValidationBoundaryError("invalid_input") from None


def _digest(value: object) -> str:
    return sha256(_bytes(value)).hexdigest()


def _report_hash(report: NumericalCheckReportV2) -> str:
    return _digest(report.model_dump(mode="json", exclude={"report_sha256"}))


def _cell(payload: QueryResult, column: str, index: int) -> int:
    if column not in payload.columns or index >= len(payload.rows):
        raise ValueError("result_ref_mismatch")
    cell = payload.rows[index][payload.columns.index(column)]
    if cell.type == "real":
        raise ValueError("unsupported_non_exact_value")
    if cell.type != "integer":
        raise ValueError("unit_mismatch")
    return int(cell.value)


def _profile_value(claim: NumericalClaimV2, payload: DataProfileV2) -> int:
    ref, calc = claim.result_ref, claim.calculation
    measure = next((item for item in payload.measures if item.field == ref.column), None)
    if measure is None or measure.unit != claim.unit or ref.cell_path != "sum":
        raise ValueError("result_ref_mismatch")
    if calc.kind != "direct_cell" or calc.inputs != (ref.column,) or calc.formula != ref.column:
        raise ValueError("unsupported_formula")
    return int(measure.sum)


def _direct_value(claim: NumericalClaimV2, payload: QueryResult) -> int:
    ref, calc = claim.result_ref, claim.calculation
    index = ref.row_index
    if (
        index is None
        or ref.cell_path != "cell"
        or calc.inputs != (f"{ref.column}[{index}]",)
        or calc.formula != calc.inputs[0]
    ):
        raise ValueError("unsupported_formula")
    return _cell(payload, ref.column, index)


def _difference_value(claim: NumericalClaimV2, payload: QueryResult) -> int:
    ref, calc = claim.result_ref, claim.calculation
    tokens = tuple(f"{ref.column}[{i}]" for i in range(len(payload.rows)))
    if (
        ref.row_index is not None
        or ref.cell_path != "cell"
        or len(calc.inputs) != 2
        or calc.formula != "-".join(calc.inputs)
        or any(t not in tokens for t in calc.inputs)
    ):
        raise ValueError("unsupported_formula")
    return _cell(payload, ref.column, tokens.index(calc.inputs[0])) - _cell(
        payload, ref.column, tokens.index(calc.inputs[1])
    )


def _query_value(claim: NumericalClaimV2, payload: QueryResult) -> int:
    ref, calc = claim.result_ref, claim.calculation
    if calc.kind == "direct_cell":
        return _direct_value(claim, payload)
    if calc.kind == "sum":
        if (
            ref.row_index is not None
            or ref.cell_path != "sum"
            or calc.inputs != (ref.column,)
            or calc.formula != f"sum({ref.column})"
        ):
            raise ValueError("unsupported_formula")
        return sum(_cell(payload, ref.column, i) for i in range(len(payload.rows)))
    if calc.kind == "difference":
        return _difference_value(claim, payload)
    raise ValueError("unsupported_formula")


def _numeric_value(claim: NumericalClaimV2, evidence: NumericEvidenceV2) -> int:
    if isinstance(evidence.payload, DataProfileV2):
        return _profile_value(claim, evidence.payload)
    return _query_value(claim, evidence.payload)


def validate_numeric(
    claim: NumericalClaimV2, evidence: NumericEvidenceV2
) -> NumericalCheckReportV2:
    """Check an attested exact result without inferring SQL semantics or tolerances."""
    input_hash = _digest(
        {"claim": claim.model_dump(mode="json"), "evidence": evidence.model_dump(mode="json")}
    )
    try:
        if claim.scope != evidence.scope:
            raise ValueError("scope_mismatch")
        if claim.unit != claim.scope.unit:
            raise ValueError("unit_mismatch")
        if (claim.result_ref.receipt_id, claim.result_ref.payload_sha256) != (
            evidence.receipt_id,
            evidence.payload_sha256,
        ):
            raise ValueError("result_ref_mismatch")
        if _numeric_value(claim, evidence) != int(claim.value):
            raise ValueError("value_mismatch")
        status: Status = "pass"
        code = "exact_match"
    except ValueError as error:
        code = str(error)
        status = "unsupported" if code.startswith("unsupported_") else "fail"
    report = NumericalCheckReportV2(
        claim_id=claim.claim_id,
        result_refs=(claim.result_ref,),
        checks=(CheckV2(name="numeric", status=status, code=code),),
        overall=status,
        input_sha256=input_hash,
        report_sha256="0" * 64,
    )
    return report.model_copy(update={"report_sha256": _report_hash(report)})


def validate_numeric_batch(
    claims: tuple[NumericalClaimV2, ...], evidence: NumericEvidenceV2
) -> tuple[NumericalCheckReportV2, ...]:
    if len(claims) > 12:
        raise ValidationBoundaryError("result_limit")
    reports = tuple(validate_numeric(claim, evidence) for claim in claims)
    content = {
        "claims": [c.model_dump(mode="json") for c in claims],
        "reports": [r.model_dump(mode="json") for r in reports],
    }
    if len(_bytes(content)) > 8192:
        raise ValidationBoundaryError("result_limit")
    return reports

"""Exact-value validation against real receipts and mutated claims."""

import json
from hashlib import sha256
from uuid import UUID

import pytest

from data_intel.contracts import SqlIntent
from data_intel.query_engine import SQLiteQueryEngine
from data_intel.sales_demo import DEMO_SOURCE
from data_intel.sales_fixture import SALES_SOURCE
from data_intel.sales_profile import profile_sales_demo
from data_intel.service_contracts import (
    QueryResult,
    QueryServiceRequest,
    adapt_query,
    runtime_info_from_bindings,
)
from data_intel.validation import (
    CalculationV2,
    ClaimScopeV2,
    NumericalClaimV2,
    NumericEvidenceV2,
    ResultRefV2,
    ValidationBoundaryError,
    validate_numeric,
    validate_numeric_batch,
)

ID = UUID("20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b")


def _hash(value: object) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(content.encode()).hexdigest()


def _query(sql: str) -> NumericEvidenceV2:
    request = QueryServiceRequest(
        version="1",
        job_id=ID,
        intent=SqlIntent(version="1", source=SALES_SOURCE, question="Count?", sql=sql, max_rows=20),
    )
    runtime = runtime_info_from_bindings("local", None, None, "3.12", "3.46")
    receipt = adapt_query(request, SQLiteQueryEngine(), runtime)
    return NumericEvidenceV2(
        receipt_id=receipt.receipt_id,
        payload=receipt,
        payload_sha256=_hash(receipt.model_dump(mode="json")),
        scope=ClaimScopeV2(source=SALES_SOURCE, unit="count"),
    )


def _claim(
    evidence: NumericEvidenceV2, value: str, column: str = "n", index: int | None = 0
) -> NumericalClaimV2:
    token = column if index is None else f"{column}[{index}]"
    ref = ResultRefV2(
        receipt_id=evidence.receipt_id,
        payload_sha256=evidence.payload_sha256,
        column=column,
        row_index=index,
        cell_path="sum" if index is None else "cell",
    )
    calc = CalculationV2(kind="direct_cell", inputs=(token,), formula=token)
    return NumericalClaimV2(
        claim_id=ID,
        claim_type="scalar",
        text="Claim",
        value=value,
        unit=evidence.scope.unit,
        scope=evidence.scope,
        result_ref=ref,
        calculation=calc,
        evidence_refs=(evidence.receipt_id,),
    )


def test_exact_query_profile_and_mutations() -> None:
    evidence = _query("SELECT count(*) AS n FROM main.sales")
    claim = _claim(evidence, "6")
    report = validate_numeric(claim, evidence)
    assert report.overall == "pass"
    assert report.report_sha256 == _hash(report.model_dump(mode="json", exclude={"report_sha256"}))
    mutations = (
        ({"value": "7"}, "value_mismatch"),
        ({"unit": "USD_cents"}, "unit_mismatch"),
        (
            {"result_ref": claim.result_ref.model_copy(update={"payload_sha256": "0" * 64})},
            "result_ref_mismatch",
        ),
    )
    for changed, code in mutations:
        assert validate_numeric(claim.model_copy(update=changed), evidence).checks[0].code == code
    profile = profile_sales_demo(DEMO_SOURCE)
    profile_evidence = NumericEvidenceV2(
        receipt_id=ID,
        payload=profile,
        payload_sha256=_hash(profile.model_dump(mode="json")),
        scope=ClaimScopeV2(source=DEMO_SOURCE, unit="USD_cents"),
    )
    profile_claim = _claim(profile_evidence, "395000", "revenue_cents", None)
    assert validate_numeric(profile_claim, profile_evidence).overall == "pass"


def test_arithmetic_non_exact_and_unsupported_rank() -> None:
    evidence = _query("SELECT units AS n FROM main.sales")
    assert isinstance(evidence.payload, QueryResult)
    values = [int(row[0].value) for row in evidence.payload.rows if row[0].type == "integer"]
    base = _claim(evidence, "0")
    sum_ref = base.result_ref.model_copy(update={"row_index": None, "cell_path": "sum"})
    sum_calc = CalculationV2(kind="sum", inputs=("n",), formula="sum(n)")
    sum_claim = base.model_copy(
        update={"value": str(sum(values)), "result_ref": sum_ref, "calculation": sum_calc}
    )
    assert validate_numeric(sum_claim, evidence).overall == "pass"
    diff_ref = sum_ref.model_copy(update={"cell_path": "cell"})
    diff_calc = CalculationV2(kind="difference", inputs=("n[0]", "n[1]"), formula="n[0]-n[1]")
    diff_claim = base.model_copy(
        update={
            "value": str(values[0] - values[1]),
            "result_ref": diff_ref,
            "calculation": diff_calc,
        }
    )
    assert validate_numeric(diff_claim, evidence).overall == "pass"
    real = _query("SELECT 1.5 AS n FROM main.sales LIMIT 1")
    assert validate_numeric(_claim(real, "1"), real).overall == "unsupported"


def test_batch_count_and_utf8_limits() -> None:
    evidence = _query("SELECT count(*) AS n FROM main.sales")
    claim = _claim(evidence, "6")
    with pytest.raises(ValidationBoundaryError, match="result_limit"):
        validate_numeric_batch((claim,) * 13, evidence)
    with pytest.raises(ValidationBoundaryError, match="result_limit"):
        validate_numeric_batch((claim.model_copy(update={"text": "é" * 900}),) * 5, evidence)

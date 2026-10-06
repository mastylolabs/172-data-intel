"""Exact-value validation against real receipts and mutated claims."""

import json
from hashlib import sha256
from uuid import UUID

import pytest
from pydantic import ValidationError

from data_intel.contracts import SourceIdentity, SqlIntent
from data_intel.query_engine import SQLiteQueryEngine
from data_intel.sales_demo import DEMO_SOURCE
from data_intel.sales_fixture import SALES_SOURCE
from data_intel.sales_profile import profile_sales_demo
from data_intel.service_contracts import (
    QueryServiceRequest,
    adapt_query,
    runtime_info_from_bindings,
)
from data_intel.validation import (
    CalculationV2,
    ClaimScopeV2,
    ExactIntegerV2,
    NumericalClaimV2,
    NumericEvidenceV2,
    QueryResultV2,
    ResultRefV2,
    validate_numeric,
)

ID = UUID("20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b")
GROUP_SQL = (
    "SELECT customer, sum(revenue_cents) AS revenue_cents FROM main.sales "
    "GROUP BY customer ORDER BY revenue_cents DESC, customer ASC"
)


def _hash(value: object) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(content.encode()).hexdigest()


def _query(
    sql: str, unit: str = "count", source: SourceIdentity = SALES_SOURCE, group: str | None = None
) -> NumericEvidenceV2:
    request = QueryServiceRequest(
        version="1",
        job_id=ID,
        intent=SqlIntent(version="1", source=source, question="Count?", sql=sql, max_rows=20),
    )
    runtime = runtime_info_from_bindings("local", None, None, "3.12", "3.46")
    original = adapt_query(request, SQLiteQueryEngine(allow_demo_source=True), runtime)
    payload = original.model_dump(mode="json") | {"version": "2"}
    receipt = QueryResultV2.model_validate_json(json.dumps(payload))
    return NumericEvidenceV2(
        receipt_id=receipt.receipt_id,
        payload=receipt,
        payload_sha256=_hash(receipt.model_dump(mode="json")),
        scope=ClaimScopeV2(source=source, unit=unit, group=group),
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
        value=ExactIntegerV2(value=value, unit=evidence.scope.unit),
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
    changed = claim.model_copy(update={"value": claim.value.model_copy(update={"value": "7"})})
    assert validate_numeric(changed, evidence).overall == "fail"
    forged_unit = claim.model_copy(
        update={"value": claim.value.model_copy(update={"unit": "USD_cents"})}
    )
    assert validate_numeric(forged_unit, evidence).checks[0].code == "unit_mismatch"
    profile = profile_sales_demo(DEMO_SOURCE)
    profile_evidence = NumericEvidenceV2(
        receipt_id=ID,
        payload=profile,
        payload_sha256=_hash(profile.model_dump(mode="json")),
        scope=ClaimScopeV2(source=DEMO_SOURCE, unit="USD_cents"),
    )
    profile_claim = _claim(profile_evidence, "395000", "revenue_cents", None)
    assert validate_numeric(profile_claim, profile_evidence).overall == "pass"


def test_arithmetic_and_mismatched_rank_kind_refuse() -> None:
    evidence = _query("SELECT units AS n FROM main.sales", "net_units")
    assert isinstance(evidence.payload, QueryResultV2)
    values = [int(row[0].value) for row in evidence.payload.rows if row[0].type == "integer"]
    base = _claim(evidence, "0")
    sum_ref = base.result_ref.model_copy(update={"row_index": None, "cell_path": "sum"})
    sum_calc = CalculationV2(kind="sum", inputs=("n",), formula="sum(n)")
    sum_claim = base.model_copy(
        update={
            "value": base.value.model_copy(update={"value": str(sum(values))}),
            "result_ref": sum_ref,
            "calculation": sum_calc,
        }
    )
    assert validate_numeric(sum_claim, evidence).overall == "pass"
    rank = base.model_copy(update={"claim_type": "ranking"})
    assert validate_numeric(rank, evidence).overall == "unsupported"


def test_difference_checks_exact_inputs_formula_and_unit() -> None:
    evidence = _query("SELECT units AS n FROM main.sales", "net_units")
    base = _claim(evidence, "-1")
    ref = base.result_ref.model_copy(update={"row_index": None})
    calc = CalculationV2(kind="difference", inputs=("n[0]", "n[1]"), formula="n[0]-n[1]")
    claim = base.model_copy(
        update={"claim_type": "comparison", "result_ref": ref, "calculation": calc}
    )
    assert validate_numeric(claim, evidence).overall == "pass"
    for bad in (
        calc.model_copy(update={"formula": "n[1]-n[0]"}),
        calc.model_copy(update={"inputs": ("n[0]", "n[99]")}),
        calc.model_copy(update={"formula": "n[0]/n[1]"}),
    ):
        assert (
            validate_numeric(claim.model_copy(update={"calculation": bad}), evidence).overall
            == "unsupported"
        )
    wrong = claim.model_copy(update={"value": claim.value.model_copy(update={"unit": "USD_cents"})})
    assert validate_numeric(wrong, evidence).checks[0].code == "unit_mismatch"


def test_ranking_recomputes_complete_group_order_and_ties() -> None:
    evidence = _query(GROUP_SQL, "USD_cents", DEMO_SOURCE, "Elm")
    assert isinstance(evidence.payload, QueryResultV2)
    assert [row[0].value for row in evidence.payload.rows][-2:] == ["Elm", "Fjord"]
    base = _claim(evidence, "5", "revenue_cents", 4)
    ref = base.result_ref.model_copy(update={"cell_path": "rank"})
    calc = CalculationV2(
        kind="rank", inputs=("customer", "revenue_cents"), formula="rank(customer,revenue_cents)"
    )
    claim = base.model_copy(
        update={"claim_type": "ranking", "result_ref": ref, "calculation": calc}
    )
    assert validate_numeric(claim, evidence).overall == "pass"
    wrong_ref = ref.model_copy(update={"row_index": 5})
    assert (
        validate_numeric(claim.model_copy(update={"result_ref": wrong_ref}), evidence)
        .checks[0]
        .code
        == "rank_mismatch"
    )
    wrong_sql = GROUP_SQL.replace(", customer ASC", "")
    with pytest.raises(ValidationError, match="unsupported_scope"):
        _query(wrong_sql, "USD_cents", DEMO_SOURCE, "Elm")


def test_group_scope_binds_each_referenced_row_and_refuses_grouped_sum() -> None:
    evidence = _query(GROUP_SQL, "USD_cents", DEMO_SOURCE, "Elm")
    assert (
        validate_numeric(_claim(evidence, "40000", "revenue_cents", 4), evidence).overall == "pass"
    )
    acme = _claim(evidence, "100000", "revenue_cents", 0)
    assert validate_numeric(acme, evidence).checks[0].code == "group_mismatch"
    ref = acme.result_ref.model_copy(update={"row_index": None})
    difference = acme.model_copy(
        update={
            "claim_type": "comparison",
            "result_ref": ref,
            "value": acme.value.model_copy(update={"value": "0"}),
            "calculation": CalculationV2(
                kind="difference",
                inputs=("revenue_cents[4]", "revenue_cents[5]"),
                formula="revenue_cents[4]-revenue_cents[5]",
            ),
        }
    )
    assert validate_numeric(difference, evidence).checks[0].code == "group_mismatch"
    total = acme.model_copy(
        update={
            "claim_type": "sum",
            "result_ref": ref.model_copy(update={"cell_path": "sum"}),
            "value": acme.value.model_copy(update={"value": "395000"}),
            "calculation": CalculationV2(
                kind="sum", inputs=("revenue_cents",), formula="sum(revenue_cents)"
            ),
        }
    )
    assert validate_numeric(total, evidence).overall == "unsupported"


def test_unverified_receipt_scope_and_id_refuse() -> None:
    evidence = _query("SELECT count(*) AS n FROM main.sales")
    for scope in (
        evidence.scope.model_copy(update={"period": {"start": "2026-01-01", "end": "2026-02-01"}}),
        evidence.scope.model_copy(update={"unit": "USD_cents"}),
    ):
        with pytest.raises(ValidationError):
            NumericEvidenceV2.model_validate(evidence.__dict__ | {"scope": scope})
    with pytest.raises(ValidationError, match="result_ref_mismatch"):
        NumericEvidenceV2.model_validate(evidence.__dict__ | {"receipt_id": ID})

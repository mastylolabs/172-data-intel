"""Local parity and rejection checks for the private Python service boundary."""

import json
from uuid import UUID

import pytest
from pydantic import ValidationError

from data_intel.contracts import SqlIntent
from data_intel.query_engine import SQLiteQueryEngine
from data_intel.sales_fixture import SALES_SOURCE
from data_intel.service_contracts import (
    QueryResult,
    QueryServiceRequest,
    RuntimeInfo,
    RuntimeProvenanceError,
    adapt_query,
    runtime_info_from_bindings,
)

JOB_ID = UUID("20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b")
SQL = "SELECT 9223372036854775807 AS n, 1.5 AS r, customer AS t, NULL AS z FROM main.sales LIMIT 1"


def _request(sql: str = SQL, max_rows: int = 20) -> QueryServiceRequest:
    return QueryServiceRequest(
        version="1",
        job_id=JOB_ID,
        intent=SqlIntent(
            version="1",
            source=SALES_SOURCE,
            question="What is the value?",
            sql=sql,
            max_rows=max_rows,
        ),
    )


def _runtime() -> RuntimeInfo:
    return runtime_info_from_bindings("local", None, None, "3.12.7", "3.46.1")


@pytest.mark.parametrize("field,value", [("version", "2"), ("job_id", "bad"), ("extra", True)])
def test_wire_request_rejects_unknown_version_uuid_and_fields(field: str, value: object) -> None:
    payload = json.loads(_request().model_dump_json())
    payload[field] = value
    with pytest.raises(ValidationError):
        QueryServiceRequest.model_validate_json(json.dumps(payload))


def test_request_round_trip_preserves_intent_and_bounds_utf8_sql() -> None:
    request = _request("SELECT customer FROM main.sales")
    assert QueryServiceRequest.model_validate_json(request.model_dump_json()) == request
    with pytest.raises(ValidationError, match="invalid_input"):
        _request(max_rows=21)
    with pytest.raises(ValidationError, match="invalid_input"):
        _request("SELECT '" + "é" * 4_000 + "'")


def test_adapter_executes_real_engine_and_preserves_exact_cell_types() -> None:
    result = adapt_query(_request(), SQLiteQueryEngine(), _runtime())
    restored = QueryResult.model_validate_json(result.model_dump_json())

    assert restored.job_id == JOB_ID
    assert restored.source == SALES_SOURCE
    assert restored.actual_sql == SQL
    assert [cell.model_dump(mode="json") for cell in restored.rows[0]] == [
        {"type": "integer", "value": "9223372036854775807", "exact": True},
        {"type": "real", "value": "1.5", "exact": False},
        {"type": "text", "value": "Acme"},
        {"type": "null", "value": None},
    ]
    assert restored.coverage == "complete_query_result"
    assert restored.analytical_validated is False


@pytest.mark.parametrize("field,value", [("sql_sha256", "0" * 64), ("row_count", 2)])
def test_result_rejects_fabricated_hash_and_shape(field: str, value: object) -> None:
    payload = json.loads(adapt_query(_request(), SQLiteQueryEngine(), _runtime()).model_dump_json())
    payload[field] = value
    with pytest.raises(ValidationError, match="invalid_result"):
        QueryResult.model_validate_json(json.dumps(payload))


def test_result_rejects_fabricated_policy_and_cells() -> None:
    payload = json.loads(adapt_query(_request(), SQLiteQueryEngine(), _runtime()).model_dump_json())
    payload["limits"]["sqlite_limits"] = {}
    with pytest.raises(ValidationError, match="invalid_result"):
        QueryResult.model_validate_json(json.dumps(payload))
    payload = json.loads(adapt_query(_request(), SQLiteQueryEngine(), _runtime()).model_dump_json())
    payload["rows"][0][0]["value"] = "9223372036854775808"
    with pytest.raises(ValidationError, match="invalid_result"):
        QueryResult.model_validate_json(json.dumps(payload))
    payload["rows"][0][1]["value"] = "nan"
    with pytest.raises(ValidationError, match="invalid_result"):
        QueryResult.model_validate_json(json.dumps(payload))


def test_result_refuses_complete_wire_payload_above_declared_limit() -> None:
    wide_text = "x" * 120
    wide_sql = "SELECT sale_id, " + ", ".join(f"'{wide_text}' AS c{i}" for i in range(15))
    request = _request(wide_sql + " FROM main.sales")
    engine = SQLiteQueryEngine()
    assert len(engine.execute(request.intent).content.content_bytes) < 16_384
    with pytest.raises(ValidationError, match="result_limit"):
        adapt_query(request, engine, _runtime())


def test_deployed_runtime_requires_binding_uuid_and_committed_revision() -> None:
    revision = "ef8eac322f95580c5c717cdef2c9eabdf7f55ff2"
    worker_id = "fe864d4b-909b-4016-8aa0-4d5cc2f499c0"
    runtime = runtime_info_from_bindings("deployed", revision, worker_id, "3.14.2", "3.50.4")
    assert runtime.build_revision == revision
    for bad_revision, bad_id in ((None, worker_id), ("unknown", worker_id), (revision, None)):
        with pytest.raises(RuntimeProvenanceError, match="runtime_incompatible"):
            runtime_info_from_bindings("deployed", bad_revision, bad_id, "3.14.2", "3.50.4")

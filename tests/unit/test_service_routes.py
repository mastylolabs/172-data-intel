"""Local private transport tests use real bounded SQL and independently known totals."""

import json
from uuid import UUID

import pytest

from data_intel.query_engine import SQLiteQueryEngine
from data_intel.sales_fixture import SALES_SOURCE
from data_intel.service_contracts import RuntimeInfo
from data_intel.service_routes import handle_service

JOB = "4233d2b5-9a08-42b9-b6e5-f8c03ab53328"
ENGINE = SQLiteQueryEngine()
RUNTIME = RuntimeInfo(
    python_version="3.14.2",
    sqlite_version="3.51.0",
    runtime_mode="local",
    build_revision=None,
    worker_version_id=None,
)


def _payload(sql: str, *, version: str = "1", source: object = SALES_SOURCE) -> bytes:
    identity = source.model_dump(mode="json") if hasattr(source, "model_dump") else source
    return json.dumps(
        {
            "version": version,
            "job_id": JOB,
            "intent": {
                "version": "1",
                "source": identity,
                "question": "Sales total?",
                "sql": sql,
                "max_rows": 20,
            },
        }
    ).encode()


def test_health_and_metadata_are_bounded_and_authoritative() -> None:
    health_status, health_body = handle_service("GET", "/health", b"", RUNTIME, ENGINE)
    assert health_status == 200
    assert json.loads(health_body)["engine_policy"] == "m2-sqlite.v1"
    status, body = handle_service("GET", "/metadata", b"", RUNTIME, ENGINE)
    metadata = json.loads(body)
    assert status == 200 and len(body) <= 4096
    assert metadata["source"] == SALES_SOURCE.model_dump(mode="json")
    assert metadata["profile"]["record_count"] == 6
    assert metadata["fields"][-1]["meaning"].startswith("Signed net USD cents")
    assert metadata["capabilities"] == ["query"]
    assert "rows" not in metadata


def test_query_returns_exact_real_execution_receipt() -> None:
    sql = "SELECT SUM(revenue_cents) AS cents FROM main.sales"
    status, body = handle_service("POST", "/query", _payload(sql), RUNTIME, ENGINE)
    result = json.loads(body)
    assert status == 200 and len(body) <= 16_384
    assert result["job_id"] == str(UUID(JOB))
    assert result["actual_sql"] == sql
    assert result["rows"] == [[{"type": "integer", "value": "130000", "exact": True}]]
    assert result["analytical_validated"] is False
    assert result["runtime"]["runtime_mode"] == "local"


@pytest.mark.parametrize(
    ("body", "expected_status", "expected_code"),
    [
        (b"{", 400, "invalid_input"),
        (_payload("SELECT sale_id FROM main.sales", version="2"), 400, "unsupported_version"),
        (_payload("DELETE FROM main.sales"), 422, "unsafe_query"),
        (b"x" * 16_385, 413, "result_limit"),
        (
            _payload(
                "SELECT sale_id FROM main.sales",
                source={**SALES_SOURCE.model_dump(mode="json"), "source_id": "support"},
            ),
            422,
            "unsupported_source",
        ),
    ],
)
def test_query_refusals_have_safe_stable_codes(
    body: bytes, expected_status: int, expected_code: str
) -> None:
    status, response = handle_service("POST", "/query", body, RUNTIME, ENGINE)
    error = json.loads(response)
    assert (status, error["code"], error["automatic_retry"]) == (
        expected_status,
        expected_code,
        False,
    )
    assert "DELETE" not in response.decode()


def test_unknown_and_support_routes_expose_no_data() -> None:
    for method, path in (("GET", "/support"), ("GET", "/query"), ("POST", "/unknown")):
        status, body = handle_service(method, path, b"", RUNTIME, ENGINE)
        assert (status, json.loads(body)["code"]) == (404, "not_found")

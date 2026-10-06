"""Private v2 catalog/profile route behavior and safe refusal tests."""

import json
from uuid import UUID

import pytest
from pydantic import ValidationError

from data_intel.catalog_v2 import CatalogV2
from data_intel.contracts import SourceIdentity
from data_intel.profile_models import DataProfileV2
from data_intel.search_models import SearchReceiptV2
from data_intel.service_v2_contracts import RuntimeProvenanceV2, ServiceEnvelopeV2
from data_intel.service_v2_routes import (
    ToolRequestV2,
    handle_service_v2,
    runtime_provenance_v2_from_bindings,
)
from data_intel.support_demo import SUPPORT_SOURCE
from data_intel.validation import QueryResultV2

JOB = UUID("20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b")
RUN = UUID("d2ebca4d-b6ce-4c98-a9e0-d7fa8e6f9ba0")
RECEIPT = UUID("fe864d4b-909b-4016-8aa0-4d5cc2f499c0")


def _runtime(mode: str = "local") -> RuntimeProvenanceV2:
    return runtime_provenance_v2_from_bindings(mode, None, None, "3.12.7", "3.46.1")


def _request(source: SourceIdentity) -> bytes:
    return (
        ToolRequestV2(version="2", job_id=JOB, run_id=RUN, source=source).model_dump_json().encode()
    )


def _query_request(
    source: SourceIdentity, sql: str = "SELECT SUM(revenue_cents) AS cents FROM main.sales"
) -> bytes:
    identity = source.model_dump(mode="json")
    return json.dumps(
        {
            "version": "2",
            "job_id": str(JOB),
            "run_id": str(RUN),
            "source": identity,
            "intent": {
                "version": "1",
                "source": identity,
                "question": "What is the total?",
                "sql": sql,
                "max_rows": 20,
            },
        }
    ).encode()


def _search_request(source: SourceIdentity, query: str = "export") -> bytes:
    return json.dumps(
        {
            "version": "2",
            "job_id": str(JOB),
            "run_id": str(RUN),
            "source": source.model_dump(mode="json"),
            "query": query,
            "max_hits": 2,
        }
    ).encode()


def test_catalog_route_returns_server_owned_json_envelope() -> None:
    status, body = handle_service_v2("GET", "/v2/catalog", b"", _runtime())
    assert status == 200
    envelope = ServiceEnvelopeV2[CatalogV2].model_validate_json(body)
    assert envelope.job_id is None and envelope.payload.catalog_revision == "m4-catalog.v1"
    assert {entry.source.source_id for entry in envelope.payload.entries} == {"sales", "support"}


def test_profile_route_executes_real_profile_and_preserves_ids() -> None:
    from data_intel.sales_demo import DEMO_SOURCE

    status, body = handle_service_v2("POST", "/v2/profile", _request(DEMO_SOURCE), _runtime())
    assert status == 200
    envelope = ServiceEnvelopeV2[DataProfileV2].model_validate_json(body)
    assert envelope.job_id == JOB and envelope.payload.record_count == 24
    assert envelope.payload.source == DEMO_SOURCE
    wire = json.loads(body)
    wire["payload_sha256"] = "0" * 64
    with pytest.raises(ValidationError, match="invalid_result"):
        ServiceEnvelopeV2[DataProfileV2].model_validate(wire)
    raw = _request(DEMO_SOURCE)
    padded = raw + b" " * (1025 - len(raw))
    status, _ = handle_service_v2("POST", "/v2/profile", padded, _runtime())
    assert status == 413


def test_profile_route_refuses_support_and_mutated_source() -> None:
    from data_intel.sales_demo import DEMO_SOURCE
    from data_intel.support_demo import SUPPORT_SOURCE

    status, body = handle_service_v2("POST", "/v2/profile", _request(SUPPORT_SOURCE), _runtime())
    assert status == 422 and json.loads(body)["code"] == "capability_mismatch"
    changed = DEMO_SOURCE.model_copy(update={"snapshot_sha256": "0" * 64})
    status, body = handle_service_v2("POST", "/v2/profile", _request(changed), _runtime())
    assert status == 409 and json.loads(body)["code"] == "source_mismatch"


def test_profile_route_rejects_unknown_source_enum_as_invalid_input() -> None:
    from data_intel.sales_demo import DEMO_SOURCE

    wire = json.loads(_request(DEMO_SOURCE))
    wire["source"]["source_id"] = "other"
    status, body = handle_service_v2("POST", "/v2/profile", json.dumps(wire).encode(), _runtime())
    assert status == 400 and json.loads(body)["code"] == "invalid_input"


def test_query_route_executes_real_sum_and_grouped_ranking() -> None:
    from data_intel.sales_demo import DEMO_SOURCE

    status, body = handle_service_v2("POST", "/v2/query", _query_request(DEMO_SOURCE), _runtime())
    assert status == 200
    envelope = ServiceEnvelopeV2[QueryResultV2].model_validate_json(body)
    assert envelope.job_id == JOB and envelope.run_id == RUN
    assert envelope.receipt_id == envelope.payload.receipt_id
    assert envelope.payload.rows[0][0].value == "395000"
    grouped = _query_request(
        DEMO_SOURCE,
        "SELECT customer, SUM(revenue_cents) AS cents FROM main.sales "
        "GROUP BY customer ORDER BY cents DESC, customer ASC",
    )
    status, body = handle_service_v2("POST", "/v2/query", grouped, _runtime())
    payload = ServiceEnvelopeV2[QueryResultV2].model_validate_json(body).payload
    assert status == 200
    assert payload.rows[0][0].value == "Acme"
    assert payload.rows[0][1].value == "100000"


def test_query_route_rejects_source_mismatch_and_keeps_v1_path_separate() -> None:
    from data_intel.query_engine import SQLiteQueryEngine
    from data_intel.sales_demo import DEMO_SOURCE
    from data_intel.service_contracts import RuntimeInfo
    from data_intel.service_routes import handle_service

    wire = json.loads(_query_request(DEMO_SOURCE))
    wire["intent"]["source"]["snapshot_sha256"] = "0" * 64
    status, body = handle_service_v2("POST", "/v2/query", json.dumps(wire).encode(), _runtime())
    assert status == 409 and json.loads(body)["code"] == "source_mismatch"
    status, body = handle_service_v2("POST", "/query", b"", _runtime())
    assert status == 404 and json.loads(body)["code"] == "not_found"
    legacy_runtime = RuntimeInfo(
        python_version="3.12.7",
        sqlite_version="3.46.1",
        runtime_mode="local",
        build_revision=None,
        worker_version_id=None,
    )
    status, body = handle_service("POST", "/query", b"{", legacy_runtime, SQLiteQueryEngine())
    assert status == 400 and json.loads(body)["code"] == "invalid_input"


def test_query_route_rejects_historical_source_and_input_limits() -> None:
    from data_intel.sales_demo import DEMO_SOURCE
    from data_intel.sales_fixture import SALES_SOURCE

    status, body = handle_service_v2("POST", "/v2/query", _query_request(SALES_SOURCE), _runtime())
    assert status == 409 and json.loads(body)["code"] == "source_mismatch"
    wire = json.loads(_query_request(DEMO_SOURCE))
    wire["intent"]["max_rows"] = 21
    status, body = handle_service_v2("POST", "/v2/query", json.dumps(wire).encode(), _runtime())
    assert status == 400
    assert json.loads(body)["code"] == "invalid_input"
    assert json.loads(body)["stage"] == "input"


def test_query_route_maps_complete_envelope_overflow_to_result_limit() -> None:
    from data_intel.sales_demo import DEMO_SOURCE

    value = "x" * 150
    columns = ", ".join(f"'{value}' AS c{index}" for index in range(4))
    wire = json.loads(_query_request(DEMO_SOURCE, f"SELECT {columns} FROM main.sales LIMIT 20"))
    status, body = handle_service_v2("POST", "/v2/query", json.dumps(wire).encode(), _runtime())
    assert status == 413
    assert json.loads(body)["code"] == "result_limit"


def test_search_route_returns_exact_targeted_ids_and_quotes() -> None:
    status, body = handle_service_v2(
        "POST", "/v2/search", _search_request(SUPPORT_SOURCE), _runtime()
    )
    assert status == 200
    envelope = ServiceEnvelopeV2[SearchReceiptV2].model_validate_json(body)
    assert envelope.payload.returned_count == 2
    assert [hit.message_id for hit in envelope.payload.hits] == ["M015", "M012"]
    assert envelope.payload.hits[0].quote.startswith("The CSV export includes")
    assert envelope.payload.limitations[0].startswith("Targeted lexical examples")


@pytest.mark.parametrize("path", ["/v2/query", "/v2/search"])
def test_v2_tool_envelopes_reject_hash_mutation_and_body_over_cap(path: str) -> None:
    from data_intel.sales_demo import DEMO_SOURCE

    body = (
        _query_request(DEMO_SOURCE) if path.endswith("query") else _search_request(SUPPORT_SOURCE)
    )
    actual, response = handle_service_v2("POST", path, body, _runtime())
    assert actual == 200
    wire = json.loads(response)
    wire["payload_sha256"] = "0" * 64
    with pytest.raises(ValidationError, match="invalid_result"):
        if path.endswith("query"):
            ServiceEnvelopeV2[QueryResultV2].model_validate(wire)
        else:
            ServiceEnvelopeV2[SearchReceiptV2].model_validate(wire)
    cap = 16_384 if path.endswith("query") else 2_048
    padded = body + b" " * (cap + 1 - len(body))
    actual, response = handle_service_v2("POST", path, padded, _runtime())
    assert actual == 413 and json.loads(response)["code"] == "result_limit"


def test_v2_tools_refuse_cross_version_and_wrong_capability() -> None:
    from data_intel.sales_demo import DEMO_SOURCE

    query = json.loads(_query_request(DEMO_SOURCE))
    query["version"] = "1"
    status, body = handle_service_v2("POST", "/v2/query", json.dumps(query).encode(), _runtime())
    assert status == 400 and json.loads(body)["code"] == "unsupported_version"
    search = json.loads(_search_request(SUPPORT_SOURCE))
    search["version"] = "1"
    status, body = handle_service_v2("POST", "/v2/search", json.dumps(search).encode(), _runtime())
    assert status == 400 and json.loads(body)["code"] == "unsupported_version"
    status, body = handle_service_v2(
        "POST", "/v2/query", _query_request(SUPPORT_SOURCE), _runtime()
    )
    assert status == 422 and json.loads(body)["code"] == "unsupported_source"
    status, body = handle_service_v2("POST", "/v2/search", _search_request(DEMO_SOURCE), _runtime())
    assert status == 422 and json.loads(body)["code"] == "unsupported_source"


@pytest.mark.parametrize(
    "method,path,body,status",
    [
        ("POST", "/v2/profile", b"{}", 400),
        ("POST", "/v2/profile", b"x" * 1025, 413),
        ("GET", "/metadata", b"", 404),
    ],
)
def test_v2_routes_refuse_malformed_oversized_and_cross_version_requests(
    method: str, path: str, body: bytes, status: int
) -> None:
    actual, response = handle_service_v2(method, path, body, _runtime())
    assert actual == status
    assert json.loads(response)["version"] == "2"


def test_runtime_provenance_requires_deployed_bindings() -> None:
    with pytest.raises(ValueError, match="runtime_incompatible") as failure:
        runtime_provenance_v2_from_bindings("deployed", None, None, "3.12.7", "3.46.1")
    assert failure.value.__cause__ is None
    deployed = runtime_provenance_v2_from_bindings(
        "deployed",
        "ef8eac322f95580c5c717cdef2c9eabdf7f55ff2",
        str(RECEIPT),
        "3.12.7",
        "3.46.1",
    )
    assert deployed.worker_version_id == RECEIPT

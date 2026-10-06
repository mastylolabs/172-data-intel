"""Private v2 catalog/profile route behavior and safe refusal tests."""

import json
from uuid import UUID

import pytest
from pydantic import ValidationError

from data_intel.catalog_v2 import CatalogV2
from data_intel.contracts import SourceIdentity
from data_intel.profile_models import DataProfileV2
from data_intel.service_v2_contracts import RuntimeProvenanceV2, ServiceEnvelopeV2
from data_intel.service_v2_routes import (
    ToolRequestV2,
    handle_service_v2,
    runtime_provenance_v2_from_bindings,
)

JOB = UUID("20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b")
RUN = UUID("d2ebca4d-b6ce-4c98-a9e0-d7fa8e6f9ba0")
RECEIPT = UUID("fe864d4b-909b-4016-8aa0-4d5cc2f499c0")


def _runtime(mode: str = "local") -> RuntimeProvenanceV2:
    return runtime_provenance_v2_from_bindings(mode, None, None, "3.12.7", "3.46.1")


def _request(source: SourceIdentity) -> bytes:
    return (
        ToolRequestV2(version="2", job_id=JOB, run_id=RUN, receipt_id=RECEIPT, source=source)
        .model_dump_json()
        .encode()
    )


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

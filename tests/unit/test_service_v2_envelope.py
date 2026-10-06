"""Fail-closed tests for the additive v2 envelope and error contracts."""

import json
from hashlib import sha256
from typing import Literal
from uuid import UUID

import pytest
from pydantic import ValidationError

from data_intel.search_models import SearchReceiptV2, SearchRequestV2
from data_intel.service_v2_contracts import (
    RuntimeProvenanceV2,
    ServiceEnvelopeV2,
    ServiceErrorV2,
    ServiceLimitV2,
    V2StrictModel,
    canonical_json,
    payload_sha256,
)
from data_intel.support_demo import SUPPORT_SOURCE
from data_intel.support_search import search_support

JOB_ID = UUID("20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b")
RUN_ID = UUID("d2ebca4d-b6ce-4c98-a9e0-d7fa8e6f9ba0")


def _runtime(mode: Literal["local", "deployed"] = "local") -> RuntimeProvenanceV2:
    return RuntimeProvenanceV2(
        python_version="3.12.7",
        sqlite_version="3.46.1",
        runtime_mode=mode,
        build_revision=None,
        worker_version_id=None,
        service_contract_revision="m4-service.v1",
    )


class SmallPayload(V2StrictModel):
    value: str


def _envelope(
    job_id: UUID | None = None,
    run_id: UUID | None = None,
    receipt_id: UUID | None = None,
) -> ServiceEnvelopeV2[SmallPayload]:
    payload = SmallPayload(value="ok")
    return ServiceEnvelopeV2[SmallPayload](
        version="2",
        payload=payload,
        payload_sha256=payload_sha256(payload),
        runtime=_runtime(),
        job_id=job_id,
        run_id=run_id,
        receipt_id=receipt_id,
    )


def test_canonical_json_and_payload_hash_are_stable() -> None:
    payload = SmallPayload(value="ok")
    assert canonical_json(payload) == b'{"value":"ok"}'
    assert payload_sha256(payload) == sha256(canonical_json(payload)).hexdigest()
    assert json.loads(canonical_json(payload)) == {"value": "ok"}


def test_job_envelope_requires_all_job_identifiers() -> None:
    envelope = _envelope(job_id=JOB_ID, run_id=RUN_ID, receipt_id=RUN_ID)
    assert envelope.job_id == JOB_ID and envelope.run_id == RUN_ID
    with pytest.raises(ValidationError, match="invalid_input"):
        _envelope(job_id=JOB_ID)


@pytest.mark.parametrize("field,value", [("version", "1"), ("payload_sha256", "0" * 64)])
def test_envelope_rejects_wrong_version_and_hash(field: str, value: object) -> None:
    data = json.loads(_envelope().model_dump_json())
    data[field] = value
    with pytest.raises(ValidationError, match=r"(invalid_result|literal_error)"):
        ServiceEnvelopeV2[SmallPayload].model_validate(data)


def test_envelope_rejects_unknown_fields_and_oversize_payload() -> None:
    data = json.loads(_envelope().model_dump_json()) | {"extra": True}
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ServiceEnvelopeV2[SmallPayload].model_validate(data)

    class LargePayload(V2StrictModel):
        value: str

    payload = LargePayload(value="x" * 17_000)
    with pytest.raises(ValidationError, match="result_limit"):
        ServiceEnvelopeV2[LargePayload](
            version="2",
            job_id=None,
            run_id=None,
            receipt_id=None,
            payload=payload,
            payload_sha256=payload_sha256(payload),
            runtime=_runtime(),
        )


@pytest.mark.parametrize("field", ["version", "job_id", "run_id", "receipt_id", "runtime"])
def test_envelope_rejects_omitted_wire_fields(field: str) -> None:
    data = json.loads(_envelope().model_dump_json())
    del data[field]
    with pytest.raises(ValidationError, match="Field required"):
        ServiceEnvelopeV2[SmallPayload].model_validate(data)


def test_runtime_rejects_omitted_contract_revision() -> None:
    data = _runtime().model_dump(mode="json")
    del data["service_contract_revision"]
    with pytest.raises(ValidationError, match="Field required"):
        RuntimeProvenanceV2.model_validate(data)


def test_real_search_receipt_round_trips_through_json_envelope() -> None:
    receipt = search_support(SearchRequestV2(source=SUPPORT_SOURCE, query="export", max_hits=2))
    envelope = ServiceEnvelopeV2[SearchReceiptV2](
        version="2",
        job_id=JOB_ID,
        run_id=RUN_ID,
        receipt_id=RUN_ID,
        payload=receipt,
        payload_sha256=payload_sha256(receipt),
        runtime=_runtime(),
    )
    assert (
        ServiceEnvelopeV2[SearchReceiptV2].model_validate_json(envelope.model_dump_json())
        == envelope
    )


@pytest.mark.parametrize(
    "field",
    [
        "version",
        "schema_revision",
        "search_policy",
        "coverage",
        "limitations",
        "analytical_validated",
    ],
)
def test_real_receipt_rejects_omitted_defaulted_wire_fields(field: str) -> None:
    receipt = search_support(SearchRequestV2(source=SUPPORT_SOURCE, query="export", max_hits=2))
    envelope = ServiceEnvelopeV2[SearchReceiptV2](
        version="2",
        job_id=JOB_ID,
        run_id=RUN_ID,
        receipt_id=RUN_ID,
        payload=receipt,
        payload_sha256=payload_sha256(receipt),
        runtime=_runtime(),
    )
    wire = json.loads(envelope.model_dump_json())
    del wire["payload"][field]
    with pytest.raises(ValidationError, match="invalid_result"):
        ServiceEnvelopeV2[SearchReceiptV2].model_validate_json(json.dumps(wire))


def test_runtime_provenance_requires_deployed_worker_metadata() -> None:
    with pytest.raises(ValidationError, match="runtime_incompatible"):
        _runtime("deployed")
    deployed = RuntimeProvenanceV2(
        python_version="3.12.7",
        sqlite_version="3.46.1",
        runtime_mode="deployed",
        build_revision="ef8eac322f95580c5c717cdef2c9eabdf7f55ff2",
        worker_version_id=UUID("fe864d4b-909b-4016-8aa0-4d5cc2f499c0"),
        service_contract_revision="m4-service.v1",
    )
    assert deployed.service_contract_revision == "m4-service.v1"


def test_surrogate_text_and_error_contract_are_safe() -> None:
    with pytest.raises(ValidationError, match="invalid_input"):
        SmallPayload(value="bad\ud800")
    error = ServiceErrorV2(
        version="2",
        code="source_mismatch",
        stage="catalog",
        job_id=JOB_ID,
        run_id=RUN_ID,
        limit=ServiceLimitV2(name="max_result_bytes", maximum=16_384),
        provider_reason=None,
        automatic_retry=False,
    )
    assert error.automatic_retry is False
    with pytest.raises(ValidationError):
        ServiceErrorV2.model_validate({"code": "secret-provider-error", "stage": "transport"})

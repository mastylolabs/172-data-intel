"""Private v2 catalog and profile adapters over the approved demo sources."""

from typing import Literal, cast
from uuid import UUID

from pydantic import BaseModel, ValidationError

from data_intel.catalog_v2 import CatalogV2, registered_catalog
from data_intel.contracts import SourceId, SourceIdentity
from data_intel.profile_models import DataProfileV2, canonical_profile_json
from data_intel.sales_fixture import FixtureError
from data_intel.sales_profile import ProfileFailure, profile_sales_demo
from data_intel.service_v2_contracts import (
    RuntimeMode,
    RuntimeProvenanceV2,
    ServiceEnvelopeV2,
    ServiceErrorCodeV2,
    ServiceErrorV2,
    V2StrictModel,
    payload_sha256,
)

PROFILE_BODY_BYTES = 1_024
V2_RESULT_BYTES = 16_384
V2Stage = Literal["input", "catalog", "profile", "transport"]


class V2RuntimeProvenanceError(ValueError):
    """Safe configuration failure without exposing binding or host details."""


class ToolRequestV2(V2StrictModel):
    """Job-bound request identity; IDs are required for every tool receipt."""

    version: Literal["2"]
    job_id: UUID
    run_id: UUID
    receipt_id: UUID
    source: SourceIdentity


def runtime_provenance_v2_from_bindings(
    runtime_mode: object,
    build_revision: object,
    worker_version_id: object,
    python_version: str,
    sqlite_version: str,
) -> RuntimeProvenanceV2:
    """Validate explicit deployed provenance for additive v2 routes."""
    if type(runtime_mode) is not str or runtime_mode not in ("local", "deployed"):
        raise V2RuntimeProvenanceError("runtime_incompatible")
    if build_revision is not None and type(build_revision) is not str:
        raise V2RuntimeProvenanceError("runtime_incompatible")
    if worker_version_id is not None and type(worker_version_id) is not str:
        raise V2RuntimeProvenanceError("runtime_incompatible")
    try:
        parsed_id = None if worker_version_id is None else UUID(worker_version_id)
        return RuntimeProvenanceV2(
            python_version=python_version,
            sqlite_version=sqlite_version,
            runtime_mode=cast("RuntimeMode", runtime_mode),
            build_revision=build_revision,
            worker_version_id=parsed_id,
            service_contract_revision="m4-service.v1",
        )
    except (TypeError, ValueError, ValidationError):
        raise V2RuntimeProvenanceError("runtime_incompatible") from None


def _error(
    code: ServiceErrorCodeV2,
    stage: V2Stage,
    job_id: UUID | None = None,
    run_id: UUID | None = None,
) -> tuple[int, bytes]:
    status = {
        "invalid_input": 400,
        "unsupported_version": 400,
        "not_found": 404,
        "source_mismatch": 409,
        "source_switch_conflict": 409,
        "unsupported_source": 422,
        "capability_mismatch": 422,
        "execution_limit": 422,
        "result_limit": 413,
        "runtime_incompatible": 503,
        "invalid_result": 422,
    }.get(code, 422)
    payload = ServiceErrorV2(
        version="2",
        code=code,
        stage=stage,
        job_id=job_id,
        run_id=run_id,
        limit=None,
        provider_reason=None,
        automatic_retry=False,
    )
    return status, payload.model_dump_json().encode("utf-8")


def _json_response(model: BaseModel) -> tuple[int, bytes]:
    payload = model.model_dump_json().encode("utf-8")
    if len(payload) > V2_RESULT_BYTES:
        return _error("result_limit", "transport")
    return 200, payload


def _envelope(
    payload: BaseModel,
    runtime: RuntimeProvenanceV2,
    request: ToolRequestV2 | None,
) -> BaseModel:
    identifiers = (
        (None, None, None)
        if request is None
        else (
            request.job_id,
            request.run_id,
            request.receipt_id,
        )
    )
    if isinstance(payload, CatalogV2):
        return ServiceEnvelopeV2[CatalogV2](
            version="2",
            job_id=identifiers[0],
            run_id=identifiers[1],
            receipt_id=identifiers[2],
            payload=payload,
            payload_sha256=payload_sha256(payload),
            runtime=runtime,
        )
    if isinstance(payload, DataProfileV2):
        return ServiceEnvelopeV2[DataProfileV2](
            version="2",
            job_id=identifiers[0],
            run_id=identifiers[1],
            receipt_id=identifiers[2],
            payload=payload,
            payload_sha256=payload_sha256(payload),
            runtime=runtime,
        )
    raise TypeError("unsupported v2 payload")


def _request(body: bytes) -> ToolRequestV2:
    if len(body) > PROFILE_BODY_BYTES:
        raise ValueError("result_limit")
    return ToolRequestV2.model_validate_json(body)


def _validation_error_code(error: ValidationError) -> ServiceErrorCodeV2:
    if any(
        item["loc"][-1:] == ("version",) and item["type"] == "literal_error"
        for item in error.errors()
    ):
        return "unsupported_version"
    return "invalid_input"


def _execute_profile(request: ToolRequestV2, runtime: RuntimeProvenanceV2) -> tuple[int, bytes]:
    if request.source.source_id != SourceId.SALES:
        return _error("capability_mismatch", "profile", request.job_id, request.run_id)
    try:
        profile = profile_sales_demo(request.source)
        canonical_profile_json(profile)
    except FixtureError as error:
        return _error(
            "source_mismatch" if error.code == "source_mismatch" else "runtime_incompatible",
            "profile",
            request.job_id,
            request.run_id,
        )
    except ProfileFailure as error:
        return _error(error.code, "profile", request.job_id, request.run_id)
    envelope = _envelope(profile, runtime, request)
    return _json_response(envelope)


def _profile(body: bytes, runtime: RuntimeProvenanceV2) -> tuple[int, bytes]:
    try:
        request = _request(body)
    except ValidationError as error:
        return _error(_validation_error_code(error), "input")
    except ValueError as error:
        code: ServiceErrorCodeV2 = (
            "result_limit" if str(error) == "result_limit" else "invalid_input"
        )
        return _error(code, "input")
    return _execute_profile(request, runtime)


def handle_service_v2(
    method: str, path: str, body: bytes, runtime: RuntimeProvenanceV2
) -> tuple[int, bytes]:
    """Dispatch private catalog/profile routes without changing v1 behavior."""
    if method == "GET" and path == "/v2/catalog":
        return _json_response(_envelope(registered_catalog(), runtime, None))
    if method == "POST" and path == "/v2/profile":
        return _profile(body, runtime)
    return _error("not_found", "transport")

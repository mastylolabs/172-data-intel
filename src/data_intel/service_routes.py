"""Private, bounded service responses; routing grants only synthetic sales capability."""

from dataclasses import asdict
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ValidationError

from data_intel.contracts import SqlIntent
from data_intel.query_engine import QueryEngine, QueryFailure
from data_intel.sales_fixture import SALES_SOURCE, FixtureError, load_sales_fixture
from data_intel.service_contracts import (
    M2_QUERY_LIMITS,
    MetadataField,
    QueryServiceRequest,
    RuntimeInfo,
    ServiceError,
    ServiceErrorCode,
    ServiceHealth,
    ServiceMetadata,
    adapt_query,
)

Stage = Literal["input", "query", "transport"]
_STATUS: dict[ServiceErrorCode, int] = {
    "invalid_input": 400,
    "unsupported_version": 400,
    "not_found": 404,
    "unsupported_transport": 400,
    "unsafe_query": 422,
    "invalid_query": 422,
    "execution_limit": 422,
    "invalid_result": 422,
    "result_limit": 413,
    "runtime_incompatible": 503,
    "unsupported_source": 422,
    "source_mismatch": 409,
}


def error_response(
    code: ServiceErrorCode, stage: Stage, job_id: UUID | None = None
) -> tuple[int, bytes]:
    error = ServiceError(code=code, stage=stage, job_id=job_id)
    return _STATUS[code], error.model_dump_json().encode("utf-8")


def _json_response(model: BaseModel, max_bytes: int) -> tuple[int, bytes]:
    payload = model.model_dump_json().encode("utf-8")
    if len(payload) > max_bytes:
        return error_response("runtime_incompatible", "transport")
    return 200, payload


def _health(runtime: RuntimeInfo, engine: QueryEngine) -> tuple[int, bytes]:
    probe = SqlIntent(
        version="1",
        source=SALES_SOURCE,
        question="Runtime capability probe",
        sql="SELECT sale_id FROM main.sales LIMIT 1",
        max_rows=1,
    )
    try:
        engine.execute(probe)
    except QueryFailure:
        return error_response("runtime_incompatible", "transport")
    return _json_response(
        ServiceHealth(version="1", engine_policy="m2-sqlite.v1", **runtime.model_dump()), 4096
    )


def _metadata(runtime: RuntimeInfo) -> tuple[int, bytes]:
    try:
        fixture = load_sales_fixture()
    except FixtureError:
        return error_response("runtime_incompatible", "transport")
    metadata = ServiceMetadata(
        version="1",
        source=fixture.source,
        schema_revision="sales-proof.v1",
        table="sales",
        fields=[MetadataField(**asdict(field)) for field in fixture.fields],
        profile=fixture.profile,
        capabilities=["query"],
        dialect="sqlite",
        engine_policy="m2-sqlite.v1",
        limits=M2_QUERY_LIMITS,
        runtime=runtime,
    )
    return _json_response(metadata, 4096)


def _request_error(error: ValidationError) -> ServiceErrorCode:
    if any(
        item["loc"][-1:] == ("version",) and item["type"] == "literal_error"
        for item in error.errors()
    ):
        return "unsupported_version"
    return "invalid_input"


def _query(body: bytes, runtime: RuntimeInfo, engine: QueryEngine) -> tuple[int, bytes]:
    if len(body) > 16_384:
        return error_response("result_limit", "input")
    try:
        request = QueryServiceRequest.model_validate_json(body)
    except ValidationError as error:
        return error_response(_request_error(error), "input")
    try:
        result = adapt_query(request, engine, runtime)
    except QueryFailure as error:
        return error_response(error.code, "query", request.job_id)
    except ValidationError as error:
        code: ServiceErrorCode = (
            "result_limit"
            if any("result_limit" in item["msg"] for item in error.errors())
            else "invalid_result"
        )
        return error_response(code, "query", request.job_id)
    return _json_response(result, 16_384)


def handle_service(
    method: str, path: str, body: bytes, runtime: RuntimeInfo, engine: QueryEngine
) -> tuple[int, bytes]:
    """Return stable status and strict JSON; the Worker owns bounded body streaming."""
    if method == "GET" and path == "/health":
        return _health(runtime, engine)
    if method == "GET" and path == "/metadata":
        return _metadata(runtime)
    if method == "POST" and path == "/query":
        return _query(body, runtime, engine)
    return error_response("not_found", "transport")

"""Private service-binding DTOs and adapter parity for the M2 Python boundary."""

import json
import math
from dataclasses import asdict
from hashlib import sha256
from typing import Annotated, Literal, cast
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from data_intel._bounded_result import Cell
from data_intel._sqlite_policy import _LIMITS
from data_intel.contracts import SourceIdentity, SqlIntent
from data_intel.query_engine import QueryEngine
from data_intel.sales_fixture import SalesProfile

Digest = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-f0-9]{64}$")]
BuildRevision = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-f0-9]{40}$")]
RuntimeMode = Literal["local", "deployed"]
ServiceErrorCode = Literal[
    "invalid_input",
    "unsupported_version",
    "not_found",
    "unsupported_transport",
    "unsafe_query",
    "invalid_query",
    "execution_limit",
    "invalid_result",
    "result_limit",
    "runtime_incompatible",
    "unsupported_source",
    "source_mismatch",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RuntimeInfo(StrictModel):
    python_version: str = Field(strict=True, min_length=1, max_length=32)
    sqlite_version: str = Field(strict=True, min_length=1, max_length=32)
    runtime_mode: RuntimeMode
    build_revision: BuildRevision | None
    worker_version_id: UUID | None

    @model_validator(mode="after")
    def require_deployed_provenance(self) -> "RuntimeInfo":
        if self.runtime_mode == "deployed" and (
            self.build_revision is None or self.worker_version_id is None
        ):
            raise ValueError("runtime_incompatible")
        return self


class RuntimeProvenanceError(ValueError):
    """Safe failure when explicit Worker provenance is missing or malformed."""

    def __init__(self) -> None:
        self.code: Literal["runtime_incompatible"] = "runtime_incompatible"
        super().__init__(self.code)


def runtime_info_from_bindings(
    runtime_mode: object,
    build_revision: object,
    worker_version_id: object,
    python_version: str,
    sqlite_version: str,
) -> RuntimeInfo:
    """Validate explicit config and the executing Worker's own metadata binding."""
    if type(runtime_mode) is not str or runtime_mode not in ("local", "deployed"):
        raise RuntimeProvenanceError()
    if build_revision is not None and type(build_revision) is not str:
        raise RuntimeProvenanceError()
    if worker_version_id is not None and type(worker_version_id) is not str:
        raise RuntimeProvenanceError()
    try:
        parsed_id = None if worker_version_id is None else UUID(worker_version_id)
        return RuntimeInfo(
            python_version=python_version,
            sqlite_version=sqlite_version,
            runtime_mode=cast("RuntimeMode", runtime_mode),
            build_revision=build_revision,
            worker_version_id=parsed_id,
        )
    except (TypeError, ValueError, ValidationError):
        raise RuntimeProvenanceError() from None


class QueryServiceRequest(StrictModel):
    version: Literal["1"]
    job_id: UUID
    intent: SqlIntent

    @model_validator(mode="after")
    def enforce_wire_limits(self) -> "QueryServiceRequest":
        if self.intent.max_rows > 20:
            raise ValueError("invalid_input")
        try:
            if len(self.intent.sql.encode("utf-8")) > 8_000:
                raise ValueError("invalid_input")
        except UnicodeEncodeError:
            raise ValueError("invalid_input") from None
        return self


class ServiceHealth(RuntimeInfo):
    version: Literal["1"]
    engine_policy: Literal["m2-sqlite.v1"]


class MetadataField(StrictModel):
    name: str = Field(min_length=1, max_length=64)
    sql_type: Literal["TEXT", "INTEGER"]
    nullable: Literal[False]
    meaning: str = Field(min_length=1, max_length=256)


class ServiceMetadata(StrictModel):
    version: Literal["1"]
    source: SourceIdentity
    schema_revision: Literal["sales-proof.v1"]
    table: Literal["sales"]
    fields: list[MetadataField] = Field(min_length=7, max_length=7)
    profile: SalesProfile
    capabilities: list[Literal["query"]] = Field(min_length=1, max_length=1)
    dialect: Literal["sqlite"]
    engine_policy: Literal["m2-sqlite.v1"]
    limits: "QueryLimits"
    runtime: RuntimeInfo


class ServiceError(StrictModel):
    version: Literal["1"] = "1"
    code: ServiceErrorCode
    stage: Literal["input", "query", "transport"]
    job_id: UUID | None = None
    limit: None = None
    provider_reason: None = None
    automatic_retry: Literal[False] = False


class IntegerCell(StrictModel):
    type: Literal["integer"]
    value: Annotated[
        str,
        StringConstraints(strict=True, max_length=20, pattern=r"^-?(0|[1-9][0-9]*)$"),
    ]
    exact: Literal[True]

    @model_validator(mode="after")
    def fit_signed_int64(self) -> "IntegerCell":
        if not -(2**63) <= int(self.value) <= 2**63 - 1:
            raise ValueError("invalid_result")
        return self


class RealCell(StrictModel):
    type: Literal["real"]
    value: str = Field(strict=True, min_length=1, max_length=64)
    exact: Literal[False]

    @model_validator(mode="after")
    def use_finite_round_trip_text(self) -> "RealCell":
        try:
            number = float(self.value)
        except ValueError:
            raise ValueError("invalid_result") from None
        if not math.isfinite(number) or repr(number) != self.value:
            raise ValueError("invalid_result")
        return self


class TextCell(StrictModel):
    type: Literal["text"]
    value: str = Field(strict=True)

    @model_validator(mode="after")
    def bound_utf8_size(self) -> "TextCell":
        try:
            too_large = len(self.value.encode("utf-8")) > 256
        except UnicodeEncodeError:
            raise ValueError("invalid_result") from None
        if too_large:
            raise ValueError("invalid_result")
        return self


class NullCell(StrictModel):
    type: Literal["null"]
    value: Literal[None]


type ServiceCell = Annotated[
    IntegerCell | RealCell | TextCell | NullCell,
    Field(discriminator="type"),
]


def _valid_shape(columns: list[str], rows: list[list[ServiceCell]], row_count: int) -> bool:
    return (
        row_count == len(rows)
        and len(columns) == len(set(columns))
        and all(len(row) == len(columns) for row in rows)
    )


def _canonical_result_bytes(columns: list[str], rows: list[list[ServiceCell]]) -> bytes:
    try:
        if any(not column or len(column.encode("utf-8")) > 64 for column in columns):
            raise ValueError("invalid_result")
        content = {
            "columns": columns,
            "rows": [[cell.model_dump(mode="json") for cell in row] for row in rows],
        }
        return json.dumps(
            content, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (UnicodeError, ValueError, TypeError):
        raise ValueError("invalid_result") from None


class QueryLimits(StrictModel):
    max_sql_bytes: Literal[8000]
    max_rows: Literal[20]
    max_columns: Literal[16]
    max_column_bytes: Literal[64]
    max_text_bytes: Literal[256]
    max_result_bytes: Literal[16384]
    progress_interval: Literal[100]
    max_progress_callbacks: Literal[500]
    query_deadline_ms: Literal[250]
    sqlite_heap_bytes: Literal[8388608]
    sqlite_limits: dict[str, int]

    @model_validator(mode="after")
    def require_declared_sqlite_limits(self) -> "QueryLimits":
        if self.sqlite_limits != _SQLITE_LIMITS:
            raise ValueError("invalid_result")
        return self


class QueryResult(StrictModel):
    version: Literal["1"]
    receipt_id: UUID
    job_id: UUID
    source: SourceIdentity
    schema_revision: str = Field(strict=True, min_length=1, max_length=64)
    engine_policy: Literal["m2-sqlite.v1"]
    actual_sql: str = Field(strict=True, min_length=1, max_length=8000)
    sql_sha256: Digest
    columns: list[str] = Field(min_length=1, max_length=16)
    rows: list[list[ServiceCell]] = Field(max_length=20)
    row_count: int = Field(strict=True, ge=0, le=20)
    result_sha256: Digest
    coverage: Literal["complete_query_result"]
    truncated: Literal[False]
    analytical_validated: Literal[False]
    limits: QueryLimits
    runtime: RuntimeInfo

    @model_validator(mode="after")
    def validate_result_shape(self) -> "QueryResult":
        if not _valid_shape(self.columns, self.rows, self.row_count):
            raise ValueError("invalid_result")
        try:
            sql_bytes = self.actual_sql.encode("utf-8")
        except UnicodeError:
            raise ValueError("invalid_result") from None
        result_bytes = _canonical_result_bytes(self.columns, self.rows)
        if len(sql_bytes) > 8_000 or len(self.model_dump_json().encode("utf-8")) > 16_384:
            raise ValueError("result_limit")
        if sha256(sql_bytes).hexdigest() != self.sql_sha256:
            raise ValueError("invalid_result")
        if sha256(result_bytes).hexdigest() != self.result_sha256:
            raise ValueError("invalid_result")
        return self


_SQLITE_LIMITS = {name.lower(): value for name, value in _LIMITS}
M2_QUERY_LIMITS = QueryLimits(
    max_sql_bytes=8000,
    max_rows=20,
    max_columns=16,
    max_column_bytes=64,
    max_text_bytes=256,
    max_result_bytes=16384,
    progress_interval=100,
    max_progress_callbacks=500,
    query_deadline_ms=250,
    sqlite_heap_bytes=8388608,
    sqlite_limits=_SQLITE_LIMITS,
)


def adapt_query(
    request: QueryServiceRequest,
    engine: QueryEngine,
    runtime: RuntimeInfo,
) -> QueryResult:
    """Adapt a validated service request to the reusable Python engine contract."""
    execution = engine.execute(request.intent)
    return QueryResult(
        version="1",
        receipt_id=uuid4(),
        job_id=request.job_id,
        source=execution.source,
        schema_revision=execution.schema_revision,
        engine_policy="m2-sqlite.v1",
        actual_sql=execution.actual_sql,
        sql_sha256=execution.sql_sha256,
        columns=list(execution.content.columns),
        rows=[[_cell_payload(cell) for cell in row] for row in execution.content.rows],
        row_count=execution.content.row_count,
        result_sha256=execution.content.content_sha256,
        coverage="complete_query_result",
        truncated=False,
        analytical_validated=False,
        limits=M2_QUERY_LIMITS,
        runtime=runtime,
    )


def _cell_payload(cell: Cell) -> ServiceCell:
    return TypeAdapter(ServiceCell).validate_python(asdict(cell))

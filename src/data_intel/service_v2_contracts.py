"""Strict additive v2 service envelope and error contracts."""

import json
from hashlib import sha256
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

V2Digest = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-f0-9]{64}$")]
BuildRevision = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-f0-9]{40}$")]
RuntimeMode = Literal["local", "deployed"]
ServiceContractRevision = Literal["m4-service.v1"]


class V2StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("*", mode="before")
    @classmethod
    def reject_surrogate_text(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                raise ValueError("invalid_input") from None
        return value


def canonical_json(value: BaseModel) -> bytes:
    try:
        return json.dumps(
            value.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, UnicodeError, ValueError) as error:
        raise ValueError("invalid_result") from error


def payload_sha256(payload: BaseModel) -> str:
    return sha256(canonical_json(payload)).hexdigest()


class RuntimeProvenanceV2(V2StrictModel):
    python_version: str = Field(min_length=1, max_length=32)
    sqlite_version: str = Field(min_length=1, max_length=32)
    runtime_mode: RuntimeMode
    build_revision: BuildRevision | None = None
    worker_version_id: UUID | None = None
    service_contract_revision: ServiceContractRevision = "m4-service.v1"

    @model_validator(mode="after")
    def deployed_metadata_is_complete(self) -> "RuntimeProvenanceV2":
        if self.runtime_mode == "deployed" and (
            self.build_revision is None or self.worker_version_id is None
        ):
            raise ValueError("runtime_incompatible")
        return self


PayloadT = TypeVar("PayloadT", bound=BaseModel)


class ServiceEnvelopeV2(V2StrictModel, Generic[PayloadT]):  # noqa: UP046
    version: Literal["2"] = "2"
    job_id: UUID | None = None
    run_id: UUID | None = None
    receipt_id: UUID | None = None
    payload: PayloadT
    payload_sha256: V2Digest
    runtime: RuntimeProvenanceV2

    @model_validator(mode="after")
    def verify_payload_digest_and_size(self) -> "ServiceEnvelopeV2[PayloadT]":
        if self.payload_sha256 != payload_sha256(self.payload):
            raise ValueError("invalid_result")
        identifiers = (self.job_id, self.run_id, self.receipt_id)
        if any(identifier is not None for identifier in identifiers) and not all(
            identifier is not None for identifier in identifiers
        ):
            raise ValueError("invalid_input")
        if len(canonical_json(self)) > 16_384:
            raise ValueError("result_limit")
        return self


class ServiceLimitV2(V2StrictModel):
    name: str = Field(min_length=1, max_length=64)
    maximum: int = Field(strict=True, ge=1, le=65_536)


ServiceErrorCodeV2 = Literal[
    "invalid_input",
    "unsupported_version",
    "access_denied",
    "source_mismatch",
    "unsupported_source",
    "capability_mismatch",
    "invalid_query",
    "unsafe_query",
    "execution_limit",
    "result_limit",
    "invalid_result",
    "runtime_incompatible",
    "python_unavailable",
    "not_found",
    "needs_clarification",
    "planning_failed",
    "model_unavailable",
    "model_output_invalid",
    "candidate_invalid",
    "validation_failed",
    "publication_failed",
    "budget_exhausted",
    "stale_job",
    "publication_conflict",
    "state_limit",
    "provider_unavailable",
    "request_conflict",
    "request_outcome_unavailable",
    "evidence_unavailable",
    "source_switch_conflict",
]
ServiceStageV2 = Literal[
    "input",
    "catalog",
    "profile",
    "query",
    "search",
    "planning",
    "candidate",
    "validation",
    "publication",
    "budget",
    "transport",
]
ProviderReasonV2 = Literal["quota", "timeout", "unavailable", "malformed"]


class ServiceErrorV2(V2StrictModel):
    version: Literal["2"] = "2"
    code: ServiceErrorCodeV2
    stage: ServiceStageV2
    job_id: UUID | None = None
    run_id: UUID | None = None
    limit: ServiceLimitV2 | None = None
    provider_reason: ProviderReasonV2 | None = None
    automatic_retry: Literal[False] = False

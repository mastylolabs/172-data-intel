"""Deterministic citation checks over preverified targeted search receipts."""

import json
import re
from hashlib import sha256
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from data_intel.contracts import SourceIdentity
from data_intel.search_models import SearchReceiptV2, SearchRequestV2, search_payload_sha256
from data_intel.support_demo import SUPPORT_SOURCE

Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$", strict=True)]
MessageId = Annotated[str, StringConstraints(pattern=r"^M[0-9]{3}$", strict=True)]
Status = Literal["pass", "fail", "unsupported"]


class _Value(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class CitationBoundaryError(ValueError):
    """Safe refusal for oversized or malformed assertion input."""


class CitationV2(_Value):
    version: Literal["2"] = "2"
    citation_id: UUID
    source: SourceIdentity
    search_receipt_id: UUID
    search_payload_sha256: Digest
    message_id: MessageId
    quote: str = Field(min_length=1, max_length=500, strict=True)
    quote_sha256: Digest
    claim_id: UUID
    coverage: Literal["targeted_lexical_search"] = "targeted_lexical_search"

    @model_validator(mode="after")
    def bounded_quote(self) -> Self:
        if len(self.quote.encode("utf-8")) > 500:
            raise ValueError("quote_limit")
        return self


class CitationEvidenceV2(_Value):
    """Envelope ID and expected request come from the verified search execution."""

    receipt_id: UUID
    payload: SearchReceiptV2
    payload_sha256: Digest
    expected_request: SearchRequestV2

    @model_validator(mode="after")
    def verify_payload(self) -> Self:
        if self.payload.version != "2" or self.expected_request.version != "2":
            raise ValueError("policy_mismatch")
        if self.payload.source != SUPPORT_SOURCE or self.expected_request.source != SUPPORT_SOURCE:
            raise ValueError("source_mismatch")
        if self.payload.request != self.expected_request:
            raise ValueError("scope_mismatch")
        if (self.payload.schema_revision, self.payload.search_policy, self.payload.coverage) != (
            "support-demo.v1",
            "m3-lexical.v1",
            "targeted_lexical_search",
        ):
            raise ValueError("policy_mismatch")
        if self.payload_sha256 != search_payload_sha256(self.payload):
            raise ValueError("payload_mismatch")
        return self


class CitationCheckV2(_Value):
    name: Literal["citation"] = "citation"
    status: Status
    code: Annotated[str, StringConstraints(min_length=1, max_length=96, strict=True)]


class CitationCheckReportV2(_Value):
    version: Literal["2"] = "2"
    citation_id: UUID
    search_receipt_id: UUID
    checks: tuple[CitationCheckV2, ...] = Field(min_length=1, max_length=4)
    overall: Status
    policy_revision: Literal["m4-citation.v1"] = "m4-citation.v1"
    input_sha256: Digest
    report_sha256: Digest


_COVERAGE = re.compile(
    r"\b\d+(?:\.\d+)?\s*%|"
    r"\b(?:prevalen\w*|trend\w*|majority|most (?:common|frequent|customers|messages)|"
    r"absence|whole.corpus|entire corpus|nobody|never|half|quarter|third|"
    r"increas\w*|decreas\w*|rose|grew|fell|declin\w*|"
    r"(?:month|week|year)\s+after\s+(?:month|week|year)|no one\s+reported|"
    r"\d+(?:\.\d+)?\s*percent(?:age)?|"
    r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:out of|in)\s+"
    r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)|"
    r"(?:every|each|all|none|no|zero)\s+(?:of\s+the\s+)?"
    r"(?:\w+\s+){0,4}(?:customers?|messages?|support requests?|complaints?|issues?))\b",
    re.I,
)
_CAVEAT = re.compile(
    r"\b(?:cannot|can't|does not|do not)\s+"
    r"(?:establish|prove|show|measure|infer)\s+"
    r"(?:prevalence|trends?|absence|whole.corpus|entire corpus)\b",
    re.I,
)
_TARGETED = re.compile(
    r"(?:one|a|the|this|another) returned (?:message|example|hit)"
    r"(?: (?:mentions?|contains?) [a-z][a-z0-9_-]{0,63})?"
    r"[.!?]?|"
    r"this example (?:cannot|can't|does not|do not) "
    r"(?:establish|prove|show|measure|infer) "
    r"(?:prevalence|trends?|absence|whole.corpus|entire corpus)[.!?]?",
    re.I,
)


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise CitationBoundaryError("invalid_input") from None


def _digest(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def _returned_quote(citation: CitationV2, evidence: CitationEvidenceV2) -> str:
    if citation.version != "2" or citation.coverage != "targeted_lexical_search":
        raise ValueError("policy_mismatch")
    if citation.source != evidence.payload.source:
        raise ValueError("source_mismatch")
    if (citation.search_receipt_id, citation.search_payload_sha256) != (
        evidence.receipt_id,
        evidence.payload_sha256,
    ):
        raise ValueError("receipt_ref_mismatch")
    hit = next(
        (item for item in evidence.payload.hits if item.message_id == citation.message_id), None
    )
    if hit is None:
        raise ValueError("message_not_returned")
    return hit.quote


def _check(citation: CitationV2, evidence: CitationEvidenceV2, assertion: str) -> str:
    returned_quote = _returned_quote(citation, evidence)
    if sha256(citation.quote.encode("utf-8")).hexdigest() != citation.quote_sha256:
        raise ValueError("quote_hash_mismatch")
    if citation.quote not in returned_quote:
        raise ValueError("quote_mismatch")
    if _COVERAGE.search(_CAVEAT.sub("", assertion)) or not _TARGETED.fullmatch(assertion):
        raise ValueError("unsupported_coverage")
    return "exact_quote"


def validate_citation(
    citation: CitationV2, evidence: CitationEvidenceV2, assertion: str
) -> CitationCheckReportV2:
    """Validate an assertion supplied by a caller who binds it to citation.claim_id.

    Only explicit returned-message/example assertions pass. The frozen citation
    DTO carries the claim ID but no assertion text; the caller binds the two.
    """
    if not isinstance(assertion, str):
        raise CitationBoundaryError("invalid_input")
    try:
        assertion_size = len(assertion.encode("utf-8"))
    except UnicodeEncodeError:
        raise CitationBoundaryError("invalid_input") from None
    if not 1 <= assertion_size <= 1024:
        raise CitationBoundaryError("invalid_input")
    input_hash = _digest(
        {
            "citation": citation.model_dump(mode="json"),
            "evidence": evidence.model_dump(mode="json"),
            "assertion": assertion,
        }
    )
    try:
        code = _check(citation, evidence, assertion)
        status: Status = "pass"
    except ValueError as error:
        code = str(error)
        status = "unsupported" if code == "unsupported_coverage" else "fail"
    report = CitationCheckReportV2(
        citation_id=citation.citation_id,
        search_receipt_id=citation.search_receipt_id,
        checks=(CitationCheckV2(status=status, code=code),),
        overall=status,
        input_sha256=input_hash,
        report_sha256="0" * 64,
    )
    report_hash = _digest(report.model_dump(mode="json", exclude={"report_sha256"}))
    return report.model_copy(update={"report_sha256": report_hash})

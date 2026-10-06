"""Strict lexical request/evidence contracts; no source loading or search execution."""

import json
import re
from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from data_intel.contracts import SourceIdentity
from data_intel.profile_models import Count
from data_intel.support_demo import SupportMessage, _bounded_string

SearchLimitations = tuple[
    Literal[
        "Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence."
    ],
    Literal[
        "No hits means this lexical query found no matching messages "
        "in the declared filtered scope."
    ],
]
SEARCH_LIMITATIONS: SearchLimitations = (
    "Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence.",
    "No hits means this lexical query found no matching messages in the declared filtered scope.",
)
Token = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-z0-9]{1,32}$")]
Label = Annotated[str, AfterValidator(SupportMessage.bounded_label)]
UTCTimestamp = Annotated[str, AfterValidator(SupportMessage.canonical_timestamp)]
Quote = Annotated[str, AfterValidator(SupportMessage.bounded_text)]
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def ascii_tokens(value: str) -> tuple[str, ...]:
    """Distinct sorted ASCII words only; no stemming, Unicode folding or expansion."""
    return tuple(sorted(set(re.findall(r"[a-z0-9]+", value.translate(_ASCII_LOWER)))))


class _SearchValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SearchRequestV2(_SearchValue):
    version: Literal["2"] = "2"
    source: SourceIdentity
    query: str
    channel: Label | None = None
    customer: Label | None = None
    start: UTCTimestamp | None = None
    end: UTCTimestamp | None = None
    max_hits: int = Field(strict=True, ge=1, le=5)

    @field_validator("query")
    @classmethod
    def bounded_query(cls, value: str) -> str:
        _bounded_string(value, 128)
        tokens = ascii_tokens(value)
        if not 1 <= len(tokens) <= 8 or any(len(token) > 32 for token in tokens):
            raise ValueError("invalid query tokens")
        return value

    @model_validator(mode="after")
    def valid_interval(self) -> Self:
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("invalid time interval")
        canonical_search_json(self)
        return self


class SearchHit(_SearchValue):
    message_id: str = Field(min_length=4, max_length=4, pattern=r"^M[0-9]{3}$")
    timestamp: UTCTimestamp
    channel: Label
    customer: Label
    score: int = Field(strict=True, ge=1, le=8)
    matched_tokens: tuple[Token, ...] = Field(min_length=1, max_length=8)
    quote: Quote

    @model_validator(mode="after")
    def valid_token_score(self) -> Self:
        if self.matched_tokens != tuple(sorted(set(self.matched_tokens))):
            raise ValueError("invalid matched tokens")
        if self.score != len(self.matched_tokens):
            raise ValueError("invalid token score")
        return self


class SearchReceiptV2(_SearchValue):
    version: Literal["2"] = "2"
    source: SourceIdentity
    schema_revision: Literal["support-demo.v1"] = "support-demo.v1"
    search_policy: Literal["m3-lexical.v1"] = "m3-lexical.v1"
    request: SearchRequestV2
    scanned_count: Count
    matched_count: Count
    returned_count: int = Field(strict=True, ge=0, le=5)
    omitted_hit_count: Count
    hits: tuple[SearchHit, ...] = Field(max_length=5)
    coverage: Literal["targeted_lexical_search"] = "targeted_lexical_search"
    limitations: SearchLimitations = SEARCH_LIMITATIONS
    analytical_validated: Literal[False] = False

    @field_validator("analytical_validated", mode="before")
    @classmethod
    def strict_unvalidated(cls, value: object) -> bool:
        if type(value) is not bool:
            raise ValueError("nonboolean policy flag")
        return value

    @model_validator(mode="after")
    def consistent_receipt(self) -> Self:
        if self.source != self.request.source:
            raise ValueError("inconsistent source")
        if not self.scanned_count >= self.matched_count >= self.returned_count:
            raise ValueError("inconsistent search counts")
        expected_hits = min(self.matched_count, self.request.max_hits)
        if self.returned_count != len(self.hits) or self.returned_count != expected_hits:
            raise ValueError("inconsistent hit count")
        if self.omitted_hit_count != self.matched_count - self.returned_count:
            raise ValueError("inconsistent omitted hits")
        if len({hit.message_id for hit in self.hits}) != len(self.hits):
            raise ValueError("duplicate hits")
        query_tokens = set(ascii_tokens(self.request.query))
        if any(not set(hit.matched_tokens) <= query_tokens for hit in self.hits):
            raise ValueError("unrequested token matches")
        return self


class SearchContentError(ValueError):
    """Safe complete-content refusal, without request/evidence diagnostics."""

    def __init__(self, code: Literal["invalid_result", "result_limit"]) -> None:
        self.code = code
        super().__init__(code)


def canonical_search_json(value: SearchRequestV2 | SearchReceiptV2) -> bytes:
    """Key-sorted UTF-8; refuse the whole request/receipt rather than truncate."""
    try:
        content = json.dumps(
            value.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, UnicodeError) as error:
        raise SearchContentError("invalid_result") from error
    maximum = 2048 if isinstance(value, SearchRequestV2) else 8192
    if len(content) > maximum:
        raise SearchContentError("result_limit")
    return content


def search_payload_sha256(receipt: SearchReceiptV2) -> str:
    return sha256(canonical_search_json(receipt)).hexdigest()

"""Approved-source targeted lexical examples, never corpus trends or absence proof."""

from time import monotonic
from typing import Literal

from pydantic import ValidationError

from data_intel.contracts import SourceId
from data_intel.sales_fixture import FixtureError
from data_intel.search_models import (
    SearchContentError,
    SearchHit,
    SearchReceiptV2,
    SearchRequestV2,
    ascii_tokens,
    search_payload_sha256,
)
from data_intel.support_demo import (
    SUPPORT_FIELDS,
    SUPPORT_REVISION,
    SUPPORT_SOURCE,
    SupportDemo,
    SupportMessage,
    load_support_demo,
)

SEARCH_SECONDS = 0.1


class SearchFailure(RuntimeError):
    """Fixed safe codes; no source text, parser detail, paths or partial results."""

    def __init__(
        self,
        code: Literal[
            "invalid_input",
            "unsupported_version",
            "unsupported_source",
            "source_mismatch",
            "runtime_incompatible",
            "execution_limit",
            "invalid_result",
            "result_limit",
        ],
    ) -> None:
        self.code = code
        super().__init__(code)


def _check_deadline(deadline: float) -> None:
    if monotonic() >= deadline:
        raise SearchFailure("execution_limit")


def _eligible(row: SupportMessage, request: SearchRequestV2) -> bool:
    if request.channel is not None and row.channel != request.channel:
        return False
    if request.customer is not None and row.customer != request.customer:
        return False
    if request.start is not None and row.timestamp < request.start:
        return False
    return request.end is None or row.timestamp < request.end


def _matching_hit(row: SupportMessage, tokens: set[str]) -> SearchHit | None:
    matched = tuple(sorted(tokens.intersection(ascii_tokens(row.text))))
    if not matched:
        return None
    return SearchHit(
        message_id=row.message_id,
        timestamp=row.timestamp,
        channel=row.channel,
        customer=row.customer,
        score=len(matched),
        matched_tokens=matched,
        quote=row.text,
    )


def _validate_hits(receipt: SearchReceiptV2, rows: tuple[SupportMessage, ...]) -> None:
    by_id = {row.message_id: row for row in rows}
    query_tokens = set(ascii_tokens(receipt.request.query))
    for hit in receipt.hits:
        row = by_id.get(hit.message_id)
        if row is None or not _eligible(row, receipt.request):
            raise SearchFailure("invalid_result")
        if (hit.timestamp, hit.channel, hit.customer, hit.quote) != (
            row.timestamp,
            row.channel,
            row.customer,
            row.text,
        ):
            raise SearchFailure("invalid_result")
        matched = query_tokens.intersection(ascii_tokens(row.text))
        if set(hit.matched_tokens) != matched or hit.score != len(matched):
            raise SearchFailure("invalid_result")


def _search(fixture: SupportDemo, request: SearchRequestV2, deadline: float) -> SearchReceiptV2:
    """Private validated-fixture calculation; the public loader alone grants identity."""
    if (fixture.source, fixture.schema_revision, fixture.fields) != (
        SUPPORT_SOURCE,
        SUPPORT_REVISION,
        SUPPORT_FIELDS,
    ):
        raise SearchFailure("source_mismatch")
    if len(fixture.rows) > 256:
        raise SearchFailure("execution_limit")
    scanned = 0
    hits: list[SearchHit] = []
    tokens = set(ascii_tokens(request.query))
    for row in fixture.rows:
        _check_deadline(deadline)
        if _eligible(row, request):
            scanned += 1
            hit = _matching_hit(row, tokens)
            if hit is not None:
                hits.append(hit)
    hits.sort(key=lambda hit: hit.message_id)
    hits.sort(key=lambda hit: hit.timestamp, reverse=True)
    hits.sort(key=lambda hit: hit.score, reverse=True)
    selected = tuple(hits[: request.max_hits])
    receipt = SearchReceiptV2(
        source=fixture.source,
        request=request,
        scanned_count=scanned,
        matched_count=len(hits),
        returned_count=len(selected),
        omitted_hit_count=len(hits) - len(selected),
        hits=selected,
    )
    _validate_hits(receipt, fixture.rows)
    search_payload_sha256(receipt)
    _check_deadline(deadline)
    return receipt


def _request(request: SearchRequestV2) -> SearchRequestV2:
    if not isinstance(request, SearchRequestV2):
        raise SearchFailure("invalid_input")
    if request.version != "2":
        raise SearchFailure("unsupported_version")
    try:
        validated = SearchRequestV2.model_validate(request.model_dump())
    except (ValidationError, SearchContentError):
        raise SearchFailure("invalid_input") from None
    if validated.source.source_id != SourceId.SUPPORT:
        raise SearchFailure("unsupported_source")
    if validated.source != SUPPORT_SOURCE:
        raise SearchFailure("source_mismatch")
    return validated


def search_support(request: SearchRequestV2) -> SearchReceiptV2:
    """One approved bounded search with no retries, cached data or hidden expansion."""
    try:
        deadline = monotonic() + SEARCH_SECONDS
        validated = _request(request)
        fixture = load_support_demo(validated.source)
        return _search(fixture, validated, deadline)
    except FixtureError:
        raise SearchFailure("runtime_incompatible") from None
    except SearchContentError as error:
        raise SearchFailure(error.code) from None
    except ValidationError:
        raise SearchFailure("invalid_result") from None
    except MemoryError:
        raise SearchFailure("execution_limit") from None

"""Strict lexical contracts and independent canonical transport/mutation checks."""

import json
from hashlib import sha256

import pytest
from pydantic import ValidationError

from data_intel.search_models import (
    SEARCH_LIMITATIONS,
    SearchContentError,
    SearchHit,
    SearchReceiptV2,
    SearchRequestV2,
    ascii_tokens,
    canonical_search_json,
    search_payload_sha256,
)
from data_intel.support_demo import SUPPORT_SOURCE


def _request(**changes: object) -> SearchRequestV2:
    return SearchRequestV2.model_validate(
        {"source": SUPPORT_SOURCE, "query": "invoice", "max_hits": 5} | changes
    )


def _hit(**changes: object) -> SearchHit:
    return SearchHit.model_validate(
        {
            "message_id": "M001",
            "timestamp": "2026-03-01T09:00:00Z",
            "channel": "billing",
            "customer": "Acme",
            "score": 1,
            "matched_tokens": ("invoice",),
            "quote": " Exact invoice text. ",
        }
        | changes
    )


def _receipt(**changes: object) -> SearchReceiptV2:
    return SearchReceiptV2.model_validate(
        {
            "source": SUPPORT_SOURCE,
            "request": _request(max_hits=1),
            "scanned_count": 16,
            "matched_count": 2,
            "returned_count": 1,
            "omitted_hit_count": 1,
            "hits": (_hit(),),
        }
        | changes
    )


def test_canonical_receipt_preserves_exact_quotes_limits_and_independent_hash() -> None:
    receipt = _receipt()
    content = canonical_search_json(receipt)
    expected = json.dumps(
        receipt.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    assert content == expected and search_payload_sha256(receipt) == sha256(expected).hexdigest()
    assert json.loads(content)["hits"][0]["quote"] == " Exact invoice text. "
    assert receipt.limitations == SEARCH_LIMITATIONS and receipt.analytical_validated is False
    assert (
        receipt.coverage == "targeted_lexical_search" and receipt.search_policy == "m3-lexical.v1"
    )
    assert SearchReceiptV2.model_validate_json(content) == receipt
    for value in (receipt, receipt.hits[0], receipt.request):
        with pytest.raises(ValidationError, match="frozen"):
            value.source = SUPPORT_SOURCE  # type: ignore[union-attr]  # Test frozen models.


def test_empty_receipt_keeps_explicit_limitations_without_proving_absence() -> None:
    receipt = _receipt(matched_count=0, returned_count=0, omitted_hit_count=0, hits=())
    assert receipt.scanned_count == 16 and receipt.hits == ()
    assert len(receipt.limitations) == 2 and receipt.analytical_validated is False
    assert _request(channel="Unknown", customer="Unknown").channel == "Unknown"


def test_ascii_token_policy_uses_no_unicode_folding_stemming_or_expansion() -> None:
    assert ascii_tokens("CSV CSV csv-export Invoice42 \u212a K École İNV") == (
        "cole",
        "csv",
        "export",
        "invoice42",
        "k",
        "nv",
    )
    assert ascii_tokens("export exports exporting") == ("export", "exporting", "exports")
    assert _request(query="INVOICE invoice").query == "INVOICE invoice"
    assert len(ascii_tokens(_request(query="a b c d e f g h").query)) == 8
    assert _request(query="a" * 32).query == "a" * 32


@pytest.mark.parametrize(
    "change",
    [
        {"version": "1"},
        {"extra": 1},
        {"query": ""},
        {"query": "   "},
        {"query": "!?"},
        {"query": "É"},
        {"query": "a" * 33},
        {"query": "a b c d e f g h i"},
        {"query": "a " * 65},
        {"query": "a\u200b"},
        {"query": "a\ud800"},
        {"query": 1},
        {"channel": " billing"},
        {"channel": "a" * 65},
        {"customer": "Acme "},
        {"customer": "\n"},
        {"max_hits": True},
        {"max_hits": "1"},
        {"max_hits": 0},
        {"max_hits": 6},
        {"max_hits": 1.0},
        {"start": "2026-02-30T09:00:00Z"},
        {"end": "2026-03-01T09:00:00.1Z"},
        {"start": "2026-03-01T09:00:00+00:00"},
        {"start": "2026-03-02T00:00:00Z", "end": "2026-03-01T00:00:00Z"},
        {"start": "2026-03-01T00:00:00Z", "end": "2026-03-01T00:00:00Z"},
    ],
)
def test_requests_refuse_malformed_types_bounds_tokens_and_intervals(
    change: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        _request(**change)


@pytest.mark.parametrize(
    "change",
    [
        {"message_id": "M01"},
        {"timestamp": "2026-03-01T24:00:00Z"},
        {"score": True},
        {"score": 0},
        {"score": 9},
        {"score": 2},
        {"matched_tokens": ()},
        {"matched_tokens": ("INVOICE",)},
        {"matched_tokens": ("invoice", "invoice")},
        {"matched_tokens": ("z", "a")},
        {"quote": None},
        {"quote": " "},
        {"quote": "x" * 501},
        {"quote": "\u0000"},
        {"channel": ""},
        {"extra": "untrusted"},
    ],
)
def test_hit_fields_tokens_and_scores_reject_mutations(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _hit(**change)


@pytest.mark.parametrize(
    "change",
    [
        {"version": "1"},
        {"schema_revision": "support-demo.v2"},
        {"source": SUPPORT_SOURCE.model_copy(update={"snapshot_sha256": "a" * 64})},
        {"scanned_count": True},
        {"scanned_count": -1},
        {"scanned_count": 257},
        {"scanned_count": 1},
        {"matched_count": 0},
        {"returned_count": 0},
        {"returned_count": 0, "omitted_hit_count": 2, "hits": ()},
        {"returned_count": 6},
        {"omitted_hit_count": 0},
        {"analytical_validated": 0},
        {"analytical_validated": True},
        {"search_policy": "semantic"},
        {"coverage": "whole_corpus"},
        {"limitations": ("No issue exists.",)},
        {"extra": 1},
        {
            "request": _request(max_hits=1),
            "returned_count": 2,
            "omitted_hit_count": 0,
            "hits": (_hit(), _hit(message_id="M002")),
        },
        {
            "request": _request(),
            "returned_count": 2,
            "omitted_hit_count": 0,
            "hits": (_hit(), _hit()),
        },
        {"hits": (_hit(matched_tokens=("login",)),)},
    ],
)
def test_receipts_reject_false_policy_counts_source_and_coverage(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _receipt(**change)


def test_utf8_request_and_quote_boundaries_remain_exact() -> None:
    query = "a " + "é" * 63
    request = _request(
        query=query,
        channel="é" * 32,
        customer="A" * 64,
        start="2026-03-01T00:00:00Z",
        end="2026-03-02T00:00:00Z",
    )
    assert request.query == query and len(query.encode()) == 128
    assert b"\xc3\xa9" in canonical_search_json(request)
    assert _hit(quote="é" * 250).quote == "é" * 250


def test_complete_payload_byte_limits_and_invalid_unicode_fail_safely() -> None:
    receipt = _receipt()
    size = len(canonical_search_json(receipt))
    padded = receipt.model_copy(update={"schema_revision": "x" * (8192 - size + 15)})
    assert len(canonical_search_json(padded)) == 8192
    invalid = padded.model_copy(update={"schema_revision": padded.schema_revision + "x"})
    with pytest.raises(SearchContentError, match=r"^result_limit$"):
        search_payload_sha256(invalid)
    for value in (
        _request().model_copy(update={"query": "x" * 2049}),
        receipt.model_copy(update={"schema_revision": "\ud800"}),
    ):
        with pytest.raises(SearchContentError) as error:
            canonical_search_json(value)
        assert str(error.value) == error.value.code

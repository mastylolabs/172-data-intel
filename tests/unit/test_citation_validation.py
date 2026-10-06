"""Exact support citation checks against returned lexical hits."""

import json
from hashlib import sha256
from uuid import UUID

import pytest
from pydantic import ValidationError

from data_intel.citation_validation import (
    CitationBoundaryError,
    CitationEvidenceV2,
    CitationV2,
    validate_citation,
)
from data_intel.sales_fixture import SALES_SOURCE
from data_intel.search_models import SearchRequestV2, search_payload_sha256
from data_intel.support_demo import SUPPORT_SOURCE
from data_intel.support_search import search_support

ID = UUID("20fdc73a-5ac2-4ee4-a6f8-a3f175455f7b")
CLAIM_ID = UUID("f3261002-7769-4d82-acf9-83a41a14e5f5")


def _case(query: str = "export") -> tuple[CitationV2, CitationEvidenceV2]:
    request = SearchRequestV2(source=SUPPORT_SOURCE, query=query, max_hits=2)
    receipt = search_support(request)
    evidence = CitationEvidenceV2(
        receipt_id=ID,
        payload=receipt,
        payload_sha256=search_payload_sha256(receipt),
        expected_request=request,
    )
    quote = receipt.hits[0].quote[:20] if receipt.hits else "not returned"
    citation = CitationV2(
        citation_id=ID,
        source=SUPPORT_SOURCE,
        search_receipt_id=ID,
        search_payload_sha256=evidence.payload_sha256,
        message_id=receipt.hits[0].message_id if receipt.hits else "M015",
        quote=quote,
        quote_sha256=sha256(quote.encode()).hexdigest(),
        claim_id=CLAIM_ID,
    )
    return citation, evidence


def test_exact_substring_and_report_hash_bind_complete_receipt() -> None:
    citation, evidence = _case()
    report = validate_citation(citation, evidence, "One returned message mentions exports.")
    assert report.overall == "pass" and report.checks[0].code == "exact_quote"
    content = json.dumps(
        report.model_dump(mode="json", exclude={"report_sha256"}),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    assert report.report_sha256 == sha256(content.encode()).hexdigest()
    assert report.policy_revision == "m4-citation.v1"
    assert (
        report.input_sha256
        != validate_citation(citation, evidence, "Another example.").input_sha256
    )


def test_foreign_receipts_ids_source_and_scope_refuse() -> None:
    citation, evidence = _case()
    changes = (
        ({"message_id": "M001"}, "message_not_returned"),
        ({"source": SALES_SOURCE}, "source_mismatch"),
        ({"search_receipt_id": CLAIM_ID}, "receipt_ref_mismatch"),
        ({"search_payload_sha256": "0" * 64}, "receipt_ref_mismatch"),
        ({"coverage": "other"}, "policy_mismatch"),
    )
    for change, code in changes:
        assert (
            validate_citation(citation.model_copy(update=change), evidence, "A returned example.")
            .checks[0]
            .code
            == code
        )
    wrong_request = evidence.expected_request.model_copy(update={"customer": "Acme"})
    with pytest.raises(ValidationError, match="scope_mismatch"):
        CitationEvidenceV2.model_validate(evidence.__dict__ | {"expected_request": wrong_request})
    with pytest.raises(ValidationError, match="payload_mismatch"):
        CitationEvidenceV2.model_validate(evidence.__dict__ | {"payload_sha256": "0" * 64})
    with pytest.raises(ValidationError, match="policy_mismatch"):
        changed_receipt = evidence.payload.model_copy(update={"search_policy": "other"})
        CitationEvidenceV2.model_validate(evidence.__dict__ | {"payload": changed_receipt})


def test_quote_bytes_case_and_whitespace_are_exact() -> None:
    citation, evidence = _case()
    for quote in (citation.quote.upper(), citation.quote + " ", " " + citation.quote):
        changed = citation.model_copy(
            update={"quote": quote, "quote_sha256": sha256(quote.encode()).hexdigest()}
        )
        assert validate_citation(changed, evidence, "A returned example.").overall == "fail"
    wrong_hash = citation.model_copy(update={"quote_sha256": "0" * 64})
    assert (
        validate_citation(wrong_hash, evidence, "A returned example.").checks[0].code
        == "quote_hash_mismatch"
    )
    with pytest.raises(ValidationError):
        CitationV2.model_validate(citation.model_dump(mode="json") | {"quote": "é" * 251})


@pytest.mark.parametrize(
    "assertion",
    [
        "Most customers have export problems.",
        "The prevalence of export complaints is high.",
        "Export complaints are trending upward.",
        "There are no export complaints in the entire corpus.",
        "There are no export complaints.",
        "90% of customers have export problems.",
        "Nine out of ten customers have export problems.",
        "9 out of 10 support requests mention exports.",
        "Every customer mentions exports.",
        "Each support request mentions exports.",
        "All messages mention exports.",
        "None of the complaints mention exports.",
        "No customers mention exports.",
        "Half of customers mention exports.",
        "A quarter of complaints mention exports.",
        "A third of support requests mention exports.",
        "One in three customers mention exports.",
        "9 in 10 customers mention exports.",
        "No one reported an export issue.",
        "All export issues were resolved.",
        "Zero export issues were resolved.",
        "Export complaints increased.",
        "Export complaints decreased.",
        "Export complaints rose.",
        "Export complaints grew.",
        "Export complaints fell.",
        "Export complaints declined.",
        "Export complaints appeared month after month.",
        "Export complaints appeared week after week.",
        "Export complaints appeared year after year.",
    ],
)
def test_targeted_quote_cannot_prove_corpus_claims(assertion: str) -> None:
    citation, evidence = _case()
    report = validate_citation(citation, evidence, assertion)
    assert report.overall == "unsupported" and report.checks[0].code == "unsupported_coverage"


def test_caveat_and_no_hits_refuse_or_pass_only_as_targeted_evidence() -> None:
    citation, evidence = _case()
    assert (
        validate_citation(citation, evidence, "This example cannot establish prevalence.").overall
        == "pass"
    )
    missing, empty = _case("zebra")
    assert (
        validate_citation(missing, empty, "No returned example.").checks[0].code
        == "message_not_returned"
    )
    with pytest.raises(CitationBoundaryError, match="invalid_input"):
        validate_citation(citation, evidence, "x" * 1025)
    with pytest.raises(CitationBoundaryError, match="invalid_input"):
        validate_citation(citation, evidence, "\ud800")

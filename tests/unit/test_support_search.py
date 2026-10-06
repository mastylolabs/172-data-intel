"""Independently known lexical IDs/counts, exact quotes and guarded failures."""

import json
import re
import warnings
from dataclasses import replace
from hashlib import sha256
from typing import cast
from unittest.mock import Mock

import pytest

from data_intel import support_search
from data_intel.contracts import SourceId
from data_intel.sales_fixture import FixtureError
from data_intel.search_models import (
    SEARCH_LIMITATIONS,
    SearchReceiptV2,
    SearchRequestV2,
    canonical_search_json,
    search_payload_sha256,
)
from data_intel.support_demo import SUPPORT_PATH, SUPPORT_SOURCE, SupportMessage, load_support_demo
from data_intel.support_search import SearchFailure, search_support


def _request(**changes: object) -> SearchRequestV2:
    return SearchRequestV2.model_validate(
        {"source": SUPPORT_SOURCE, "query": "export", "max_hits": 5} | changes
    )


def _assert_exact_source_hits(receipt: SearchReceiptV2) -> None:
    rows: dict[str, dict[str, str]] = {
        row["message_id"]: row for row in map(json.loads, SUPPORT_PATH.read_text().splitlines())
    }
    tokens = set(re.findall("[a-z0-9]+", receipt.request.query.lower()))
    for hit in receipt.hits:
        row = rows[hit.message_id]
        assert (hit.quote, hit.timestamp, hit.customer, hit.channel) == (
            row["text"],
            row["timestamp"],
            row["customer"],
            row["channel"],
        )
        expected = tuple(sorted(tokens.intersection(re.findall("[a-z0-9]+", row["text"].lower()))))
        assert hit.matched_tokens == expected and hit.score == len(expected)


@pytest.mark.parametrize(
    "change,ids,scanned,matched",
    [
        ({}, ("M015", "M012", "M009", "M005", "M002"), 16, 5),
        ({"query": "login"}, ("M013", "M006", "M003"), 16, 3),
        ({"query": "billing"}, ("M014", "M010", "M007", "M004", "M001"), 16, 5),
        ({"query": "invoice duplicate"}, ("M014", "M001", "M010", "M007", "M004"), 16, 5),
        ({"query": "EXPORT export", "max_hits": 2}, ("M015", "M012"), 16, 5),
        ({"query": "exports"}, (), 16, 0),
        ({"query": "zebra"}, (), 16, 0),
        ({"customer": "Acme"}, ("M009", "M005"), 4, 2),
        ({"channel": "billing"}, (), 5, 0),
        ({"channel": "Billing"}, (), 0, 0),
        ({"customer": "Unknown"}, (), 0, 0),
        ({"start": "2026-03-05T11:00:00Z", "end": "2026-03-09T13:00:00Z"}, ("M005",), 4, 1),
    ],
)
def test_known_queries_filters_and_period_edges_match_independent_oracles(
    change: dict[str, object], ids: tuple[str, ...], scanned: int, matched: int
) -> None:
    request = _request(**change)
    receipt = search_support(request)
    assert tuple(hit.message_id for hit in receipt.hits) == ids
    assert (
        receipt.scanned_count,
        receipt.matched_count,
        receipt.returned_count,
        receipt.omitted_hit_count,
    ) == (scanned, matched, len(ids), matched - len(ids))
    assert receipt.source == SUPPORT_SOURCE and receipt.schema_revision == "support-demo.v1"
    assert receipt.search_policy == "m3-lexical.v1" and receipt.analytical_validated is False
    assert (
        receipt.limitations == SEARCH_LIMITATIONS and receipt.coverage == "targeted_lexical_search"
    )
    _assert_exact_source_hits(receipt)
    content = canonical_search_json(receipt)
    assert len(content) <= 8192 and search_payload_sha256(receipt) == sha256(content).hexdigest()
    assert SearchReceiptV2.model_validate_json(content) == receipt


def test_timestamp_and_id_ties_and_complete_quotes_keep_source_order_independent() -> None:
    base = load_support_demo()
    rows = tuple(
        base.rows[0].model_copy(update={"message_id": message_id, "text": " export export "})
        for message_id in ("M003", "M001", "M002")
    )
    receipt = support_search._search(replace(base, rows=rows), _request(max_hits=2), float("inf"))
    assert tuple(hit.message_id for hit in receipt.hits) == ("M001", "M002")
    assert receipt.matched_count == 3 and receipt.omitted_hit_count == 1
    assert all(hit.quote == " export export " and hit.score == 1 for hit in receipt.hits)


@pytest.mark.parametrize(
    "change,code",
    [
        ({"query": "!?"}, "invalid_input"),
        ({"query": "É"}, "invalid_input"),
        ({"query": "a" * 33}, "invalid_input"),
        ({"max_hits": True}, "invalid_input"),
        ({"query": {"raw": "private_query_sentinel"}}, "invalid_input"),
        ({"max_hits": "private_limit_sentinel"}, "invalid_input"),
        ({"version": "1"}, "unsupported_version"),
        (
            {"source": SUPPORT_SOURCE.model_copy(update={"source_id": SourceId.SALES})},
            "unsupported_source",
        ),
        (
            {"source": SUPPORT_SOURCE.model_copy(update={"meaning_revision": "support-demo.v2"})},
            "source_mismatch",
        ),
        (
            {"source": SUPPORT_SOURCE.model_copy(update={"snapshot_sha256": "f" * 64})},
            "source_mismatch",
        ),
    ],
)
def test_copied_input_and_identity_fail_before_loader(
    change: dict[str, object], code: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    loader = Mock(side_effect=AssertionError("must not read"))
    monkeypatch.setattr(support_search, "load_support_demo", loader)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        with pytest.raises(SearchFailure) as error:
            search_support(_request().model_copy(update=change))
    assert str(error.value) == error.value.code == code
    assert not captured
    assert "private_" not in str(error.value)
    loader.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        FixtureError("fixture_missing"),
        FixtureError("fixture_invalid"),
        FixtureError("source_mismatch"),
        MemoryError("secret"),
    ],
)
def test_loader_failures_have_safe_codes_no_retry(
    failure: Exception, monkeypatch: pytest.MonkeyPatch
) -> None:
    loader = Mock(side_effect=failure)
    monkeypatch.setattr(support_search, "load_support_demo", loader)
    expected = "execution_limit" if isinstance(failure, MemoryError) else "runtime_incompatible"
    with pytest.raises(SearchFailure, match=f"^{expected}$"):
        search_support(_request())
    loader.assert_called_once_with(SUPPORT_SOURCE)


@pytest.mark.parametrize("ticks", [[0.0, 0.1], [0.0, 0.0, 0.1], [0.0] * 17 + [0.1]])
def test_deadline_expires_before_during_or_after_scan_without_partial_receipt(
    ticks: list[float], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(support_search, "monotonic", Mock(side_effect=ticks))
    with pytest.raises(SearchFailure, match=r"^execution_limit$"):
        search_support(_request())


def test_invalid_record_budget_metadata_and_typed_inputs_refuse() -> None:
    base = load_support_demo()
    for fixture, code in (
        (replace(base, schema_revision="support-demo.v2"), "source_mismatch"),
        (replace(base, rows=base.rows * 17), "execution_limit"),
    ):
        with pytest.raises(SearchFailure, match=f"^{code}$"):
            support_search._search(fixture, _request(), float("inf"))
    with pytest.raises(SearchFailure, match=r"^invalid_input$"):
        search_support(cast("SearchRequestV2", None))
    empty = support_search._search(replace(base, rows=()), _request(), float("inf"))
    assert (empty.scanned_count, empty.matched_count, empty.returned_count) == (0, 0, 0)


@pytest.mark.parametrize(
    "change",
    [
        {"quote": "Fabricated export."},
        {"message_id": "M999"},
        {"matched_tokens": ("wrong",)},
        {"score": 2},
        {"channel": "billing"},
    ],
)
def test_returned_hit_integrity_refuses_fabricated_source_cells_and_scores(
    change: dict[str, object],
) -> None:
    receipt = search_support(_request(max_hits=1))
    altered = receipt.model_copy(update={"hits": (receipt.hits[0].model_copy(update=change),)})
    with pytest.raises(SearchFailure, match=r"^invalid_result$"):
        support_search._validate_hits(altered, load_support_demo().rows)
    filtered = receipt.model_copy(update={"request": _request(customer="Acme")})
    with pytest.raises(SearchFailure, match=r"^invalid_result$"):
        support_search._validate_hits(filtered, load_support_demo().rows)


def test_serializer_cap_and_invalid_loaded_row_map_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = search_support(_request())
    # Inject malformed constructor output; the real canonical serializer still enforces its cap.
    oversized = receipt.model_copy(update={"schema_revision": "x" * 8192})
    monkeypatch.setattr(support_search, "SearchReceiptV2", Mock(return_value=oversized))
    with pytest.raises(SearchFailure, match=r"^result_limit$"):
        search_support(_request())
    monkeypatch.undo()
    base = load_support_demo()
    bad_row: SupportMessage = base.rows[0].model_copy(update={"text": "export " * 72})
    monkeypatch.setattr(
        support_search, "load_support_demo", Mock(return_value=replace(base, rows=(bad_row,)))
    )
    with pytest.raises(SearchFailure, match=r"^invalid_result$"):
        search_support(_request())

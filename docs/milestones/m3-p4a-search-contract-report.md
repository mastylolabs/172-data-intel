# M3-P4a search contract milestone report

## Result

M3-P4a is complete and merged in [PR #35](https://github.com/mastylolabs/172-data-intel/pull/35). It freezes strict `SearchRequestV2`, `SearchHitV2` and `SearchReceiptV2` contracts, deterministic ASCII token policy, exact filter/request/source invariants, fixed coverage limitations, canonical UTF-8 serialization and payload hashing with an 8,192-byte receipt ceiling. It does not scan the support corpus or publish search results. The merged `main` revision is `e4ddb81810659ffb06f9f92f7f400816a793a370`.

A provider review found and required one correction before merge: receipts now require `returned_count == min(matched_count, max_hits)`, so positive matches cannot be silently omitted when capacity remains. The corrected head added a discriminating regression and an independent 180-case count matrix.

## Verification

- Corrected-head CI passed twice: runs `37415713134` and `37415717053`.
- Independent QA PASS: local receipt `.git/172x/m3-p4a-qa.md` (not committed; implementation/provider evidence is on [PR #35](https://github.com/mastylolabs/172-data-intel/pull/35)). Fresh detached gate passed 534 Python tests and 40 Vitest tests, strict mypy, Ruff/format, TypeScript and Radon A (average 2.984; all functions A/B).
- Independent review PASS: local receipt `.git/172x/m3-p4a-review.md` (not committed); the initial provider finding and corrected-head verification are recorded there. Provider approval and guarded merge are on [PR #35](https://github.com/mastylolabs/172-data-intel/pull/35).
- New search-model coverage: 100% (98/98 statements, 24/24 branches). Combined QA coverage is 94.5704%; later execution/service/build gaps remain.
- Independent ASCII token and canonical JSON/hash oracles passed. The 8,192-byte canonical payload boundary is tested at 8,192 accepted and 8,193 refused. Raw transport admission is intentionally a later service boundary.
- Scope count: 399 handwritten changed lines and 18 prose lines excluded under AGENTS.md. No search loader scan, service route, model/UI or deployment change.

## Problems and limits

The first provider review exposed a real invariant gap: a positive match could have an empty hit list. The contract was corrected before merge, the stale provider thread was resolved after fresh QA/review, and the corrected head passed all gates. Source-backed retrieval, deadline handling, exact quote production, citation validation and deployed behavior remain unverified.

## Hardest technical problem

The hardest problem was making the receipt itself enforce evidence completeness without coupling it to an execution implementation. Strict request/receipt models validate source identity, filter/count consistency, token bounds, fixed limitations, immutable hits and canonical payload limits. The corrected count invariant prevents silent omission while still allowing deliberate top-hit omission only when `matched_count` exceeds `max_hits`.

## Next milestone

Proceed with P4b: execute targeted lexical search over the approved support corpus using these contracts. It must apply the frozen tokenization/ranking/filter/deadline rules, return complete exact quotes and IDs, enforce scan/result limits and hashes, and preserve the explicit limits against trend, prevalence or absence claims. The user’s existing full-go authorization covers continuation; P4b remains separately reviewed with its own QA, report and merge gates.

# M3-P6 milestone report: deterministic support citations

Date: 2026-10-06

## Delivered behavior

PR #42 ([merged pull request](https://github.com/mastylolabs/172-data-intel/pull/42)) adds strict `CitationV2`, verified search evidence, exact returned message IDs and quotes, source/request/policy/payload bindings, quote hashes, bounded safe input errors, and `CitationCheckReportV2` hashes. Unsupported prevalence, trend, absence, and whole-corpus assertions use a default-deny targeted sentence policy; only explicit returned-message/example statements or the supported caveat can pass. The verified main revision is `294b575134c4595e89d14f1bb10a12a383cb5af5`.

## Problems and resolutions

Independent QA found that a finite keyword deny-list allowed natural-language paraphrases of corpus claims. The validator now defaults to a narrow targeted assertion grammar, with real-receipt regressions for standalone and embedded prevalence, trend, and absence claims. QA also found lone-surrogate input escaping as `UnicodeEncodeError`; the boundary now returns `CitationBoundaryError("invalid_input")`. The caller-to-`claim_id` association remains an explicit P7/M4 candidate-envelope obligation because the frozen P6 DTO carries the ID but not assertion text.

## Hardest technical problem

The hardest problem was preventing one exact support quote from being treated as population evidence. A deny-list cannot classify arbitrary model prose safely, so the implementation chose a small default-deny grammar for targeted examples and tested it against mutated real search receipts. This fails closed and keeps semantic entailment in the later Analyst/Validator boundary.

## Verification

- `make gate`: PASS; 624 Python tests, 40 Vitest tests, Ruff, mypy, TypeScript and Radon (average A; no C-or-worse functions).
- `make coverage`: PASS; 1,551 Python statements, 438 branches, 93% total branch-aware coverage. `citation_validation.py`: 92% (30 branches, 4 partial branches). Remaining gaps include malformed DTO branches, a few safe failure branches and the unimplemented private service/runtime consumers.
- PR #42 exact-head QA: PASS at `c7900a2`; exact-head independent review: APPROVED; configured provider review and approval: PASS; two provider threads resolved; guards passed before merge.
- Integration/deployed checks: real local `search_support` receipts and mutation probes passed. No P6 private v2 route, Agent claim binding, live model call, or deployed citation validation was run; those are downstream acceptance work.

## Next milestone

M3-P7 should add the private v2 service envelopes and consumer parity for catalog, profile, query, search, and numerical/citation validation while preserving all v1 routes and existing deployments. It must prove source/runtime/hash/job bindings and refuse malformed, oversized, cross-version, and public requests before M4 Agent orchestration.

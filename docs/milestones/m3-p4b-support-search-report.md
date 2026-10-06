# M3-P4b support search milestone report

## Result

M3-P4b is complete and merged in [PR #37](https://github.com/mastylolabs/172-data-intel/pull/37). The private search boundary now scans the approved support corpus with deterministic ASCII token matching, exact case-sensitive filters and UTC half-open periods, stable score/time/ID ranking, complete exact quotes, filter-scoped counts, bounded top hits, canonical payload hashes, a 100 ms deadline and safe fixed failures. It validates returned hits against the loaded source before publication and preserves the explicit limitations that targeted lexical examples cannot establish trends, prevalence or absence. The merged `main` revision is `82eb529c9bc90073fa44a44461dcaefe39b8297c`.

## Verification

- Corrected-head CI passed twice: runs `37417688765` and `37417694113`.
- Independent QA PASS: local receipt `.git/172x/m3-p4b-qa.md` (not committed; implementation/provider evidence is on [PR #37](https://github.com/mastylolabs/172-data-intel/pull/37)). Fresh detached gate passed 571 Python tests and 40 Vitest tests, strict mypy, Ruff/format, TypeScript and Radon A (average 3.0204; all functions A/B).
- Independent review PASS: local receipt `.git/172x/m3-p4b-review.md` (not committed); the initial warning-leak finding and corrected-head verification are recorded there. Provider approval and guarded merge are on [PR #37](https://github.com/mastylolabs/172-data-intel/pull/37).
- New search execution coverage: 100% (92/92 statements, 36/36 branches). Combined QA coverage is 95.0095%; existing service/build/FFI gaps remain.
- Independent QA ran 1,280 oracle combinations covering character/token behavior, IDs, quotes, scores, counts, order, filters, ties, deadlines, identity and result limits. Corrected-head QA also ran six malformed copied-request variants with zero warnings, zero stderr, no raw sentinel and no loader I/O.
- Scope count: 388 handwritten changed lines and 29 prose lines excluded under AGENTS.md. No service route, model/UI, dependency or deployment change.

## Problems and limits

The first review found that Pydantic serialization warnings leaked raw copied query/max-hit values before safe rejection. The corrected boundary uses warning-free revalidation and has explicit zero-warning/no-I/O regressions. Search remains private and local; v2 service exposure, citation validation, native Agent/UI integration, live model calls and deployed behavior are unverified.

## Hardest technical problem

The hardest part was keeping targeted retrieval evidence trustworthy when both requests and source text are untrusted. The search starts its deadline before validation/loading, authorizes the complete identity, scans only eligible loaded rows, ranks distinct token matches deterministically, validates every selected hit against the original row and request filters, and hashes only the bounded canonical receipt. This prevents fabricated quotes, hidden filtering, silent result omission and unsupported whole-corpus claims.

## Next milestone

Proceed with the private v2 Python service boundary for catalog/profile/query/search envelopes, preserving v1 proof behavior and adding strict job IDs, runtime provenance, payload hashes, streamed body/result limits and safe v2 errors. This remains a separate reviewed milestone before native Agent coordination and web chat. The user’s existing full-go authorization covers continuation with the same independent QA, review, provider and guarded-merge gates.

# M3-P2c sales query milestone report

## Result

M3-P2c is complete and merged in [PR #31](https://github.com/mastylolabs/172-data-intel/pull/31). The private query engine now supports the approved `sales-demo.v1` identity through an explicit trusted opt-in while retaining the existing proof-only default used by the v1 service. The engine reuses the existing read-only SQLite authorizer, progress/heap/statement limits, bounded result content and exact hashes. The merged `main` revision is `5e4246efd893b5be81d666a5e0189d7c3e2696b6`.

The demo path was tested for whole-source totals, monthly grouping, customer ranking and ties, period comparisons, returns, zero values, half-open date filters, empty aggregates, invalid SQL, unsafe SQL, result/execution limits, full identity mismatch, isolated connections and safe loader failures. The profile now advertises `query` only after this reviewed integration. Existing v1 service metadata/routes/contracts and proof-fixture behavior remain unchanged.

## Verification

- Current-head CI passed twice: runs `37412037206` and `37412052297`.
- Independent QA PASS: local receipt `.git/172x/m3-p2c-qa.md` (not committed; implementation and provider evidence are on [PR #31](https://github.com/mastylolabs/172-data-intel/pull/31)). Fresh detached gate passed 403 Python tests and 40 Vitest tests, strict mypy, Ruff/format, TypeScript and Radon A (average 2.9599; all functions A/B).
- Independent review PASS: local receipt `.git/172x/m3-p2c-review.md` (not committed); no MF, NH or Q findings. Provider review and approval are recorded on [PR #31](https://github.com/mastylolabs/172-data-intel/pull/31).
- Combined Python coverage measured by QA: 93.5405%; the new context and profiler paths are 100%, and new query-engine changes are covered. Existing query/service/build/FFI gaps remain.
- Independent standard-library CSV calculations reproduced January `(8, 7, 105000)`, February `(8, 12, 140000)`, March `(8, 10, 150000)`, customer cents `Acme 100000, Cedar 80000, Bright 75000, Delta 60000, Elm 40000, Fjord 40000`, period differences `35000` and `10000`, returns `(4, -4, -45000)`, zeros `D004/D014/D023`, and novel filtered results.
- Scope count: 255 handwritten changed lines; 22 README/TODO prose lines excluded under AGENTS.md. No new dependency, fixture, v1 route, TypeScript contract or deployment change.

## Problems and limits

The existing v1 service constructs the default query engine directly. Making that default accept the demo would have silently changed the v1 service source behavior, so the implementation uses an explicit `allow_demo_source` opt-in for later private/v2 callers. Deployed demo querying, v2 service exposure, support search, validation, model calls, UI and Cloudflare deployment remain unverified and outside this slice.

## Hardest technical problem

The hardest problem was extending generic execution without weakening the approved-source boundary. The context now resolves either complete registered sales identity before reading its fixed path, builds an isolated in-memory database, and reuses the same authorizer and bounded result controls. The engine refuses the demo before context access unless a trusted caller opts in, preserving v1 compatibility while enabling the next private integration.

## Next milestone

Proceed with the next bounded M3 capability: load the exact 16-message support corpus under its byte/hash/schema contract, then add targeted lexical retrieval with message IDs, complete exact quotes, deterministic ranking and explicit coverage limitations. The user’s existing full-go authorization covers continuation; this remains a proposed, separately reviewed milestone with its own QA, report and merge gates.

# M3-P2b sales profiler milestone report

## Result

M3-P2b is complete and merged in [PR #29](https://github.com/mastylolabs/172-data-intel/pull/29). The approved `sales-demo.v1` source now produces a deterministic bounded `DataProfileV2` receipt with source/schema/field meanings, whole-source dimensions, exact signed integer measures, fixed omissions, canonical serialization, and a payload SHA-256. The merged `main` revision is `54aab25aa56699c923d4b727b066e1d28437a31d`.

The implementation enforces approved-source identity, a 256-record ceiling, a 100 ms monotonic execution budget, int64-safe results, a 4,096-byte canonical receipt limit, and safe fixed failure classifications. It does not activate query execution, support retrieval, claim validation, model calls, UI, or deployment.

## Verification

- Exact-head CI passed twice: runs `37410508096` and `37410582750`.
- Independent QA PASS: local receipt `.git/172x/m3-p2b-profile-qa.md` (not committed; the merged implementation is [PR #29](https://github.com/mastylolabs/172-data-intel/pull/29)). Clean checkout passed 373 Python tests and 40 Vitest tests, strict mypy, Ruff/format, and Radon A (average 2.9551; all functions A/B).
- Independent review PASS: local receipt `.git/172x/m3-p2b-review.md` (not committed); no MF, NH, or Q findings. The provider review and approval are recorded on [PR #29](https://github.com/mastylolabs/172-data-intel/pull/29).
- New profiler coverage: 56/56 statements and 12/12 branches (100%). Combined Python coverage measured by QA: 93.2668% (905/965 statements; 217/238 branches). Existing gaps remain in SQL/result/service/build/FFI paths and the build CLI.
- Independent fixture arithmetic reproduced 24 records, dates 2026-01-01 through 2026-03-31, dimensions 6/4/2, units `count=24,min=-1,max=4,sum=29`, and USD cents `count=24,min=-15000,max=45000,sum=395000`.
- Actual canonical payload measured 1,988 UTF-8 bytes with SHA-256 `361b38fe212f1b18b210a296cb84df1fcf644a0703f74f20c73ecbfd5c01ab34`.

## Problems and limits

The profile contract had to be split from its implementation to keep each reviewable PR under the repository's 400-line handwritten limit. No implementation defect or review finding remained. Deployed profiling and the later generic query, support, validation, service, model, and UI capabilities remain unverified and are intentionally outside this milestone.

## Hardest technical problem

The difficult part was making a useful whole-source receipt without allowing unbounded or imprecise values into downstream planning. The profiler therefore consumes only the manifest-verified typed loader, performs integer-only statistics with explicit int64 checks, caps dimension labels while retaining whole-source distinct counts, hashes only the bounded canonical receipt, and starts the deadline before loading, checks it during scanning, and checks it before success. This preserves exactness and makes later query and validation stages auditable.

## Next milestone

Proceed with the next independent M3 analytical capability after this report: a bounded generic read-only query engine integrated with the approved sales source and profile. It must preserve source identity, support filtering/aggregation/grouping/ranking/period comparisons, enforce statement/result limits, and be tested against independent fixture questions and invalid queries. Support corpus loading/search and deterministic answer validation remain separate dependent slices. No user decision is needed for that scoped work under the existing authorization.

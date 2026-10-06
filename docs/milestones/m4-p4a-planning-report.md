# M4 P4a planning foundation report

## Delivered behavior

PR [#21](https://github.com/mastylolabs/172-data-intel/pull/21) merged into `main` at verified revision `54ee9e91084cf336bf1431a6c91f8b52320d17bd`. The native Proof Agent now has a typed `/proof/plan` foundation for the sales source: it loads bounded authoritative metadata from the private Python Worker, builds a metadata-only prompt, requests one temperature-zero Llama 3.3 JSON-schema response, validates `plan` or `clarify`, and persists the candidate for refresh. It bounds request and response bytes, classifies provider failures without raw details, enforces a 30-second model wait, reserves a per-session 12-calls/hour model admission, and rejects same-UUID changed-input replays with `request_conflict`.

The checked-in deployment intentionally has no `ProofBudget` binding. Deployed planning therefore fails closed with `budget_unavailable` before metadata or Workers AI dispatch. The existing reviewed P3b deployment was preserved; this foundation was not uploaded or used to change the live service.

## Problems and resolutions

The first model response schema placed `additionalProperties:false` at a union root without root properties, which could reject every valid provider response. Root properties and branch-specific closure were added and independently validated with Ajv. Review also found an unbounded model wait, missing deployed Agent provenance validation, and missing pre-dispatch request reservation; all were corrected with tests. A final independent check found that same UUID with a different question replayed the old candidate; an internal SHA-256 request key now returns `request_conflict` and remains hidden from public state.

The global cross-session 24-calls/day budget Durable Object, a retained multi-ID request journal, legacy Durable Object state bootstrap, SQL execution from candidates, Validator/publication, support retrieval, frontend, and live AI smoke remain for the next bounded slice.

## Hardest technical problem

The hardest problem was making a real model boundary inspectable without allowing an unbounded or unverifiable call. The solution keeps metadata, schema, byte limits, provider classification, timeout, provenance, reservation, and candidate persistence inside the native Agent while leaving deployment fail closed until the global budget contract exists. This preserves a testable model path with mocks and prevents the incomplete budget design from becoming a live paid or quota-consuming route.

## Verification evidence

- Repository gate: passed on the merged head; Ruff format/check, mypy on 26 files, 249 Python tests, Radon average A (2.9187) under enforced average 2.89, TypeScript typecheck, and 35 Agent tests.
- Agent coverage: 94.81% lines/statements, 87.28% branches, 100% functions; `index.ts` 91.96% lines and 83.33% branches.
- Independent QA: exact-head PASS on `a727174a01aa283a6fe7a99458403a754ce38604`; same-input replay avoided a second model call, changed input returned 409, missing provenance and missing budget refused before dispatch, and twelve restored session admissions were bounded.
- Wrangler 4.147.0 dry run passed with `ProofAgent`, `TOOLS`, `AI`, `CF_VERSION_METADATA`, and deployed runtime variables; it performed no upload.
- Deployed AI execution, Durable Object restart persistence, global budget admission, and real Workers AI free-quota behavior were not run. No paid billing was enabled.

## Next milestone

P4b should add the global `ProofBudget` Durable Object with a 24-calls/day admission, a bounded retained request journal and legacy-state bootstrap, then activate the binding only after independent QA and provider review. It should deploy a reviewed revision using the existing secret and run one free-quota smoke check; if the free quota is exhausted, retain the fail-closed behavior and continue with mocks. No decision is needed from the user under the existing full GO and no-paid-billing authorization.

# M4 domain receipt schemas milestone report

Date: 2026-10-06  
Merged implementation: [PR #53](https://github.com/mastylolabs/172-data-intel/pull/53)  
Verified main revision: `b5645acbe1ac7ac479bf2f797f0233cedb218650`

## Delivered behavior

The app package now parses the four deterministic Python v2 payloads before later Agent work consumes them: the closed two-source catalog, the sales profile, the sales query result with tagged cells, and targeted support search receipts. The common envelope validator now has operation-specific payload ceilings and identifier rules. Query receipts recompute SQL and canonical result hashes, bind payload receipt/job IDs to the envelope, and bind nested query runtime provenance to the common runtime. Support tokenization mirrors the Python ASCII-only policy. Year-zero profile dates, malformed controls, unknown fields, altered source identities, inconsistent counts, and over-limit payloads are rejected with bounded errors.

The implementation merged after two independent correction cycles. Provider review found and the implementation fixed Python parity for real `0.0` cells and ASCII-only tokenization, then fixed query runtime provenance mixing and year-zero dates. All three provider threads were resolved before merge.

## Verification

- `npm ci --prefix workers/app`: passed; 0 vulnerabilities.
- `npm run typecheck --prefix workers/app`: passed.
- App tests: 8 passed; final app coverage was 93.04% statements (reported by the implementation/QA run).
- `make gate`: passed on the final head: 669 Python tests, 48 Agent tests, and 8 app tests; Ruff, mypy, formatting, and Radon checks passed.
- `make coverage`: passed with 93% measured Python coverage.
- Independent QA-v3: PASS on `135a37a6ad209ed45ac6091ef3d3644026ff0168`, including four Python-generated v2 envelope round trips and strict/mutation checks.
- Independent PR review-v3: APPROVED on the same head; configured provider approval was submitted, all three provider threads were resolved, and guarded merge confirmed PR #53 merged.

The final implementation diff was 327 changed handwritten lines in the merged squash commit. It stayed within the repository's 301–400-line allowance because the four payload contracts, envelope composition, hash/provenance checks, and boundary tests form one coherent foundation. No generated files, datasets, Python service code, deployment resources, or `PROMPTS.md` were changed.

## Problems and remaining issues

The first QA pass found a Python/TypeScript real-cell mismatch for `0.0` and Unicode case folding that diverged from the ASCII tokenizer. Provider review then identified runtime provenance mixing and year-zero profile dates. Each was fixed with focused tests and fresh QA/review on the corrected head. A transient local Vitest missing-chunk error occurred immediately after `npm ci`; the full gate passed on retry after the locked install completed.

Service-binding transport, Cloudflare serialization, browser behavior, native public Agent orchestration, candidate/Validator publication, deployed smoke tests, and live Workers AI remain unverified. The existing Agent dependency audit warning is outside this slice and remains a maintenance risk. The current QA environment used Node 23.3.0, while the package declares Node 20/22/24-compatible tooling; CI and deployment will provide the runtime evidence later.

## Hardest technical problem

The hardest problem was preserving byte-for-byte and token-for-token compatibility between Python's strict producer models and TypeScript's Zod consumer. A schema that looked structurally correct still differed on Python's `repr(0.0)`, ASCII-only case mapping, JavaScript year-zero date handling, and runtime provenance attribution. The solution was to generate Python route vectors, compare them with TypeScript mutation probes, and add explicit asynchronous hash and provenance checks at the envelope boundary. This keeps deterministic execution authoritative while making the future Agent fail closed on mixed or malformed receipts.

## Next milestone

Build the runnable public Agent/service bridge as a separate bounded slice. It should use a new Worker name and service binding, preserve the existing private Agent and Python deployments, call `/v2/catalog`, `/v2/profile`, `/v2/query`, and `/v2/search`, persist selected-source/session/job state in a native Durable Object, and return safe progress/error envelopes. It must include integration tests with mocked bindings and no live paid model calls. Browser chat, candidate/Validator publication, preview deployment, and the free-allowance Llama check follow as separate reviewed slices.

## Decisions needed

None for the next implementation slice. The user has already authorized guarded implementation and preview/final deployment within this MVP, with free Workers AI allowance only and no paid billing. Live Llama execution remains an explicit later verification item; if the free quota is exhausted, mocked and deterministic checks will continue and the gap will be recorded.

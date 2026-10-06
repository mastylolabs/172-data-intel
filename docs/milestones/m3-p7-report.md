# M3-P7 milestone report: private v2 service wiring

Date: 2026-10-06

## Delivered behavior and merged revision

PRs [#44](https://github.com/mastylolabs/172-data-intel/pull/44), [#45](https://github.com/mastylolabs/172-data-intel/pull/45), [#46](https://github.com/mastylolabs/172-data-intel/pull/46), [#47](https://github.com/mastylolabs/172-data-intel/pull/47), and [#48](https://github.com/mastylolabs/172-data-intel/pull/48) are merged. Together they provide the bounded v2 catalog, profile, read-only query, and targeted support-search envelopes, adapters, and private Python Worker dispatch. v1 routes remain separate and unchanged. The verified `main` revision is `44e3ac262e1854baea10a84b636f48f4e7e59325`.

The Worker enforces endpoint body caps, validates runtime provenance, maps transport and stream failures to safe errors, and does not expose a public route. Real local execution verified the demo sales profile, a `395000`-cent sales total, grouped/ranked results, and support IDs `M015` and `M012` with exact quotes.

## Problems and resolutions

Independent review found nested DTO mutability, historical-source acceptance, incorrect input-limit classification, complete-envelope overflow escaping as a Pydantic exception, and malformed request-property failures escaping the Worker. The v2 models now deep-copy nested values, adapters require the exact registered demo source, input and result limits have distinct safe codes, envelope validation is fenced, and initial request routing catches the transport exception family. All findings were fixed on the reviewed heads and their provider threads were resolved before guarded merges.

## Hardest technical problem

The hardest problem was preserving a single safety boundary across Python service contracts and the Workers runtime. The solution keeps source identity, job/run bindings, payload hashes, runtime provenance, and endpoint caps in the v2 envelope, then makes the Worker a private transport adapter that validates and maps failures without changing v1 behavior. This lets the later Agent call one typed boundary while keeping the old deployed resources untouched.

## Tests, coverage, and gaps

- `make gate`: PASS on the merged PR #48 head; 669 Python tests and 40 Vitest tests, Ruff, mypy, TypeScript, and Radon all passed. Radon reported average complexity A and no C-or-worse blocks in the canonical `src tests` scope.
- `make coverage`: PASS; 1,880 statements and 530 branches with 93% total branch-aware coverage (109 statements missed and 56 partial branches). Lower-coverage areas are safe failure branches in contracts, validation, service adapters, and the Worker build helper; they remain explicit gaps rather than untested claims.
- Independent QA passed the exact final PR #48 head, including v1 regression, v2 dispatch, exact/max-plus-one caps, malformed URLs, throwing request properties, stream failures, and real local sales/support results. Independent review approved it; configured provider review and approval passed and the guarded merge completed.

## Integration and deployed checks

Local Worker-entrypoint integration passed with mocked Worker SDK objects and real Python execution. The prior deployed M2 tools and Agent resources were preserved. The new v2 Worker has not yet been deployed, so Cloudflare service-binding parity, live v2 endpoint smoke tests, live Workers AI behavior, browser flows, and Agent-to-tool calls remain unverified.

## Next milestone

M4 begins with a bounded Agent/Durable Object v2 session-state slice: source selection, isolated session snapshots, job status, and typed calls that preserve the existing `/proof/*` contract. Follow-on slices will add the Python bridge, deterministic Analyst/Validator publication checks, web chat, preview deployment, and final smoke tests. No user decision is needed; the existing authorization continues to cover this work.

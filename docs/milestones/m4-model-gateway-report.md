# M4 model gateway milestone report

## Delivered behavior

PR [#61](https://github.com/mastylolabs/172-data-intel/pull/61) is merged into `main`.
The app now has a bounded Workers AI planner gateway using the fixed free-only
Llama 3.3 model `@cf/meta/llama-3.3-70b-instruct-fp8-fast`. The gateway validates
server-owned request and source identity, sends bounded catalog/profile context,
uses a strict JSON response schema, caps input/output and tokens, times out a
single model call, and returns redacted no-retry failure classes. The Wrangler
configuration contains the additive `AI` binding. Public routes do not invoke the
gateway yet; orchestration is the next slice.

Verified merged `main` revision: `2d2142c8096a8e7c6b3e56ca61f6894ef4a41ac0`.

## Problems and remaining limitations

The first independent review found that free-only quota code `4006` was reported
as generic unavailability. A follow-up corrected code-only and structured HTTP
`429` handling. Provider review then identified documented code `3036`; it is now
also classified as daily free-allocation quota with HTTP `429`, without exposing
provider details or retrying automatically. The final provider thread was resolved
and the approval was submitted on the exact merged head.

The gateway remains an internal adapter. It has no public ask route, candidate or
Validator orchestration, accepted answer memory, browser UI, or deployed live
model check. Object-response and multibyte UTF-8 boundary tests remain a
non-blocking follow-up recommendation.

## Hardest technical problem

The hardest problem was making an external model boundary deterministic and safe
for the contracts already merged in M4. The gateway treats questions and source
metadata as bounded data, binds returned proposal identity to the server request,
source, and approved snapshots, validates the complete proposal with the strict
contract parser, and maps quota, capacity, timeout, malformed output, and limit
failures to stable redacted results. This keeps model variability outside the
publication path until a separate orchestration slice can apply deterministic
execution and Validator checks.

## Verification evidence

- App tests: 38 passed.
- App coverage: 88.90% statements, 84.32% branches, 90.90% functions, 93.39% lines.
- `npm run typecheck --prefix workers/app`: passed.
- `make gate`: passed, including Ruff, mypy, pytest, and Radon (average A).
- Wrangler dry-run with the additive AI binding: passed.
- `git diff --check`: passed.
- Independent QA: PASS at exact head `7d5b043f83447250377462d6bde3bc1e6219b66f`.
- Independent review: APPROVED locally at the same exact head.
- Configured provider bot approval: passed after resolving the stale `3036` review thread.
- Live Workers AI call and deployed runtime: unrun by design; routine checks used mocks.
- No billing, credits, or existing deployed resources were changed.

## Next milestone

Implement the AppAgent orchestration slice: admission against the existing
session budget, planner integration, clarification handling, generation and
cancellation fencing, and deterministic handoff to the existing Python tool
receipts. Keep the public bridge additive and preserve the current state and
transport contracts. The live model check should remain a single free-allowance
smoke test after the route and deployment slices are ready.

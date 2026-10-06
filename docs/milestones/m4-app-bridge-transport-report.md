# M4 app bridge transport milestone report

## Delivered

PR #55, [feat(app): add bounded bridge transport](https://github.com/mastylolabs/172-data-intel/pull/55), merged through the guarded 172X process. Verified `main` revision: `4b7d17b`.

The app package now has a reusable private v2 transport boundary. It validates strict profile, query, and support-search requests, projects only approved search fields, streams request and service bodies with byte ceilings and fatal UTF-8 handling, cancels readers on overflow and read/decoder failures, maps failures to bounded safe codes, and binds returned source, job, run, payload hash, and runtime provenance to the dispatched operation. No public Worker, Durable Object, model call, UI, or deployment was included.

## Evidence

- Independent QA: PASS for exact head `b0d6ae0a8c0a424fd0f2fb7e9a7ec09bb5894282`; 15 app tests; 92.80% statement and 95.02% line coverage.
- Independent review: APPROVED for the exact head; the source-binding, stream-cancellation, strict-text, and status findings were rechecked. One non-blocking observation remains: channel/customer whitespace is stricter in the Python boundary and will be enforced again at the public route boundary.
- `make gate`: PASS — Ruff format/check, mypy, 669 Python tests, 48 Agent tests, 15 app tests, Radon average complexity A (3.1315), and complexity enforcement.
- App install/typecheck: PASS; app audit reported zero vulnerabilities.
- Handwritten changed lines: 297, below the 400-line cap. README prose is excluded under `AGENTS.md` and the lockfile was unchanged.

## Problems and remaining issues

The first bridge implementation mixed transport and Durable Object lifecycle responsibilities and had real review defects. It was re-cut instead of merged: the known-defective public Worker head was discarded, the provider threads were resolved as obsolete, and its lifecycle work was preserved locally for a dependent PR. No existing Worker, deployment, billing setting, or prompt log was changed.

This milestone does not prove native Agent/DO persistence, live service binding, Workers AI availability, browser behavior, or Cloudflare deployment. Those checks are intentionally unrun because this PR has no Worker entry point or Wrangler configuration. The existing `workers/agent` npm audit findings remain pre-existing and outside this PR.

## Hardest technical problem

The hardest problem was making a service-binding result trustworthy across two runtimes. The transport now recomputes envelope hashes, checks the complete source identity against the outbound request, requires the expected job/run IDs for every non-catalog operation, verifies runtime mode, and rejects oversized or malformed streams before publication. This keeps later Agent state code from treating a valid receipt from the wrong operation as evidence for the current question.

## Next milestone

Build PR B from `4b7d17b`: the public native Agents SDK Worker and `MvpAppAgent` Durable Object. It must add opaque cookie isolation, source selection, profile/query/search jobs, durable state, cancellation/reset/expiry fencing, bounded replay outcomes, deadline reconciliation, and a deterministic fake Agent/DO lifecycle harness. It must remain within 400 handwritten lines and pass fresh QA, configured provider review, and guarded merge before browser/model work begins.

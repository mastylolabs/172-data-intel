# M4 P4b: global planning budget report

Date: 2026-10-06
Verified `main`: `c1ea02f430e63fdf20435d6fb0b0e760bbe4b9d1`

## Delivered behavior

PR [#23](https://github.com/mastylolabs/172-data-intel/pull/23) adds the cross-session planning budget needed to activate the reviewed P4a planner. A SQLite-backed `ProofBudget` Durable Object admits at most 24 model starts per UTC day using serialized storage updates. The Agent keeps the existing 12-start hourly session limit and fails closed when global admission is unavailable. The v2 SQLite migration is append-only and the binding is resolved by Wrangler.

The Agent now retains a server-only journal of the latest 32 request identities and input fingerprints. A retained same-input completed request replays its persisted plan; changed input returns a conflict; a retained incomplete or replaced request returns `request_outcome_unavailable` without another model call. Existing P3b/P4a state is normalized on first access, including interrupted legacy reservations. Source changes preserve replay protection and reset still revokes the old session.

## Verification

- Engineering gate on the implementation head: Ruff format/check, mypy (26 files), 249 Python tests, canonical Radon average complexity A 2.9187, the enforced declaration average A 2.89, TypeScript typecheck, and 40 Vitest tests: all passed under the repository's A/B policy.
- Agent coverage: 94.75% statements/lines, 86.25% branches, 100% functions.
- Independent QA passed the exact head and additionally checked 48 concurrent budget admissions (24 accepted), UTC rollover, restoration, shared cross-session exhaustion, per-session precedence, 32-entry retention, replay/conflict/unavailable outcomes, legacy bootstrap, privacy, and safe malformed/provider failures.
- Wrangler 4.147.0 dry-run resolved `ProofAgent`, `ProofBudget`, the private tools service, AI binding, version metadata, and the SQLite v2 migration. No upload occurred for this slice.
- Provider checks passed on the current head: two GitHub gates, resolved review threads, configured `172x-reviewer-bot` approval, and guarded squash merge.
- Important coverage gaps: concurrency, UTC rollover, and journal-boundary probes were additional uninstrumented checks; actual Cloudflare migration, restart/concurrency, deployed-request, and live-model paths remain unverified.

The implementation diff contained 219 handwritten changed lines (206 additions and 13 deletions); 14 README prose lines, lockfiles, and bundled data were excluded from the code budget.

## Problems and resolutions

The initial migration used `new_classes`, which selects the legacy KV-backed Durable Object storage path. Independent review identified that as a Workers Free deployment risk for a new namespace. The migration was corrected to `new_sqlite_classes` and the exact-head gate, dry-run, QA, provider review, and merge were repeated. Review also identified that a legacy in-flight `plan_request_id` could be dropped when `plan` was null; normalization now preserves that reservation and returns the safe unavailable outcome.

## Hardest technical problem

The difficult boundary was preserving request identity across Durable Object schema evolution while keeping duplicate submissions from dispatching another model call. The solution is a bounded journal containing only the request UUID, a hash-derived input key, and completion state; it is normalized from older state before reads and kept out of client responses. This retains the safety property without storing unbounded prompts or model output in the journal, while the persisted plan remains the replay source for a completed request.

## Limitations and unverified checks

This slice was validated locally and in Wrangler dry-run. Actual Cloudflare namespace migration, live Durable Object concurrency/restart behavior, deployed P4b planning requests, and a live Workers AI Llama 3.3 call were not run. The free Workers AI preflight remains quota-limited; no paid billing or credit purchase was enabled. The existing P3b deployment was preserved. The global counter conservatively consumes an admission before later metadata or provider failure and has no refund path.

## Next milestone

Next is **M3: reproducible datasets and verified analytical tools**. It must add the complete sales fixture/profile, support JSONL targeted retrieval, and deterministic numerical/citation validation contracts before dependent M4 publication work resumes. After M3 is reviewed and merged, M4 can execute approved Analyst plans through the private Python service, validate candidate answers, and retain accepted evidence. Final web chat remains M5. No user decision is needed under the existing full GO; live LLM checks remain limited to the Workers AI free allowance.

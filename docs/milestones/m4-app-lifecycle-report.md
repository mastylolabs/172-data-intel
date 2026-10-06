# M4 app lifecycle milestone report

## Delivery

PR [#57](https://github.com/mastylolabs/172-data-intel/pull/57) is merged into
`main`. The verified main revision is
`9009780085f837205b99c91e66bf7a82d79ac0bd`.

The public app now exports a native Agents SDK `MvpAppAgent` Durable Object and
routes opaque cookie sessions to isolated durable state. It exposes strict
same-origin JSON routes for state, source selection, profile, generic read-only
query, targeted support search, cancellation, and reset. State persists selected
source, active jobs, terminal receipts, two owned replay outcomes, expiry
handling, generation/cancel fencing, and safe error responses. The bridge validates
catalog/source capabilities, request and result bounds, source/job/run identity,
query/search envelopes, and private tools runtime provenance. Wrangler dry-run
confirms the Durable Object, private `TOOLS` service binding, version metadata,
and fail-closed tools provenance variables.

## Problems and resolutions

The first lifecycle implementation compared the Python tools Worker version ID to
the public app Worker version ID. Independent QA found that this would reject
every valid deployed receipt. The app now validates against explicit
`TOOLS_BUILD_REVISION` and `TOOLS_WORKER_VERSION_ID` values, which are supplied
from the private service deployment; blank values fail closed.

Review also found that terminal cancellation could rewrite a successful job and
that expired cancellation could remain non-terminal. Cancellation is now a
no-op for terminal jobs, and deadline reconciliation completes a
`cancel_requested` job as cancelled. Public search rejects malformed lexical
token shapes before durable work is queued. Duplicate request handling respects
active versus terminal phases, and owned replay snapshots bind their result to
the recorded job.

## Verification evidence

- App: 24 tests passed; coverage was 88.49% statements, 85.19% branches,
  88.07% functions, and 92.74% lines.
- Repository gate: `make gate` passed with 669 Python tests, 48 Agent tests,
  24 app tests, Ruff, mypy, and Radon average complexity A (3.13148).
- Wrangler: `npx wrangler deploy --dry-run --config workers/app/wrangler.jsonc`
  passed with `MvpAppAgent`, `TOOLS`, version metadata, and tools provenance
  bindings.
- Diff budget: 400 counted handwritten lines exactly; generated lockfile and
  README prose were excluded under AGENTS.md counting rules.
- Independent QA: PASS on exact head `5f47f4931cf0eb91c6526c6429279de622d9853c`.
- Independent review: correctness findings closed; native restart and fully
  independent persisted two-session tests remain a documented follow-up.
- Provider review: configured `172x-reviewer-bot` approved the exact head;
  four review threads were resolved; guarded merge eligibility passed.

The lifecycle harness uses fake Agent/DO state and mocked service responses.
No live Cloudflare request, Durable Object restart, deployed private-service
receipt, browser test, or Workers AI call was run in this milestone. The final
application must verify those separately. No existing Worker, deployment,
billing setting, or prompt log was changed.

## Hardest technical problem

The hardest problem was preserving runtime provenance across a service binding.
The public app and Python tools Worker each have their own Cloudflare version
metadata identity, so comparing them directly is invalid. The bridge now keeps
the service identity as an explicit deployment input and validates every receipt
against that mapping while retaining local mode for deterministic tests. This
keeps failures fail-closed without conflating two Worker identities.

## Next milestone

The next bounded milestone should add Analyst planning, bounded Workers AI calls
with Llama 3.3, separate candidate and Validator calls, deterministic
publication checks, and durable answer memory on top of the merged lifecycle.
The following slice can add the browser chat and preview deployment. The final
deployment still needs the exact private tools build revision and version UUID
for the service binding; those values should be captured when the reviewed tools
resource is deployed or a new preserved resource is created. Workers AI live
checks remain conditional on the free allowance and will not enable billing.

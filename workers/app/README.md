# MVP public Agent bridge

This package is the runnable public JSON bridge for the MVP. It is a native
Agents SDK Worker backed by the `MvpAppAgent` Durable Object and an opaque,
cookie-keyed session. It calls the private Python v2 service through the `TOOLS`
service binding. Existing `workers/agent` and `workers/tools` resources remain
unchanged.

```sh
npm ci --prefix workers/app
npm run typecheck --prefix workers/app
npm test --prefix workers/app -- --coverage
npx wrangler deploy --dry-run --config workers/app/wrangler.jsonc
make gate
```

The public routes are `GET /api/state` and same-origin `POST /api/source`,
`/api/ask`, `/api/profile`, `/api/query`, `/api/search`, `/api/cancel`, and
`/api/reset`. `POST /api/ask` accepts `{version: "2", request_id, question}`
and returns a durable 202 job snapshot. The Agent loads the approved catalog,
loads the sales profile when needed, and calls the bounded free-only planner;
the public state exposes only the validated proposal, publication, or clarification, safe
model failure, and the remaining per-session model-call budget. For a successful
query or search plan, the Agent executes the approved read-only tool call, builds
bounded evidence, runs a separate capped Validator call, and persists either a
published answer or a safe refusal. Numeric sales answers currently require one
exact integer result; support answers contain exact returned message quotes and
the fixed targeted-search limitations. No-hit answers describe only the declared
filtered scope. The private
Agent service's existing `ProofBudget` admits at most 24 free planner starts
per UTC day through a token-protected service route. Configure the same secret
placeholder `replace-with-32-byte-random-value` in both Workers with
`wrangler secret put PLANNER_BUDGET_TOKEN`; never commit or log its value. Ask
jobs allow the bounded tool work plus the 30-second planner timeout within a
60-second deadline; existing profile/query/search jobs retain their shorter deadline.
Profile-only plans and unsupported result shapes remain safe refusals; clarification
behavior is unchanged. Jobs return a 202 snapshot and are polled through `/api/state`.
Sessions are
isolated by an opaque cookie, reset rotates the cookie, and selected source,
active job, terminal receipts, replay outcomes, expiry, cancellation, and reset
fencing are durable state. The bridge validates source, job/run identity,
hashes, runtime mode, strict input fields, and bounded streams before exposing a
receipt. Support search is targeted lexical evidence with exact IDs and quotes;
it does not establish corpus prevalence or absence.

The private binding in Wrangler points to the existing `172x-data-intel-m2-tools`
Worker for preview verification. Before a deployed app publish, replace the
empty `TOOLS_BUILD_REVISION` and `TOOLS_WORKER_VERSION_ID` vars with the exact
private tools Worker build revision and version-metadata UUID; blank values fail
closed. The separate Validator uses the same free-only Llama 3.3 model with a
12,288-byte input cap, 8,192-byte output cap, 256 output tokens, zero temperature
and no automatic retry. This package does not deploy or enable paid billing. The
planner gateway also uses `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, with 12,288-byte input,
8,192-byte output, one call, zero temperature and no automatic retry. Its local
tests use a fake AI binding; `/api/ask` is the first public route that invokes
it, and no live model check is claimed here.

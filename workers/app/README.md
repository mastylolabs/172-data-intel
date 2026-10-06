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
`/api/profile`, `/api/query`, `/api/search`, `/api/cancel`, and `/api/reset`.
Jobs return a 202 snapshot and are polled through `/api/state`. Sessions are
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
closed. Workers AI planning, separate candidate and
Validator calls, publication, and browser chat are the next application slice;
this package does not deploy or enable paid billing.

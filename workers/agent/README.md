# Restricted native Agent bridge (P3b-2)

This project exposes the operator-only `/proof/*` surface through a native
Cloudflare Agent backed by a SQLite Durable Object. The outer Worker checks the
bearer token before Durable Object lookup, hashes a server-issued cookie for
session identity, and forwards only the restricted proof routes. Agent state
writes are server-only; source selection and reset are synchronous, and `/proof/sql`
calls the private Python `TOOLS` service binding.

```sh
make typescript-gate
npm test --prefix workers/agent -- --coverage
```

The root `make gate` invokes `typescript-gate`: a clean lockfile install, TypeScript
typecheck and Vitest tests. The existing CI quality workflow therefore enforces
these checks alongside the Python gate.

The Agent project pins Agents SDK 0.26.0, Zod 4.6.5 and Vitest 3.2.7. The Python
tools Worker retains its separately reviewed Wrangler 4.127.1. The checked-in
`wrangler.jsonc` declares the `ProofAgent` SQLite migration and private `TOOLS`
service binding; deployment credentials and authorization remain operator-owned.

This slice intentionally defers LLM planning, uploads, frontend routes, and async
job lifecycle. `/proof/query` is reserved and returns `unsupported_transport`;
the synchronous engine receipt is not an AI answer or a deployed lifecycle claim.

`contracts.ts` forbids unknown fields, pins the source/policy limits, bounds SQL
and typed cells, checks result shape, and hashes the Python canonical result
format. `validatedResult` also verifies SQL/result digests and complete payload
size. Integer values remain signed int64 decimal strings; REAL values remain
finite strings with `exact:false`, without a certified decimal error bound or a
JavaScript reimplementation of Python's float `repr`. Python owns that canonical
float-spelling check. Agent provenance is validated independently from Python.
The stream reader enforces raw byte limits, strict UTF-8 and safe cancellation
without replacing the original size/parse/FFI failure.

`tests/fixtures/*.json` are generated from `handle_service` at Python baseline
`a0beff4` with synthetic deployed runtime IDs and `SELECT SUM(revenue_cents) AS
total FROM sales`; they are test fixtures, not live deployment evidence. The
metadata and receipt use the real six-row packaged fixture and actual Python
engine hashes. Hash/state/auth/service integration and durable lifecycle/budget
acceptance require the dependent bridge. Background execution and AI follow later.

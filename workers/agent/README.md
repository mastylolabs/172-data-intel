# Agent wire foundation (P3b-1)

This project validates the existing private Python service wire boundary. It does
not run an Agent, expose HTTP routes, call AI, or establish deployed compatibility.
The Wrangler scaffold has no entrypoint, Durable Object or service binding yet;
do not deploy this foundation. The next reviewed slice adds the native Agent and
restricted engine proof bridge using the private `TOOLS` binding.

```sh
npm ci --prefix workers/agent
npm run typecheck --prefix workers/agent
npm test --prefix workers/agent
npm test --prefix workers/agent -- --coverage
```

The Agent project pins Agents SDK 0.26.0, Zod 4.6.5, Wrangler 4.147.0 and Vitest
3.2.7. The Python tools Worker retains its separately reviewed Wrangler 4.127.1.
The scaffold disables workers.dev and preview URLs and uses a distinct name from
the reference application. Credentials, public routes and deployment authorization
belong to the dependent bridge/deployment work, not this wire foundation.

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

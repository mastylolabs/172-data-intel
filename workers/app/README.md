# App bridge transport

This package contains the bounded private transport foundation for the public
MVP. It calls only the current Python v2 service paths (`/v2/catalog`,
`/v2/profile`, `/v2/query`, and `/v2/search`) through a mocked Fetcher
contract. The public Worker, native Agent/Durable Object lifecycle, browser UI,
model calls, and deployment are deferred to the dependent bridge slice. The
existing `workers/agent` and Python service remain independent.

The transport accepts strict request DTOs, projects search fields explicitly,
streams request and response bodies under byte limits with fatal UTF-8 decoding,
applies a five-second private-call timeout, and validates the existing domain
envelopes, runtime mode, and expected job/run identities before returning a
receipt. It never exposes service error bodies.

```sh
npm ci --prefix workers/app
npm run typecheck --prefix workers/app
npm test --prefix workers/app -- --coverage
make gate
```

The exported DTO schemas pin the reviewed sales/support source hashes and bound
question, SQL, search, filter, and result sizes. Search date intervals are
canonical UTC timestamps with an end after the start. `buildToolBody` drops
public request metadata from the Python search body and adds only the v2 job,
run, and source envelope fields. Callers still own capability and authorization
checks at the future public Agent route boundary.

`validatedDomainEnvelope()` validates the common Python v2 envelope, recomputes
the typed payload digests, and checks receipt-specific identity/source/runtime
rules. `executeTool` then binds every non-catalog response to the active job
and run supplied by its caller; catalog is the only operation with null envelope
identifiers.

The app contract foundation also provides Python-compatible canonical JSON and
hashing for the domain receipts. Exact analytical numbers remain decimal strings;
the bridge does not turn deterministic receipts into claims or publication.

Tests use deterministic Fetcher responses and cover all four private paths,
foreign identifiers, malformed UTF-8, stream overflow, strict search projection,
tampered/invalid service responses, and safe service failures. The next bridge
slice adds the public Agent and Durable Object lifecycle, strict `/api` routes,
durable session state, cancellation/reset fencing, and Wrangler resources.
Candidate/Validator schemas, Workers AI, and the web chat remain later
capabilities.

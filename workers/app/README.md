# App contract foundation

This separate package prepares the public MVP's TypeScript boundary. It contains
no Worker entry point, route, resource configuration, model call or deployment.
The existing `workers/agent` and Python v1 surface remain independent. App tests
pin patched Vitest/coverage 4.1.11; use Node 20, 22 or >=24 as its supported runtimes.

```sh
npm ci --prefix workers/app
npm run typecheck --prefix workers/app
npm test --prefix workers/app -- --coverage
make gate
```

Closed source identities pin the reviewed sales/support demo hashes. Questions
preserve their exact text within 1,024 UTF-8 bytes. Planner proposals require every
field, with explicit nulls for unused fields. They are source-bound structural
proposals; SQL safety, lexical request validation, capabilities and authorization
belong to the existing Python boundaries and later orchestration.

`validatedEnvelope()` validates the common Python v2 envelope and recomputes the
raw and typed payload digests. Its caller must provide a strict payload schema,
the appropriate payload ceiling and the operation's required identifier semantics;
only catalog consumers may accept three null IDs. This foundation does not yet
validate every domain receipt or bind an envelope to an active job.

Canonical JSON follows Python's Unicode code-point key ordering and UTF-8 hashing.
It accepts safe integers, strings, booleans, null and plain collections; it rejects
floats, unsafe integers, negative zero, invalid Unicode and lossy values. Exact
analytical numbers arrive as decimal strings. Later consumers must retain that
domain or explicitly verify any additional numeric representation.

Prompts reuse the reference's closed proposals and independent Validator context,
adapted for generic SQL, net cents and bounded lexical evidence. No retries or
reference operation menu are imported. `supportedClaims()` checks complete claim
dispositions and deterministic success; it grants no publication authority.

Next slices must add strict domain receipts and candidate/Validator schemas,
budgeted calls, source/job/hash binding, fenced publication and the web chat before
this package becomes a runnable app.

# Milestone M2 P3b report: native Agent bridge

## Delivered behavior and merged changes

P3b-1 established the TypeScript/Python wire contracts in [PR #17](https://github.com/mastylolabs/172-data-intel/pull/17). P3b-2 added the native `ProofAgent` Durable Object bridge, restricted `/proof/*` routes, bearer authentication before Durable Object lookup, hashed cookie sessions, server-only state changes, source selection/reset, strict Python receipt and provenance validation, complete SafeError responses, a ten-second private-service timeout, and Wrangler bindings/migration in [PR #18](https://github.com/mastylolabs/172-data-intel/pull/18).

The verified `main` revision is `60d775566525b8899b949d5cf046a026fe321af3`.

## Deployment and test evidence

The private Python tools Worker is deployed as `172x-data-intel-m2-tools`, version `583c65b7-b54b-4d84-953b-259b5ca6e9c6`, from reviewed revision `a0beff4e4aa9bc4a28bc2bc7597549c405513d50`. The Agent Worker `172x-data-intel-m2-agent` was first uploaded as version `b43e3f83-f9d2-4967-8c06-27ddf1117387`; its first SQL attempt correctly failed closed because the deployment omitted `BUILD_REVISION`. The same reviewed code was redeployed with `BUILD_REVISION=60d775566525b8899b949d5cf046a026fe321af3` and is running as version `190c7b66-dab3-4f67-b9fa-cce955029b04`. `PROOF_TOKEN` was generated as 32 random bytes and stored with Wrangler; its value is not recorded. The Agent Worker has no public route or deployment target.

Fresh current-head verification passed: `make gate` (249 Python tests, Ruff, mypy, Radon, TypeScript typecheck, 29 Vitest tests); TypeScript coverage was 98.55% statements/lines, 91.12% branches, and 100% functions. Wrangler dry-run resolved the Durable Object, private `TOOLS` service binding, version metadata, and runtime variable without upload. The handwritten P3b-2 diff is exactly 400 added lines under the repository counting rules.

A remote preview invocation was attempted first; Cloudflare returned HTTP 500/error 1101 because `wrangler dev --remote` does not support Durable Objects. A temporary protected Worker-to-Worker harness was then deployed as `172x-data-intel-m2-smoke` (version `28785700-6985-45b1-9e2b-2428877dd724`) and deleted after the smoke run. Through that harness, the deployed Agent returned a real SQL receipt with total `130000`, a grouped ranking of South `75000`, North `55000`, East `0`, `unsafe_query` for a DELETE, `unsupported_source` for support SQL, refresh-retained receipt state, isolated sessions, and reset cookie rotation with the old cookie receiving 403. The receipt carried Python Worker version `583c65b7-b54b-4d84-953b-259b5ca6e9c6` and Agent version `190c7b66-dab3-4f67-b9fa-cce955029b04`. The harness and both temporary tokens were removed after testing; the Agent remains private with no public route.

## Problems, resolutions, and remaining limitations

The implementation initially returned incomplete error envelopes, accepted short proof tokens, had unbounded service-binding waits, and reused reset cookies. Those findings were fixed, retested on the current head, resolved in the provider review, and included in the guarded merge. The remaining development install reports four transitive npm audit findings (two moderate and two critical); the quality gate still passes. The first deployment omission of `BUILD_REVISION` was corrected before the successful live receipt, and the corrected version is the recorded deployment.

This milestone intentionally does not include Llama, analytical planning, support retrieval, validator publication, uploads, frontend chat, or the durable asynchronous job lifecycle. `/proof/sql` is an engine-only receipt and is not an AI answer.

## Hardest technical problem

The hardest problem was preserving a truthful boundary between the native Agent session and the Python Worker. The bridge now validates the Python metadata, source identity, schema/policy limits, request identity, complete result hashes, and Python runtime separately from Agent provenance before persisting the receipt. Reset revocation is stored in Durable Object state while the public state projection omits the revocation marker, and the outer Worker rotates the cookie only after a successful reset.

## Coverage, tests, and gaps

The repository gate passed with 249 Python tests and 29 TypeScript tests. TypeScript coverage measured 98.55% statements/lines, 91.12% branches, and 100% functions. Uncovered branches are valid service-error forwarding and an unknown internal Agent path. Tests mock the Agents SDK and service binding; no live Durable Object or deployed binding execution was completed.

## Next milestone

P4 can now add one free-quota Workers AI planning call against this verified Agent-to-Python boundary; if the free allocation is exhausted, retain the current engine-only behavior and defer paid billing. P3c/P4 must still add durable lifecycle/budgets and the Analyst/Validator chain before the final chat. Later slices can add the validator, targeted support retrieval, and the web chat with separate focused PRs.

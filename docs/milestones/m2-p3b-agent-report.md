# Milestone M2 P3b report: native Agent bridge

## Delivered behavior and merged changes

P3b-1 established the TypeScript/Python wire contracts in [PR #17](https://github.com/mastylolabs/172-data-intel/pull/17). P3b-2 added the native `ProofAgent` Durable Object bridge, restricted `/proof/*` routes, bearer authentication before Durable Object lookup, hashed cookie sessions, server-only state changes, source selection/reset, strict Python receipt and provenance validation, complete SafeError responses, a ten-second private-service timeout, and Wrangler bindings/migration in [PR #18](https://github.com/mastylolabs/172-data-intel/pull/18).

The verified `main` revision is `60d775566525b8899b949d5cf046a026fe321af3`.

## Deployment and test evidence

The private Python tools Worker is deployed as `172x-data-intel-m2-tools`, version `583c65b7-b54b-4d84-953b-259b5ca6e9c6`, from reviewed revision `a0beff4e4aa9bc4a28bc2bc7597549c405513d50`. The Agent Worker `172x-data-intel-m2-agent` was uploaded from reviewed `main` and has version `b43e3f83-f9d2-4967-8c06-27ddf1117387`. `PROOF_TOKEN` was generated as 32 random bytes and stored with Wrangler; its value is not recorded. Both Workers have no public route or deployment target.

Fresh current-head verification passed: `make gate` (249 Python tests, Ruff, mypy, Radon, TypeScript typecheck, 29 Vitest tests); TypeScript coverage was 98.55% statements/lines, 91.12% branches, and 100% functions. Wrangler dry-run resolved the Durable Object, private `TOOLS` service binding, version metadata, and runtime variable without upload. The handwritten P3b-2 diff is exactly 400 added lines under the repository counting rules.

A remote preview invocation was attempted for deployed smoke testing. Cloudflare returned HTTP 500/error 1101 because `wrangler dev --remote` does not support Durable Objects; the Wrangler log states to use local development instead. The deployed Worker has no route, so no live HTTP smoke receipt was claimed. Durable Object persistence, service-binding networking, and a deployed SQL receipt remain unverified until a route or supported integration harness is authorized and implemented.

## Problems, resolutions, and remaining limitations

The implementation initially returned incomplete error envelopes, accepted short proof tokens, had unbounded service-binding waits, and reused reset cookies. Those findings were fixed, retested on the current head, resolved in the provider review, and included in the guarded merge. The remaining development install reports four transitive npm audit findings (two moderate and two critical); the quality gate still passes.

This milestone intentionally does not include Llama, analytical planning, support retrieval, validator publication, uploads, frontend chat, or the durable asynchronous job lifecycle. `/proof/sql` is an engine-only receipt and is not an AI answer.

## Hardest technical problem

The hardest problem was preserving a truthful boundary between the native Agent session and the Python Worker. The bridge now validates the Python metadata, source identity, schema/policy limits, request identity, complete result hashes, and Python runtime separately from Agent provenance before persisting the receipt. Reset revocation is stored in Durable Object state while the public state projection omits the revocation marker, and the outer Worker rotates the cookie only after a successful reset.

## Coverage, tests, and gaps

The repository gate passed with 249 Python tests and 29 TypeScript tests. TypeScript coverage measured 98.55% statements/lines, 91.12% branches, and 100% functions. Uncovered branches are valid service-error forwarding and an unknown internal Agent path. Tests mock the Agents SDK and service binding; no live Durable Object or deployed binding execution was completed.

## Next milestone

P3c should provide a supported deployed integration harness or a deliberately authorized protected route, then record real Agent-to-Python SQL receipts and refresh/reset evidence. P4 can add one free-quota Workers AI planning call only after that proof; if the free allocation is exhausted, retain the current engine-only behavior and defer paid billing. Later slices can add the validator, targeted support retrieval, and the web chat with separate focused PRs.

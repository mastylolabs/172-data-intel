# M4-C0 / P5 foundation milestone report

## Delivered behavior and merged revision

PR #39, [freeze M4 conversation contracts](https://github.com/mastylolabs/172-data-intel/pull/39), merged the reviewed architecture, threat, and UX contracts. PR #40, [add deterministic numeric validation](https://github.com/mastylolabs/172-data-intel/pull/40), merged the first bounded P5 implementation. The verified `main` revision is `a98ca28c49943b6170fd18e90f6a00a280f544bf`.

The delivered P5 slice accepts strict v2 numeric claims with the frozen nested exact-integer value object, binds evidence to approved source/schema, receipt ID, payload hash, and server-derived units, and recomputes exact direct cells, sums, and profile measures. It refuses fabricated or contradictory receipt metadata and fails closed for ranking, difference, batch, and unsupported SQL semantics. Batch, ranking, difference, service envelopes, Agent orchestration, UI, and deployment remain dependent work.

## Problems and resolutions

The independent review found a flat numeric value shape that contradicted the frozen contract, forged receipt IDs and scope units that could pass, and a Radon C-complexity block. The implementation now uses the nested value DTO, binds receipt and unit identity to trusted payloads, and separates payload digest verification to keep complexity within the repository gate. The untested batch helper was removed from this bounded PR and is explicitly deferred to its own slice.

## Hardest technical problem

The hardest problem was preventing self-attested numeric claims from becoming evidence. The solution validates the immutable receipt wrapper before claim evaluation, derives query units from the approved SQL shape and source identity, compares the claim scope and nested value unit, and recomputes the referenced cell or sum from the receipt. This preserves exact integer semantics while keeping unsupported calculations non-publishable.

## Tests, coverage, and gaps

The merged head passes 574 Python tests and 40 Vitest tests. `make gate` passed Ruff formatting/lint, mypy, pytest, Radon complexity (A/B only; enforced average 3.02), TypeScript typecheck, and Vitest. `make coverage` reports 93% total branch-aware coverage (1,399 statements, 380 branches; 79 statements and 36 branch partials missed). The new validation module measures 81% branch-aware coverage; remaining gaps include overflow and several malformed/non-exact branches. Independent QA passed the exact merged head and provider approval was recorded before the guarded merge.

Deployed live LLM behavior, the real v2 Python service producer/envelope, Worker-to-Python runtime parity, rank/tie and difference policies, batch limits, Agent persistence, browser behavior, and Cloudflare preview/final deployment remain unverified in this milestone.

## Next milestone

Implement the focused P5 difference and ranking validator contracts and tests, then deliver the P6 citation validator and P7 v2 Python service envelopes as separate reviewed slices. After those prerequisites, implement the native Agent/ Durable Object coordination and web chat, followed by guarded preview and final deployment smoke tests using the free Workers AI allowance only.

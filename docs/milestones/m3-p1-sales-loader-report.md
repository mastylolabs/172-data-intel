# M3-P1 sales loader report

Date: 2026-10-06
Verified `main`: `5aa93a7dbd64db8cc7e9e41079bb69594d48e39b`

## Delivered behavior

PR [#26](https://github.com/mastylolabs/172-data-intel/pull/26) implements the first M3 capability from the merged C0 contracts. It bundles the distinct 24-row `sales-demo.v1` CSV (1,025 bytes, SHA-256 `a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f`) and exposes a server-owned strict immutable loader. It validates the full identity before file access, caps bytes/rows/physical lines/cells, requires canonical UTF-8/LF CSV framing and header, rejects malformed/coerced dates and signed integers, enforces dimension and paired sign/zero rules, and rejects duplicate IDs. The existing six-row `sales-proof.v1` loader, metadata and receipts remain unchanged.

Independent fixture oracles verify 24 records, 29 net units, 395000 net cents, the January/February/March totals, date range, order, returns, zero row and proof-source separation. The loader is documented but is not registered with the query engine, service routes or Agent.

## Verification and review

- Full `make gate` on the implementation head: Ruff format/check, mypy 28 files, 307 Python tests, TypeScript typecheck, 40 Vitest tests, and Radon A 2.9631 with enforced declaration average A 2.93: pass.
- Independent QA on exact head: clean detached checkout and fresh gate pass; new loader 100% statements/branches (87/87 statements, 30/30 branches), overall Python/scripts coverage 92.5208%; independent hash/oracle, malformed, identity-before-access, immutability and proof-preservation checks pass.
- Both current-head CI runs passed. Configured `172x-reviewer-bot` approved the exact head, provider threads were clear, and guarded squash merge produced main `5aa93a7`.
- Handwritten diff: 337 lines (140 loader/model and 197 tests). The 301–400 count is coherent for strict resource/parser controls, independent oracles and malformed-input regressions; 25 bundled CSV lines and 69 prose lines are excluded.

## Problems and resolutions

The implementation review identified no correctness finding. The main implementation risk was preserving the old proof source while introducing a distinct complete source; separate identity, path, hash, schema/meaning revision and regression tests prevent accidental replacement.

## Hardest technical problem

The hardest part was making the expanded fixture trustworthy without changing the existing proof boundary. The solution keeps the old loader untouched and adds a separate strict model/loader whose manifest is checked before typed rows are returned. This gives M3 a reproducible source while preserving historical receipts and the current engine’s six-row assumptions.

## Limitations and unverified checks

M3-P1 does not implement deterministic profiles, generic engine integration for the complete source, support JSONL loading/search, numerical or citation validation, private v2 service routes, M4 publication, web chat, deployment or live Workers AI. Loader behavior is tested locally and in CI; actual Cloudflare runtime/resource behavior and expanded-source deployed receipts remain unverified. Overall coverage gaps remain in pre-existing modules; the new loader itself is fully covered. No paid billing or live model call occurred.

## Next milestone

Next is M3-P2: deterministic bounded profiling for the approved sales source, with exact integer/currency semantics, explicit omissions and independent profile oracles. It depends on this merged P1 source and the reviewed C0 profile contract. Generic engine integration follows as its own bounded slice; support source/retrieval and claim/citation validation remain separately gated M3 work.

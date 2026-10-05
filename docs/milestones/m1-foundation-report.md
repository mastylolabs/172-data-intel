# M1: Public offline engineering foundation

Status: **complete**, 2026-10-05 UTC. Scope and acceptance criteria:
[delivery plan](../mvp-delivery-plan.md) and [M1 brief](m1-foundation-brief.md).
This is the first foundation milestone; the shareable application remains planned.

## Delivered behavior and merge evidence

- Python >=3.12 src-layout application with public uv dependencies and tracked lock.
- Ruff formatting/linting, strict mypy, pytest, Radon and explicit complexity
  enforcement through the same `make gate` locally and in CI.
- Frozen, versioned source-identity and generic SQL-intent models with strict
  payload limits, malformed-input rejection and lossless valid round-trips.
  These models validate untrusted proposals; they do not authorize or execute SQL.
- Installation, commands, boundaries and remaining work documented in README/TODO.
  The approved build prompt was appended before implementation; excluded material
  and the reference application's prompt history were not imported.

All M1 implementation changes merged in
[PR #1](https://github.com/mastylolabs/172-data-intel/pull/1) at
`2026-10-05T05:23:10Z`. Verified local and remote `main` revision:
**`98408bd9da415522c2ad08c480e77cde72989820`**. Its tree is identical to reviewed
head `00b5f514bad9e7203e89b49952f7a0985c03afbb`.

Independent QA-v2 returned PASS. Separate review found no unresolved findings;
the configured bot submitted [current-head approval](https://github.com/mastylolabs/172-data-intel/pull/1#pullrequestreview-5410257798).
`agents github gate` passed with two successful checks and zero unresolved threads;
`agents github merge` confirmed MERGED using the configured squash method.
No provider gate or branch protection was changed or bypassed.

The PR contains **362 handwritten changed lines**, within the explained 301–400
coherence allowance. Exclusions: 395 prose lines and 626 generated lockfile lines.
The original architecture remains byte-identical (SHA256
`2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd`).
The separate reference repository, PR and deployment received no changes.

## Problems, resolution and hardest technical problem

An initial engineer gate caught malformed indentation in a generated test fixture;
it was corrected before the initial PR and the complete gate rerun. Independent
QA then demonstrated that default Radon discovery omitted C11 methods in nested
and function-local classes. The first QA report remains preserved as FAIL.

That discovery gap was the hardest problem: a reporting command could succeed
while missing code that violates the mandatory complexity limit. The correction
walks every Python function/class declaration with AST and uses Radon's scoring,
counting each declaration once. This retains established scoring while making
discovery explicit. Committed nested/local-class regressions reject C+; B10 still
accepts. Fresh independent QA and review verified the original failures and extra
async/decorated/nesting probes. One of two allowed feedback returns was used.

## Tests, coverage and integration evidence

| Check | Actual result |
| --- | --- |
| Final `main`: `make gate` | PASS: Ruff format/lint, strict mypy, 39 pytest tests, Radon and enforced thresholds |
| Complexity on `main` | Canonical average A2.533; all-declaration enforced average A2.84; no C+ declaration |
| Final `main`: `make coverage`, macOS / CPython 3.14.2 | 39 passed; 43/43 statements and 11/12 branch destinations; total 54/55 = **98.18%** |
| Package coverage locally | 15/15 statements = **100%**; no executable branches |
| Checker coverage locally | 28/28 statements = **100%**; 11/12 branches = **91.67%** |
| [Merged-main CI](https://github.com/mastylolabs/172-data-intel/actions/runs/37267552390), CPython 3.12.15 | SUCCESS: frozen install, full gate and coverage; 39 tests each run; 52/52 statements, 11/12 branches; total 63/64 = **98.44%** |
| Independent same-tree package integration | PASS: canonical install, lock check, README import, wheel/sdist build and wheel-source inspection |
| Applicable TypeScript/browser/deployed checks | Unrun: M1 contains no TypeScript, UI, service or deployment |

Python versions count executed annotations differently, accounting for the
statement-denominator difference. The sole uncovered branch is
`scripts/check_complexity.py:46->exit`, the non-main import guard. Dependency and
Pydantic internals are excluded. Extra independent async/decorated probes are
observed evidence, not permanent regression tests. Local receipts, versioned QA
and review reports and coverage JSON are retained under `.git/172x/`.

## Remaining limitations and next milestone

SQL execution, datasets/profiles, retrieval/citations, deterministic claim checks,
Workers AI, native Agent/durable sessions and web chat are not implemented in M1.
No live analytical calculation or deployment result is claimed. Engine/runtime
compatibility and operational limits remain unverified.

Next proposed milestone: **M2, deployed Agent–Python–AI compatibility proof**.
Review runtime/access/execution contracts first, then use small PRs to prove real
generic SQL execution, Llama 3.3 integration and persistent isolated state with
distinct Cloudflare resources. Present evidence and options if that boundary
cannot work. No M1 decision remains open; user instruction is required to begin M2.

This report is saved locally after verifying merged `main`; it is not part of the
implementation PR. Work stopped at the requested milestone checkpoint.

Continuation addendum: the user reviewed M1 and gave full GO for all remaining
milestones at 2026-10-05 05:41:21 UTC, retaining a report after each. That later
instruction supersedes the pause; M1 evidence and verified revision above remain
unchanged. This known report may join the scoped M2 prerequisite-document PR.

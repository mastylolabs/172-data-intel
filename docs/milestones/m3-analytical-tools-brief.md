# Build brief: M3 reproducible datasets and verified analytical tools

## Result, authority and sources

**M3-BRIEF-v1**, 2026-10-05. Outcome: reproducible synthetic sources and bounded Python analytical tools whose results, search evidence and mechanical claim checks can be independently verified. Authoritative implementation baseline: `origin/main` **`41af237377aa959c55ecbdbf1a72f45f2b730866`**, inspected through Git objects; this does not assert the shared working branch is at that revision. This is a prebuild brief, not implementation readiness or M2 completion evidence.

The original build and subsequent full GO in [PROMPTS.md](../../PROMPTS.md) authorize continued approved milestones, guarded merges and scoped deployments with reports after each. The continuation recorded 2026-10-05 20:48:37 UTC requires routine model mocks, free Workers AI allowance only for live LLM checks, no paid billing enablement or credit purchase, and continued independent work if quota is exhausted. Independent specialist readiness, QA, current-head configured bot approval and provider gates remain required; no new routine human approval is requested.

| Source / identity | Evidence used and limit |
| --- | --- |
| [AGENTS.md](../../AGENTS.md), [delivery plan](../mvp-delivery-plan.md), immutable [architecture](../architecture.md) | Engineering gate, small complete PRs, Python ownership, source grounding and validation responsibilities. Architecture SHA256 `2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd`; preserve it unchanged. |
| Baseline above: [M2 contracts](m2-runtime-contracts.md), [threat controls](m2-threat-controls.md), [proof experience](m2-proof-experience.md), `src/data_intel/` and query/fixture/service tests | Existing source/version/hash and exact numeric transport, generic bounded read-only SQLite, private service and proof separation. Inspection is not a fresh test run. Current source metadata is specifically the six-row sales proof; M3 cannot silently replace its identity. |
| Baseline [P3b report](m2-p3b-agent-report.md) and subsequent planning/budget reports | Reported integration/state work is historical input. M3 acceptance and the complete live Llama chain are not certified by this brief; no final M2 acceptance report was inspected. |
| Read-only reference `/Users/zbigniew/dev/code/172x-data-intelligence`: `sources.py`, `execution.py`, `validation.py` | Reusable ideas: strict identifiers, source hashes, bounded lexical evidence and exact-quote checks. Its fixed sales operations and weak numeric token membership are unsuitable substitutes for generic SQL and claim-to-evidence validation. Its gross-dollar sales meanings differ from the target's signed net cents. No prompt history was consulted or imported; verify adapted behavior in this repository. |

## Actors, scope and non-goals

A contributor reproduces fixture loading, profiles, queries, searches and validations locally. An independent QA engineer checks results against separately calculated fixture oracles. Later Analyst/Validator roles consume typed, bounded tools; this milestone does not publish a supported chat answer.

In scope: complete sales CSV and support JSONL fixtures; server-owned source identities and explicit field meanings; deterministic bounded profiling; approved-source generic SQL; targeted support search with exact IDs/quotes and declared limits; typed numerical/citation validation; private Python service contracts and integration checks. Keep the reviewed Python/runtime/query safety boundary; changes require affected review.

Defer model planning/clarification and semantic query-meaning judgment, independent model validation, candidate answer publication, conversation/UI changes, uploads, connectors, OAuth, PostgreSQL, Parquet, vector search, whole-corpus classification, containers, distributed execution and scale claims. Preserve the reference repository, PR and deployment. M3 tools must not present mechanical validation as analytical or semantic approval.

## Stable requirements

| ID | Required behavior |
| --- | --- |
| BR-M3-01 | Bundle reproducible synthetic sources with documented provenance, schema/meaning revisions, actual byte hashes, approved server paths and strict typed loading. Define grain, units, signs, nulls, dates/time zones, uniqueness and period boundaries explicitly; no model guesses or client-authoritative hashes. |
| BR-M3-02 | Compute deterministic sales/support profiles from actual approved data; bound context and disclose every omitted detail. Preserve exact money/integer semantics and declare non-exact values. A changed source or meaning cannot reuse an old identity or invalidate historical receipts silently. |
| BR-M3-03 | Extend the reusable query boundary to the reviewed sales source without named sales-operation dispatch. Preserve deny-default read-only policy, execution/result limits, actual SQL/source receipts and refusal rather than incomplete success. |
| BR-M3-04 | Search support text using reviewed targeted lexical matching and explicit filters/ranking/limits. Return source identity, message IDs and exact source quotes; explain what was searched and what was omitted. Hits/no hits cannot establish corpus trends, prevalence or absence. |
| BR-M3-05 | Validate typed numerical claims against identified query results, units, scope and explicitly supported calculations; validate citations against retrieved approved evidence. Reject fabricated/stale/cross-source evidence and unsupported claims. Numeric token membership alone is insufficient. |
| BR-M3-06 | Keep profiling, execution, calculations and deterministic validation in Python >=3.12; expose strict versioned private service inputs/results with bounded errors. Preserve cross-runtime parity and existing private access controls; source text never grants tool authority. |
| BR-M3-07 | Deliver scoped PRs with relevant tests/docs, canonical gate, independent QA/review, measured coverage and truthful milestone receipts. Routine tests are offline/mocked; no paid LLM or unrelated deployment work. |

## Acceptance criteria and status

All **AC-M3-01–08 are unverified** at this handoff. Existing six-row test expectations are inputs, not acceptance evidence for the complete datasets.

| ID / trigger | Observable result and required evidence |
| --- | --- |
| AC-M3-01 — Contributor loads both bundled sources (BR-01) | Actual bytes reproduce declared hashes and typed rows; explicit meanings cover every field. Missing/extra columns, duplicate IDs, invalid encodings/types/dates, unsupported nulls, oversized input and source/meaning mismatch fail clearly. New identities coexist truthfully with historical proof receipts. |
| AC-M3-02 — QA profiles approved data (BR-02) | Independently known row counts, ranges, null/dimension facts and exact numeric statistics agree; deterministic repeated output and bounded profile omissions are tested. Profile limits and empty/invalid-source behavior are explicit. |
| AC-M3-03 — QA executes varied and novel sales SQL (BR-03) | Filtering, aggregation, grouping, ranking/ties and period comparisons match independently calculated fixture results, including returns/zero/period edges where meanings permit. Record exact SQL/hash/units; unsafe/malformed/excessive queries still refuse under existing controls. |
| AC-M3-04 — QA searches support (BR-04) | Independent expected IDs/order/quotes agree for matching, filters, ties, no-hit and overflow cases. Every quote resolves exactly to its source message; searched scope, matching rule and omissions remain inspectable. No-hit and hit receipts carry the coverage limitation. |
| AC-M3-05 — QA mutates numerical evidence/claims (BR-05) | Wrong values, units, periods, denominator/calculation bindings, stale hashes or unsupported result references reject; valid exact claims pass. Tests distinguish non-exact SQL values and mechanical checks from semantic query/answer approval. |
| AC-M3-06 — QA mutates citations/coverage claims (BR-04/05) | Fabricated IDs, changed quotes, non-retrieved or cross-source citations and unsupported whole-corpus assertions reject under the reviewed typed contract. Literal search words do not themselves become affirmative analytical claims. |
| AC-M3-07 — QA calls private service boundaries (BR-06) | Strict request/result versions and Python/TypeScript parity, if exposed, pass integration checks; malformed/unapproved operations fail safely. No source-path selection, unbounded evidence, secrets or unsupported answer publication is introduced. Identify local versus deployed checks separately. |
| AC-M3-08 — Coordinator closes M3 (BR-07) | Implementation PRs are merged through guarded gates; report verified main/PR links, full gate and applicable TypeScript checks, independently measured unit coverage/counts/gaps, integration/deployed failures or unrun checks and remaining M2/live-AI uncertainty. No unsupported completion claim. |

## PR boundaries and first implementation handoff

Each PR targets 200–300 handwritten added+deleted lines after formatting and never exceeds 400, including tests/scripts/config; explain 301–400. Bundled datasets, prose and generated locks are excluded but reviewed. Split complete increments if needed; do not compress code or omit tests. These are candidate boundaries, not a fixed PR count.

| Slice | One coherent capability and dependencies |
| --- | --- |
| M3-C0 — prerequisite prose contracts | Architect owns source/schema/meaning evolution, bounded profile/search receipts, claim/result associations and private service versions; security owner reviews the affected threat/control delta. Freeze identical sources and obtain affected independent READY; merge contracts before dependent implementation. |
| **M3-P1 — first bounded foundation** | Complete sales CSV, field-meaning/provenance document, server-owned identity and strict loader with independent fixture oracles/failure tests. Depends on C0. Preserve the existing six-row proof source and executable behavior; do not add profiles, query-policy changes, service routes, support search or model/UI code in this PR. |
| M3-P2 — sales analytical tools | Deterministic bounded sales profile, followed by generic engine integration with the complete source and novel independent SQL oracles; split profile and engine capabilities if needed. Depends on P1 and reviewed query/source contract. |
| M3-P3 — support source foundation | JSONL fixture, explicit meanings/provenance/hash, strict bounded loader and independently checked records. Depends on C0; may proceed independently of sales tools after stable contracts. |
| M3-P4 — targeted retrieval | Bounded support profile/search and exact evidence receipt; split profiling/search if needed. Depends on P3 and reviewed matching/filter/ranking/coverage contract. |
| M3-P5/P6 — deterministic validation | Separate numerical claim/result checks and citation/retrieval checks with independent mutation tests. Depend respectively on stable P2 and P4 receipts and reviewed claim contracts; do not implement the later model Validator. |
| M3-P7 — private service integration | Expose implemented tools through reviewed strict private Python DTOs/routes, affected cross-runtime parity and integration tests; split endpoints if needed. Depends on each exposed tool and merged interface contracts. No public route/access expansion. |

The P1 engineer receives this frozen brief, merged C0 source/meaning/loading contract, baseline contracts/source code, AGENTS.md and the immutable architecture. Proposed affected areas: a distinct bundled sales dataset under `src/data_intel/fixtures/`, focused source/meaning models and loader under `src/data_intel/`, behavior tests under `tests/unit/`, and focused fixture documentation/README/TODO. Exact filenames and schema identity come from C0. P1 acceptance is AC-01's sales portion plus AC-08's per-PR checks: independent expected bytes/hash/row identity, known totals/period examples calculated separately, malformed/boundary failures and proof-source regression checks. No whole-M3 acceptance is claimed from P1.

## Decisions, uncertainty and complete handoff

Facts: origin/main resolves to the full baseline above; original architecture hash is unchanged; the inspected engine is generic and its current approved source is the six-row proof. Observations: existing tests specify real query/failure cases, but no checks were rerun by this author. Inference: adding a separately versioned full source first permits useful offline work without rewriting historical proof identity. Assumptions: none authorize new source semantics, limits, costs or readiness.

**Material architecture/security review is required before affected code.** DEC-M3-01 (architect/data owner): complete fixture schema/meaning evolution, bounded profiles, exactness and source catalog/version migration. DEC-M3-02 (architect/security owner): bounded JSONL loading, lexical/filter/ranking rules, quote/evidence limits and private service/control changes. DEC-M3-03 (architect/validation owner): typed claim-to-result/calculation association, citation scope and mechanical/semantic validation separation. Existing budgets are not implicitly increased. No new UX design or engine selection is needed unless an owner finds a material boundary change. Risks: stale hashes, changed money meanings, result association errors, untrusted support instructions, approximate arithmetic treated as exact, and lexical coverage overstated as corpus knowledge.

- **Receiver/action:** coordinator sends this identical M3-BRIEF-v1 and exact baseline to architect and security/control owners for scoped C0 decisions, then affected independent readiness. After C0 merges, give only P1 to its engineer; QA and configured reviewer remain independent on the current head.
- **Artifact/evidence:** this document, stable BR-M3-01–07 / AC-M3-01–08, cited baseline and source ledger. All M3 criteria are unverified. No engineer, reviewer, provider or deployed success is asserted by this authoring task.
- **Residual decisions/risks:** owned above; return evidence/options if approved runtime or controls cannot support a tool. Changes to frozen source identities require fresh affected review; independent slices may proceed only on stable merged prerequisites.
- **Human/external state:** existing full GO and deployment authority persist, with no paid LLM and no routine approval question. Preserve unrelated work. This handoff changes prose only; no code, branch/index, commit, provider action, merge, deployment or reference write. Report each milestone and continue within authorized scope, keeping incomplete work explicit.

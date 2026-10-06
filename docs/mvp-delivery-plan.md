# Working MVP delivery plan

Artifact: MVP-DELIVERY-v1, 2026-10-04. Active implementation sequence for the
current build prompt in [PROMPTS.md](../PROMPTS.md). This plan supersedes the
proposed milestone sequence in [implementation-plan.md](implementation-plan.md)
for this build; it preserves that document and the original
[architecture](architecture.md) as references. Actual acceptance is recorded in
the [milestone reports](milestones/m1-foundation-report.md).

Continuation authority: the user prompt recorded 2026-10-05 05:41:21 UTC gives
full GO for all remaining approved MVP milestones without intervention. Save a
report after each and continue from stable merged prerequisites. This supersedes
the earlier milestone pauses; engineering, independent review and provider gates
remain unchanged.

The deliverable is a shareable Cloudflare application: a native Agent backed by a
Durable Object, Workers AI with Llama 3.3, Python >=3.12 analytical tools, and web
chat over bundled synthetic sales CSV and support JSONL. Preserve the Orchestrator,
deterministic Data Profiler, conditional Semantic role, Analyst, and independent
Validator as logical responsibilities. Keep bulk data outside model contexts.

## Bounded capabilities and dependencies

Each row is a useful foundation or capability. Candidate PR boundaries describe
coherent changes, not a fixed PR count. Split further when required by the code
budget, keeping tests and documentation with their behavior. Start dependent
implementation only after prerequisite contracts are reviewed and merged.

| Milestone | Dependencies | Capability and candidate PR boundaries | Acceptance evidence |
| --- | --- | --- | --- |
| **M1: Public offline engineering foundation** | Existing guidance and current authorization | Python src-layout, public uv dependencies/lock, canonical tooling and enforced complexity gate, CI, meaningful unit tests, minimal versioned source/query-intent contracts, README/TODO. First boundary is the single foundation PR described in [M1 brief](milestones/m1-foundation-brief.md); split only if a complete change cannot fit 400 lines. | Public local setup; full `make gate`; CI invokes the same gate and fails on C+ complexity; valid contract round-trips and rejection of malformed/unsupported input; measured unit line/branch coverage and gaps. No runtime or SQL-execution certification. |
| **M2: Deployed Agent–Python–AI compatibility proof** | M1 merged; affected runtime, access and execution contracts reviewed | Resolve the smallest compatible deployed Python query engine through a measured probe. Candidate boundaries: public runtime/engine adapter with tiny synthetic correctness fixture and read-only/resource controls; native Agent service binding and Llama 3.3 integration; persistent conversation/source-state proof and preview smoke checks. | Real native Agent → deployed Python engine → Workers AI path; model-generated SQL rather than named sales operations; independently known results for representative filtering, aggregation, grouping, ranking and period comparison queries; persisted source/history survive refresh; isolated sessions; invalid/unsafe queries refuse. Record actual runtime/package versions and failures. If the boundary fails, present evidence and options before adopting an incompatible alternative. |
| **M3: Reproducible datasets and verified analytical tools** | M2 runtime/engine boundary merged | Candidate boundaries: complete synthetic sales fixture, explicit field meanings/source hashes and deterministic profiling; general-query exactness/evidence limits; support JSONL import/profile and targeted search; deterministic numerical/citation validation and typed Python service responses. | Independent fixture totals and novel queries; documented grain, units/null/time meanings; malformed fixtures fail clearly; source hashes identify evidence; query execution/result bounds refuse excess work; exact message IDs/quotes resolve; search limits are explicit and results cannot establish prevalence, whole-corpus trends or absence. Mutated numbers, scope and citations fail deterministic validation. |
| **M4: Durable, independently validated analysis conversations** | M3 source/evidence/validation contracts merged | Candidate boundaries: bounded Analyst planning and clarification/conditional Semantic path; candidate claims plus separate Llama 3.3 Validator context; Agent coordination/publication gate; durable accepted memory, isolation, budgets, retry and interruption handling. | Plans use question/schema/profile/field meanings; ambiguous meaning asks for clarification; Validator checks query meaning, numerical claims, citations and candidate answer before publication; wrong or insufficient claims fail/abstain. Refresh/follow-ups retain selected source and accepted evidence. Duplicate submit, cancellation, disconnect, stale completion and provider failure have explicit safe outcomes; model calls/retries/context are bounded; session separation and secret redaction pass adversarial tests. |
| **M5: Shareable web chat and final deployed acceptance** | M4 merged; affected UI/operational contracts reviewed | Candidate boundaries: source selection, suggested questions and chat/progress; answer/evidence inspection and clarification/failure UI; integration/browser fixes; public setup/deployment instructions and final authorized Cloudflare deployment. | Both dataset journeys and questions beyond suggestions work in the reviewed deployment; evidence is inspectable and candidates remain private until validated. Applicable TypeScript/browser checks, refresh/follow-up/isolation/unsafe-input tests and full Python gate pass. Record real model/provider failures and measured unit coverage. Final report supplies live URL, setup/deploy instructions, examples, test results and limitations. |

The first P3 boundary, **P3a**, adds private Python service routes and bounded
Worker request transport after P2, the source-refresh correction in PR #13,
and the shared transport foundation in PR #15 are merged. Acceptance:
authoritative bounded health/metadata, exact typed query
receipts, stable refusals for malformed/unsafe/oversized requests, no public route,
full engineering gate, measured coverage and a clean non-uploading Worker dry-run.
This foundation does not add the native Agent, AI or deployment; the dependent
restricted Agent/state/budget/proof bridge owns actual deployed service receipts.

P3b is split to preserve the 400-line ceiling after normal formatting:
**P3b-1** is the independently tested TypeScript project/wire-validation foundation
(strict schemas, bounded streams, Python hash parity and root/CI TypeScript gate);
**P3b-2** depends on its reviewed merge and adds the native Agent, authenticated
cookie-isolated engine bridge, Wrangler configuration and service-failure tests.
Deployment, async lifecycle/budgets and AI-chain acceptance remain separate dependent
work; P3b-1 is not a deployable Worker.

M2 preview resources must use distinct names from the reference application's
resources. The reference repository `/Users/zbigniew/dev/code/172x-data-intelligence`,
its PRs and running deployment remain unchanged. Reuse inspected sound components
and corrections only through scoped changes and fresh verification here; exclude
its prompt history entirely. No deployment happens in M1.

## Reviews that affect this MVP

The [architecture review](architecture-review.md) is planning evidence, not an
application readiness verdict. F-02/03/14 motivate M1 boundary validation, bounded
payloads and public tooling. F-04 makes the early M2 deployed probe mandatory.
F-01/05/09/10 govern M3 deterministic profiles, targeted retrieval, claim checks and
source/meaning versions. F-07/08/11/12/15 govern M4 state authority, budgets,
isolation, durable evidence and publication. The original architecture stays
byte-identical. Larger-workload partitioning, distributed recovery, scale/capacity
recommendations and broader source capabilities remain deferred.

Later milestones need focused runtime, data, security and UX handoffs before their
affected implementation. M1 has no external execution or user interface and fits a
bounded `172X dev-loop` without separate UX, runtime-selection or threat contracts.
This is a workflow-scope statement, not approval of downstream policies.

## PR delivery and evidence

Follow [AGENTS.md](../AGENTS.md), Conventional Commits and the 172X guarded process.
Verify project activation and configured reviewer access. Give each engineer a
bounded handoff; keep implementation, independent QA and review separate. Target
200–300 changed handwritten lines per PR; explain 301–400 and never exceed 400.
Count additions plus deletions after normal formatting across code, tests, scripts
and handwritten configuration. Exclude and individually review prose, generated
files, locks and bundled datasets. Do not compress code or omit tests to fit.

Each PR records scope, dependencies, acceptance evidence, measured code-line count
and exclusions. Run the canonical `make gate`, enforce Radon A/B acceptance, and
run applicable TypeScript/browser checks. Fresh affected checks, independent QA
and configured provider bot approval must apply to the current head; resolve
required findings and preserve branch protection/provider gates before guarded
merge. The user authorizes scoped implementation, guarded merges and Cloudflare
preview deployments; routine per-PR confirmation is unnecessary. An explicit
inspection hold applies only to the named PR. Approval does not waive gates.

Measure unit line and branch coverage for implemented code and report uncovered
paths. The behavioral target is meaningful success, failure and boundary coverage;
the user supplied no percentage threshold. Do not report mocked model plumbing as
live model-quality or deployed compatibility evidence.

## Milestone checkpoints and exclusions

After each milestone, confirm its implementation PRs merged into `main`, rerun its
acceptance checks and save a report under `docs/milestones/`: delivered behavior,
PR links, verified main revision, problems/resolutions/remaining issues, hardest
technical problem/solution/rationale, measured coverage and test counts/gaps,
integration/deployed failures or unrun checks with reasons, and the next milestone
and needed decisions. Under the continuation authority above, present/save each
report and continue authorized independent work. Record actual blockers without
inventing passed checks or changing billing, scope or provider protections.
Corrections use focused PRs with the same checks and reviews.

Defer uploads, live connectors, OAuth, PostgreSQL, Parquet, vector search,
full-corpus classification, containers, distributed execution and large-scale
benchmarks. Keep operating limits, retention and public-release/license choices
explicit when activated; do not invent account quotas, cost or capacity claims.
Record later user prompts subject to explicit logging exclusions and secret
redaction. The excluded preparation instruction is not part of the prompt log.

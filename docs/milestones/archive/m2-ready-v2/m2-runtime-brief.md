# Build brief: M2 deployed runtime proof

## Result and identity

Artifact **M2-BRIEF-v2**, 2026-10-05; supersedes M2-BRIEF-v1 (SHA256 `a58c8a9cced2c10ffb9f694fe64960c998879a09b7e641d7ce25605e08d74efb`) only for P2/P3 phase ownership, the P4 prerequisite and affected source/handoff identity, following the principal architect's accepted recommendation in M2-ARCH-v3. Outcome: prove a real native Cloudflare Agent → Python >=3.12 generic query engine → Workers AI Llama 3.3 integration with persistent isolated source/history state. Depends on merged M1 at `98408bd9da415522c2ad08c480e77cde72989820`. Workflow: scoped `172X idea-to-build`; prebuild independent review returns used **0/2**; this is owner sequence reconciliation. Scope, non-goals, BR constraints and AC outcomes are unchanged. This brief is not implementation readiness or runtime certification.

The latest user instruction, recorded 2026-10-05 05:41:21 UTC in [PROMPTS.md](../../PROMPTS.md), gives full GO for all remaining approved MVP milestones without intervention, retaining reports after each. It supersedes the older milestone pauses and routine human build/merge gates. Scope and independent specialist readiness, QA, current-head bot approval, guarded merges and provider protections remain mandatory. Preview deployment is already authorized; no new permission request is needed within scope.

## Source and authority ledger

| Consulted source / identity | Supported direction or observation | Limits |
| --- | --- | --- |
| Original build and latest continuation prompts in target [PROMPTS.md](../../PROMPTS.md) | Native Agent/DO, Python analytics, generated SQL, Llama 3.3, durable isolation, early deployed proof and full GO | No larger workload, private-data or alternative runtime authorization |
| [AGENTS.md](../../AGENTS.md); [MVP-DELIVERY-v1](../mvp-delivery-plan.md); [M1 brief](m1-foundation-brief.md) | Small complete PRs, canonical checks, independent delivery and this milestone boundary | Latest continuation supersedes prior pauses; M1 envelopes grant no SQL safety or execution authorization |
| [M1 report](m1-foundation-report.md), merged-main identity above; `src/data_intel/contracts.py` | Report records PR #1 merge, 39 tests and measured coverage; inspected contracts only validate source/SQL proposals | Report evidence is not rerun here; no deployed engine/model evidence exists in M1 |
| Immutable [architecture](../architecture.md); [architecture review](../architecture-review.md) F-02/03/04/07/08/11/15 | Deterministic execution, explicit bounds and versions, state authority/isolation, validation-before-answer publication | Original architecture remains unchanged; proposed refinements require scoped review |
| [Cloudflare mapping](../cloudflare-mapping.md) CF-FEASIBILITY-v2; [validation plan](../validation-plan.md) VALIDATION-v1; ADR [0002](../decisions/0002-python-and-cloudflare-boundaries.md), [0006](../decisions/0006-durable-job-ownership.md), [0008](../decisions/0008-security-and-independent-operation.md) | Dated runtime/package constraints and proposed binding, safety, state and failure probes | These are proposals, not current-platform or application certification; specialist owners recheck activated platform facts |
| Read-only reference `/Users/zbigniew/dev/code/172x-data-intelligence`, inspected HEAD `f91ad87a33e4f8f45d38eb092ec484d6d9164c0b`: `src/entry.py`, `service.py`, `worker/index.ts`, transport/lifecycle tests, ADR-0010 and MVP-TEST-v2 | Useful service-binding/state patterns; documented data-bundling, AI object/string-output and SDK transport corrections; documented quota failures | No prompt history consulted/imported. Its fixed sales operations do not satisfy generic SQL. Deployed receipts are historical reference evidence, not fresh proof here |
| Coordinator preflight, 2026-10-05; inspected `.git/172x/m2-ai-preflight.json` | Supplied doctor/reviewer/Cloudflare access checks pass. Exactly one Llama request returned HTTP 429/code 4006 with daily-free-allocation rejection and `success=false` | Access is not integration success. No billing change, quota-reset time, runtime support or live-AI success is established |
| [M2-ARCH-v3](m2-runtime-contracts.md), READY_FOR_REVIEW, SHA256 `ddfb5fbb1aedae396a6434fc0c42ebf433280c548ea6b0ff6c684a800c1d3c21`; inspected phase/handoff amendment at checkout `27879001213de4c8bc0a656002aadada24a23815` | Accepted owner recommendation: P2 private adapter/build readiness; P3 first restricted Agent/state/budget/proof bridge and actual deployed service-bound SQL/control/version/oracle receipts; P3 engine/control success precedes P4 | Affected independent readiness remains pending; archived M2-READY-v1 identities stay historical; no new runtime/control/AI acceptance inferred |

Authority: explicit current user direction and engineering rules control; preserved architecture and planning findings guide specialists; reference behavior is evidence to challenge and freshly verify. No product conflict blocks defining M2.

## Product intent, actors and bounded scope

An anonymous synthetic-demo session selects a bundled source, submits a clear fixture question and receives an inspectable technical execution receipt or explicit failure. The operator independently checks exact fixture results and refresh/state isolation. A contributor can reproduce offline checks with public tools. M2 proves integration; it does not publish an unvalidated candidate as a supported analytical answer.

In scope: reviewed runtime/query/access/transport contracts; tiny immutable synthetic sales fixture with explicit schema, meanings, hash and independent oracles; bounded generic read-only SQL; private Python analytical boundary; minimal native Agent/AI adapter; persistent selected source and bounded history; safe failure and actual deployed receipts. Selection of the support source may be persisted without advertising an unimplemented support-query capability.

Non-goals: complete datasets/profiling, targeted support retrieval, full conditional Semantic/Analyst/Validator product, validated chat publication, final web chat, uploads/connectors/OAuth, PostgreSQL/Parquet/vector search/full-corpus classification, containers, distributed execution and scale claims. No copying the reference's prompt log or altering its repository, PRs or deployment.

## Constraints and cross-discipline requirements

| Stable ID | Required outcome / source | Responsible owner |
| --- | --- | --- |
| BR-M2-01 | Preserve Python >=3.12 analytical ownership and native Agent/DO plus Llama 3.3; choose the smallest compatible engine through real deployed evidence, not local-wheel assumptions (user; F-04) | Architect and feasibility owner |
| BR-M2-02 | Model generates SQL from bounded question/schema/fixture profile/field meanings; one reusable query interface supports filtering, aggregation, grouping, ranking and period comparisons, rather than named sales operations (user) | Architect; scoped engineers |
| BR-M2-03 | Approved data only; read-only execution, forbidden access/effects and declared execution/result/context/model-call/retry bounds enforced by code, with clear refusal (user; F-02/03/11) | Security/architecture owners; engineers |
| BR-M2-04 | Server-owned isolated anonymous session state persists source/history across refresh; no client-selected foreign state or parallel authority; interrupted work has a truthful outcome (user; F-07/08/11) | Architecture and UX owners |
| BR-M2-05 | Versioned typed cross-runtime receipts identify actual SQL, source/hash/meaning, result limits and runtime/engine/model versions; exact numeric transport cannot silently lose precision (user; F-02) | Architecture/data owners |
| BR-M2-06 | Inspectable integration success/failure with no unsupported chat answer before later validation; secrets and source instructions cannot gain tool authority (architecture §§16–18; F-11/15) | UX/security owners |
| BR-M2-07 | Preserve reference resources and original architecture; public dependencies; scoped PRs with fresh QA/bot/guarded merge evidence and measured coverage/report (user; AGENTS) | Coordinator; engineer; QA/reviewer |

## Acceptance criteria

All **AC-M2-01–07 are unverified** at this prebuild handoff. Criteria inherit their cited BR/source; runtime/security decisions below block affected implementation, not authorized specialist preparation.

| ID / actor, condition and trigger | Observable result and acceptable evidence |
| --- | --- |
| AC-M2-01 — Specialists review the runtime/access/query/state contracts (BR-M2-01/03/04/05/06) | Identified compatible architecture/UX/security boundary and independent READY disposition, with resolved material gaps; prerequisite contracts reviewed and merged before dependent code |
| AC-M2-02 — Operator invokes the deployed native Agent proof (BR-M2-01/02/05) | Actual service-bound Python executes real generated SQL; Llama 3.3 is called in the chain; retained receipts identify deployed versions and Python >=3.12. Local emulation/mocks are separate evidence |
| AC-M2-03 — QA exercises the tiny fixture using varied and novel questions/SQL (BR-M2-02/05) | Filtering, aggregates, groups, ranking and period comparison match independent expected results; record actual SQL, source hash/meanings and exact outputs, not model assertions |
| AC-M2-04 — QA submits unsafe, malformed, unauthorized or excessive work (BR-M2-03) | Writes and forbidden table/file/network/extension/function access reject; execution/result/model bounds refuse deterministically; tests cover limit edges and resource exhaustion under the selected engine |
| AC-M2-05 — Two independent sessions select sources, submit and refresh (BR-M2-04) | Each retains its own ordered bounded history/source; foreign/guessed state or transport writes deny; interruption/failure cannot masquerade as completed proof. Offline and deployed isolation/state probes are identified separately |
| AC-M2-06 — Provider/binding/schema failure occurs or output is malformed (BR-M2-03/06) | Safe classified error, bounded attempts and no false success/unsupported answer; object/string AI response forms and unknown shapes tested; secrets absent from prompts/logs/receipts. Actual quota failure remains failure, not model success |
| AC-M2-07 — Coordinator completes the milestone (BR-M2-07) | Merged PR links and verified main, full Python gate plus applicable TypeScript/proof-surface checks, measured unit coverage/test counts/gaps and real deployed receipts recorded in M2 report; incomplete checks are explicit |

## Candidate PR boundaries and dependencies

Each candidate targets 200–300 handwritten changed lines and must remain ≤400 after formatting, including tests/config/scripts; explain 301–400. Split coherently if needed. Prose, bundled data and generated locks are excluded but reviewed. No engineer receives the whole M2 or MVP.

| Candidate | Scoped deliverable / files or areas | Prerequisite |
| --- | --- | --- |
| M2-C0 | Prose-only reviewed runtime/query/access/state/UX contracts and dispositions; this brief, known M1 report and authorized prompt append may join | Identical brief to design/architecture, security input and independent prebuild READY; no code |
| M2-P1 | Tiny sales fixture/meaning document and reusable bounded engine interface/implementation with independent query/safety tests in `src/data_intel/` and `tests/` | C0 merged; reviewed engine/query policies |
| M2-P2 | Thin private Python adapter, typed request/result parity, public runtime manifests/dependencies, local failure tests and private build/upload/provenance readiness; no SQL execution proof claimed | P1 merged; stable reviewed service/access/provenance contract and affected contract amendment merged |
| M2-P3 | First reviewed restricted native Agent/state/budget/proof bridge with session/source/history and transport safeguards; actual deployed Python service-binding SQL/control/version/oracle receipts through the restricted proof surface; separate preview resources | P2 merged; reviewed state/transport/isolation/budget/proof contracts; private adapter/build readiness. Build/upload alone cannot satisfy engine/control proof |
| M2-P4 | Bounded Llama 3.3 generated-SQL integration and diagnostic receipt smoke tests; setup and measured integration evidence | P3 prerequisite bridge reviewed and merged, with successful actual deployed engine/control proof; reviewed model/input/output/budget contracts. AC-M2-02 still requires the real native-Agent → service-bound Python executing generated SQL → Llama chain |

## Evidence, uncertainty and risks

Facts: build/preview/guarded delivery and uninterrupted milestone continuation are authorized; the accepted architecture recommendation assigns actual deployed service-bound engine/control proof to P3. Observations: v1's M1-only repository inspection is historical; this amendment inspects M2-ARCH-v3's phase/handoff text at the identified checkout and reruns no code or deployed checks. Inferences: the staged bridge resolves the route prerequisite without treating private build/upload as execution proof; reference corrections can reduce avoidable integration defects, but their receipts cannot certify this different generic engine. Assumptions: none authorize technical, privacy, cost or scope decisions.

Unknowns **DEC-M2-01** engine/runtime/package/dialect fit (architect/feasibility); **DEC-M2-02** safe execution/access/result/AI budgets and data disclosure/retention (architecture/security); **DEC-M2-03** state ownership, session/transport enforcement, interruption and proof-surface behavior (architecture/UX). Resolve and review before affected implementation. If the agreed boundary fails, record exact evidence/options and return to its owners; do not silently substitute an incompatible topology. The observed quota rejection leaves live-AI acceptance unverified; independently reviewed engine/service slices may proceed on merged stable contracts, but M2 is incomplete until AC-M2-02 passes. No billing/plan change or invented reset time. Risks: unsafe SQL, precision loss, SDK state-write exposure, unbounded retries, leaking session text and confusing a proof receipt with a validated answer.

## Complete handoff envelope

- **Receiver/action:** coordinator sends this identical M2-BRIEF-v2 with M2-ARCH-v3 to the architecture/UX/infrastructure/threat owners for affected source/mapping acknowledgement, then obtains fresh affected independent readiness against the frozen bundle before dependent phase changes. Keep archived M2-READY-v1's identities historical; prebuild independent returns remain 0/2.
- **Artifact/source identity:** this v2 supersedes the exact v1 hash above only for phase ownership/dependencies and source/handoff identity; M2-ARCH-v3's inspected hash is in the ledger, with historical merged-M1 baseline retained. Stable BR-M2-01–07 / AC-M2-01–07, scope and non-goals are unchanged. Changed artifacts require identified versions and fresh affected review.
- **Acceptance/evidence:** all seven criteria unverified; M1 completion/reference corrections are inspected inputs only. No M2 compatibility, isolation, model success, specialist READY, QA, provider approval or deployment is claimed.
- **Assumptions/decisions:** no material assumptions; technical/security/UX decisions belong to named DEC owners, while user scope and full GO are established. The accepted phase recommendation separates P2 private readiness from P3 actual deployed proof; successful P3 engine/control proof is required before P4, without weakening the real-chain AC-M2-02. Candidate PR boundaries may split to preserve coherence and the hard budget.
- **Residual risks:** listed above; architecture/security/UX define enforceable controls and independent QA tests them at the exact code/deployment versions. Scope failure returns evidence/options without weakening criteria.
- **Human/external state:** user build/merge/preview authority is sufficient; no inspection hold or additional routine human gate. This authoring task performs no code, branch, commit, push, PR, merge, deployment or reference write. Report each milestone and continue within the full GO, preserving independent/provider gates.

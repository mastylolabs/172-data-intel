# Design-to-architecture contract matrix: M2 runtime proof

## Result

**READY — M2-READY-v1**, 2026-10-05. Independent prebuild recommendation for the bounded operator experiment, not runtime acceptance, security certification, QA PASS or provider approval. The reviewer authored none of the five source contracts. Prebuild independent returns remain **0/2**; no material gap requires a return.

The contracts define implementable normal/refusal/recovery behavior without granting the model authority or promising unsupported background lifetime. SQLite remains a conditional deployed experiment, with mandatory controls failing closed. A failed AI preflight does not establish engine incompatibility and cannot satisfy the real-chain criterion. User full GO recorded in target PROMPTS.md at 2026-10-05 05:41:21 UTC supplies existing build/guarded-merge/preview authority; contract merge and independent current-head checks remain prerequisites.

### Exact inspected sources and authority

| Artifact / recorded input state | SHA256 |
| --- | --- |
| [M2-BRIEF-v1](m2-runtime-brief.md), prebuild; all AC unverified | `a58c8a9cced2c10ffb9f694fe64960c998879a09b7e641d7ce25605e08d74efb` |
| [M2-ARCH-v2](m2-runtime-contracts.md), READY_FOR_REVIEW | `32ebdca3c0c64b036fdc707f23fd3a6cdee3ab59c8613ce70dd942568dc6de5d` |
| [M2-UX-v3](m2-proof-experience.md), reconciled / READY_FOR_REVIEW | `b81032a6c02056d532508b1c8c39fa48f72a8f806b0334e2478d77aadfd4af45` |
| [M2-INFRA-v3](m2-infrastructure-assessment.md), READY_FOR_REVIEW | `ec6984e632f729fe0e8e814fd4cf26f4a086dce51546d84922f5d8c58c6595ac` |
| [M2-THREAT-v2](m2-threat-controls.md), READY_FOR_REVIEW | `aab5c23097ea3e9f2691ea9d7f129a2a7a7bb384f8da484859cc5b9c1a03f89e` |
| Preserved [original architecture](../architecture.md) | `2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd` |

Authority: explicit current user direction and AGENTS.md → M2 brief → preserved architecture and active MVP delivery plan → identified reference evidence. ARCH-v2's references to the earlier UX/infra versions explicitly describe amendment provenance; current UX-v3, THREAT-v2 and INFRA-v3 identify and reconcile the exact ARCH-v2. They do not compete as current versions. The review read no reference prompt history and made no reference changes.

## Flow-to-contract matrix

Statuses below evaluate **prebuild contract compatibility**. They do not report implemented behavior. Locations refer to the frozen sources above.

| BR/AC and user step | UX behavior / content | Data and ownership | Interface / authorization | Failure and recovery | Evidence / design status | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| BR-01/03/04/05/06; AC-01; review prerequisites | FLOW-3; diagnostic-only boundary | Python fixture/analytics, native Agent state, private budget DO | ARCH boundaries and rollout; no public SDK routes | Conditional runtime proof fails closed; owners retain evidence/options | **satisfied**: BRIEF lines49/63; ARCH17–27/107; UX12–20; specialist mappings below. Contract merge still pending. | Coordinator |
| BR-01/02/05; AC-02; FLOW-1 submit/poll/inspect | ST-2/3 labels engine versus AI chain and local versus deployed | Server metadata identity, exact executed SQL and each Worker's own provenance | ARCH53–63/75–83/89; one AI then matching bound query | Quota/invalid output fails without chain receipt; no analytical answer | **satisfied**: provenance and success predicates agree with UX20/26 and THREAT CTRL-05/11; actual live chain **unverified**. | Agent/runtime engineers |
| BR-02/05; AC-03; compare execution to oracle | ST-3 includes zero-row query scope; no absence claim | Six declared rows, signed integer cents/units, explicit meanings and independent totals | Generic SELECT/CTE interface; exact integer strings, approximate REAL strings | Duplicate labels, blobs/nonfinite and overflow refuse whole result | **satisfied**: ARCH31–61; UX26; CTRL-02/05. Independent execution/oracle tests **unverified**. | Python engineer / QA |
| BR-03; AC-04; FLOW-3 unsafe/oversized/denied work | ST-4/5/6/10 typed refusal and limits | Only main.sales approved columns/functions; global and session counters | ARCH41–47/67–77/89–93; streamed body/result caps; deny by default | Unsupported source/malformed input zero calls; missing mandatory controls refuse; no partial success/retry | **satisfied**: controls and UX27–33 agree; actual enforcement **unverified**. | Python / outer Worker / budget engineers |
| BR-04; AC-05; FLOW-2 refresh/two sessions/interrupt | ST-1/2/6/8/9/10 retained source/history and truthful terminal state | Server-hashed random cookie; one active owned job; bounded journal/history | ARCH69–85; no client routing/state authority; queued202 only after durable expiry schedule | Cancel/startup/deadline fences; scheduling failure zero dispatch; GET reconciles expiry and never resumes; evicted outcome never reruns while ID retained | **satisfied**: expiry and idempotency states compose with CTRL-08/09; offline/deployed races and lifetime probes **unverified**. | Agent engineer / QA |
| BR-03/06; AC-06; provider/schema/binding failure | ST-7/9 classified failure or bounded clarification, no unsupported answer | Model proposal is untrusted; receipts never become analytical memory | ARCH51–63/89–103 strict schemas, required nullable fields, one call/no retry, safe logging | Object/string output checked; timeout/late result cannot publish; no invented quota reset | **satisfied**: UX30–33 and CTRL-05/06/07/10; failure/secret tests **unverified**. | Agent / Python engineers |
| BR-07; AC-07; FLOW-3 delivery/report | Preserve failed and unrun checks explicitly | Distinct new resources; original architecture/reference preserved | ARCH25/107; AGENTS code budget, independent QA/bot and guarded merge | Disable/rollback identified new versions; no billing or runtime substitution | **satisfied**: INFRA47–51 and CTRL-11; implementation merges, coverage and report **unverified**. | Coordinator |
| Visual/browser accessibility and responsive UI | No screens in M2; textual named status/fields only | Not activated | No browser product surface | M5 owns later UI criteria | **not applicable**: BRIEF27–29; UX35–37. Parsing/serialization remains required. | Later UX owner |

## Activated specialist contracts

Every row is **satisfied as a compatible design obligation; implementation unverified**. Later QA/security reviews must inspect the exact code/head and deployed receipts. No control is approved as working by this review.

| Criterion | Required property and realization | Verification owner / exact evidence | Gap |
| --- | --- | --- | --- |
| CTRL-01 | Bearer before lookup; exact mutation Origin; server cookie/DO name; deny SDK writes/Upgrade; private Python | Outer Worker/Agent engineers; independent QA/security. THREAT62 ↔ ARCH67–75 ↔ UX18/29 | None |
| CTRL-02 | Trusted fixture bytes/hash/schema/meaning and server identity; no support fallback | Python engineer; QA mutated fixtures/identities/oracles. THREAT63 ↔ ARCH31–37/53/57 ↔ UX28 | None |
| CTRL-03 | Fresh in-memory, read-only, default-deny authorizer; unchanged single SQL; required sales read | Python engineer; QA/security denied categories and cleanup. THREAT64 ↔ ARCH41–43 | None |
| CTRL-04 | Verified SQLite/heap/progress limits; fail closed when unavailable; no thread/CPU guarantee | Python/runtime engineer; QA actual control/exhaustion probes. THREAT65 ↔ ARCH41/45 ↔ INFRA22/25 | None |
| CTRL-05 | Incremental caps; strict receipts; exact integer/approximate REAL; Python/TS digest parity; own actual UUID/build | Python/Agent engineers; QA/security golden, boundary and provenance probes. THREAT66 ↔ ARCH51–63 ↔ UX20/26 | None |
| CTRL-06 | Bounded untrusted SQL-or-clarify proposal, no synthesized answer or receipt truth in memory | Agent engineer; QA/security output/injection cases. THREAT67 ↔ ARCH81/89 ↔ UX32 | None |
| CTRL-07 | Durable admission/count before calls; one AI/query, no retry; global counts survive cookie rotation | Agent/budget engineers; QA caps/concurrency/failures. THREAT68 ↔ ARCH89–93 ↔ UX33 | None |
| CTRL-08 | Durable queued identity/expiry, best-effort dispatch, generation/source/deadline fences; GET recovery | Agent engineer; QA scheduling failure, duplicates, expiry, restart and stopped-work probes. THREAT69 ↔ ARCH77–83 ↔ UX31–33 | None |
| CTRL-09 | Whole-state byte bound, latest receipt/history/journal bounds; seven-day logical expiry/reset | Agent engineer; QA/security renewal/eviction/cleanup races. THREAT70 ↔ ARCH71–85 ↔ UX24/33 | None |
| CTRL-10 | Environment secrets; safe errors/log allowlist; content only in authorized context/state/receipt | Owning engineers/operator; QA/security sentinel scans. THREAT71 ↔ ARCH67/93/103 ↔ UX30/51 | None |
| CTRL-11 | Conditional target proof, public pins, reviewed build/version/deployment mapping, protected rollout | Runtime engineer/coordinator; QA/security exact runtime/config/receipts. THREAT72 ↔ ARCH25/55/63/107 ↔ INFRA23/47–49 | None |
| INFRA runtime and lifecycle | Python >=3.12/SQLite/FFI/control fit measured on target; 60s is a fence, not promised lifetime | Runtime/Agent engineers; INFRA21–25 ↔ ARCH27/55/83; streaming and background observations pending | None in experiment design |
| INFRA operating/cost/rollback | Separate new resources; measured safe metadata; no total bill/SLO/restore guarantee or plan change | Coordinator/operator; INFRA27–50 ↔ ARCH25/91/103/107; actual meters/account allowances unknown | None in experiment design |

## Gap register

No material REVISE/BLOCKED item was found. Expected experiment evidence is not a missing prebuild contract. The actual AI failure is retained below as an acceptance blocker, not silently accepted risk or a passed check. Any changed source invalidates affected rows and requires owner correction and fresh compatibility review.

## Evidence and uncertainty ledger

- **Facts:** target PROMPTS.md's latest full GO supersedes routine milestone pauses, preserving reports; AGENTS/current plan preserve independent gates and the hard code budget. BRIEF49–55 defines M2's diagnostic acceptance. No billing/plan upgrade or incompatible boundary is authorized.
- **Observations:** all six SHA256 values verified with `shasum -a 256`; five source documents, AGENTS, current delivery plan, original architecture and target continuation text inspected. Sanitized `.git/172x/m2-ai-preflight.json` shows one Llama request, max_tokens8, HTTP429/code4006, success=false and daily allocation rejection. Resource inventory contains only the two reference-prefixed Worker names, with recheck required before provisioning. No credentials were read.
- **Baseline engineering observation:** `make gate` in the target repository passed: Ruff formatting/lint, strict mypy, 39 pytest tests, Radon average A2.5333 and explicit complexity enforcement average A2.84 with no C+ function. This checks the existing M1 code only; it supplies no M2 runtime/control evidence or measured M2 coverage.
- **Inference:** current typed contracts and state/error transitions compose because producer/consumer limits, identity predicates, job fences and diagnostic labels agree. Conditional controls make unsupported runtime behavior a recorded failure instead of requiring an engineer to invent a fallback.
- **Assumptions:** no material product/security/runtime premise is assumed as fact. Ordinary implementation choices must preserve these contracts; target compatibility remains an experiment outcome.
- **Decision:** READY for contract delivery and the authorized bounded experiment; no preferred framework or future workload recommendation added. Readiness concerns the identified design only.
- **Unknowns:** pinned target package/runtime/control availability, streamed FFI enforcement, total isolate fit, actual Native Agent background lifetime, real AI-chain availability, operational meters and all implementation checks. Owners/pass conditions are named above. No external documentation was freshly researched by this review; platform claims are identified specialist inputs and require target evidence.

## Residual risks and follow-ups

| Risk / evidence | Blocking? | Pass condition / next owner |
| --- | --- | --- |
| Live model access rejected in one actual preflight | Blocks AC-02 completion; does not block independent contract/engine work | Coordinator obtains successful bounded real Llama chain within existing authority; retain failure if unavailable, without billing change/reset-time inference. |
| SQLite/Python/WASM controls or resource fit may differ from local | Blocks runtime acceptance until proved | Runtime/Python engineer and independent QA demonstrate required target controls and exact oracles; missing control fails closed with evidence/options. |
| Best-effort background work may stop; stale completion/expiry races | Blocks state acceptance until tested | Agent engineer and QA produce success plus scheduling/stopped-work/expired-read/cancel/restart receipts; no resumption/lifetime guarantee. |
| Bearer/cookie possession, physical provider storage and in-flight cost | Does not expand M2 authority | Operator maintains restricted transport, minimal logical retention and measured safe diagnostics; no account identity, forensic deletion, bill ceiling or production certification claimed. |
| Generated SQL may be semantically wrong despite valid execution | Supported-answer publication remains deferred | M2 labels unvalidated receipts; later Validator milestone owns analytical meaning/claim checks. |

## Acceptance and handoff envelope

- **Receiver/action:** coordinator; record this independent READY disposition, deliver the reviewed prose contracts through the authorized QA/bot/guarded process, and permit scoped dependent implementation only after prerequisites merge. This reviewer does not dispatch engineers.
- **Artifact/source state:** M2-READY-v1 at `docs/milestones/m2-readiness-review.md`; exact five source identities above, original architecture unchanged, prebuild return count0/2. The matrix evaluates prebuild compatibility only.
- **Acceptance:** AC-M2-01 independent compatibility disposition is **satisfied**, but AC-01 as a whole remains **unverified** until contract merge. AC-M2-02–07 remain **unverified**; AC-02 includes the known failed preflight and no successful real chain. CTRL-01–11 are compatible specified obligations, with implementation/control satisfaction **unverified**. UI dimensions are **not applicable** in M2.
- **Evidence limits:** documentary inspection and sanitized supplied observations; no M2 code/control/runtime/model/browser tests or QA/security verdict supplied. No code/commit/provider approval/merge/deployment, reference write or prompt-history import performed by this review.
- **Assumptions/open decisions:** none material for this experiment's implementability; actual runtime compatibility and AI availability are unresolved outcomes owned above, not authority to choose an incompatible fallback or spend.
- **Residual risks:** listed above with next owners and pass conditions; preserve incomplete evidence in milestone reports.
- **Human/external gate:** latest user full GO is already evidenced, so no routine confirmation is pending. READY is this reviewer's local recommendation, not a new user approval or any provider action. Independent current-head engineering/QA/security as applicable, configured bot approval, provider protections and guarded delivery remain required.

# Risks and questions

Artifact: RISKS-v1. Original planning research: 2026-10-04. **Proposed; not implemented.**
Uses the same DEC-01–DEC-07 register as [BRIEF-v1](engineering-brief.md).
Workers AI with Llama 3.3 and isolated anonymous sessions over bundled synthetic
datasets are specified MVP directions. Runtime compatibility and model behavior
remain unverified until tested. The remaining recommendations concern enforcement,
policies, and future work; they do not reopen model or demonstration-scope selection.

## Decisions for the human owner

| ID | Decision and recommended option | Alternatives and trade-off | Needed before |
| --- | --- | --- | --- |
| DEC-01 | Accept Python as primary language with a thin JS/TypeScript Cloudflare Agents integration when needed; Python contracts/rules/control/execution, a compatible general SQL engine and durable Agent memory; Workflows are a future long-job option | An all-Python SDK integration needs a compatibility proof; native Python DO/Workflow support alone does not establish npm Agents SDK parity. A large TS rewrite conflicts with the intended primary language and duplicates logic. | Runtime spike and public toolchain selection |
| DEC-02 | Define semantics and supported questions for synthetic sales CSV with model-generated SQL and synthetic support JSONL with targeted search | The two-dataset direction is established for planning. PostgreSQL, Parquet, live Slack/OAuth, vector search, and exhaustive classification remain future work; specify extension contracts separately. | Connector and golden-question scope |
| DEC-03 | Approve a conservative experimental envelope and choose total job/monthly spend, latency, supported file/query shapes, concurrency and evidence limits; candidates are in MVP-v1 | Larger defaults increase latency, source pressure and model cost. No throughput/cost/SLA values have been measured. Use observed small/medium results to set a published envelope. | Budget/admission implementation and large/target-platform tests |
| DEC-04 | Exact structured SQL results; cited targeted text evidence; frozen fixture scope and agreed definitions; no silent approximation or prevalence inference. Choose durable-memory, interrupted-job, retry/replan/cancel, publication, and retention policies. Future broad counts and live DB snapshots need separate contracts. | Exact replay of long mutable-source jobs may require a snapshot/export with storage, privacy and source-load cost. Sampling/approximation is viable only with an explicit answer contract. Future distinct-message theme counts differ from thread/ticket/customer prevalence; targeted MVP evidence supports neither whole-corpus count nor absence. | Analytical, freshness, recovery and evidence contracts |
| DEC-05 | Use isolated anonymous sessions over bundled synthetic datasets; define server-owned session enforcement, protected secrets, Workers AI/Llama 3.3 data handling, retention/deletion, safe queries, and per-session/global limits | Authenticated private workspaces, login, OAuth, enterprise tenancy, sensitive data, and uploads are future work. Sharing synthetic fixtures does not authorize access to another session's history, jobs, or evidence. | Anonymous-session enforcement, model-data handling, and deployment |
| DEC-06 | Choose public project/sample license (MIT or Apache-2.0 are candidates), maintenance expectations and an operating budget | License is the owner's decision; third-party sample acquisition/redistribution must be checked separately. The current repository has no evidenced release-license decision. Private 172X tooling cannot be required to build or operate it. | Public code/sample redistribution and release |
| DEC-07 | Review the packet and proposed ADRs, request changes or authorize a specified next stage | Authorize a bounded milestone and follow AGENTS.md for routine QA/bot-approved guarded PR merges. Deployment needs its own authorization; a proposal is not previous-build approval. | Next milestone scope and checkpoint |

The cleanup preserves PROMPTS.md unchanged. Record technical decisions in the
relevant proposed ADR only when their scope and authority are established; do not
import approvals, sessions, or verification from the previous build.

## Material risks and mitigation ownership

Likelihood is unquantified unless later measurements establish it. Impact and
concrete failure are more useful than invented risk scores at this stage.

| Risk | Failure and evidence | Mitigation / owner | Scope and residual uncertainty |
| --- | --- | --- | --- |
| Runtime mismatch | Linux analytics wheels or npm Agents semantics assumed to work in Pyodide; local tests pass, deployment fails | Compatibility spike with pinned Python/SDK packages, schema parity and public fallback; feasibility owner | MVP and scale; documented support is not selected-package proof |
| Overstated scale | Stable agent diagram mistaken for uniform cost/latency over 20 MB–2 TB | Publish measured workload envelope; execution adapter and admission; infrastructure/QA | Both; no dataset/concurrency benchmarks performed |
| Native platform documentation drift | Current Workflows pages conflict in some tabulated/prose limits; newer Basin/Container capabilities invalidate older assumptions | Preserve conflict in mapping, pin versions and verify actual account/runtime; feasibility/operations | Both; quota and plan-specific behavior untested |
| Unbounded metadata/intermediates | Thousands of columns/groups/partitions or long text bypass row-only caps | Byte+token+cardinality limits, paged manifests, externally stored results, explicit refusal; architecture/backend | Both; budgets await approval and tests |
| Incomplete targeted/future corpus evidence | Top-k candidates or prose partition summaries presented as all-source frequency | MVP targeted-scope labels; future canonical eligible IDs, coverage ledger and deterministic reducer; analytical/QA | MVP refuses broad claims; future exhaustive coverage still cannot prove semantic labeling accuracy |
| Aggregate/join bias | Averages of averages, summed distinct counts or join multiplication produce credible wrong results | Exact merge algebra/grain contracts, independent reference queries and adversarial fixtures; Python execution/QA | Both; complex future operations may require a different engine |
| Correlated Validator failure | Analyst and second model agree from the same inadequate evidence | Claim-evidence contract, deterministic invariants, authorized audit queries and independent context; validation owner | MVP; model quality is empirical, never guaranteed by role separation |
| Duplicate effects/recovery | Retried job/exec commits twice, checkpoint missing after write, late result wins after cancel | Stable work keys, canonical committed receipt, state-owner fencing and fault injection; control/execution owners | Both; cross-store transactions are not automatically provided |
| Mutable source semantics | Profiling/query/audit observe different versions or currency meaning changes under unchanged field name | Snapshot/source/schema/semantic versions, explicit freshness policy and compatible-resume rules; connector/semantics owners | Both; live DB snapshot durability across crash is not automatic |
| Authorization/content attacks | Source text induces tools, SQL reads files, guessed IDs reveal another anonymous session's history, job, or evidence, logs contain credentials | Server-owned session/bundled-source policy, constrained plan compiler, least privilege, source content as data, safe logs; security/backend owners | MVP; full threat/control review required before actual trust boundaries are built |
| Read-only API overprivileged token | Query cannot write SQL but credentials can mutate R2/catalog | Negative permission tests and minimum effective token capability; deployment/security owners | Future Basin adapter; current official examples require independent scrutiny |
| Ineffective cancellation | HTTP abort leaves Container subprocess or source query running; retries launch extra work | Executor-native abort/process ownership, generation fencing, actual cancellation reporting; control/backend | Both; outstanding provider charges may remain unavoidable |
| Future near-data compute claim | Edge or Container location assumed to equal R2/DB location | Actual scan/remote-read and latency measurements; push query to source or native engine; infrastructure | Both; DO/Container colocation is not guaranteed |
| Retention/provenance conflict | Platform state expires or evidence deleted while citations claim reproducibility | Immutable evidence with approved retention and storage sized to the workload, protected live references, explicit expiration/deletion behavior; operations/security | Both; retention duration and erasure requirements undecided |
| Cost explosion | All-corpus classification, long histories, retries and scans grow linearly or worse | Preflight total budget, bounded fan-out, source/provider concurrency, caches scoped/versioned, actual usage ledger; operations | Both; Llama 3.3 baseline is specified, but actual usage/rates and workload costs are unverified |
| Open-source dependence | Build refers to private package/tool/service or undocumented owner credentials | Public locks/recipes, no private imports, offline fixtures/tests, clean contributor audit; maintainer/QA | MVP; public license and operating model pending |

## Questions requiring evidence rather than preference

- Can the native Agent/Python boundary and selected general SQL engine exchange
  typed contracts, persist bounded memory, and handle interruption safely?
  Future DO/Workflow recovery needs separate evidence.
- Does the chosen file executor fit realistic scan/intermediate/spill workloads,
  and when does native Basin SQL or an existing source warehouse outperform it?
- Does Llama 3.3 planning/validation behavior and targeted search meet independent expectations? Future
  whole-corpus classification needs predeclared rare-theme/uncertainty thresholds
  and a total budget.
- Can target-platform cancellation stop owned work, and are duplicate writes,
  anonymous-session isolation, secrets, safe SQL, resource limits, and reconnect behavior correct at every boundary?
- What concurrency, storage retention and p95 latency are measured at the
  contributor's actual Cloudflare plan/quotas and source locations?

These become explicit experiments in [VALIDATION-v1](validation-plan.md) and
[the mapping](cloudflare-mapping.md). They are not decisions an agent can resolve
by preference or architectural confidence.

## Readiness and delivery

No implementation or application verification is present in `172x-data-intel`.
Resolve policies and runtime gaps before affected implementation. The engineering
gate is unavailable without a Makefile/tooling baseline; that is unverified
readiness, not a pass. Within an approved milestone, AGENTS.md requires small PRs,
a hard 400-line handwritten-code cap, independent QA and configured bot approval
on the current head, and guarded merges. Present the milestone report and pause
before the next milestone; deployment is separately authorized.

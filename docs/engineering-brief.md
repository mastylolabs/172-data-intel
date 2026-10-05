# Engineering brief: 172X Data Intelligence

Artifact: BRIEF-v1. Original planning research: 2026-10-04.
**Planning proposal for `172x-data-intel`; no implemented behavior or build approval is recorded.**
Repository path: `/Users/zbigniew/dev/code/172x-data-intel`.

## Purpose and authority

Build toward an independent open-source, evidence-first chat analysis system.
The active proposed MVP uses synthetic sales CSV and support-message JSONL,
model-generated SQL through a general query engine, targeted support search,
a native Cloudflare Agent, durable conversation memory, inspectable evidence,
and independent validation. Python >=3.12 remains the primary analytical language;
a minimal native SDK adapter may use TypeScript after compatibility review.
Workers AI with Llama 3.3 is the MVP model baseline. The demonstration uses isolated
anonymous sessions over the bundled synthetic datasets. These are established
scope directions; runtime compatibility and model behavior remain unverified until tested.

[AGENTS.md](../AGENTS.md) controls engineering and approved-milestone delivery.
The unchanged [original architecture](architecture.md) records design intent.
[PROMPTS.md](../PROMPTS.md) contains the original bootstrap, whose older path and
wider source suggestions are historical context. This brief records the current
planning direction; it does not infer approval from absent previous-build prompts.

## Source and authority ledger

External documentation research is dated 2026-10-04. Keep its update dates and
citations as research provenance; recheck platform facts before implementation.
Documentation does not establish application behavior, capacity, or cost.

| ID / source and version or location | Authority and material content | Conflicts or limits | Status |
| --- | --- | --- | --- |
| S-01: Original bootstrap in PROMPTS.md and current planning direction | Evidence-first chat, Python primary, Cloudflare target, independent operation, and two synthetic datasets in the active MVP | Workers AI with Llama 3.3 and anonymous sessions are specified; budgets, retention, runtime/model behavior, and deployed acceptance remain unverified or open | Planning input |
| S-02: AGENTS.md | Engineering gate, small PRs, independent QA/bot review, guarded merge, milestone reports and checkpoints | Planning recommendations cannot weaken these requirements | Repository authority |
| S-03: docs/architecture.md | Original separation, reasoning roles, durable execution, validation, and provenance | Size examples are aspirations, not benchmark evidence | Unchanged architectural reference |
| S-04: Repository inventory | Guidance, original architecture, prompt history, and planning documents | No application, fixtures, tests, Makefile, pyproject.toml, or runtime/deployment evidence | Documentation-only baseline |
| S-05: [Cloudflare Agents product page](https://agents.cloudflare.com/) | User-named platform overview | Marketing positioning does not establish end-to-end correctness, unlimited computation, or application cost | Consulted |
| S-06: [Agents documentation](https://developers.cloudflare.com/agents/), updated 2026-09-18 | Documents runtime, harness, channels, tools, recovery, and model integration as separate capabilities | Feature availability does not select the product's component or language boundaries | Consulted |
| S-07: [Agents API](https://developers.cloudflare.com/agents/runtime/agents-api/), updated 2026-08-04, and [Agents limits](https://developers.cloudflare.com/agents/platform/limits/), updated 2026-06-03 | Agents require Durable Objects; SDK examples use TypeScript; individual instances are addressed by identity and have finite inherited service limits | SDK compatibility with the selected Python approach is unverified; large numbers of instances do not prove throughput of one instance | Consulted |
| S-08: [Agents with Workflows](https://developers.cloudflare.com/agents/concepts/workflows/), updated 2026-07-12 | Documents complementary real-time Agent interaction and durable multi-step background execution | Successful step persistence is not evidence that arbitrary external effects are idempotent | Consulted |
| S-09: [Python Workers](https://developers.cloudflare.com/workers/languages/python/), updated 2026-09-17; [Python standard library](https://developers.cloudflare.com/workers/languages/python/stdlib/), updated 2026-06-22; [Python packages](https://developers.cloudflare.com/workers/languages/python/packages/) | Python Workers and service bindings are documented; execution uses Pyodide; library and runtime constraints must be checked | A local CPython package install is not proof of deployed Worker compatibility | Consulted |
| S-10: [Python Worker examples](https://developers.cloudflare.com/workers/languages/python/examples/) and [Python Workflows SDK](https://developers.cloudflare.com/workflows/python/), both updated September 2026 | Document Python Durable Objects and Python Workflow entrypoints, including compatibility flags | Do not assume that Python Durable Objects or Workflows are unavailable based on older information; selected SDK/tool combinations still need a spike | Consulted |

Explicit current user direction governs product intent and authorized scope;
AGENTS.md governs engineering. Architectural intent and dated vendor documentation
supply design inputs, not approval or measured application readiness.

## Product intent, actors, and scope

An anonymous user selects a bundled synthetic dataset, asks a question, inspects
execution evidence, and receives a supported answer or explicit limitation/clarification.
Server-owned session scope isolates conversations, memory, jobs, and evidence while
allowing shared read-only synthetic fixtures. A contributor can reproduce fixtures
and offline tests through public tools. Session enforcement details, model-data
handling, retention, license, and operating budget remain policy decisions.
No persona research or private ecosystem behavior is assumed.

The active MVP needs typed source/capability/query/search/evidence contracts,
bounded model context, deterministic calculations and checks, separate Validator
context, durable chat/source/accepted-answer memory, and explicit interrupted-job,
retry, cancellation, and publication behavior. Protected secrets, safe generated-SQL
execution, session isolation, and per-session/global limits remain MVP requirements.
Memory alone cannot promise durable
resumption of in-flight work. Business logic belongs in Python application code;
the native Agent adapter owns platform interaction rather than copied analytics.

Authenticated private workspaces, login, OAuth, enterprise tenancy, PostgreSQL,
Parquet, uploads/live connectors, full-corpus classification,
vector search, Containers, distributed orchestration, and large-scale benchmarks
are future work. Preserve expansion contracts and the research reasoning for
these capabilities without making them first-MVP requirements. The present work
is documentation cleanup; application code, tool scaffolding, and deployment are
outside its scope.

## Constraints and cross-discipline requirements

| ID | Constraint or observable outcome | Source | Affected outcome / owner |
| --- | --- | --- | --- |
| BR-01 | Evidence-first chat over bundled synthetic datasets in isolated anonymous sessions, using Workers AI with Llama 3.3 | S-01; S-03 §§1, 24 | MVP proposal; architecture and later UX owners |
| BR-02 | Two synthetic datasets: sales CSV and support-message JSONL with public reproducible samples | S-01 | MVP proposal and validation owners |
| BR-03 | Question → execution → evidence → validation → supported answer must be an explicit end-to-end path | S-01; S-03 §§8–18 | Architecture and validation owners |
| BR-04 | Bulk data stays in data/execution layers; agents receive compact metadata, references, plans, limited evidence, and results | S-01; S-03 §§5, 12 | Architecture and feasibility owners |
| BR-05 | Agents reason, plan, select tools, review evidence, and explain; infrastructure accesses, queries, retrieves, computes, transforms, aggregates, stores, and executes reliably | S-01; S-03 §§2, 13 | Architecture owner |
| BR-06 | Connector and execution contracts support future expansion without replacing the core reasoning architecture | S-01; S-03 §20 | Architecture owner; evidence required for compatibility claim |
| BR-07 | Assess Cloudflare Agents ecosystem against current official docs, service limits, and native capabilities | S-01; S-05–S-10 | Feasibility owner |
| BR-08 | Python >=3.12 is the main language; use uv and the typed src-layout engineering standards and canonical gate | S-01; S-02 | Implementation planning owner; main-language compatibility unresolved |
| BR-09 | Standalone open-source build, run, tests, and deployment require no private 172X code or infrastructure | S-01 | Architecture and contributor-documentation owners |
| BR-10 | Prefer correctness, operational simplicity, low cost, and maintainability; justify major dependencies | S-01; S-02 | Architecture and feasibility owners; no numeric cost target supplied |
| BR-11 | Keep initial architecture unchanged; record suggested changes separately with evidence and trade-offs | S-01 | Architecture review and coordinator |
| BR-12 | Each material finding records current assumption, concrete failure/contract gap, evidence and uncertainty, MVP/scale relevance, recommendation/trade-off, and validation | S-01 | Architecture and feasibility review owners |
| BR-13 | Inspect roles, typed contracts, bounded context, near-data compute, retrieval coverage, partition correctness, durable recovery, retry classes, validator sufficiency, freshness, security, provenance, and scaling | S-01 | Architecture and feasibility review owners |
| BR-14 | Plan realistic small and large dataset tests for correctness, provenance, recovery, security, latency, cost, concurrency, storage, and backpressure | S-01 | Validation owner; measurements remain unverified |
| BR-15 | Cloudflare mapping must explain responsibility, fit, runtime/service constraints, state/storage owner, failure/recovery, and cost/scaling for every proposed component | S-01 | Feasibility owner |
| BR-16 | Preserve existing prompt history unchanged during cleanup; record planning decisions separately without importing previous-build authority | S-01 | Documentation owner |
| BR-17 | This baseline describes planned work only; use AGENTS.md for approved-milestone delivery and obtain separate deployment authorization | S-01 | Milestone and deployment owner |
| BR-18 | Maintain a consistent brief, architecture review, feasibility mapping, plans, risks, research ledger, and proposed decision records | S-01; S-02 | Coordinator |


BR identifiers preserve traceability across the retained planning documents.
Broader source/security/scale criteria apply when their future capabilities enter
scope; they do not silently enlarge the active MVP.

## Planning and future build acceptance

All application criteria are unverified. Planning criteria describe what to review,
not historical approvals or test results.

| ID | Observable result / acceptance evidence |
| --- | --- |
| AC-01 | Protected architecture, AGENTS.md, and existing PROMPTS.md stay unchanged during cleanup; no cleanup prompt is appended |
| AC-02 | Planning documents and decision index agree on repository identity, proposal status, active MVP, and future scope; local links resolve |
| AC-03 | Architecture findings retain assumption, gap, evidence/uncertainty, relevance, trade-off, and falsifiable validation |
| AC-04 | Roles, boundaries, coverage, durability, validation, freshness, security, and scale have explicit dispositions and owners |
| AC-05 | Two synthetic source proposals explain value, effort, reproducibility, semantics, citations, and tests; broader sources remain future work |
| AC-06 | Cloudflare mapping preserves runtime evidence, constraints, storage/state ownership, failure paths, and unrun compatibility experiments |
| AC-07 | Delivery milestones have bounded capabilities, dependencies, candidate PR boundaries, and acceptance evidence; validation distinguishes MVP from future experiments |
| AC-08 | Planning status is honest: documentation present, application absent, no imported build approval or test/deployment success claimed |
| AC-09 | Future supported sales/support question uses Workers AI with Llama 3.3 and leads through actual generated SQL or targeted search to evidence, deterministic checks, independent validation, and an accepted answer or explicit limitation |
| AC-10 | Future models receive bounded metadata/results/evidence and references, never bulk datasets; overflow/truncation/refusal is explicit |
| AC-11 | Future refresh/follow-ups preserve bounded durable memory within isolated anonymous sessions; retries, restart, duplicate submission, disconnect, and cancellation obey reviewed job/publication contracts without claiming unbuilt Workflow recovery |
| AC-12 | Future public clean clone builds/runs/tests with no private 172X package/service/skill; opt-in deployment uses a contributor's own authorized account |
| AC-13 | Future claims identify source/schema/semantic versions and access scope; evidence is traceable and retained or explicitly unavailable |
| AC-14 | Future make gate passes Ruff format/lint, strict mypy, pytest, and inspected Radon A/B acceptance; CI matches; independent QA/bot review and guarded delivery satisfy AGENTS.md |

## Evidence and uncertainty

The original architecture separates reasoning from deterministic execution,
conditional semantics, technical retry from replan, validation, and provenance.
The dated source ledger supports investigating native Agent/DO/Workflow boundaries.
It does not prove package compatibility, idempotency, validator quality, or scale.
Python Workers use Pyodide; native Linux packages and full CPython semantics must
not be assumed from a successful local install. The repository has no runtime,
model, connector, recovery, or scale evidence to certify.

Convert architectural descriptions into small, testable contracts before dependent
build work. Record actual budgets and failure outcomes; never replace uncertainty
with an invented throughput, cost, accuracy, or service target.

## Decisions and unknowns

| ID | Remaining decision or evidence | Consequence / criteria |
| --- | --- | --- |
| DEC-01 | Native Agent/Python boundary and compatible general query engine; verify minimal SDK adapter, package/runtime fit, and durable-memory owner | Topology, public setup, and cross-runtime parity; AC-06/12 |
| DEC-02 | Sales/support fixture semantics and supported questions within the two-dataset direction; broader connectors and exhaustive text remain future scope | Reproducibility, query flexibility, targeted retrieval bounds; AC-05/09 |
| DEC-03 | Context/evidence/query limits, retries, total spend, latency, concurrency, and measured workload envelope | Admission and acceptance targets; AC-07/10 |
| DEC-04 | Exactness, units/grain/time semantics, clarification authority, source/evidence retention, interrupted-job/retry/cancel/publication policy | Supported claims and durable behavior; AC-07/09/11/13 |
| DEC-05 | Enforce the specified anonymous-session scope over bundled synthetic fixtures; protected secrets, model-data handling, retention/deletion, and resource limits; login/private workspaces/OAuth/enterprise tenancy are future work | Security and deployment policy; AC-07/13 |
| DEC-06 | Public code/sample license, maintenance expectations, and operating budget | Independent contribution and release; AC-07/12 |
| DEC-07 | Next authorized milestone and which proposals/policies to accept or revise | Milestone scope and checkpoint; deployment remains separately authorized |

The Llama 3.3 baseline and anonymous-session demonstration scope are specified.
Remaining choices are proposed policies or unverified behavior. AGENTS.md governs routine PR delivery
within an approved milestone; do not invent another per-PR human approval gate.

## Risks and unresolved conflicts

| Risk or conflict | Evidence / uncertainty | Affected IDs | Blocking? | Mitigation or owner |
| --- | --- | --- | --- | --- |
| Main Python requirement may not map directly to the demonstrated Agents SDK usage | SDK examples use TypeScript while Python platform capabilities are documented; exact interop and packaging untested | BR-07/08; AC-06/12 | Blocks final topology/build, not planning | Feasibility checks current SDK/runtime contracts and proposes a bounded spike |
| Stable reasoning architecture is mistaken for demonstrated arbitrary dataset scalability | Initial §20 describes 20 MB/20 GB/2 TB and optional engines without measured workloads or budgets | BR-04/06/14; AC-07/10 | Blocks scale claims | Architecture defines envelope; feasibility/validation measures boundary and cost |
| Validator appears independent but cannot recompute or challenge claims from the evidence supplied | Initial §16 lists inputs but no concrete evidence schema or coverage guarantees | BR-03/13; AC-09/13 | Blocks supported-answer acceptance contract | Architecture defines evidence sufficiency and validation ownership |
| Broad corpus summaries miss rare themes or double-count records/threads | Initial §10 proposes partition/aggregate without coverage/merge contract | BR-13/14; AC-04/10/11 | Blocks future broad-coverage guarantee | Architecture and validation define measurable completeness/approximation behavior |
| Anonymous-session enforcement and retention details remain unreviewed; future private-source permissions need separate policy | User explicitly requests assessment; initial architecture lacks operational policy detail | BR-13; AC-07/13 | Blocks security/freshness build acceptance | Human resolves DEC-04/05 with architecture recommendations |
| Documentation review is mistaken for application verification | No application baseline or runtime tests exist | BR-14/17; AC-07/08/14 | Blocks engineering-ready or performance verdict | All stages label evidence and preserve gate state |


## Next planning step

Resolve policy and runtime gaps against the [MVP proposal](mvp-proposal.md),
[delivery plan](implementation-plan.md), [validation plan](validation-plan.md),
and [decision index](decisions/README.md). A platform capability, planning review,
or saved document is not evidence of implementation or authorization to deploy.

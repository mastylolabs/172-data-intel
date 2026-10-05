# Architecture review: 172X Data Intelligence

## Result and scope

Artifact: ARCH-REVIEW-v1. Original architecture research: 2026-10-04.
**Proposed refinements for `172x-data-intel`; no application readiness or approval is claimed.**
Uses the [engineering brief](engineering-brief.md), unchanged
[original architecture](architecture.md), and [engineering rules](../AGENTS.md).
Runtime experiments, product policies, UX states, trust controls, and independent
readiness review remain dependencies before affected implementation.

The active [MVP proposal](mvp-proposal.md) is two synthetic datasets: sales CSV
through model-generated SQL in a general query engine and support JSONL through
targeted search. Native Cloudflare Agent chat, durable memory, evidence, and a
separate Validator are required planning capabilities. Workers AI with Llama 3.3
is the MVP model baseline; runtime compatibility and model behavior remain
unverified until tested. Use isolated anonymous sessions over bundled synthetic
datasets. Keep session isolation, protected secrets, safe queries, and per-session/
global resource limits in scope; authenticated private workspaces, login, OAuth,
and enterprise tenancy are future work. The findings below also
preserve the broader architecture's future reasoning. PostgreSQL, Parquet, uploads,
exhaustive text, Workflows for long jobs, Containers, and distributed scale are
future options, not a requirement to build the entire catalog for the first MVP.

The initial separation of reasoning, data execution, and durable coordination is sound. The main
weakness is that descriptions of these boundaries do not yet define enforceable contracts. A
small profile can describe a large dataset, but bounded metadata alone does not prove bounded
computation, complete coverage, correct aggregation, affordable inference, or reproducibility.
Retain the conceptual design and make its guarantees conditional on explicit source, operation,
evidence, and recovery contracts.

## What to preserve

| Initial decision | Assessment and reason to keep it | Qualification |
| --- | --- | --- |
| Agents reason; deterministic infrastructure executes (§§2, 13, 23) | Directly meets BR-04/05 and supports testable calculation and recovery | Profiling, arithmetic verification, deduplication, budget enforcement, and authorization must actually be deterministic |
| Control plane need not be an LLM (§4) | Workflow transitions, retries, and enforcement have clear mechanical behavior | Capability selection can use an Analyst proposal; policy and routing enforcement belong to code |
| Conditional semantics (§§6–7) | Avoids expensive inference when definitions are already approved | Known connector structure does not establish business definitions or source-specific sensitivity |
| Analyst plans retrieval and analysis (§§8–11) | One analytical planner is enough for the proposed MVP | It proposes an executable typed plan; it does not authorize arbitrary code or data access |
| Separate execution and analytical correctness (§17) | A successfully executed query can answer the wrong question | Numeric, time-window, coverage, and duplication checks should be deterministic inputs to analytical review |
| Independent Validator (§16) | Preserves challenge before supported answers are published | Independence is a role/context boundary, not a guarantee of correctness from a second LLM call |
| Provenance and human clarification (§§18–19) | Essential to evidence-first answers and unresolved semantics | Requires immutable evidence identities, retention, approved definitions, and visible replay limits |
| Stable reasoning boundary across engines (§20) | A useful portability objective | Operation capabilities, SQL dialects, snapshots, error semantics, and resource envelopes must be tested per adapter |

Do not turn each reasoning role into a deployed service. Start with explicit modules and separate
model invocations where needed; add a runtime boundary only for platform integration, durable work,
or execution isolation that is necessary for the selected workload. This is an architectural
recommendation, not an inference about an existing application: the repository has no application
baseline.

## Evidence basis and limits

Repository assertions below refer to specific initial architecture sections, BRIEF-v1, and
AGENTS.md. The retained review records official-page research on 2026-10-04; the
[research ledger](research-sources.md) is a useful shared index. Documentation establishes exposed
capabilities and constraints. It establishes neither this application's behavior nor account-specific
capacity. Recheck platform details before implementation. No application benchmark or security test is available.

| Evidence | Established fact relevant to this review | Limit of the evidence |
| --- | --- | --- |
| [Agents overview](https://developers.cloudflare.com/agents/), [product site](https://agents.cloudflare.com/) | The ecosystem separates channels, harness, durable runtime, tools, and model access | Platform positioning is not an end-to-end analysis guarantee |
| [Agents API](https://developers.cloudflare.com/agents/runtime/agents-api/), [chat agents](https://developers.cloudflare.com/agents/communication-channels/chat/chat-agents/) | Native SDK usage is documented with JavaScript/TypeScript; persistent chat and streaming are available | Native use of that SDK from the chosen Python approach is unverified |
| [Python Workers](https://developers.cloudflare.com/workers/languages/python/), [runtime](https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/), [packages](https://developers.cloudflare.com/workers/languages/python/packages/) | Python runs through Pyodide/WebAssembly; package support covers pure Python, PyEmscripten, and included Pyodide packages | Local CPython installation does not prove target-runtime compatibility |
| [Python examples](https://developers.cloudflare.com/workers/languages/python/examples/), [Python Workflows](https://developers.cloudflare.com/workflows/python/) | Python Durable Objects and Workflow entrypoints are documented; Workflows require the documented compatibility flags | Selected SDK interoperation, Python version, and package versions still need testing |
| [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), [Durable Object limits](https://developers.cloudflare.com/durable-objects/platform/limits/) | Worker isolate memory is 128 MB, including WebAssembly; SQLite-backed Objects have finite storage and runtime limits | More objects do not increase the resources of one object or make a global coordinator unbounded |
| [Agents with Workflows](https://developers.cloudflare.com/agents/concepts/workflows/), [Workflow rules](https://developers.cloudflare.com/workflows/build/rules-of-workflows/) | Durable steps and real-time sessions have complementary responsibilities; calls inside retried steps need application idempotency | Completed-step persistence is not an atomic commit across external services |
| [Workflow limits](https://developers.cloudflare.com/workflows/reference/limits/) | Non-stream step results/events, total state, step count, concurrency, and retention are finite | The page's concurrency table and narrative currently differ; resolve before capacity acceptance |
| [Queue delivery](https://developers.cloudflare.com/queues/reference/delivery-guarantees/), [fiber recovery](https://developers.cloudflare.com/agents/runtime/execution/durable-execution/) | Queue delivery can repeat; fiber recovery requires application handling of saved state | Neither feature supplies the partition/result commit protocol |
| [Basin SQL](https://developers.cloudflare.com/basin-sql/), [Basin Catalog](https://developers.cloudflare.com/basin-catalog/), [SQL limitations](https://developers.cloudflare.com/basin-sql/reference/limitations-best-practices/) | These formerly R2-named services are GA; SQL supports joins over the documented Iceberg/Parquet path | Resource-intensive intermediates and dialect limits remain; generic CSV/JSON querying is not implied |
| [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | Read Committed statements can observe different committed views; Repeatable Read holds a transaction view | A replacement transaction after failure does not recreate the former view automatically |
| [DuckDB security](https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview) | Query APIs can access files, network, extensions, and process resources | Read-only-looking SQL and parameters alone are not an isolation boundary |
| [Container lifecycle](https://developers.cloudflare.com/containers/concepts/architecture/), [R2 lifecycles](https://developers.cloudflare.com/r2/buckets/object-lifecycles/), [Agent tracing](https://developers.cloudflare.com/agents/runtime/operations/observability/tracing/) | Container disk is ephemeral by default; lifecycle removal is asynchronous; traces can truncate and are not a lossless record | Durable source/evidence ownership, deletion, and provenance remain application responsibilities |
| [Container API](https://developers.cloudflare.com/containers/api/durable-object-container/), [process execution](https://developers.cloudflare.com/containers/guides/execute-commands/) | Request cancellation does not stop an exec process; child processes need separate lifetime control; under `durable_object` scheduling a configured exec user retains root capabilities | A Linux executor still needs explicit isolation, bounded output and cancellation; a nonroot ID is not sufficient proof |

## Responsibilities and smallest proposed boundary

The important journey is: authorized question → frozen scope → semantic clarification when needed
→ approved executable plan → durable execution → claim/evidence package → independent validation
→ published answer. A client disconnect must not turn partially executed work into a completed
answer. User-visible states below are required data/state needs; their detailed interface design is
reserved for the UX owner.

| Component / role | Owns and produces | Inputs / consumers | Deterministic or reasoning | Authority and failure boundary | MVP disposition |
| --- | --- | --- | --- | --- | --- |
| Chat/session adapter | Conversation, job subscriptions, ordered progress projection, references to accepted answers | User/API; job controller | Deterministic transport; delegates analytical reasoning | Validates server-owned anonymous session scope, checks session-owned state access; cannot declare a candidate validated; reconnect reads authoritative job revision | Required native Agent; verify minimal Python/SDK boundary under DEC-01 |
| Job controller / Orchestrator | JobRecord, active plan revision, budgets, cancel epoch, attempt ledger, accepted result pointers, publish state | Chat, Analyst, executor, Validator | Deterministic state machine | Authorizes capabilities, rejects stale commits, serializes transitions, enforces retry/replan budgets | Required; one authority per job |
| Durable runner | Scheduled steps, checkpoint/cursor state, waits and technical retry execution | Controller commands, external result refs | Deterministic | Workflow runtime resumes step orchestration; controller owns application status and publication | Future long-running path; first MVP needs durable memory and explicit interruption outcomes |
| Profiler | DataProfile derived from scope and execution capability | Source adapter; Analyst/optional semantic interpretation | Deterministic profile service | Records exact/estimated/sample statistics; returns schema/source errors instead of inventing fields | Required; a standing Profiler LLM is unnecessary |
| Optional profile interpretation | Ambiguous structural hypotheses and clarification requests | Bounded DataProfile/excerpts | Reasoning | Cannot turn a guessed key/type into an authoritative execution fact | Invoke only for ambiguity; can share Semantic capability |
| Conditional Semantic capability | Proposed definitions or approved-version references; ambiguity report | Profile, approved dictionary, human clarification | Reasoning; deterministic version/approval checks | Human or configured authority approves consequential units/meaning; model confidence is not approval | Required conditional path; no universal taxonomy |
| Analyst | AnalysisPlan, candidate claims, explanation and proposed replans | Question, profile, semantics, allowed capabilities, bounded evidence | Reasoning | Cannot grant access, enlarge budget, mark coverage complete, or alter accepted execution facts | Required; one role rather than a service per source |
| Connector | Authorized source resolution, schema, snapshot/cursor, capability descriptor | Opaque SourceRef, scope, policy context | Deterministic access | Source-native permissions plus application authorization; stable source/snapshot errors | Required for the two synthetic datasets; live connectors are future work |
| Execution adapter | Tool validation, queries/retrieval/transforms, partitioning, merge operations, ExecutionResult | Valid plan operations and capability tokens | Deterministic operations; explicitly marked model classification if requested | Owns resource isolation and source-side execution; refuses unsupported operations | Required; workload-dependent runtime |
| Deterministic validation service | Arithmetic, scope, provenance integrity, coverage, merge and time-window checks | Immutable results/manifests/claims | Deterministic | Executes independently named checks; cannot infer uncertain business meaning | Required; use testable rule functions |
| Independent Validator | ValidatorReport on every material candidate claim and overall answer | Original question, approved semantics, actual executed plan, evidence, deterministic checks | Reasoning with bounded verification tools | Separate invocation/context from Analyst; lacks capability to mutate evidence or self-publish | Required; independence must be observable and tested |
| Evidence/provenance repository | Immutable typed artifacts, ownership/access metadata, hashes and lineage edges | Controller/executor; authorized Validator/user | Deterministic storage | Does not serve credentials or bypass live authorization; tracks expired/deleted evidence | Required compact immutable evidence; external storage when size/retention requires it |
| Human | Meaning/policy approval, correction or continuation after bounded failure | Clarification, failed checks, proposed plan | Judgment | Decisions versioned with actor and effective scope; new facts trigger explicit revision | Required path; no implicit approval by timeout |

**Proposed first-MVP ownership:** Python owns analytical contracts, profiling,
query/search execution, policy functions, and deterministic validation. A native
Cloudflare Agent owns durable conversation/source/accepted-answer memory and may
wrap the single canonical job/publication authority for small analyses. Its
minimal TypeScript integration must not duplicate Python analytics. Verify JSON
contracts, evidence persistence, and interrupted-job behavior before selecting
this wrapper. A general SQL engine executes model-generated queries only after
deterministic dialect, source, function, read-only, and resource checks.

**Future durable execution:** one job-scoped authority, plausibly a Python Durable
Object wrapping the controller, can own longer jobs; a Workflow schedules/checkpoints
references and R2 holds large or long-lived immutable outputs. The Agent reads
progress from that authority. This is an extension candidate, not a second job
store to create in the MVP. Linux/Container execution is needed only if selected
packages/workloads require it. See F-04 and the [Cloudflare mapping](cloudflare-mapping.md).

## Material findings

Each finding uses the six fields requested in BR-12. Priorities describe effect on the proposed
contract, not an approval to build. “Required before affected implementation” means the gap cannot
be left for engineers to guess.

### F-01 — Preserve the roles, make profiling and enforcement deterministic

1. **Current decision/assumption:** §§4–6, 13, 22 name a Data Profiler Agent and list schema detection,
   counts, null rates, candidate keys, and anomalies beside ambiguous interpretation. The
   Orchestrator controls execution and capability routing.
2. **Concrete limitation/failure:** a profiler LLM could report an exact row count from a sample,
   treat a coincidental sample key as unique, or choose a capability that the connector cannot
   execute. Routing and budget policy can drift if inferred through conversation.
3. **Evidence and uncertainty:** §5 already prefers deterministic tooling and §2 supplies the
   controlling principle. No executable profile or routing contract exists in the reviewed
   architecture. No implemented agent behavior was observed; duplication is a risk, not an observed
   runtime defect.
4. **Relevance:** both; required before affected MVP implementation.
5. **Proposed change and trade-offs:** use the role matrix above. Build profiling as a deterministic
   service with optional ambiguity interpretation; have the Analyst propose strategies and code
   enforce authorized capabilities and budgets. Fewer mandatory model calls reduce operational
   complexity; ambiguous cases still need a supported clarification path.
6. **Falsifiable validation:** profile malformed schemas and sampled duplicate keys; exact facts
   must match deterministic fixtures, estimates must be labeled, and no model output may overwrite
   them. Disable model access and verify ordinary profile generation and routing enforcement still
   operate.

### F-02 — Contract descriptions need authorization, compatibility, and errors

1. **Current decision/assumption:** §§5–6, 9, 16, 18 call profiles, plans, semantic models, results,
   and provenance typed artifacts; examples mainly describe successful content.
2. **Concrete limitation/failure:** a plan can silently switch currency, execute against a newer
   schema, invoke an unsupported operation, or consume a truncated result as complete. Different
   adapters may interpret one field differently while their JSON remains syntactically valid.
3. **Evidence and uncertainty:** the initial examples omit version, session/access scope, exactness,
   partial status, output grain, stable errors, and compatibility rules. AGENTS.md requires precise
   types and external input validation. There is no code to test contract enforcement yet.
4. **Relevance:** both; required before all execution integration.
5. **Proposed change and trade-offs:** adopt the contract catalog below and small capability-specific
   ports. External payloads use validated typed models, internal values use frozen value objects,
   structural adapter interfaces use Protocol. The extra fields create an initial implementation
   cost but prevent silent portability and correctness failures; avoid a universal query language.
6. **Falsifiable validation:** round-trip shared golden payloads through every selected producer and
   consumer; reject unknown major versions, missing snapshot/authorization/coverage fields, illegal
   operations, unit mismatches, and stale plan revisions with stable errors.

### F-03 — Compact context must be enforced, including profiles and validation

1. **Current decision/assumption:** §§5, 12, 20 expect kilobyte-scale profiles and compact reasoning
   artifacts irrespective of source volume; the 50 KB illustration is not an acceptance target.
2. **Concrete limitation/failure:** wide schemas, high-cardinality histograms, giant cells, many
   partitions, accumulated tool messages, or an all-claims validation bundle can overflow memory
   or model context even when raw files are never included. Exact profiling itself may scan the
   whole dataset and become more expensive than the question.
3. **Evidence and uncertainty:** the initial architecture has no byte/token/sample/output budget
   or truncation semantics. Workers memory is a shared 128 MB isolate limit, including WebAssembly
   allocations. The actual model tokenizer, quality under reduction, and package overhead remain
   unknown. [Workers limits](https://developers.cloudflare.com/workers/platform/limits/).
4. **Relevance:** both; boundary enforcement belongs in MVP.
5. **Proposed change and trade-offs:** enforce model-boundary and execution budgets described below;
   keep full schemas/manifests/results in storage with bounded views and explicit omitted content.
   Cache profiles only by source/schema/scope/authorization version. Allow estimated statistics
   where the plan does not require exact values, declaring method/error. Bounded views can require
   more tool calls or refusal; total work is still workload-dependent.
6. **Falsifiable validation:** increase rows, columns, field lengths, categories, partitions, and
   conversation length separately. Instrument every model request and result buffer; exceeding
   configured limits must produce an authorized bounded retrieval/replan or stable budget error,
   never silent loss of completeness. Targets require DEC-03 approval.

### F-04 — Near-data execution and Python compatibility depend on the adapter

1. **Current decision/assumption:** §§12–13, 20 intend near-data queries and interchangeable
   execution engines; the prompt selects Python >=3.12 and Cloudflare Agents.
2. **Concrete limitation/failure:** a Python package that works locally can fail in Pyodide; a
   Container that downloads every remote file is not necessarily near the data; large join/spill
   operations can exceed runtime limits. Replacing an engine can change decimal/null/date/SQL
   behavior even if the role diagram is unchanged.
3. **Evidence and uncertainty:** Python Workers/DO/Workflows are documented, while native Agents SDK
   examples use TS/JS. Supported package classes are constrained. Basin SQL/Catalog are currently
   GA, support joins and an Iceberg/Parquet path, with resource-sensitive intermediates; claims that
   Cloudflare lacks analytical SQL or all Python durability are stale. No chosen package/runtime
   combination was tested. [Python packages](https://developers.cloudflare.com/workers/languages/python/packages/),
   [Python examples](https://developers.cloudflare.com/workers/languages/python/examples/),
   [Python Workflows](https://developers.cloudflare.com/workflows/python/),
   [Basin SQL](https://developers.cloudflare.com/basin-sql/),
   [SQL limitations](https://developers.cloudflare.com/basin-sql/reference/limitations-best-practices/).
4. **Relevance:** both; runtime selection and supported operation envelope block final MVP topology.
5. **Proposed change and trade-offs:** retain portable contracts; future PostgreSQL adapters push
   supported filters and aggregates to the source. Evaluate a bounded file engine in local CPython/Linux and native
   Basin analytics for suitable R2 workloads; defer mandatory Iceberg ingestion and multiple query
   engines. Keep Python business logic primary, and approve a minimal TS shim only if its native
   SDK benefit is demonstrated. An extra runtime adds packaging and operations; Worker-only
   execution would instead restrict packages and workload size.
6. **Falsifiable validation:** after approval, test pinned dependencies, actual Python version,
   JSON contracts, Workflow-to-controller calls, cancellation, decimal/timestamp behavior, cold
   start, streaming and memory in the target runtime. Compare bytes transferred/scanned, predicate
   pushdown and correct results for local files, source SQL, and any native analytical candidate.

### F-05 — Targeted retrieval and corpus-wide claims need different coverage contracts

1. **Current decision/assumption:** §§10–11, 21 offer semantic/hybrid retrieval and partitioned
   analysis for broad support themes.
2. **Concrete limitation/failure:** a top-k search can provide examples of a problem while missing
   its competitors; it cannot establish the most frequent complaint, absence of a complaint, or a
   whole-corpus denominator. Recursive partition prose summaries can discard rare themes and
   then make lost information unrecoverable.
3. **Evidence and uncertainty:** the initial retrieval strategies have no declared coverage mode,
   denominator, recall/error claim, or completeness test. This logical limitation follows from
   selecting only ranked hits: unselected records remain unknown. It does not require a claim that
   a particular search implementation is defective. Model interpretation quality remains untested.
4. **Relevance:** both; targeted-scope honesty is required in the MVP; exhaustive coverage is future work.
5. **Proposed change and trade-offs:** declare `targeted`, `exhaustive`, or `sampled_estimate` execution
   mode. Use lexical/metadata search for bounded targeted evidence initially. Corpus-wide counts
   require a frozen exhaustive record set, declared unit and taxonomy/rules, record-level
   classifications, and deterministic aggregation. Preserve those labels as artifacts rather than
   merge prose. Genuine model-generated labels remain uncertain even with exhaustive coverage;
   report classification quality/uncertainty separately from execution coverage. Full scans cost
   more; arbitrary corpus-wide inferred-theme claims may be refused or deferred.
6. **Falsifiable validation:** hide an important rare theme outside top-k hits; the system must not
   call the targeted result exhaustive. For broad mode, compare manifest and classification
   coverage to all frozen IDs; use independent reviewed labels to evaluate semantic errors and
   rare-theme misses. Reject prevalence and absence claims when mode/evidence cannot support them.

### F-06 — Partition coverage and merge algebra must preserve the analysis unit

1. **Current decision/assumption:** §§9–10, 14, 16 partition, analyze, and aggregate while expecting
   no double-counting or loss.
2. **Concrete limitation/failure:** offset paging over changing rows skips/duplicates records;
   overlapping thread context inflates complaint counts; averaging partition averages is wrong;
   distinct customer counts, global ranks and quantiles may not merge from compact local outputs.
3. **Evidence and uncertainty:** the initial document has no PartitionManifest, ownership rule,
   merge state, or completeness invariant. A mathematical counterexample: a partition with one
   value 1 and a partition with nine values 9 have means 1 and 9; mean-of-means is 5, while the
   correct global mean is 8.2. No application partition experiment ran.
4. **Relevance:** future partitioned analysis; exact engine aggregation still needs valid grain and arithmetic in the MVP.
5. **Proposed change and trade-offs:** freeze the scope and canonical unit (row/document/message/
   thread/customer), partition disjoint counted ownership, and distinguish optional overlapping
   context. Check expected/processed/rejected identities. Use operation-specific merge states:
   sum/count; average as sum and count; exact distinct via global key handling; ranking after
   global per-entity aggregation; quantiles via compatible exact computation or approved sketches.
   Approximation requires recorded method/error. Such state can grow; spill or source-side compute
   is preferable to pretending every aggregate is a small constant-size summary.
6. **Falsifiable validation:** repartition the same snapshot, shuffle/duplicate deliveries and
   inject missing partitions; accepted exact outputs must match a single-scope reference and be
   invariant to partition count/order. Overlapping context cannot change counted totals. Median,
   distinct, skewed averages and cross-partition entities need adversarial cases.

### F-07 — Checkpoints alone do not supply safe external result commits

1. **Current decision/assumption:** §§4, 14 assume completed partitions survive failure and work
   units are idempotent whenever possible.
2. **Concrete limitation/failure:** an executor writes an artifact and crashes before checkpoint;
   retry writes a duplicate and aggregation counts both. A timed-out old attempt can finish after
   a newer plan or cancellation and publish a stale result. A mutable source cannot necessarily be
   reread after recovery with the same data.
3. **Evidence and uncertainty:** Workflows persist completed steps, but calls within a failed step
   can repeat; Queues offer at-least-once delivery. Fibers require application recovery logic.
   External effect idempotency, snapshot persistence, and fencing are not specified in the initial
   architecture. Container request cancellation does not stop an exec process; retry can start a
   second process. [Workflow rules](https://developers.cloudflare.com/workflows/build/rules-of-workflows/),
   [Queue delivery](https://developers.cloudflare.com/queues/reference/delivery-guarantees/),
   [fiber recovery](https://developers.cloudflare.com/agents/runtime/execution/durable-execution/),
   [Container API](https://developers.cloudflare.com/containers/api/durable-object-container/).
4. **Relevance:** both; the MVP needs recovery for its selected durable path.
5. **Proposed change and trade-offs:** use the state/commit protocol below: stable logical work ID,
   immutable output, idempotent accepted-result pointer, attempt fencing and cancellation epoch.
   Resume only under the source snapshot contract. Workflow state holds references, not the
   evidence system of record. A controller commit cannot atomically encompass an external store,
   so reconcile orphan outputs rather than claim universal exactly-once execution. This adds a
   small ledger and reconciliation responsibility.
6. **Falsifiable validation:** kill execution before upload, after upload, before commit, after
   commit and before checkpoint; redeliver and delay old attempts. Each logical unit must have one
   accepted contribution, no stale publication, and a visible retry/failed/snapshot-lost outcome.

### F-08 — Retry classes are right, but errors and budgets need deterministic policy

1. **Current decision/assumption:** §15 distinguishes technical retry and reasoning retry;
   §§16, 19 bound correction loops, without a policy schema.
2. **Concrete limitation/failure:** retrying invalid SQL wastes cost; every resource error can
   trigger a fresh plan indefinitely; schema change can be “corrected” by guessing a new field.
   Layered model/client/Workflow retry defaults multiply attempts and hide total spend.
3. **Evidence and uncertainty:** §15's nonexistent-column example can mean invalid generated SQL
   or source schema drift; these require different dispositions. No attempt, elapsed-time, scan,
   model, or spend ledger is defined. The recommended limits and acceptable terminal outcomes are
   DEC-03/04 decisions, not supplied service targets.
4. **Relevance:** both; required before autonomous replanning.
5. **Proposed change and trade-offs:** use a stable error taxonomy and one controller-owned budget
   policy. Technical retry repeats a logically identical operation/snapshot/plan under configured
   attempts/backoff/deadline; replanning creates a new immutable revision with a reason and changed
   preconditions. Authorization, semantic ambiguity, budget exhaustion and lost snapshots fail or
   escalate; they cannot be solved by blind retry. Explicit decisions reduce autonomy but make
   failures and costs bounded.
6. **Falsifiable validation:** inject timeouts, 429s, bad syntax, schema drift, exhausted capacity,
   permission revocation and unsupported semantics. Assert the permitted class, same-operation
   technical retry, distinct plan revision for replan, exact ledger totals and termination at the
   approved policy limits, including nested client retries.

### F-09 — Validator independence requires claim-level evidence and independent checks

1. **Current decision/assumption:** §§16–18 give the Validator question, plan, results, candidate
   answer and provenance, and expect it to catch arithmetic, duplication and analytical errors.
2. **Concrete limitation/failure:** the Validator can agree with an incorrect query if it receives
   only a polished answer and aggregate; it cannot discover omitted partitions or a wrong join
   denominator without manifest/query/unit evidence. A second invocation can share the same model
   blind spots and untrusted instructions.
3. **Evidence and uncertainty:** the initial inputs are categories rather than sufficiency
   contracts; no claim registry, independent check interface or abstention state is defined. A
   provenance path shows how a result was made, not whether it answers the question. No model
   reliability claim is supported by measurements here.
4. **Relevance:** both; central to MVP supported-answer acceptance.
5. **Proposed change and trade-offs:** add typed claims and ValidatorReport below. Deterministic
   checks handle arithmetic, actual scope, units, coverage and artifact integrity; an independent
   read-only verification capability can recompute material claims against retained scope. Give
   the Validator immutable execution evidence and approved semantics, not Analyst hidden reasoning.
   Require claim dispositions and `insufficient_evidence`; rerun even apparently successful
   execution when checks warrant it. Separate context/tool authority is required. Analyst and
   Validator use Workers AI with Llama 3.3 in separate contexts for the MVP; correlated errors
   remain unverified by model agreement. Different-model diversity is a future experiment,
   with unproven benefit and additional cost.
6. **Falsifiable validation:** seed wrong joins, denominator, sign, currency, causal inference,
   duplicated units, missing coverage, and unsupported citations. Validator must fail or abstain
   on each material unsupported claim; compare a verified golden answer and measure false passes
   and false rejections separately. No universal error-free validator claim is permitted.

### F-10 — Snapshots, freshness, schema and semantics need different versions

1. **Current decision/assumption:** §§4–6, 19 reuse trusted semantic models and allow questions such
   as “this month” and “last 24 hours”; §18 expects source traceability.
2. **Concrete limitation/failure:** moving “now” shifts scope on retry; a field changes units without
   changing type; edited/deleted messages change the denominator; a cached profile or model
   survives incompatible source evolution. Restarting a query against live PostgreSQL can mix
   former and current data.
3. **Evidence and uncertainty:** initial examples do not freeze time, business timezone,
   source/schema version, consistency mode or semantic approval. PostgreSQL defaults can observe
   different views across statements, while Repeatable Read is transaction-bound. Historical
   snapshots and restart retention depend on the source adapter.
   [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html).
4. **Relevance:** both; necessary for multi-step MVP comparisons and validation.
5. **Proposed change and trade-offs:** resolve relative time once; record half-open boundaries,
   timezone and source watermark. Pin file manifests/content hashes. Use a consistent DB
   transaction for bounded live reads; if recovery cannot reattach/recreate its scope, declare
   `SNAPSHOT_LOST`, restart the full analysis under a new scope, or use an explicitly approved
   persisted extract. Version physical schema and business definitions separately; cache keys
   include them. Reliable replay may require storage or refuse long-lived live transactions;
   copying sensitive data requires DEC-05 approval.
6. **Falsifiable validation:** edit/add/delete records, change units/types/column names, cross
   timezone/DST/month boundaries and break the source transaction mid-job. No accepted answer may
   mix snapshots or reuse incompatible definitions; visible freshness and reproducibility mode
   must match the actual evidence.

### F-11 — Security must govern all artifacts and tools, not just connectors

1. **Current decision/assumption:** §§7, 22 mention sensitivity, access restrictions, connectors
   and tools, but give no server-owned session authority or future tenant model.
2. **Concrete limitation/failure:** a forged SourceRef, job ID, object path, cached profile or
   retrieval hit reveals another user's data; a malicious source excerpt directs tool use; generated
   SQL reads unrelated files or credentials; revocation leaves a previously accepted answer visible.
3. **Evidence and uncertainty:** no authorization/tenant/secrets/untrusted-content contract is
   present in the initial architecture. Service bindings provide internal connectivity, not
   end-user source permissions. DuckDB documents file/network/extension access and the need for
   isolation. The MVP uses isolated anonymous sessions and bundled synthetic data;
   DEC-05 tracks enforcement/retention details, with private workspaces and tenancy deferred. If a future Container uses
   `durable_object` scheduling, its exec process retains root capabilities despite a nonroot
   `user`; do not use that setting as intra-Container isolation.
   [Service bindings](https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/),
   [DuckDB security](https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview),
   [Container API](https://developers.cloudflare.com/containers/api/durable-object-container/).
4. **Relevance:** both; anonymous-session isolation is required in the MVP; private-source tenancy is future work.
5. **Proposed change and trade-offs:** server-owned anonymous session scope gates conversation,
   memory, jobs, evidence, retries, and publication over bundled read-only synthetic fixtures.
   Shared fixture access does not grant another session's state. Resolve secrets server-side.
   Future authenticated workspaces add identity, membership, and row/field permissions.
   Treat source/model content as untrusted data; permit allowlisted tools/operations with bounded
   network/file capabilities and isolated execution. A read-only DB role and parameterized values
   supplement structural query validation for future private database adapters. Anonymous sessions
   simplify the demonstration without proving enterprise tenant isolation. Protect secrets and
   enforce safe query/resource boundaries; test session isolation before any live demonstration.
6. **Falsifiable validation:** cross-session job/history/evidence access attempts, injected
   instructions, malicious paths/SQL/extensions, resource-limit failures, secret
   rotation and log scans must demonstrate denial and safe failure without leaking evidence or
   secrets. Future private-data tests add membership/ACL revocation and cross-tenant access probes.

### F-12 — Durable provenance needs its own retention and replay contract

1. **Current decision/assumption:** §§4, 18 preserve execution history and source-to-claim
   provenance for validation/debugging/reproducibility.
2. **Concrete limitation/failure:** expired Workflow state, truncated traces, changed sources, lost
   Container disk or deleted object evidence make the claim chain unreplayable. A log-only link
   cannot establish the exact query inputs or stored output.
3. **Evidence and uncertainty:** Workflow completed-state retention is finite; Agents tracing
   explicitly is not a lossless record and may truncate payloads. Container disk is ephemeral by
   default, and R2 lifecycle deletion is asynchronous. Actual retention obligations are undecided.
   [Workflow limits](https://developers.cloudflare.com/workflows/reference/limits/),
   [Agent tracing](https://developers.cloudflare.com/agents/runtime/operations/observability/tracing/),
   [Container lifecycle](https://developers.cloudflare.com/containers/concepts/architecture/),
   [R2 lifecycles](https://developers.cloudflare.com/r2/buckets/object-lifecycles/).
4. **Relevance:** both; compact durable evidence is necessary in the MVP.
5. **Proposed change and trade-offs:** retain immutable provenance manifests independently of
   runtime logs and checkpoints, with authorized artifact access, source/scope/schema/semantic/
   engine/model/prompt versions, result hashes and accepted attempts. Separate computational
   reproducibility from live-source reread and nondeterministic model regeneration. Specify expiry,
   deletion and tombstones, plus an explicit “evidence expired / unavailable” answer state. More
   retention costs storage and can conflict with privacy; require DEC-04/05 policy.
6. **Falsifiable validation:** replay deterministic calculations from pinned retained artifacts,
   compare hashes within documented numeric tolerance, expire runtime state/logs and verify the
   evidence path still works. Delete/revoke evidence and verify the system reports its replay
   limit and removes access rather than claiming retained proof.

### F-13 — Stable agent interfaces are a scaling strategy, not scale evidence

1. **Current decision/assumption:** §20 expects conceptually similar behavior at 20 MB, 20 GB and
   2 TB with execution infrastructure substituted; §§4, 23 include budgets and cost discipline.
2. **Concrete limitation/failure:** one global controller becomes a hot spot; many small partitions
   exceed Workflow steps/state; high-cardinality merge outputs grow; retries cause provider/query
   overload; orphan artifacts and indexes grow without retention; broad semantic labeling costs
   rise with records even if each model request is small.
3. **Evidence and uncertainty:** the size tiers are aspirations without workload/capacity/cost
   evidence. Cloudflare limits per isolate/Object/Workflow, while Basin SQL resource behavior
   depends on intermediates. The Workflow limits page currently lists 50,000 paid active instances
   in its table but still says 10,000 in narrative; account-level acceptance must resolve this.
   [Durable Object limits](https://developers.cloudflare.com/durable-objects/platform/limits/),
   [Workflow limits](https://developers.cloudflare.com/workflows/reference/limits/),
   [SQL limitations](https://developers.cloudflare.com/basin-sql/reference/limitations-best-practices/).
4. **Relevance:** both; basic admission/resource limits now, distributed scale mechanisms later.
5. **Proposed change and trade-offs:** define a workload envelope (size, files, rows/width,
   selectivity, group cardinality, joins, evidence and model volume), admission/backpressure,
   per-job/source/provider concurrency limits, measurable resource ledgers and artifact lifecycle.
   Store partition manifests by reference; use bounded cursor pages rather than unbounded steps.
   Add Queues, distributed engines, catalogs or more executors only when measurements show need.
   Bounded admission can increase latency or reject jobs, making capacity limits explicit.
6. **Falsifiable validation:** increase data size and independently increase question concurrency,
   partitions, group cardinality and provider latency; measure queue wait, CPU/memory/spill,
   scan/transfer bytes, tokens, accepted result rate, retry amplification, storage growth and spend.
   Validate correctness under overload before accepting a supported tier. DEC-03/06 owns targets.

### F-14 — Independent open-source operation needs a public reference path

1. **Current decision/assumption:** §§1, 24 call the project open-source and part of 172X; §3 labels
   the interaction surface “172X UI/API”; §20 lists several future engines.
2. **Concrete limitation/failure:** contributors cannot build/run/deploy without private imports,
   identity services or orchestration skills; adopting every listed engine creates unnecessary
   maintenance. A polished planning package could be mistaken for a passing Python project gate.
3. **Evidence and uncertainty:** BR-09 explicitly forbids private runtime dependencies; initial
   repository contains guidance/architecture and no implemented application/engineering tooling.
   AGENTS.md's `make gate` cannot be certified without required tools/configuration. License and
   supported local/deployment prerequisites remain DEC-06 decisions.
4. **Relevance:** MVP first; compatibility and maintenance also affect future scale.
5. **Proposed change and trade-offs:** use a public Python package and documented local reference
   path with reproducible fixtures, mocked model tests and separately documented Cloudflare
   deployment adapter. 172X specialist skills are authoring aids, never contributor/runtime
   prerequisites. Define public protocols around selected source/execution adapters; defer a
   plugin marketplace, generic lakehouse and multiple engine integrations. A local reference
   runner validates application contracts but cannot certify managed-platform recovery.
6. **Falsifiable validation:** after build approval, a clean public-only environment must install,
   run sample chat, execute offline tests, pass the canonical gate, and follow the documented
   deployment procedure using its own account, with no private registry, service, skill or import.

### F-15 — Streaming must respect validation before supported publication

1. **Current decision/assumption:** §3 sends the answer to the user after Validator PASS; the prompt
   calls for chat and the Cloudflare ecosystem supports streaming chat.
2. **Concrete limitation/failure:** a standard streaming harness can expose the Analyst's fluent
   candidate conclusion before validation; a later failure cannot undo what the user saw. A stale
   PASS or delayed completion callback can publish a superseded/cancelled answer.
3. **Evidence and uncertainty:** native chat streams model output, while the initial architecture
   has no message-level candidate/publication state or active-revision check. The exact custom
   integration has not been tested. [Chat agents](https://developers.cloudflare.com/agents/communication-channels/chat/chat-agents/).
4. **Relevance:** MVP; also a publication race at scale.
5. **Proposed change and trade-offs:** stream authorized status and progress; persist candidate
   claims internally. Publish the supported answer atomically only when its report applies to
   the active plan/scope/claim hashes and current authorization/cancel epoch. If a provisional
   answer is a desired future UX, its labels and interaction are a separate human decision.
   Validation adds answer latency; native chat convenience needs a small custom publication gate.
6. **Falsifiable validation:** force validation failure, disconnect/reconnect, repeated events,
   out-of-order PASS, plan revision, cancellation and permission revocation. The client must never
   receive a supported answer from an unvalidated or stale candidate.

## Proposed typed contract catalog

This catalog includes MVP contracts and future partition/long-job extensions, not implemented
Python classes. The approved next stage must select the relevant subset and translate it into
versioned schemas and protocol tests. Small mandatory enums should be
explicit; avoid arbitrary raw dictionaries passed between layers.

### Common envelope and compatibility

Every cross-boundary artifact has `contract_name`, `schema_version`, immutable `artifact_id`,
`created_at`, producer/build version, `job_id` where applicable, server-owned anonymous
`session_id`/access scope, data classification, content digest and retention/access metadata.
Future private-workspace contracts add authenticated principal/workspace/tenant scope.
Human-visible names and machine identity are distinct. Artifact IDs are opaque, not bearer authority.
Data references exclude passwords, connection strings, authorization headers and signed URLs.

Resolve MVP state access at each read/execution/publication boundary using server-owned
anonymous session scope and server-issued resource/operation capabilities, with policy revision
and expiry. Only bundled synthetic sources are available. Authenticated identities and private
row/field grants are future-workspace extensions.
Policy metadata in model output cannot issue a capability. New consumers reject unknown major
versions. Additive changes require documented defaults and conformance tests; unknown operation
kinds are rejected. Pin in-flight plans to supported producer/consumer versions. Migrations create
new artifacts with lineage; do not silently reinterpret retained evidence.

Wire encoding must preserve meaning across Python/JavaScript/source engines: canonical UTC
timestamps plus explicit business timezone, defined null/missing distinction, exact decimal/unit
representations, safe count/identifier encoding, and rejection of non-finite numbers or silent
precision loss. Define canonical encoding and digest algorithm with the schema; hashes exclude the
digest field itself. Numeric tolerance is permitted only where an operation's approved accuracy
contract defines it. Interoperability tests must include values that cannot round-trip safely as
ordinary JavaScript floating-point numbers.

| Contract / producer → consumer | Required fields | Invariants and success meaning | Stable failure / recovery |
| --- | --- | --- | --- |
| **SourceRef** / connector registry → profiler/executor | Source ID/type; logical dataset/table/object IDs; connector and capability versions; schema fingerprint; snapshot capability; access-scope/policy revision; credential handle resolved only server-side | Ref resolves only to allowed sources; identity cannot be replaced by a model-provided path; live source identity and immutable data version are separate | `SOURCE_NOT_FOUND`, `ACCESS_DENIED`, `CREDENTIAL_UNAVAILABLE`, `SOURCE_UNAVAILABLE`, `UNSUPPORTED_SOURCE`; no credential leakage; retry only availability class |
| **ScopeSnapshot** / connector/controller → all later stages | Snapshot ID and refs; canonical filter AST/parameters; resolved start/end and timezone; data-as-of/watermark; acquisition time; schema version; consistency mode; immutable file manifest or transaction/extract identity; count/estimate methodology; completeness; expiry and replay mode | Relative time is frozen once; boundaries are explicit and half-open where selected; one analysis uses one declared compatible snapshot set; `exact` cannot mean best-effort live reads; cross-source temporal alignment is stated | `SNAPSHOT_LOST`, `SOURCE_CHANGED`, `SCOPE_UNAVAILABLE`, `INCOMPATIBLE_SCHEMA`, `STALE_SCOPE`; restart under new scope or authorized extract; never silently mix |
| **DataProfile** / deterministic profiler → semantics/Analyst | Source/scope/schema refs; field types and nullability; row/document unit; counts/nulls/distributions/key hypotheses each with exact/sample/estimate marker, method and coverage; sample refs and selection seed/method; malformed/rejected counts; capability descriptor; omitted fields/statistics; profile cost and freshness | No bulk data; sampled uniqueness is a hypothesis; exact count includes declared inclusion/exclusion rules; full schema/sample artifacts remain external; estimates are not implicit planning facts | `PROFILE_INVALID`, `UNSUPPORTED_FORMAT`, `MALFORMED_SOURCE`, `BUDGET_EXCEEDED`, `INCOMPATIBLE_SCHEMA`; partial profile explicitly exposes omissions and cannot certify complete scope |
| **SemanticModel** / semantic capability or approved dictionary → Analyst/Validator | Model/version and schema binding; definitions and authority/status; entities and grain; keys/relationships/join cardinality; measures and units/currency; timezone/fiscal periods; null/credit/status rules; ambiguities and alternatives; evidence refs; human approval actor/time/scope; sensitivity/policy refs | Guesses remain proposed; confidence is labeled model judgment unless calibrated; no unit-changing inference becomes approved by reuse; compatible physical schema does not imply compatible business meaning | `SEMANTICS_UNRESOLVED`, `SEMANTICS_INCOMPATIBLE`, `APPROVAL_REQUIRED`; ask targeted clarification or restrict supported claims |
| **AnalysisPlan** / Analyst → controller/executor/Validator | Immutable plan ID/revision/hash; question and scope/profile/semantic refs; typed dependency DAG; operation/capability/dialect and params/query artifact per step; assumptions; input/output schema and grain; exactness/coverage mode; partition/merge rules; expected validation checks; evidence selection; budgets/deadlines; retry/replan policy IDs | DAG is acyclic and operations allowlisted; all data inputs authorized/pinned; output grain/units explicit; each result depends on declared inputs; planner cannot enlarge approved policy; human Markdown rendering is non-executable | `INVALID_PLAN`, `UNSUPPORTED_OPERATION`, `CAPABILITY_MISMATCH`, `BUDGET_EXCEEDED`, `ACCESS_DENIED`, `SEMANTICS_UNRESOLVED`; mechanical invalidity rejected; authorized replan gets new revision |
| **ExecutionResult** / adapter → controller/Analyst/Validator | Logical work ID and accepted attempt; plan/scope/operation hashes; status; result schema/grain/units; output artifact refs/digests and bounded view; exactness/approximation method/error; rows/units read, excluded, rejected, produced; coverage/manifest ref; truncation; actual query/params; engine/version/settings; duration/resource/spend metrics; warnings/error | Success is operation success, not analytical PASS; `partial` is distinct from `complete`; bounded view cannot certify full output; only accepted attempts contribute; actual execution is recorded, not just requested plan | `EXECUTION_FAILED`, `RESOURCE_LIMIT`, `SOURCE_CHANGED`, `SNAPSHOT_LOST`, `CANCELLED`, `STALE_ATTEMPT`, `INVALID_OUTPUT`; results remain immutable; resume/replan follows error policy |
| **PartitionManifest** / executor → controller/merge/Validator | Manifest ID/hash, frozen scope, partition algorithm/version; canonical counted unit and stable identity; ranges/key ownership/cursor rules; expected count or verification method; counted versus context IDs; external paged partition list; accepted work result refs; missing/rejected/duplicate totals; ordering; merge algebra/version; completion certificate | Counted ownership is disjoint and covers declared included scope; overlap only supplies context; retries cannot add a second contribution; completion requires all expected units accounted for under rejection policy; checksum alone is not proof of correct algorithm | `COVERAGE_GAP`, `DUPLICATE_UNIT`, `INCOMPATIBLE_PARTITION`, `INCOMPLETE_EXECUTION`, `MERGE_UNSUPPORTED`; withhold exhaustive claims and reconcile/recompute |
| **Evidence** / executor/repository → Analyst/Validator/user | Evidence ID; source/snapshot locator; authorized record/unit identity and version; query/transform/result lineage; content/output hash; bounded excerpt/aggregate with units; selection method and coverage/omissions; trusted metadata versus untrusted content marker; sensitivity; retention/access state | Excerpt matches retained artifact at cited location; selection and truncation visible; citations do not imply corpus coverage; ACL applies before selection and on read; no embedded source instructions gain tool authority | `EVIDENCE_MISSING`, `EVIDENCE_HASH_MISMATCH`, `ACCESS_DENIED`, `EVIDENCE_EXPIRED`, `EVIDENCE_INSUFFICIENT`; retrieve permitted immutable evidence or abstain |
| **Claim / CandidateAnswer** / Analyst → Validator/publisher | Claim IDs/text/type; value/formula/units/denominator where numeric; scope/time; evidence and actual result refs; exactness versus estimated/model-inferred status; assumptions and exclusions; comparisons/uncertainty; candidate hash; citations; claim hierarchy; requested answer coverage | Every material assertion has a disposition; no causal inference from correlation without appropriate evidence; exhaustiveness and prevalence require matching mode; narrative cannot erase limitations; claim count/context obey budgets | `UNSUPPORTED_CLAIM`, `UNIT_MISMATCH`, `SCOPE_MISMATCH`, `MISSING_EVIDENCE`; revise with new hash or escalate; candidate is not published as supported |
| **ValidatorReport** / independent validator → controller/publisher | Report/version; question, plan/scope/semantic/candidate hashes; validation policy and model/check versions; per-claim `supported` / `unsupported` / `insufficient_evidence`; deterministic check results and verification query refs; completeness/semantic limitations; overall PASS/FAIL/NEEDS_CLARIFICATION; bounded remediation; validator context/tool audit ref | Report applies only to its immutable inputs; deterministic failures cannot be overruled by fluent agreement; PASS means all required claims/checks pass the configured policy, not infallible truth; insufficient evidence cannot silently become supported | `VALIDATION_FAILED`, `EVIDENCE_INSUFFICIENT`, `SEMANTICS_UNRESOLVED`, `VALIDATOR_UNAVAILABLE`, `BUDGET_EXCEEDED`; bounded retry/replan or human clarification; no automatic publish |

Additional small contracts are necessary: `CapabilityDescriptor` lists supported operations,
dialects, types, snapshot modes, ACL/filter behavior and limits; `ExecutionError` supplies safe code,
stage, operation/revision, retry disposition and correlation ID; `JobRecord` and `WorkUnit` implement
the lifecycle below. They should remain focused rather than introduce a generic plugin runtime.

## Context, intermediate-result and evidence bounds

No specific numeric budget has been approved. DEC-03 must set policy values after representative
measurements. Model context windows and platform payload ceilings are outer technical constraints,
not sensible application budgets by themselves.

| Boundary | Required bound and enforcement | Completeness behavior |
| --- | --- | --- |
| Source profile → reasoning | Encoded bytes and tokenizer-estimated tokens; field/statistic count; category cardinality; sample rows/documents, per-field characters and total sample bytes; authorized fields | Bounded relevant views plus full-schema reference; explicit omitted fields; no sample-derived exact assertions |
| Model input/output | Total system/question/history/contracts/tools/evidence/result tokens; maximum generated plan/claim bytes and counts; per-job calls/tokens/spend | Validate before execution; shrink bounded context or request narrower scope; refuse if required evidence cannot fit under approved policy |
| Execution → control/reasoning | Maximum inline bytes/rows/cells; external output refs; buffer/stream/spill limits; deadline; scanned/transfer bytes where measurable | Truncation marked; completeness refers to full artifact, not displayed page; oversized result causes deterministic artifact storage or error |
| Partition coordination | Bounded page size and cursor/manifest refs; per-partition unit/byte/model limits; max in-flight tasks; total job limits | All partitions remain enumerable outside model context; accepted result ledger/coverage certificate required |
| Analyst → Validator | Bounded claim groups, actual result refs, coverage/semantic summaries and verification pages | Validation may be batched; all material claim IDs must receive a final disposition before publish; missing batch is incomplete validation |
| Evidence → user/model | Authorized count/bytes/excerpt length and stable citation pages; per-job evidence retention | Show selection and scope; no unconstrained raw artifact download into an agent; full output access is a separately authorized user operation |
| Follow-up / cache | Bounded conversation view, summaries with lineage, cache ownership/schema/scope/policy versions | Cached evidence cannot extend scope or bypass revocation; remembered conclusions do not replace source verification |

Apply limits before buffering and before model invocation, using both encoded size and model token
accounting. A huge quoted field or a wide schema can violate limits while row count is small.
Refusal/replan is visible, not quiet truncation. Limited per-call context does not imply constant
total inference: exhaustive model labeling still grows with corpus size. Likewise a constant-size
manifest reference does not mean its persisted manifest, output or merge state remains constant-size.

## Scope and partition correctness

Use the smallest source-specific method that proves the requested scope. File scope is an immutable
ordered manifest of content identities and parser/schema settings. DB scope is a supported stable
read or approved persisted extract. An offline JSONL corpus is pinned and enumerable. Indexes are
derived projections with build/source watermark and ACL semantics; they are not the data source of
truth.

Targeted retrieval may support “show evidence of refund complaints.” It does not support “refunds
were the leading complaint across all conversations” without independent whole-scope measurement.
Broad analysis must define whether it counts messages, distinct threads, customers or occurrences,
whether multiple labels per unit are allowed, and how context outside the time window is used.
Thread context may overlap, but each counted unit has one owner. Duplicated export records and
duplicate deliveries are separate problems and both need a policy.

Exact execution over supplied fixture labels demonstrates coverage and arithmetic. Inferred labels
need separately evaluated interpretation; processing every document does not prove each label is
right. A “most common” inference must disclose its classification/taxonomy uncertainty even when the
underlying processing manifest is complete. Deterministic label counts must not be marketed as
validated free-form understanding.

| Operation | Safe merge requirement | Unsafe shortcut to reject |
| --- | --- | --- |
| Count/sum | Disjoint declared unit ownership; additive partials with inclusion/rejection rules | Sum repeated deliveries or overlapping context counts |
| Mean/rate | Merge sufficient numerator/denominator state with consistent null/unit/time rules | Mean of partition averages; ratio of averages |
| Distinct entity count | Global deduplication or key-disjoint ownership; approved compatible sketch if approximate | Sum local distinct counts when entities span partitions |
| Top entities | Complete per-entity totals or a proven distributed selection algorithm before global rank | Keep only local top-k when groups span partitions |
| Quantile/median | Exact source/global operation, or compatible sketch with declared approximation contract | Average local medians/percentiles |
| Themes | Stable taxonomy/rule/model version and unit-level labels; deterministic count merge; semantic quality evidence | Merge recursive prose summaries and infer corpus prevalence |

## State, durability, cancellation and recovery

### Sources of truth

| State/data | Proposed sole authority | Persistence and consistency |
| --- | --- | --- |
| External data | Source owner, or explicitly approved immutable extract | Adapter reports consistency and replay availability; an index/cache cannot redefine source scope |
| Session/access policy and credential resolution | Server-owned anonymous session/bundled-source boundary; future private-workspace policy | Session scope versioned and checked; credentials never pass to model or evidence; authenticated identity is future work |
| Semantic approval | Versioned semantic repository | Immutable approved version and approval actor/scope; supersession explicit |
| Job state, active revision, budgets, cancel epoch, accepted work | Python controller module behind one job authority | Atomic controller transitions; one accepted pointer per logical unit; monotonic state revision |
| Durable scheduling/checkpoints (future long jobs) | Cloudflare Workflow | Stores cursors/artifact refs; scheduling success does not certify analytical completeness |
| Result/evidence/provenance artifacts | Immutable artifact repository, plausibly R2 with compact access/index metadata | Content digest, owned namespace, committed refs; no assumption of transaction with controller |
| Chat/progress view | Session adapter projection | May lag/repeat; sequence/revision deduplication; reconnect reads authoritative status |
| Logs/metrics/traces | Diagnostics system | Helps detect failure; does not substitute for evidence or accepted state |

Proposed user-visible job states: `queued`, `profiling`, `awaiting_clarification`, `planning`,
`executing`, `validating`, `replanning`, `cancel_requested`, `cancelled`, `completed`, `failed`,
`budget_exhausted`. State transitions carry revision/correlation/time and safe reason. “Completed”
requires accepted scope/results, validator report and publication commit; partial execution and
insufficient evidence are never disguised as completed success. The final UX names can be refined
without changing these state distinctions.

### Work-unit commit protocol for future partitioned execution

1. The controller creates a logical work identity from job/plan revision, scope hash, operation
   hash and partition identity. Retry keeps this identity. A changed analytical plan creates new
   work identities. An attempt has a unique ID, lease/fence generation and the current cancel epoch.
2. Execution checks authorized capability, snapshot validity, budget reservation and fencing before
   work. It emits immutable output under attempt-specific identity; large outputs never live only
   on executor disk. Record model input/output artifacts according to approved privacy policy;
   stochastic model retry is not assumed to regenerate identical labels.
3. After output integrity/metadata validation, the controller atomically accepts one result pointer
   for that logical unit if revision, fence and cancel epoch remain active. Duplicate acceptance
   returns the accepted pointer; competing late attempts are rejected. Merge reads only accepted
   pointers, never all files found under a prefix.
4. The Workflow checkpoints the accepted reference. If a crash separates upload, controller commit
   and checkpoint, recovery asks the authority for acceptance before repeating. Orphan uploads are
   unaccepted artifacts to reconcile/expire; they do not contribute to aggregates.
5. Publication checks active revision, matching ValidatorReport/claim hashes, completed coverage,
   approved semantics, current access and cancel epoch, then commits the accepted answer once.

This gives one accepted logical contribution through application enforcement. It does not promise
one physical execution, one billable model call, or an atomic transaction across Workflow, R2 and
   external source. Source/model calls may repeat after ambiguous failure; budgets and attempt history
must record that exposure.

Cancellation is cooperative and fenced: accepting cancellation increases the cancel epoch,
prevents new work and stale publication, requests source query/provider cancellation where supported,
and drains or disregards in-flight attempts. An external query can finish after cancellation and
still incur cost. `cancel_requested` is distinct from confirmed `cancelled`; delayed results cannot
revive the job. A user retry starts a new authorized revision/job, not a reset of terminal history.

If the selected executor uses Container `exec`, retain process identity and an explicit bounded
completion/output protocol; HTTP abort alone is not successful cancellation. Signals reach the
direct process, while children can survive, so test process-group control or job-dedicated Container
termination. Drain large stdout/stderr with bounds instead of calling an unbounded output buffer.
The Container API documents these limitations; process control still needs target-version tests.
[Process execution](https://developers.cloudflare.com/containers/guides/execute-commands/).

### Technical retry versus analytical replan

| Failure | Infrastructure disposition | Analytical/human disposition |
| --- | --- | --- |
| Transient network/provider timeout or permitted 429 | Repeat same logical operation under configured backoff, attempt/deadline/spend budget; honor source retry guidance | No LLM replan for a purely transient failure |
| Invalid generated query/unsupported operation | No blind repeat; typed error and actual capability evidence | Analyst can revise supported operation under replan budget |
| Runtime resource limit | Avoid repeating identically when deterministic; preserve measurements and partial refs | Authorize smaller work units, better pushdown, different adapter or narrower question; otherwise escalate |
| Schema/source changed or snapshot lost | Stop affected scope; no silent new snapshot | Reprofile/reapprove as needed and restart under new scope, or explicit human decision |
| Ambiguous unit/business meaning | No technical retry | Clarification or supported narrower conclusion |
| Permission revocation / secret unavailable | Deny/restrict, rotate/reconfigure through authorized operator | Model cannot negotiate broader permission |
| Validator unsupported claim / insufficient evidence | Preserve report; re-execution only through revised plan | Bounded correction or clarification; repeat identical Validator calls only for transient availability |
| Total budget exhausted / cancellation | Terminal safe status; no hidden nested retries | Human continuation requires an explicit new authorized policy/revision |

Controller-owned policy supplies maximum attempts, deadline, allowed backoff, scan/compute/model
budgets, analytical revisions and escalation outcome. No numeric limits are asserted here.
Record each automatic/client/platform retry layer to prevent multiplicative attempt budgets.

## Data lifecycle, source evolution and security

The MVP uses isolated anonymous sessions over bundled synthetic fixtures and Workers AI with
Llama 3.3. Protect session history, memory, jobs, evidence, and server secrets; enforce bundled
source allowlists and per-session/global query/model limits. Model-data handling and retention
need explicit rules; anonymous sessions do not establish enterprise tenancy or private-data safety.
Authenticated private workspaces, login, OAuth, and enterprise tenancy are future work. Define
private-data classification/disclosure policy before that extension. Future source ACLs apply before profiling or retrieving,
especially before counts/aggregates that could reveal restricted data. Results and evidence inherit
at least the source sensitivity and access scope. Recheck access on continuation and reads; artifact
keys, job IDs and citations confer no authority.

Source, physical schema, semantics, index and execution versions are independent. New versions
invalidate incompatible profiles/plans/caches. Authorized compatible evolution may be accepted
through explicit adapter rules; a silent cast or field rename is not a semantic decision. Retained
artifacts record their original schema. Restart cannot reinterpret old evidence with a new semantic
definition without creating a new lineage revision.

Retention is a policy contract requiring DEC-04/05: retain inputs or source snapshot references,
results, label artifacts, plans, provenance, answers and credentials according to their distinct
purpose. Store expiry/replay mode on artifacts; do not promise indefinite source retention. Delete
or revoke access to derived caches/indexes/evidence as well as originals, and retain only authorized
minimal tombstones describing unavailable lineage. App access revocation must be immediate at the
permission boundary even if physical lifecycle cleanup is asynchronous. R2 lifecycle rules are
cleanup aids, not a complete privacy deletion protocol.

Secrets are resolved only within authorized connectors, scoped per source, rotated and redacted from
tool errors/logs/model inputs. The execution environment receives only the resources required for
the plan. Untrusted documents, sample values, schema descriptions and model-generated SQL remain
data/proposals. Tool names, permitted effects, filesystem paths, network targets and budget decisions
come from infrastructure policy, not text found in the source. Retrieval filters and authorization
must be tested together; prompt instructions alone cannot isolate tenants or prevent exfiltration.

Activated specialist dependencies for a later authorized stage are: a threat-modeling specialist
for the stable identity/data/tool boundary; UX/UI owner for progress, clarification, evidence and
failure states; and infrastructure assessment for conditional hosting/capacity/cost. No such review
is claimed completed by this artifact. The final stable architecture needs independent readiness
review before affected implementation; milestone delivery follows AGENTS.md.

## Critical-path stress plan and scaling path

| Path | Normal behavior | Failure/overload and detection | Safe visible response and recovery owner |
| --- | --- | --- | --- |
| Connect/profile | Authorized source → declared scope/profile | Bad parser/schema, stale ACL, enormous profile; validation and budget metrics | Invalid/partial profile or source error; connector/controller owns recovery; ambiguity → human |
| Plan | Typed authorized capabilities and approved meanings | Unsupported query, missing semantics, context overflow; contract checks | Clarify/reject/bounded replan; Analyst proposes, controller enforces |
| Execute | Source-side/bounded adapter, accepted work ledger | Timeout, provider quota, source drift, memory/spill limit, duplicate attempt; structured errors/metrics | Retry identical transient work or record replan/snapshot loss; executor and controller own reconciliation |
| Merge/coverage | Frozen canonical units and supported algebra | Missing units, duplicated context, huge grouping, incompatible label/merge versions | Incomplete execution or resource error; no exhaustive claim; deterministic merge owner |
| Validate | Checks plus independent claim review | Missing evidence, unsupported conclusion, unavailable model, oversized bundle | Insufficient evidence/clarification/bounded correction; Validator/controller own gate |
| Publish/reconnect | Active accepted answer and monotonic status revision | Disconnect, duplicate callbacks, cancellation/ACL change, stale report | Progress may lag; authoritative read/reconciliation; stale publication rejected by controller |
| Retain/replay | Authorized immutable artifacts and lineage | Expired evidence, changed source, orphan growth, traces gone | Visible replay limit; repository/operator owns retention and cleanup |

No latency/concurrency/cost/SLA was supplied. Proposed workload cases are experiments to authorize,
not performance commitments. Start with the synthetic sales CSV and support JSONL fixtures.
Parquet, billing/PostgreSQL fixtures, and whole-corpus classification are future workloads. Large files, many files, row width, skew/high-cardinality groups,
join growth, selective versus full scans, and model-labeling volume stress different boundaries.
NYC TLC public Parquet is a realistic scan/schema workload, not clean analytical ground truth;
synthetic oracle data supplies expected results. Multiple-source joins are not automatically in
MVP because two datasets are selected.

First scale through source-side query and bounded execution with job-local authority, admission
limits and artifact references. Next improve partition size/pushdown and source/provider concurrency
using measurements. Add queue-based load smoothing only if bursts require it; Cloudflare Queues
duplicates still use the same commit protocol. Add native Basin Catalog/SQL or another analytical
engine only after capability/parity/cost evidence justifies its ingestion/operations burden. Avoid a
global serialized controller, unbounded step fan-out or a central raw-data store by default.

Measure end-to-end latency split into queue wait, planning, source reads, compute, model, validation
and publish; CPU/memory/spill and transfer/scan bytes; rejected/duplicate/covered units; retries and
replans; tokens/model calls; storage and orphan growth; and attributable spend. Correlation IDs link
diagnostics to durable provenance without logging sensitive payloads. Source/provider quotas and
tenant/job fairness remain application policy even if the platform can instantiate many workers.

The 20 MB / 20 GB / 2 TB language in §20 is a useful scaling aspiration, **not measured support**.
Two datasets with the same byte size can differ radically in query cost. A documented native
distributed engine supports a future path, but throughput, completeness, correctness and cost for
this project remain unverified at every tier.

## Priority coverage and requirement traceability

| Requested challenge priority | Disposition / evidence location | BR / AC trace | Future validation owner |
| --- | --- | --- | --- |
| Orchestrator, Profiler, conditional Semantics, Analyst, Validator responsibilities | Preserve roles; deterministic profiler and explicit authority matrix; F-01/09/15 | BR-03/05/13; AC-03/04/09 | Architecture/QA; later UX reconciliation |
| Deterministic work assigned to infrastructure | Mechanical profile, checks, merge, policy enforcement; F-01/06/08/09 | BR-05; AC-04/09/11 | Python implementation/QA |
| Typed contracts | Common envelope and full contract catalog; F-02 | BR-06/08/13; AC-04/10/13 | Backend/adapter conformance QA |
| Bounded context/intermediates/samples/evidence | All-boundary budgets, wide data and validator batching; F-03 | BR-04/10/13; AC-04/10 | Feasibility/QA; DEC-03 human |
| Near-data query/compute and Python/platform compatibility | Source SQL, workload adapters, conditional shim/native analytics; F-04 | BR-07/08/15; AC-04/06/12 | Feasibility/runtime spike |
| Targeted and broad retrieval | Mode/coverage contracts; exhaustive frozen scope and semantic uncertainty; F-05 | BR-01/03/13; AC-04/09/10 | QA/model evaluation; DEC-02/04 human |
| Partition/aggregate omissions, duplicates, misleading conclusions | Canonical units, manifest and operation-specific merge algebra; F-06 | BR-03/13/14; AC-04/10/11 | Deterministic execution/QA |
| Checkpoints, idempotency, cancellation, retries, recovery | Sole state authority, fencing/commit/reconciliation protocol; F-07 | BR-03/13; AC-04/11 | Feasibility/fault-injection QA |
| Separate bounded technical retry and analytical replan | Error/retry table and shared budgets; F-08 | BR-10/13; AC-04/11 | Controller/QA; DEC-03/04 human |
| Validator sufficient evidence | Claim/report catalog and independent checks; F-09 | BR-01/03/13; AC-04/09/13 | QA/independent reviewer |
| Source change, freshness, schema and semantic uncertainty | Scope/version lifecycle and clarification; F-10 | BR-03/13; AC-04/13 | Connector/semantics QA; DEC-04 human |
| Anonymous-session isolation, secrets, source injection; future tenant permissions | Session-scoped state access, safe query tools, per-session/global limits; future private-data policy/threat contract; F-11 | BR-09/13; AC-04/12/13 | Security/QA; DEC-05 policy details |
| Observability/provenance, debugging/reproducibility | Durable manifests separate from traces, retention/replay modes; F-12 | BR-03/13/14; AC-04/07/13 | Backend/operations/QA |
| Scaling, concurrency, backpressure, storage, latency, cost | Workload envelope, admission, metrics and measured evolution; F-13 | BR-04/06/10/14/15; AC-04/06/07/10 | Infrastructure/feasibility; DEC-03/06 human |
| Focused sources/MVP and public independence | Bounded adapters/local public reference, F-14 | BR-02/09/10; AC-05/12 | Coordinator/contributor reproduction |
| Validation before supported chat publication | Candidate isolation and publication gate, F-15 | BR-01/03; AC-09/11/13 | Frontend/backend/QA |

The matrix preserves requirement traceability and proposed validation ownership.
It is not a record of previous agent sessions, approvals, or passing application
checks. AC-09–AC-14 remain unverified future behavior; no Makefile or application
baseline exists. The [validation plan](validation-plan.md) distinguishes active
MVP checks from future coverage, recovery, and scale experiments.

## Proposed ADR topics and unresolved decisions

All topics below are **awaiting approval**. They are inputs for separate ADRs, not accepted choices.

| Proposed topic | Recommendation / options | Decision mapping and revisit evidence |
| --- | --- | --- |
| Runtime/language boundary | Python primary; minimal native Agents shim only if justified; compare all-Python path and target-runtime packages | DEC-01; revisit SDK/runtime support or spike failure |
| Small modular control plane and sole job authority | Python policies plus canonical Agent-wrapped small-job state; future job-local authority, Workflow scheduling, session projection, external artifacts | DEC-01/03/04; revisit demonstrated hot spots or ownership change |
| Typed capabilities and versioned evidence contracts | Narrow source/execution interfaces; explicit source scope, coverage, units and stable errors | DEC-02/04; revisit new source capability mismatch |
| Retrieval coverage and partition algebra | Separate targeted evidence from exhaustive/sampled analysis; canonical units and deterministic merge | DEC-02/04; revisit semantic-quality or corpus-cost findings |
| Source snapshots and semantic approval | Immutable file scope; bounded consistent DB scope or approved extract; explicit replay and human definitions | DEC-04/05; revisit source freshness or recovery needs |
| Claim-level validation and publication gate | Deterministic checks plus separate Validator; publish only matching active accepted evidence | DEC-04; revisit measured false-pass/latency trade-offs |
| Recovery/cancellation and bounded budgets | Accepted work ledger, idempotency/fencing, separate technical/replan policy, no universal exactly-once claim | DEC-03/04/06; revisit fault/overload evidence |
| Session isolation, model-data handling and retention | Isolated anonymous demo sessions; bundled synthetic sources, protected secrets, safe queries, resource limits; future authenticated/private tenancy | DEC-05; session enforcement needs tests; private-data/tenant operation requires future threat/control contracts |
| Public reference execution and dependencies | Public Python package/fixtures and Cloudflare adapters; local runner does not certify managed recovery | DEC-06; license and clean-environment reproduction required |

The main human choices remain BRIEF-v1 DEC-01–DEC-07: language/platform boundary; semantics for the two MVP datasets
and future broad-text scope; supported workload/budget targets; exactness/semantic/freshness/retry policy;
anonymous-session enforcement/model-data handling/retention; license/cost/maintenance constraints; and explicit next-stage approval.
These cannot be turned into material assumptions by the architect.

## Readiness boundary

Retain all fifteen findings and their six-field technical reasoning as planning
inputs. Resolve DEC-01–DEC-07, select the MVP contract subset, and independently
review runtime, UX, and security before affected implementation. No runtime/model/
scale experiment, account quota inspection, or production evidence is recorded.
Important remaining risks are correlated model error, query-engine/runtime fit,
evidence sufficiency, duplicate or stale publication, access/retention behavior,
and unmeasured budgets. Broader corpus coverage, live-source replay, partition
recovery, and resource-heavy scale require their own future acceptance evidence.

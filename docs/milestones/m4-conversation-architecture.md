# Architecture: M4 validated conversation and private v2 tool boundary

## Result and identity

- **Architecture ID/version:** `M4-ARCH-v2`, 2026-10-06
- **Status:** `READY_FOR_REVIEW` after the M4-C0 `REVISE` return; independent design review, threat review, implementation, QA, provider approval, merge and deployment remain pending.
- **Source brief:** [M4-BRIEF-v1](m4-conversation-brief.md), recorded pre-build gate `M4-C0`; stable requirements `BR-M4-01` through `BR-M4-10` and acceptance criteria `AC-M4-01` through `AC-M4-10`.
- **Other authority:** immutable [original architecture](../architecture.md), SHA256 `2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd`; [M3-ARCH-v1](m3-analytical-tools-contracts.md); [M2 runtime contracts](m2-runtime-contracts.md); [AGENTS.md](../../AGENTS.md).
- **UX/UI artifact:** [M4-UX-v2](m4-conversation-ux.md); its exact hash is recorded by the readiness matrix. The job state and response distinctions below are reconciled with that UX contract; independent design-architecture review remains pending and no new public-access policy is invented here.
- **Current repository/revision inspected:** `origin/main` `d4e03731af28ce1c9c0b53b8c59a133acd3edd4a`, with current merged M3 source files and M4 planning/budget reports. Current working HEAD may contain uncommitted brief work; this artifact does not depend on it.
- **Decision owner and receivers:** principal architect owns this proposal; coordinator routes it to the M3 contract owners, backend/Agent implementers, UX owner, threat/security reviewer and independent design-architecture reviewer. This v2 resolves GAP-01–06 from the prior readiness matrix.
- **Human build-gate state:** the user’s full GO authorizes approved milestones and guarded delivery. It does not replace independent readiness, QA, configured provider review, branch protection or guarded merge.
- **Replaces or depends on:** depends on M3 source identities and merged P1–P4b behavior. It is additive to v1 and does not rewrite v1 state or contracts.

## M2 control amendments for v2

M2 `CTRL-06` and `CTRL-07` remain unchanged for every v1 `/proof/*` path and
for the v1 planner: its 12,288-byte input, 8,192-byte output, one-model/one-
query job and existing 12/hour session plus 24/day global admissions still
apply. This M4 contract adds a separately versioned v2 Validator context with
the 32,768-byte cap above because it must carry complete bounded receipts and
field meanings; it has its own 4,096-byte output cap, strict JSON verdict and
the same no-stream/no-technical-retry rules. The v2 six-model/two-tool job
ceiling is stage accounting under the existing session/hour and global/day
ceilings, not a quota increase or a widening of v1. A v2 admission record
must consume the existing `ProofBudget` owner, and mixed-version calls cannot
share or reset counters.

The canonical v2 model-stage policy is:

| Stage | Context/request cap | Output cap / max tokens | Admission and retry |
| --- | ---: | ---: | --- |
| Analyst planning | 12,288 bytes | 8,192 bytes / 512 | one call; one optional bounded replan; same session/global counter |
| Conditional Semantic clarification | 12,288 bytes | 2,048 bytes / 256 | zero or one call only when meanings are unresolved; no retry |
| Candidate drafting | 24,576 bytes | 4,096 bytes / 512 | one call; no retry; candidate remains private |
| Independent Validator | 32,768 bytes | 4,096 bytes / 512 | one call; no retry; malformed/uncertain dispatch consumes admission |

All rows use the same `ProofBudget` model admission and the 12/hour session and
24/day global ceilings. A v2 job has at most six model calls (including one
replan) and two tool calls; a stage that is not needed consumes no admission.
Max+1 request/output bodies refuse before dispatch, and SDK/provider retries
are disabled. These caps are application bounds, not latency or quota claims.

## Scope, goals, and non-goals

The target is a private, synthetic-data MVP conversation: one isolated session selects one approved source, asks a bounded question, obtains deterministic tool evidence, creates a candidate answer with typed claims/citations, runs independent validation, and exposes an accepted answer only after an atomic publication commit. Refresh and same-source follow-ups read the Durable Object’s authoritative state.

Goals:

- Complete the deferred M3-P5 numerical, M3-P6 citation and M3-P7 private-service boundaries so M4 consumers do not guess wire behavior.
- Keep Python >=3.12 authoritative for fixture loading, profiling, SQL/search execution, calculations and mechanical validation.
- Keep TypeScript small: native Agents SDK coordination, Durable Object state/fences, Workers AI calls and transport.
- Preserve the Orchestrator, deterministic Data Profiler, conditional Semantic role, Analyst and independent Validator responsibilities.
- Make source identity, scope, hashes, result units, claims, citations, model calls and runtime versions inspectable without exposing secrets or raw diagnostics.
- Bound context, evidence, state, calls, retries and publication and fail closed on mismatches.

Non-goals:

- Public chat, accounts, OAuth, uploads, live connectors or private data; these remain M5/future scope.
- PostgreSQL, Parquet, vector search, full-corpus classification, containers, distributed execution or large-workload claims.
- Cross-source joins or inferred relationships between the sales and support fixtures.
- Paid model usage, billing changes, quota purchases, guaranteed background completion, physical exactly-once execution or provider-backup deletion.
- Changing fixture bytes, field meanings, the SQLite boundary, v1 routes, v1 proof receipts or the original architecture document.

## Sourced constraints and non-functional needs

| Constraint or outcome | Source/version | Measurement boundary | Status | Owner or unknown |
| --- | --- | --- | --- | --- |
| Full source identity, immutable fixture hash and implemented capabilities | BR-M4-01; M3-ARCH-v1 | Catalog response and every v2 receipt | confirmed contract; runtime proof pending | Python catalog owner |
| Deterministic tools and validation; model output never grants tool authority | BR-M4-02/04/05; original architecture §§2, 4, 13, 17–18 | Python service and Agent handoff | confirmed contract | Backend/Agent owners |
| Clarify missing meaning/period/scope before execution | BR-M4-03; original architecture §§6, 19 | Plan admission and job state | confirmed contract | Analyst/UX owners |
| Independent Validator before publication | BR-M4-05/06; original architecture §§16–18 | Candidate-to-publication transaction | confirmed contract; live model pending | Validator/Agent owners |
| Session/hour and global/day model ceilings, no paid usage | BR-M4-08; M4 P4b report; user cost authority | Durable Object admission before each model call | confirmed policy; deployed proof pending | Budget/operations owner |
| Python >=3.12 and small TypeScript Agents layer | BR-M4-10; AGENTS.md | Package/runtime and source ownership | confirmed constraint | Coordinator |
| Private v2 service only through service binding; no credentials in requests | M3-ARCH-v1; M2 runtime contracts | Worker route and binding tests | confirmed contract; deployed proof pending | Runtime/security owner |
| Limits are safety bounds, not latency or scale promises | M3-ARCH-v1; architecture review F-03/F-13 | Per request/job receipt and report | confirmed interpretation | Architect/QA |

The numeric limits in this document are MVP safety policy choices. They are not throughput,
latency, availability or cost SLOs. Any limit change is a versioned contract amendment and requires
fresh affected tests and review.

## Source-to-contract traceability

| Source IDs | UX/UI flow and state/data need | Owning boundary | Interface/data/authorization contract | Failure/recovery contract | Criterion status and evidence |
| --- | --- | --- | --- | --- | --- |
| BR-M4-01; AC-M4-01 | Source picker persists the complete identity and capabilities; stale selection is visible as unavailable | Catalog + v2 session DO | `CatalogV2`, `SourceIdentity`, `SessionStateV2` | `source_mismatch`, `unsupported_source`; no path access; user selects a fresh catalog identity | unverified; M3 catalog identities are existing evidence, v2 route not implemented |
| BR-M4-02/03; AC-M4-02 | Progress shows profiling/planning or clarification before tools; follow-up is tied to source/job | Agent + Python tools | `AnalysisPlanV2`, `ClarificationV2`, profile/query/search envelopes | strict plan refusal; clarification terminal state; no assumed execution | unverified; design contract only |
| BR-M4-04; AC-M4-03 | Accepted answer exposes inspectable claims, exact result references and support quotes/limitations | P5/P6 validators + candidate store | `NumericalClaimV2`, `CitationV2`, `CandidateAnswerV2` | deterministic check failure withholds candidate; no free-floating claim | unverified; P5/P6 implementation pending |
| BR-M4-05; AC-M4-04 | Validation progress is separate from answer; failed validation is not presented as success | Validator adapter + Agent | `ValidatorInputV2`, `ValidatorReportV2` | mechanical FAIL cannot be model-overridden; provider/malformed verdict fails closed | unverified; independent validator pending |
| BR-M4-06; AC-M4-05 | Only accepted answer enters history; candidate/failure states remain private and inspectable as safe status | DO publication transaction | `PublicationRequestV2`, `AcceptedAnswerV2` | one fenced atomic commit; stale/cancelled/mismatched commit rejected | unverified; publication implementation pending |
| BR-M4-07; AC-M4-06 | Refresh/reconnect shows authoritative phase; cancel/source switch/reset cannot resurrect work | DO job authority | `JobRecordV2`, generation/cancel fences, request journal | stale completion ignored; retained replay/conflict/unavailable; no automatic rerun | unverified; lifecycle implementation pending |
| BR-M4-08; AC-M4-07 | Budget refusal is explicit; no hidden retries or billing change | session DO + `ProofBudget`/budget record | per-stage reservation and global/session ceilings | uncertain calls consume admission; quota is a classified failure | unverified; existing v1 budget evidence is prerequisite only |
| BR-M4-09; AC-M4-08/09 | Same-source accepted memory survives refresh; foreign/rejected/evicted evidence is unavailable | server-owned DO state | cookie-derived session routing; bounded accepted memory; no client state writes | 403/404/409 safe errors; reset/source change fences old work | unverified; threat review and QA pending |
| BR-M4-10; AC-M4-10 | Report includes revisions, coverage, deployment and live/free-model result | guarded delivery | v1 preservation + additive v2 schemas | rollback to prior worker/resource versions; no claim from local mocks | unverified; all later evidence pending |

## Current and target context

### Current boundaries and evidence

The Python repository currently owns the pinned sales/support fixtures, M3 profile/search models,
SQLite query engine and v1 private service routes. The TypeScript Worker owns the native Agent,
Durable Object state, v1 proof transport and P4 planning/budget foundation. Existing v1 contracts
are strict but expose only the historical sales proof identity and do not represent an accepted
conversation. M3 reports and tests are prerequisite evidence, not evidence that v2 routes or
publication exist.

### Target topology

```text
Browser / operator transport (M5-visible surface, private during M4)
        │ server-authenticated request; no direct Python access
        ▼
Outer Agent Worker ── derives session DO name from server cookie ──► ConversationAgent DO
        │                                                        │
        │ native Agent/DO state, job/fences, budgets, publication │ Workers AI Llama 3.3
        │                                                        │ (Analyst / optional Semantic /
        │                                                        │  Candidate / Validator)
        │                                                        ▼
        └────────────── service binding TOOLS ─────────────► Python Tools Worker >=3.12
                                                              catalog/profile/query/search
                                                              P5/P6 mechanical checks
```

The browser never supplies a source path, Durable Object name, session identity or capability.
The outer Worker authenticates the existing private surface and routes only to the server-derived
session DO. The DO calls the Python Worker through a service binding; the Python Worker has no
public v2 route and never receives credentials, cookies or model prompts beyond the bounded typed
request fields required for a tool. Workers AI is called only by the Agent, with a server policy
prompt and bounded untrusted question/content data.

The M4 implementation may retain the existing class/binding names (`ProofAgent`, `ProofBudget`,
`TOOLS`) while adding a separate v2 state record and additive handlers. It must not make the v1
`/proof/*`, `/health`, `/metadata` or `/query` DTOs wider or reinterpret their receipts.

## Components, ownership, and contracts

| Component/boundary | Responsibility | Owns | Interfaces/consumers | Operating owner | Evidence or decision |
| --- | --- | --- | --- | --- | --- |
| Catalog registry | Resolve complete approved source tuple and actual capabilities | source identity, schema/meaning/profile revisions, manifest metadata, limits | `/v2/catalog`; Agent | Python/runtime | M3 identities; v2 catalog pending |
| Data Profiler | Deterministically create bounded profile from catalog identity | `DataProfileV2`, profile digest | `/v2/profile`; Analyst/Validator | Python | sales profile exists; support profile only if implemented |
| Query/Search tools | Execute only approved read-only operations and return immutable receipts | query/search receipts, runtime/hash provenance | `/v2/query`, `/v2/search`; Agent | Python | M3 query/search implementations; v2 envelopes pending |
| Numerical validator (P5) | Check numeric claims against exact result cells/approved calculations | `NumericalCheckReportV2` | internal module or private `/v2/validate/numeric`; Candidate/Validator | Python | contract pending implementation |
| Citation validator (P6) | Check exact returned support hit IDs/quotes and coverage limits | `CitationCheckReportV2` | internal module or private `/v2/validate/citation`; Candidate/Validator | Python | contract pending implementation |
| ConversationAgent DO | Orchestrate stages, invoke models, persist session/job state, enforce fences | job journal, accepted memory, publication pointer | native Agent + outer transport | Agent/runtime | v1 DO exists; v2 record pending |
| Proof/global budget DO | Serialize hourly/daily admissions without user text | stage counters and retained request identities | Agent only | Agent/runtime | P4b budget is prerequisite; v2 stage accounting pending |
| Validator model call | Independent structured challenge over identical immutable inputs | `ValidatorReportV2` | Workers AI, Agent | Agent/operations | separate call required; live quota pending |
| Delivery/QA/review | Measure source, runtime and deployed behavior | reports, receipts, coverage and gate evidence | coordinator/reviewers | coordinator | later milestone evidence |

### Common v2 envelope and canonicalization

All v2 JSON uses strict objects and rejects unknown fields, unknown major versions, non-finite
numbers, surrogate code points and ambiguous null/missing values. Timestamps are UTC RFC3339 with
`Z`; date ranges use the source’s declared calendar meaning. UTF-8 byte limits are measured before
JSON parsing where a request body is streamed and after canonical serialization for responses.

`canonical-json.v1` is UTF-8 JSON with recursively lexicographically sorted object keys, array order
preserved, `ensure_ascii=false`, separators `,` and `:`, and no NaN/Infinity. A digest is SHA-256
lowercase hexadecimal over canonical bytes with the digest field omitted. Producers calculate the
digest; consumers recompute it before using content. A hash is integrity evidence, never an access
capability.

Every v2 service envelope is:

```json
{
  "version": "2",
  "job_id": "UUID",
  "run_id": "UUID",
  "payload": {},
  "payload_sha256": "64 lowercase hex characters",
  "runtime": {
    "python_version": "3.12.x",
    "sqlite_version": "...",
    "runtime_mode": "local|deployed",
    "build_revision": "40 lowercase hex characters or null",
    "worker_version_id": "UUID or null",
    "service_contract_revision": "m4-service.v1"
  }
}
```

`runtime_mode=deployed` requires both build revision and Worker version ID. Agent provenance is
separate and includes the Agent Worker version/build and `agents_version`; the Python Worker cannot
assert it. `job_id` identifies the logical user operation and `run_id` identifies one stage attempt.
Neither is bearer authority. Catalog responses use `run_id=null` and `job_id=null` because they are
not job-owned; all job-bound tool calls require both IDs.

### M3-P7 precedence and compatibility

`M4-ARCH-v2` is the canonical `m4-service.v1` contract for the unimplemented
M3-P7 v2 routes and all new Agent consumers. It supersedes the earlier M3-P7
draft's job-only request shape by adding `run_id`, the duplicated full source
tuple, and the runtime envelope. That draft remains historical design input.
Existing v1 `/health`, `/metadata`, `/query`, `/proof/*` routes, DTOs, hashes
and state are unchanged; v1 consumers never receive v2 fields. Conformance
tests cover both families and reject a v1 payload at a v2 route and vice versa.

### Source catalog and profile contracts (M3-P7)

`CatalogV2` is bounded to 4,096 UTF-8 bytes and contains no filesystem path, credential handle,
question, message text or private session state. Each server-owned `display_name` is at most 64
UTF-8 bytes, `description` at most 160 bytes, and each capability-help value at most 180 bytes;
these are explanatory text only and never grant a capability.

```json
{
  "version": "2",
  "catalog_revision": "m4-catalog.v1",
  "entries": [
    {
      "source": {"version":"1","source_id":"sales","snapshot_sha256":"a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f","meaning_revision":"sales-demo.v1"},
      "schema_revision": "sales-demo.v1",
      "profile_revision": "m3-profile.v1",
      "kind": "structured",
      "display_name": "Sales demo",
      "description": "Synthetic net sales lines for bounded structured analysis.",
      "capability_help": {"profile":"Summarize fields and bounded statistics.","query":"Ask for read-only totals, groups, rankings or period comparisons."},
      "capabilities": ["profile","query"],
      "record_count": 24,
      "manifest_bytes": 1025,
      "scope": "complete_immutable_fixture"
    },
    {
      "source": {"version":"1","source_id":"support","snapshot_sha256":"c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536","meaning_revision":"support-demo.v1"},
      "schema_revision": "support-demo.v1",
      "profile_revision": null,
      "kind": "messages",
      "display_name": "Support messages",
      "description": "Synthetic support messages for targeted lexical examples.",
      "capability_help": {"search":"Find matching messages with exact IDs and source quotes; hits do not establish prevalence."},
      "capabilities": ["search"],
      "record_count": 16,
      "manifest_bytes": 3091,
      "scope": "complete_immutable_fixture"
    }
  ]
}
```

The historical proof identity remains `36ea7edc3c94c5df1320946f1fcefb6bc5c6e7252cf2242344ee70f168d78396` with `sales-proof.v1`; it is never silently remapped to the demo. The implementation
must use the registered values above and the M3 manifest, never a caller-provided path or abbreviated hash. A catalog entry
is selectable only if the requested capability is listed and the loader reproduces the registered
bytes/hash/record count. A support profile entry may be added in a separately tested contract slice;
until then the catalog must omit `profile`, and an attempted profile operation returns
`capability_mismatch` rather than fabricated metadata.

`DataProfileV2` is the existing M3 typed profile shape: full `source`, `schema_revision`,
`profile_revision`, ordered fields with meanings/null counts, bounded exact dimensions/measures,
explicit omissions, capabilities and `analytical_validated:false`. The profile response is the
common envelope with `payload=DataProfileV2`, payload <=4,096 bytes, whole envelope <=16,384 bytes.
Profile operation starts a new `run_id`; it cannot change source identity or analytical validation.

### Query and search contracts (M3-P7)

The v2 query request is a strict object with no client result fields:

```json
{
  "version":"2",
  "job_id":"UUID",
  "run_id":"UUID",
  "source": {"version":"1","source_id":"sales","snapshot_sha256":"...","meaning_revision":"sales-demo.v1"},
  "intent": {
    "version":"1",
    "source": {"version":"1","source_id":"sales","snapshot_sha256":"...","meaning_revision":"sales-demo.v1"},
    "question":"bounded original question",
    "sql":"SELECT ...",
    "max_rows":20
  }
}
```

The service verifies that request and intent source tuples match exactly, source is registered with
`query`, SQL is read-only and allowlisted by the existing `m2-sqlite.v1` policy, and all result
limits are enforced before returning. The response is an envelope whose payload is a new
`QueryResultV2` with the v1 exact cells/columns/actual SQL/result hash/coverage/limits/runtime
fields, `version:"2"`, the full demo source identity and `analytical_validated:false`. It does
not mutate or widen `QueryResult` v1. `max_rows` is capped at 20 for this service even though the
transport-only `SqlIntent` allows a larger value.

The v2 search request is the existing strict `SearchRequestV2` fields plus `job_id` and `run_id` at
the service boundary. The inner payload remains the M3 exact request: support source tuple,
case-sensitive channel/customer filters, UTC `[start,end)`, ASCII token policy and `max_hits 1..5`.
The response payload is the existing `SearchReceiptV2`; its exact quote, score, hit ordering,
scanned/matched/returned/omitted counts and both fixed targeted-search limitations are preserved.
Search never returns whole-corpus prevalence, absence or trend claims.

For all tools, service errors are strict `ServiceErrorV2`:

```json
{
  "version":"2",
  "code":"invalid_input|unsupported_version|access_denied|source_mismatch|unsupported_source|capability_mismatch|invalid_query|unsafe_query|execution_limit|result_limit|invalid_result|runtime_incompatible|python_unavailable|not_found",
  "stage":"input|catalog|profile|query|search|transport",
  "job_id":"UUID or null",
  "run_id":"UUID or null",
  "limit":{"name":"max_result_bytes","maximum":16384},
  "provider_reason":null,
  "automatic_retry":false
}
```

`limit` is null unless a fixed policy limit is the safe explanation; no request, SQL, quote,
path, raw exception, credential or provider body appears. A known input/version/capability refusal
consumes no tool or model admission. Private binding timeout has no automatic retry.

### Field-level conversation DTOs

The following are the canonical public projections for Agent/UI consumers. All
objects are strict v2 objects; IDs are UUIDs and every text field has the byte
limit shown. `SessionSnapshotV2` contains `revision`, `selected_source`,
`catalog_revision`, `job: JobStatusV2|null`, `history`,
`accepted_answers:[AcceptedAnswerV2]` (at most four owned answers with their
`AcceptedEvidenceV2` projections), `accepted_memory`, `dropped_history`,
`actions` and `expires_at`. `GET /v2/session` returns this snapshot at one
durable revision, is capped at 65,536 bytes, and returns either all listed
accepted projections or typed `evidence_unavailable` markers; no unnamed
client-created detail route is required. `JobStatusV2` contains
`job_id`, `request_id`, `phase`, `source`, `progress_stage`, `message`,
`clarification: ClarificationV2|null`, `candidate_visible:false`,
`accepted_answer_id`, `error`, `started_at`, `deadline_at` and `revision`.
The only allowed `actions` are `submit`, `cancel`, `select_source`, `reset`,
`retry_new_request` and `reconnect`; each action is server-authorized and has
`enabled` plus a safe `reason`.

`ClarificationV2` contains `clarification_id`, `job_id`, `request_id`,
`source`, `question` (512 bytes), `reason` (`missing_meaning|ambiguous_period|
unsupported_scope|missing_filter`), `expires_at`, `resolved:false|true`, and
`resolution: {response_id, answer, response_sha256, resolved_at}|null` where
`answer` is at most 512 bytes and is bound to the same `clarification_id`,
`request_id`, source tuple and next `job_id`; a response cannot be reused for a
different question or source. `ClarificationSummaryV2` stores only those IDs,
the source label and a 256-byte summary after resolution.
`EvidenceRefV2` contains `evidence_id`, `kind` (`query|search|profile`),
`source`, `payload_sha256`, `receipt_id`, `scope`, `coverage` and
`availability` (`available|evidence_unavailable`); it carries no path or raw
diagnostic. `AcceptedAnswerV2` contains `answer_id`, `publication_id`,
`source`, `question` (1,024 bytes), `answer` (4,096 bytes), `claims`,
`citations`, `limitations`, `evidence`, `plan_sha256`, `validator_report_sha256`,
`accepted_at` and `historical_v1:false`. `HistoryEntryV2` is a bounded summary
of an accepted answer, clarification or failure with `entry_id`, `kind`,
`created_at`, `source`, `answer_id|null`, `status`, `summary` (512 bytes),
`evidence_ids` (at most 8) and `availability`.

Each accepted answer also stores an `AcceptedEvidenceV2` projection for every
material claim or citation: `evidence_id`, `kind`, `source`, `receipt_id`,
`payload_sha256`, `scope`, `coverage`, `availability`, and a bounded
`display_payload` containing the complete referenced numeric cells or complete
support hits/quotes plus counts and fixed limitations. A query projection is
limited to 4,096 bytes and a search projection to 6,144 bytes; unreferenced
receipt rows remain represented by their verified receipt hash and are never
rendered as accepted evidence. The projection is the refresh-safe evidence
view, not a rewritten analytical receipt, and is included in state-cap accounting.

The source-switch transition is explicit: when idle, persist the new catalog
tuple and clear only unresolved clarification; when active, atomically bump
`generation`, increment `cancel_epoch`, mark the old job `cancelled`, preserve
accepted history with its source labels, then persist the new selection. A
failed transition returns `source_switch_conflict` and retains the old source.
Reconnect observes the resulting snapshot; it never replays a fenced job.

### Numerical validation contract (M3-P5)

The P5 module and optional private route `/v2/validate/numeric` use `m4-numeric.v1`. The validator
accepts only actual `QueryResultV2`/`DataProfileV2` payloads whose envelope and payload digests,
source identity, schema/profile revision and runtime provenance have already been verified.

A `NumericalClaimV2` is:

```json
{
  "version":"2",
  "claim_id":"UUID",
  "claim_type":"scalar|ranking|comparison|count|sum",
  "text":"bounded candidate claim text",
  "value":{"kind":"exact_integer","value":"395000","unit":"USD_cents"},
  "scope":{"source":{},"period":{"start":"2026-01-01","end":"2026-04-01","timezone":"UTC"},"group":null},
  "result_ref":{"receipt_id":"UUID","payload_sha256":"64 hex","column":"revenue_cents","row_index":null,"cell_path":"sum"},
  "calculation":{"kind":"direct_cell|sum|difference|rank","inputs":["result-ref-or-claim-id"],"formula":"bounded canonical expression"},
  "evidence_refs":["receipt-id"],
  "exact":true
}
```

The canonical MVP numeric value is a signed decimal integer string with an explicit unit. The
checker requires exact integer equality for exact result cells and approved integer calculations;
units, source tuple, period/filters, group identity, result digest and cell/row reference must all
match. `rank` checks the complete returned grouped result and deterministic tie order. The checker
rejects missing/foreign/changed result refs, source or period mismatch, denominator/unit mismatch,
non-finite values, overflow, fabricated rows and unsupported formulas. It never calls a model.

A query `real` cell (`exact:false`) or any calculation containing one is **unsupported for a
material MVP claim** under `m4-numeric.v1`; the checker returns `unsupported_non_exact_value` and
publication must abstain or ask for a narrower exact question. This is an explicit safe refusal,
not a claim that the value is false. Adding an approved tolerance requires a new policy revision,
operation-specific error bounds and independent cross-runtime tests; it cannot be inferred from
floating-point formatting.

`NumericalCheckReportV2` contains `version`, `claim_id`, `result_refs`, `checks` (each with
`name`, `status:"pass|fail|unsupported"`, safe `code`), `overall:"pass|fail|unsupported"`,
`policy_revision:"m4-numeric.v1"`, `input_sha256` and `report_sha256`. It is valid only for the
exact immutable inputs named by its hashes. A batch has at most 12 claims and 12 reports and is
<=8,192 bytes; any overflow refuses the whole batch.

### Citation validation contract (M3-P6)

The P6 module and optional private route `/v2/validate/citation` use `m4-citation.v1`. A
`CitationV2` binds one candidate assertion to one returned support hit:

```json
{
  "version":"2",
  "citation_id":"UUID",
  "source": {"version":"1","source_id":"support","snapshot_sha256":"...","meaning_revision":"support-demo.v1"},
  "search_receipt_id":"UUID",
  "search_payload_sha256":"64 hex",
  "message_id":"M001",
  "quote":"exact nonempty substring of the returned complete quote",
  "quote_sha256":"64 hex",
  "claim_id":"UUID",
  "coverage":"targeted_lexical_search"
}
```

The checker recomputes the search payload digest, finds the exact message ID in the returned hits,
requires source identity/policy/scope equality and checks `quote` as a case-sensitive, unmodified,
nonempty substring of that hit’s complete original quote. It checks `quote_sha256` over the exact
UTF-8 quote. Changed punctuation, whitespace, case, IDs, source/hash, unreturned hits and foreign
receipts fail. There is no quote normalization, query-word substitution or corpus-wide inference.
A citation can support a targeted example only; a candidate assertion of prevalence, whole-corpus
trend or proof of absence fails with `unsupported_coverage` even if the quote is exact.

`CitationCheckReportV2` contains `version`, `citation_id`, `search_receipt_id`, `checks`,
`overall:"pass|fail|unsupported"`, `policy_revision:"m4-citation.v1"`, `input_sha256` and
`report_sha256`. A batch is at most 8 citations and 8 reports and <=8,192 bytes. P6 owns no model
call and does not alter the search receipt or quote.

### Analysis plan, claims, candidate and Validator contracts

`AnalysisPlanV2` is the only executable planning artifact. It is immutable and includes:

- `version:"2"`, `plan_id`, `job_id`, `plan_revision` and `plan_sha256`;
- original question, selected full source identity, profile/capability refs and optional resolved semantic ref;
- `mode:"query"|"search"|"clarify"`, an acyclic ordered step list (`profile`, `query`, `search`, `clarify`), expected input/output grain and units;
- exact query/search request refs or a clarification payload; no model-supplied path, capability or authorization;
- coverage (`complete_query_result` or `targeted_lexical_search`), required deterministic checks, context/evidence limits, stage budget and deadline;
- `producer` (`analyst`), `prompt_revision`, and model/runtime provenance when a model produced it.

The plan is rejected if a step is unknown, cyclic, unallowlisted, source-mismatched, over limits,
not supported by catalog capabilities or semantically unresolved. A human-readable rendering is
non-executable. Known bundled meanings skip the Semantic role. If a question asks for unsupported
meaning, relative period or corpus-wide support conclusions, the Analyst returns `ClarificationV2`
with one bounded question/limitation and no tool dispatch.

A `CandidateAnswerV2` is private until publication and contains:

- `version:"2"`, `candidate_id`, `job_id`, `run_id`, question and source identity;
- `plan_id/sha256`, ordered `claims` (maximum 12), ordered `citations` (maximum 8), bounded answer text (maximum 4,096 UTF-8 bytes), explicit limitations (maximum 4), and requested-question coverage;
- every material claim’s typed numeric value/result refs or typed citation refs; qualitative text without evidence is non-material only when labeled limitation/clarification;
- `candidate_sha256`, `analyst_runtime`, `model_id` and `prompt_revision`.

A candidate with a fabricated result ref, unsupported claim, unsupported citation coverage, mismatched
source/scope/unit, omitted material claim disposition or altered quote is rejected. Candidate text,
claims and citations are not copied into accepted history until publication passes.

`ValidatorInputV2` is constructed by the Agent from the immutable original question, resolved
clarification, the complete bounded profile/field-meaning context (or the complete catalog meaning
context for support), the complete actual query or search receipt, candidate, P5/P6 reports, source
and runtime provenance, and requested-question coverage. A single job has one tool receipt: the
worst-case byte calculation is profile/meanings 4,096 + query receipt 16,384 + candidate 4,096 +
plan/question/provenance 4,096 + checks/report dispositions 4,096 = 32,768 bytes. Search jobs
use an 8,192-byte receipt and remain below that cap. The canonical input cap is therefore 32,768
bytes with max+1 boundary tests; no rows, meanings or material evidence are silently dropped.
Its digest is recorded before dispatch. It contains no client state authority and no raw credentials.

`ValidatorReportV2` contains `version:"2"`, `report_id`, `job_id`, `run_id`, `candidate_id`,
`candidate_sha256`, `plan_sha256`, `source`, `validator_policy:"m4-validator.v1"`,
`prompt_revision`, `validator_call:"performed|skipped_deterministic_failure|failed"`, separate `deterministic_checks` and `claim_dispositions` (`supported`,
`unsupported`, `insufficient_evidence`), `overall:"pass|fail|needs_clarification"`, bounded
`remediation`, `validator_runtime`, `model_id`, `input_sha256` and `report_sha256`. A PASS requires
all required deterministic checks PASS, every material claim supported, requested coverage complete,
and a successful independent structured Validator model call. A deterministic failure prevents a
model PASS; the report may record `validator_call:"skipped_deterministic_failure"`. Missing,
malformed, stale or input-mismatched reports are failures, never publication authorization.

The Validator model receives the candidate and evidence as untrusted bounded data under a server
prompt. It cannot call tools, alter source identity, grant capabilities or change deterministic
reports. Its output is a strict JSON verdict only; provider errors, quota refusal and malformed
output consume the reserved model admission and produce safe non-publication.

### Durable session, job, run and publication contracts

The server-owned v2 session key is derived from the authenticated private session cookie exactly as
v1 derives its DO name. Client-provided session IDs, job IDs, run IDs, source paths and evidence IDs
never select storage. Use one `ConversationStateV2` value in the session DO for the public projection
and bounded accepted state; keep the existing v1 state under its existing key/schema. No automatic
migration relabels a v1 proof receipt or planning candidate as an accepted v2 answer. If a future
migration displays v1 artifacts, each must carry `historical_v1` and remain non-accepted.

`SessionStateV2` contains:

```text
version:"2", revision:uint64, selected_source:SourceIdentity|null,
selected_catalog_revision, history:[HistoryEntryV2] (max 12),
accepted_answers:[AcceptedAnswerV2] (max 4 owned answers with AcceptedEvidenceV2 projections),
accepted_memory:[AcceptedMemoryV2] (max 4 same-source summaries), dropped_history:uint,
active_job:JobRecordV2|null, expires_at:UTC timestamp
```

Accepted memory stores bounded text plus lineage (`answer_id`, source tuple, plan/report hashes,
accepted-at) and never stores rejected candidate prose or unverified model summaries. Canonical
state accounting is UTF-8 bytes of the sorted-key JSON projection, including field names and arrays:
each history entry is <=1,024 bytes, accepted-memory entry <=4,096, accepted answer plus its
evidence projections <=12,288, clarification/error <=1,024,
the active job <=4,096, and each request-journal outcome is only `{request_id,input_sha256,job_id,
terminal_code,publication_id|null}` <=256 bytes (32 entries maximum). The complete state must be
<=65,536 bytes before every write. When a new accepted entry would exceed the cap, evict its oldest
accepted answer/evidence projection and accepted-memory entry first, then oldest history entries, replacing each with an
`evidence_unavailable` marker; never evict the active job, current selection, clarification or the
last journal outcome needed for same-request replay. If the marker itself cannot fit, refuse the
publication with `state_limit` and keep the candidate private. History is logically retained for
seven days only while owned; an unavailable marker cannot be reused as a fact. Refresh is a
read/reconciliation operation; it never resubmits work.

`JobRecordV2` contains:

```text
job_id:UUID, request_id:UUID, input_sha256:64hex, source:SourceIdentity,
plan_id/plan_sha256:nullable, generation:uint64, cancel_epoch:uint64,
phase:queued|profiling|semantic|planning|executing|candidate|validating|replanning|
      cancel_requested|completed|awaiting_clarification|failed|interrupted|cancelled|budget_exhausted,
started_at, deadline_at, active_run_id:UUID|null, stage_runs:[StageRunV2] (max 8),
model_calls:uint (max 6), query_calls:uint (max 2), candidate_id/report_id/publication_id nullable,
error:ServiceErrorV2|null, clarification:ClarificationV2|null, accepted_answer_id:UUID|null
```

Each `StageRunV2` has `run_id`, stage, attempt (always 1 for a technical attempt), input/output
digests, start/finish times, runtime provenance and terminal status. A replan is a new plan revision
and stage run under the same job, not a retry of a failed physical call. No technical/provider SDK
retry is automatic. At most one analytical replan is allowed when the Validator returns a bounded
remediation that does not require new source scope; otherwise the job becomes failed or clarification.

For each new request, the DO atomically stores the queued job and input hash before any awaited
call. The request journal retains the latest 32 `{request_id,input_sha256,job_id,outcome}` entries.
Same ID and same hash returns the retained owned outcome without another model/tool call; same ID and
different hash returns `request_conflict`; retained ID with evicted/missing outcome returns
`request_outcome_unavailable`; after journal eviction there is no idempotency guarantee. A new source
selection, reset, cancellation, restart reconciliation or expiry increments the relevant generation
or cancel epoch and fences old work.

A stage admission is reserved before dispatch and is never refunded after an uncertain timeout. MVP
limits are: 12 model calls per session rolling hour, 24 model calls per UTC day globally, 30 accepted
jobs per session rolling hour, 128 tool attempts per UTC day globally, 6 model calls and 2 tool calls
per job, one active job per session, one optional replan, 30-second model wait, 10-second service
binding wait and 60-second job publication deadline. These are application safety limits; no reset
or billing behavior is implied. The current P4b budget remains the global source of truth until a
reviewed v2 budget record is merged; v2 must not create a second uncoordinated counter.

The publication transaction is a single serialized DO state transition:

1. Verify the current job ID, generation, cancel epoch, selected source hash, plan/candidate/report hashes and deadline.
2. Verify all required P5/P6 reports pass and the independent Validator report is PASS for the exact immutable input hashes.
3. Verify the candidate has no unsupported material claims and the accepted answer/evidence state fits the total state cap.
4. Create one `AcceptedAnswerV2` and history entry with `publication_id`; set job `completed`; update bounded accepted memory and revision in one durable write.
5. On duplicate publication, return the existing owned `publication_id`; on any mismatch, write no accepted state and return `stale_job`/`publication_conflict`.

The answer becomes visible only after the durable write succeeds. A model/tool completion after cancel,
source change, reset, expiry, newer job, deadline or DO restart can never publish. If the write fails,
the candidate remains private and the job returns a safe failure/reconciliation state; a later read may
reconcile only from the stored job and hashes, never from a live promise.

Cancellation is cooperative: the DO first increments `cancel_epoch`, marks `cancel_requested` and
prevents new stages; once in-flight work is observed or reconciled, it commits `cancelled` with no
receipt/candidate publication. Late callbacks are ignored. An expiry callback is keyed by job ID,
generation and deadline; an expired active job is reconciled to `interrupted` on every authorized read.
Disconnect loses transport only; it does not resubmit or imply success. Source change follows the
transition above: it fences and cancels an active job, preserves source-labelled accepted history,
clears unresolved clarification, and commits the new selection atomically; reset uses the same fence
but clears owned v2 history according to the UX retention policy.

## Critical flows and failure/recovery

| Flow | Normal path | Failure/overload | Detection | Safe/user-visible response | Recovery and owner | Evidence/unknown |
| --- | --- | --- | --- | --- | --- | --- |
| Source selection | Catalog → exact source tuple persisted | stale hash/capability missing | registry/hash check | `source_mismatch` or `capability_mismatch`; keep old selection | user selects listed identity; Python owner fixes catalog | v2 route unimplemented |
| Sales answer | profile → Analyst query plan → Python query → candidate → P5 → Validator → publish | unsafe SQL, wrong result, model quota or malformed candidate | strict DTO, receipt/hash and stage checks | failure/clarification; no answer/history mutation | new user request or one bounded replan; Agent owner | live chain unknown |
| Support example | catalog → Analyst search plan → Python targeted search → exact citations → P6 → Validator → publish | no hits, unsupported corpus claim, forged quote | receipt counts/limitations and exact substring check | targeted evidence or explicit limitation; no prevalence statement | narrower query/new request; Python/Agent owner | support profile capability may be absent |
| Refresh/follow-up | GET reads DO and same-source accepted memory | expired/evicted or source changed | revision/retention reconciliation | explicit `evidence_unavailable`/clarification | user asks fresh bounded question | deployed restart unverified |
| Duplicate/cancel | journal replay or generation fence | same UUID changed input, late callback | input hash/cancel epoch/active job | conflict/replay/cancelled; no rerun or stale publish | user supplies fresh UUID; Agent owner | fault injection pending |
| Budget/quota | reserve before each stage | session/global cap, provider 429, timeout | durable counters and classified provider status | budget/model_quota safe error; no reset-time claim | continue offline/mock work; operations owner | free allowance may remain exhausted |
| Publication | fenced all-check PASS → one DO write | storage/write/race failure | state revision/publication ID | no visible answer; safe failure/reconciliation | retry only as a new authorized request after terminal recovery; Agent owner | atomic write proof pending |

## Security lifecycle

- **Authoritative policy:** M2 threat controls, M3 contracts, AGENTS.md secret/logging rules and user synthetic-only/full-GO/cost direction.
- **Assets:** synthetic fixtures, source hashes/meanings, session cookie, DO state, model prompts/outputs, candidate/evidence/provenance, Python service binding and Workers AI quota.
- **Trust boundaries:** private outer Worker → session DO; session DO → service binding; session DO → Workers AI. Browser/model/source text is untrusted. The Python service does not trust job IDs, source identity or model SQL until strict validation and catalog resolution.
- **Preventive controls:** server-derived DO routing; strict bodies/unknown-field rejection; full source tuple checks; allowlisted read-only SQL; bounded search/profile/results/context; P5/P6 mechanical checks; independent Validator; no model capabilities; no secrets in context/logs; per-session/global admissions.
- **Detective controls:** content/runtime/source/payload hashes; stage/run provenance; safe structured errors; revision/generation/cancel fences; QA mutations for foreign IDs, altered quotes/results, stale callbacks and secret sentinels.
- **Recovery:** fail closed, retain no unaccepted answer, fence late work, reconcile expired jobs on read, preserve v1, roll back additive v2 worker/service versions.
- **Threat/control dependency:** affected M2 threat controls `CTRL-01`, `CTRL-05` through `CTRL-11`; a fresh threat/security review is required because candidate/evidence/model boundaries and publication are activated. This document is not that review.
- **Residual security risk:** possession of the current private bearer/cookie can access its synthetic session under the existing operator model; this does not establish identity or public-data security. Provider-backup deletion is not promised.

## Infrastructure and operating dependencies

The selected hosting remains the existing Cloudflare Workers + native Agents SDK + Durable Object +
Python Worker service binding + Workers AI topology. No new paid service or infrastructure product is
selected. The existing `ProofBudget`/SQLite v2 migration is the budget precedent; a v2 implementation
must extend one authoritative budget owner rather than create a bypass.

Workers AI live checks use the configured Llama 3.3 model and free allowance only. Mocks may cover
routine unit/integration tests but cannot satisfy live model or deployed acceptance. Quota exhaustion
is an observed failure for that check, not a reason to enable billing. Actual Cloudflare Worker
version IDs, Python runtime, SQLite fit, DO restart/background lifetime, model availability and
service-binding provenance remain deployment evidence to collect.

No infrastructure assessment was activated by this architecture slice. If the implementer proposes a
new store, queue, public route, account/auth boundary or materially different runtime, stop and route
it to infrastructure/threat owners before implementation.

## Rollout, compatibility, and recovery

1. Merge/review M3-P5 and P6 contracts and implementation, then additive P7 v2 catalog/profile/query/search and validator routes. Keep v1 routes and fixtures unchanged.
2. Deploy the reviewed private Python Worker; verify catalog/source hashes, runtime provenance, limits and v1 regression before using it from the Agent.
3. Add v2 session/job/fence/budget records and native Agent orchestration. Keep v1 state under its current schema/key. Use mocks first; one free-only live model probe is separate evidence.
4. Add candidate/P5/P6/Validator/publication slices. Run local exact oracles, mutations, session isolation, refresh/follow-up, cancellation, restart and provider-failure tests before guarded merge.
5. Deploy a reviewed preview, record both Worker version IDs/build revisions and run the two source smoke journeys. Roll back by selecting the prior reviewed Worker versions or disable private v2 handlers; never alter fixture bytes or v1 state.
6. Final M4 report records merged PR links, verified main revision, exact coverage/tests, runtime/deployed results, free-quota failures and unrun checks. M5 UI/public surface remains a later milestone.

Mixed-version behavior: v1 consumers continue to send/receive version 1; v2 consumers reject v1
where a v2 artifact is required and vice versa. Unknown major versions fail closed. Additive fields
require a minor/policy revision and conformance tests. No retained artifact is silently reinterpreted.

## Consequential decisions

| Decision/ADR | Owner | Alternatives | State | Evidence/rationale | Reversibility/revisit trigger |
| --- | --- | --- | --- | --- | --- |
| ADR-M4-01 additive v2 service/state boundary | Architect/runtime | broaden v1; replace proof state | proposed | v1 is deployed/reviewed proof behavior; separate state prevents relabeling | reversible before v2 consumers; revisit only with migration evidence |
| ADR-M4-02 one fenced DO publication transaction | Architect/Agent | client publication; multi-store event chain | proposed | DO serialization and one bounded state object provide smallest atomic answer visibility | revisit if measured state size or lifecycle requires artifact store |
| ADR-M4-03 P5/P6 deterministic refusal for non-exact/unsupported coverage | Architect/validation | model-only check; guessed tolerance; whole-corpus implication | proposed | exact fixture receipts and targeted search limitations are authoritative; model agreement cannot prove arithmetic/coverage | new policy only with operation-specific evidence and independent tests |
| ADR-M4-04 shared stage admission and bounded correction | Architect/budget/security | hidden SDK retries; separate unbounded counters | proposed | existing 12/hour, 24/day budgets and user free-only authority; every uncertain call must count | revisit after measured quota/latency evidence and explicit cost authority |
| ADR-M4-05 server-derived session routing | Architect/security | client session/job routing; public identity | proposed | preserves v1 isolation and synthetic operator scope | revisit only with a new authenticated workspace threat contract |

These are proposals for independent review; none is a human approval or implementation claim.

## Implementation criteria

| Criterion | Responsible receiver | Observable pass condition | Required evidence | Dependency/gate |
| --- | --- | --- | --- | --- |
| ARCH-1 | M3-P5 owner | Numeric claims/checks use exact typed result refs, deterministic equality/units/scope and safe non-exact refusal | focused tests, mutation matrix, canonical hashes | P5 contract review |
| ARCH-2 | M3-P6 owner | Citations accept only returned IDs and exact nonempty quote substrings with source/hash/scope match; coverage limits remain | focused tests for valid/forged/changed/cross-source/unsupported coverage | P6 contract review |
| ARCH-3 | M3-P7 owner | Catalog/profile/query/search and optional validator routes enforce v2 envelopes, identity, byte limits, hashes, runtime provenance and safe errors | Python route tests, parity tests, v1 regression, body/result max+1 | P5/P6 merges and service review |
| ARCH-4 | Agent/backend owner | Plan, candidate, validator and job schemas reject unknown/foreign/stale inputs; model output has no authority | TS/Python contract tests, mocked model cases | P7 v2 service merged |
| ARCH-5 | Agent/runtime owner | New job is durably queued before dispatch; each stage has run ID, admission and fence; duplicate/change/cancel/expiry/restart outcomes are truthful | deterministic fault injection and exact state snapshots | threat/architecture readiness |
| ARCH-6 | Validator/Agent owner | Mechanical checks precede model PASS; independent structured Validator receives immutable hashes and cannot override deterministic FAIL | captured bounded validator input, malformed/FAIL/PASS tests | P5/P6 and model adapter |
| ARCH-7 | Agent/runtime owner | Only one fenced publication transaction exposes accepted answer/history; failed/late/cancelled candidates remain private | race, write-failure and duplicate-publication tests | ARCH-4–6 |
| ARCH-8 | QA/coordinator | Both sources execute real fixture oracles and mutations; refresh/follow-up/isolation/budget/error/secret tests pass; v1 regressions pass | independent QA report and coverage | guarded PR gates |
| ARCH-9 | Operations/coordinator | Preview/final runtime IDs, hashes, model receipts, failures and unrun checks are recorded; free-only policy remains | deployment receipts and milestone report | review/approval/guarded deployment |

## Evidence and uncertainty ledger

### Facts

- M4-BRIEF-v1 explicitly requires the exact source, plan, claims/citations, Validator, publication, job/fence, budget, isolation and v1 compatibility boundaries.
- M3-ARCH-v1 defines complete sales/support identities, strict profile/query/search receipts and targeted-search limitations; current implementation has v1 proof routes and M3 tool modules but no v2 publication contract.
- The original architecture assigns reasoning to agents and deterministic operations to infrastructure and requires independent validation before publication.
- Existing M4 P4a/P4b reports define a native Agent/DO planner and 12/hour session plus 24/day global model admissions, with live/deployed paths still unverified.

### Observations

- Inspected `src/data_intel/service_contracts.py`, `service_routes.py`, `profile_models.py`, `search_models.py`, `workers/agent/src/contracts.ts` and `workers/agent/src/index.ts` at the recorded baseline.
- Existing v1 service/Agent DTOs reject unknown fields and validate result/source/runtime hashes, but they represent proof receipts rather than accepted answers.
- No code, tests, provider call, deployment, branch, PR, merge or external approval was performed by this architecture task.

### Inferences

- A separate v2 state record is the smallest compatibility-preserving path because it prevents old proof/planning state from becoming accepted analytical history.
- A single bounded DO state write is sufficient for MVP publication and avoids introducing an unreviewed artifact store or cross-service transaction. This is an implementation hypothesis that must be tested against the 65,536-byte cap and runtime behavior.
- Rejecting material non-exact numeric claims is safer and more reproducible than inventing a tolerance; a later policy can add exact operation-specific tolerance.
- Support targeted search can ship with catalog schema/meanings and no support profile capability; requesting an unimplemented profile must refuse rather than fabricate one.

### Assumptions

- Existing private service binding remains available to the Agent and is not exposed to browsers.
- The existing operator-only authentication/origin/cookie controls remain the M4 transport boundary until the UX/security owners reconcile a v2 surface.
- The current P4b budget owner can be extended or versioned once, without resetting existing counters.

If any assumption is false, implementation stops at the affected boundary and routes evidence/options to
the architecture/runtime/security owner; no silent substitution is allowed.

### Decisions

- Use additive v2 contracts and state, preserving all v1 wire behavior and fixture identities.
- Make Python mechanical checks authoritative for numeric/citation support; require separate model Validator PASS for publication.
- Treat stage/run IDs and hashes as association/integrity data, never as authorization.
- Count every model stage and uncertain timeout against shared free-only budgets; no automatic provider retry.

### Unknowns

- Cloudflare Python runtime package/SQLite support and total-isolate resource fit for v2 checks.
- Native Agent/DO background lifetime, restart, cancellation and serialized state behavior under target deployment.
- Free Workers AI availability, actual model response shape/latency and deployed version provenance.
- Whether full accepted answer/evidence state stays under the 65,536-byte cap for the selected claim/citation limits.
- UX transport/state wording and security review disposition for the M4 conversation surface.

## Acceptance-criteria status

All M4 architecture acceptance criteria are **unverified**. This artifact freezes proposed contracts and
ownership; it does not claim implementation, QA, runtime, provider, merge or deployment evidence.

| Criterion ID | Status | Evidence | Blocker/owner, if separate |
| --- | --- | --- | --- |
| AC-M4-01 | unverified | v2 catalog/session/migration rules defined here | M3-P7 + Agent/QA |
| AC-M4-02 | unverified | plan/profile/query/search contracts defined here | P7 + Analyst/QA |
| AC-M4-03 | unverified | P5/P6 claim/citation contracts defined here | P5/P6 + QA |
| AC-M4-04 | unverified | Validator input/report and model boundary defined here | Validator/Agent + free-model QA |
| AC-M4-05 | unverified | publication transaction defined here | Agent/runtime + fault injection |
| AC-M4-06 | unverified | job/run/fence/replay/cancel rules defined here | Agent/runtime + deployed QA |
| AC-M4-07 | unverified | stage/global/session budgets defined here | budget/security + deployed QA |
| AC-M4-08 | unverified | accepted memory/eviction/source binding defined here | Agent/UX/security |
| AC-M4-09 | unverified | transport/context/secret boundaries defined here | security/QA |
| AC-M4-10 | unverified | rollout/report obligations defined here | coordinator + guarded workflow |

## Residual risks and unresolved decisions

| Risk or decision | Evidence state | Impact | Mitigation or option | Authorized owner/state |
| --- | --- | --- | --- | --- |
| P5/P6 exact numeric and citation DTOs need independent conformance review | proposed only | Candidate/publication cannot start | review contracts before code; mutation tests | validation owners |
| One DO state write may exceed target runtime/state limits | unknown | Publication or refresh may fail | measure exact bounded state; reduce retained summaries only through versioned policy | runtime/architect |
| Model can produce semantically wrong but executable SQL | known architecture risk | Wrong answer candidate | profile/meaning context, result checks, independent Validator, clarify unsupported meaning | Analyst/Validator/QA |
| Free quota may remain exhausted | observed historical failure in M2 reports | Live Llama acceptance remains unverified | mocks for routine work; one free-only live probe later; never enable billing | coordinator/operations |
| Background execution may stop after request/disconnect | prior reports explicitly unverified | Candidate may remain terminal interrupted | durable queued state, expiry reconciliation and deployed lifetime probes; no false completion | Agent/runtime/QA |
| Client cookie possession permits session access | existing operator model | No strong user identity/privacy guarantee | synthetic-only private scope; future auth requires new threat contract | security/product |
| UX state naming and public transport are not yet independently reviewed | M4-UX-v2 supplies the state/accessibility contract; design readiness is pending | M4/M5 handoff ambiguity | design review checks the exact UX/architecture trace before visible implementation | UX owner/reviewer |

No unresolved issue here requires a new human product decision within the already authorized synthetic
MVP. Any proposed public access, private-data handling, paid usage, larger workload or new infrastructure
is outside this handoff and must return to its owning decision authority.

## Human and external-action state

- Human full GO and free-only/no-paid-billing direction are recorded in M4-BRIEF-v1; no additional human approval is claimed.
- This is a local architecture proposal. Independent design-architecture readiness, threat/security review, QA, provider bot approval, guarded merge and deployment have not occurred in this task.
- No provider, procurement, model, branch, PR, merge, deployment or notification action was performed.
- Pending: scoped contract review; M3-P5/P6/P7 implementation; affected threat/UX review; independent QA and current-head provider review; preview/final smoke evidence; M4 report.

## Handoff envelope

- **Receiver and requested action:** coordinator. Route this exact artifact to the M3-P5 numerical owner, M3-P6 citation owner, M3-P7 Python service owner, UX owner, threat/security reviewer and independent design-architecture reviewer. The immediate accountable next action is independent design-architecture review of `M4-ARCH-v2` against `M4-BRIEF-v1`; do not start dependent Agent/publication implementation until affected readiness and prerequisite contract merges are recorded.
- **Artifact:** `docs/milestones/m4-conversation-architecture.md`, `M4-ARCH-v2`, source baseline `origin/main` `d4e03731af28ce1c9c0b53b8c59a133acd3edd4a`; original architecture SHA256 above.
- **Acceptance status:** `AC-M4-01` through `AC-M4-10` unverified; ARCH-1 through ARCH-9 are proposed implementation criteria. No acceptance, merge, provider approval or deployment is implied.
- **Evidence state and limits:** source/document/code inspection only; current M3 reports are historical prerequisites, not fresh v2 evidence. No runtime, test, provider, security, browser, restart, cancellation, live model or deployed check was performed here.
- **Assumptions and impact:** private service binding, existing operator transport and one shared budget owner remain available. If false, stop at that boundary and return an evidence-backed alternative; do not expose a public route or reset counters.
- **Unresolved decisions:** independent reviewers must confirm the additive state boundary, one-write publication, strict non-exact refusal, shared budgets and server-derived session routing. UX-v2 already reconciles visible state names; security must review candidate/evidence/model handling.
- **Residual risks:** deployed DO lifetime/restart, free model availability, semantic SQL correctness, cookie-based identity and browser evidence remain explicit above.
- **Actual external-action state:** no branch, code, PR, commit, provider review/approval, merge or deployment occurred in this authoring slice.

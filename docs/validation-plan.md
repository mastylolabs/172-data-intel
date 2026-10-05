# Validation plan

Artifact: VALIDATION-v1. Original planning research: 2026-10-04. **Proposed; all application checks unrun.**
Traces BR-03–BR-09/BR-13/BR-14 and AC-07/09–AC-14 in [BRIEF-v1](engineering-brief.md).
This is a test design. No application, small/large dataset run, model evaluation,
Cloudflare integration test, load test or fault-injection evidence exists in this repository.
Documentation checks alone cannot establish a product PASS.

## Active MVP acceptance

The active scope is two synthetic datasets, model-generated SQL through a general
query engine, targeted support search, native Cloudflare Agent chat, durable
memory, evidence inspection, and independent validation. Fixtures, evaluators,
and tests below are planned, not imported test results. Workers AI with Llama 3.3
is the specified MVP model baseline; runtime compatibility and model behavior
remain unverified until tested. Use isolated anonymous sessions over bundled
synthetic datasets. Authenticated private workspaces, login, OAuth, and enterprise
tenancy are future work; session isolation, protected secrets, safe SQL, and
per-session/global resource limits remain MVP acceptance requirements.

| Acceptance need | Proposed evidence |
| --- | --- |
| Generated SQL and query flexibility | Sales questions with novel supported filters, groups, rankings, and time comparisons; inspect actual model SQL and compare exact results with independent oracles. A fixed list of named sales operations does not satisfy this requirement. |
| Safe general engine | Reject mutation, unauthorized tables/files/network/extensions/functions, malformed SQL, oversized results, and resource exhaustion. Verify engine-level restrictions and typed boundaries, not just model instructions. |
| Anonymous-session safety and limits | Two independent anonymous sessions share bundled read-only fixtures but cannot access each other's history, jobs, memory, or evidence; server secrets stay out of models/logs/artifacts; per-session and global query/model limits refuse excess work. |
| Targeted support evidence | Independent relevance/quote/ID/time-filter expectations; empty search is a search miss, not population absence; broad prevalence requests are refused or narrowed. |
| Native Agent and durable memory | Real Agent/Python contract parity; source/history/accepted-answer/evidence references survive refresh and restart; follow-up intent stays bounded; conversations stay separated; memory does not imply in-flight job resumption. |
| Independent validation and publication | Mutate amounts, units, dates, meaning, citations, and coverage claims; deterministic checks plus separate Workers AI/Llama 3.3 Validator context/audit capabilities reject or abstain; failed/stale candidates never publish. |
| Public reproduction and quality | Clean public clone with synthetic fixtures and offline model doubles; canonical gate and applicable adapter/UI checks; real model and authorized deployed tests reported separately from mocks. |

Future cases below retain valuable test reasoning for PostgreSQL, Parquet, uploads,
exhaustive classification, Workflows, Containers, and scale. They do not expand MVP
acceptance. Case tables label future-only cases and mixed cases explicitly.

## Evidence levels and acceptance ownership

1. Python unit/contract tests use pytest and independent expected values. They
   establish local analytical and boundary behavior.
2. Local MVP integration runs exercise synthetic CSV/JSONL, the general SQL engine,
   durable memory, and platform emulation where supported. Future runs add
   PostgreSQL and long-job ledgers. Mock external models/network/time where
   required; do not mock pure analytical functions.
3. Later authorized Cloudflare MVP tests exercise native Agent/Python bindings,
   durable memory and publication; future tests add Workflow replay/Container shutdown.
   Local emulation is not target-runtime evidence. No deployment is authorized by this plan.
4. Model evaluation uses labeled held-out corpora, malicious content and mutations,
   with deterministic arithmetic checks alongside independent semantic judgment.
5. Scale tests measure real scanned/output bytes, memory, tokens, elapsed time,
   queueing, errors and cost under a fixed workload. Report the observed envelope,
   rather than inferring terabyte support from a small run.

Human DEC-03/04/05 approves workload, semantic-quality thresholds, total spend,
latency/concurrency targets and privacy/retention policy before dependent tests.
The correctness invariants below are proposed pass conditions derived from the
user's evidence-first requirement, not claims that tests have already passed.

## Reproducible data tiers

| Tier / inputs | Why it is representative | Proposed scale and limits | Oracle/evidence |
| --- | --- | --- | --- |
| S: MVP synthetic sales CSV | Manually inspectable net sales, time windows and declared row grain | 1,000 records plus deliberately malformed/empty variants; actual bytes recorded | Hand-calculated golden cases, Decimal monetary totals, independently authored SQL expectations |
| S-text: MVP synthetic support JSONL | Manually reviewed targeted relevance and source citations; exhaustive-theme labels are future variants | 200 messages with rare themes, unknowns, multi-label cases, long threads and malicious instructions | Separate evaluator label file and human audit; labels withheld from agents |
| M: future generated structured corpus | Deterministic keys/distributions and controllable source changes | 1 million rows, CSV and Parquet forms, loaded into local PostgreSQL; measure compressed and scanned bytes separately | Generator-version/seed manifest plus independent streaming reference totals; no shared analytical implementation with system under test |
| M-text: future bounded broad corpus | Tests future exhaustive coverage and model budgets | 10,000 messages, balanced/skewed/rare variants; token-aware partitions with deliberately oversized messages | Exact eligible-ID set and reference mechanical aggregation; independently assessed model labels |
| L: future realistic public file workload | Real schema, distributions, bad records and remote reads | Pinned TLC month, then additional months until measured workload is around 20 GB; this is a test input, not an MVP service promise | Download/lookup hashes, dictionary version, independent approved reference queries and explicit cleaning policy |
| XL: future execution-adapter workload | Tests stable control contracts under genuinely large source execution | 100 GB, then 2 TB of generated partitioned Parquet or source-side tables, only after cost approval and L evidence | Independent source-engine totals and immutable manifest; executor chosen for actual resource envelope |
| O: future load/permission extension | Control-plane limits can fail even with tiny data | Proposed 1, 10 and 50 simultaneous jobs; two isolated tenants; slow provider/source and disconnected clients | Correlated trace, admission decisions, complete outcome ledger, tenant-negative probes |

Tier sizes are illustrative predeclared scenarios. They must be adapted to approved
budgets before running; record actual versions, rows, physical/scanned bytes,
hardware or Cloudflare plan, settings and quotas. A replicated 2 TB file corpus
with one trivial repeated key does not establish general 2 TB join performance.
Large fixtures stay in the data plane and are optional downloads/generation,
never context attachments or Git assets.

TLC rows are not semantic ground truth. Pin inputs and compare execution against
agreed reference queries; evaluate data-quality exclusions separately. Synthetic
tests establish exactness, and realistic data tests expose operational limits.

## Correctness and coverage scenarios

**Scope labels:** MVP = applies to the active slice; Future = outside it;
MVP + future variants = use the small-fixture path now and defer larger/source-specific
extensions. Every case is an unrun specification, not a pass/fail record.

| ID | Scenario and fault | Proposed pass condition | Tier / owner | Scope |
| --- | --- | --- | --- | --- |
| V-01 | Sales time-window question with returns, zero previous sales, nulls and mixed currencies | Exact totals under approved definitions; undefined percentages explicitly marked; currencies never silently combined | S/M; Python QA | MVP |
| V-02 | Fact-to-fact join repeats invoice/usage rows; duplicate business keys straddle partitions | Grain/preaggregation prevents multiplication; declared duplicate policy enforced; equal-looking legitimate rows remain distinct when source semantics require | S/M; execution QA | Future |
| V-03 | DST transition, leap day, month end, timezone and “last 24 hours” versus calendar day | Frozen `as_of`, zone, UTC interval and half-open bounds lead to reference-matching inclusion; clarification on ambiguity | S; contract QA | MVP |
| V-04 | Weighted means, distinct counts, median, skewed top-k and null denominators across uneven partitions | Global result matches oracle; unsupported merge algebra rejected; approximate result can only appear under explicit approved policy with method/error information | S/M/L; analytical QA | MVP + future variants |
| V-05 | Randomly repartition eligible records; duplicate, omit, reorder and retry a partition | Manifest proves exact distinct-ID coverage; identical result for every valid partitioning; missing/duplicate work cannot yield complete status | S/M-text; recovery QA | Future |
| V-06 | Rare complaint only in last partition; targeted top-k misses it | MVP targeted answer reports its retrieval scope and refuses prevalence; future exhaustive mode processes the full manifest and includes qualifying rare evidence; no unsupported “none” or population prevalence claim | S-text/M-text; semantic QA | MVP + future variants |
| V-07 | Multi-label messages, bot text, thread boundaries and duplicated exports | Denominator is approved eligible-message set; count distinct `(message_id, theme)`; overlapping totals disclosed; filters/rejections recorded; thread/customer/ticket totals not inferred | S-text/M-text; semantic QA | Future |
| V-08 | Corpus contains a very long message/thread, thousands of labels/groups/columns or result rows | Per-artifact and per-model budgets enforced before serialization; bounded previews and pagination, explicit omission/truncation; cannot silently drop records from exhaustive mode | S/M/L; boundary QA | MVP + future variants |
| V-09 | Empty source, all rows malformed, no lexical matches, incomplete source pagination | Distinguish empty population, rejected input, search miss and incomplete coverage; appropriate clarification/error/abstention, no fabricated answer | S/S-text; product QA | MVP |
| V-10 | Analyst produces correct arithmetic with wrong business meaning or unsupported causal inference | Validator rejects semantic mismatch/causal overreach or requires approved clarification; exact execution alone cannot PASS the answer | S; independent Validator evaluation | MVP |

For future whole-corpus analysis, a classifier is judged separately from the reducer. The reducer must count
its committed labels exactly; classification accuracy, rare-class recall and
unknown rate are measured against held-out human labels. Approve per-class
thresholds before evaluating model behavior; MVP calls use Workers AI with Llama 3.3; never tune them after seeing a result.
Deterministic mock-model fixtures prove plumbing only. They do not prove semantic
quality. Preserve human disagreement and uncertainty instead of forcing clean labels.

## Provenance and independent verification

| ID | Scenario | Proposed pass condition | Scope |
| --- | --- | --- | --- |
| V-11 | Alter a claim amount, date, denominator, citation or unit in an otherwise valid answer | Deterministic verification or independent Validator fails each material mutation; claim IDs map to actual committed results and immutable source scope | MVP |
| V-12 | Replace evidence body while keeping its locator; attempt source update after analysis | Hash/revision check detects replacement; source version is visible; retained evidence supports replay or reports expiration explicitly | MVP |
| V-13 | Validator receives only Analyst prose or a capped preview for a full-table total | Insufficient-evidence status; validator requests a bounded audit query/receipt instead of accepting the preview as proof | MVP |
| V-14 | Analyst and Validator use Workers AI with Llama 3.3 in separate contexts and agree on a false statement | Test shows correlated-error exposure; independent prompts/context plus deterministic invariants and adversarial corpus decide acceptance, not agreement alone | MVP |
| V-15 | Replay a validated job later with identical approved plan/data/semantic versions | Deterministic numeric artifacts reproduce; retained model output is auditable. New model calls need not reproduce identical prose and must not be described as deterministic replay | MVP |
| V-16 | Query result exceeds preview budget; one claim needs evidence omitted from the summary | Evidence retrieval remains bounded and permission-checked; insufficient support blocks that claim; neither raw result nor entire lineage is pushed into context | MVP |

For exact numeric claims, a useful evidence package includes source/snapshot scope,
query/operator version, normalized parameters, grain, eligible counts, rejection
counts, result schema, exact aggregate artifacts/hashes, and a reproducible audit
operation. A few sampled rows support illustration, not proof of a population sum.
For text claims, keep canonical record IDs, quoted spans, label/taxonomy versions,
coverage and unknown counts, with model-derived meaning identified as such.

## Recovery, idempotency and cancellation

| ID | Injection point | Proposed pass condition | Scope |
| --- | --- | --- | --- |
| V-17 | Container/worker dies before result write, after immutable write but before ledger commit, or after commit before ack | Retry with the same work identity accepts at most one canonical completion; no duplicate aggregation; uncommitted objects can be safely reconciled/collected | MVP + future variants |
| V-18 | Technical timeout after successful external operation; duplicate/out-of-order completion | Stored result reused where possible; generation/plan/source/work key verified; late completion cannot overwrite a newer attempt or terminal outcome | MVP |
| V-19 | Partition 73 fails after 1–72 commit | Only unfinished work is scheduled again; committed partitions reused; coverage checked before reduction; no restart of complete corpus work | Future |
| V-20 | Network/model 429/5xx versus invalid schema, denied permission or insufficient evidence | Only transient errors use technical retry; analytical replan creates a new plan revision; permanent/security failures stop appropriately; persisted counters/deadline prevent budget reset | MVP |
| V-21 | Cancellation during model request, source query, Container process, result commit or Workflow wait | Stop new work; mark/fence cancellation durably; signal/abort remote operations where supported; suppress late answer publication; report actual cost of work that could not be aborted | MVP + future variants |
| V-22 | Process spawns children; request abort/retry does not kill execution | Explicit process-group/container shutdown or executor-native cancellation stops owned work; repeated exec cannot start uncontrolled duplicates. HTTP abort alone is not treated as successful cancel | Future |
| V-23 | Chat refresh/disconnect, Agent restart and reconnect; future Workflow replay | Selected source, ordered history, accepted plan/answer/evidence references persist; bounded follow-ups preserve user intent; isolated anonymous sessions over bundled fixtures cannot read each other's history/jobs/evidence; interrupted-job outcome follows contract; terminal evidence comes from accepted artifacts, not memory-generated facts. Future replay notifications are deduplicated | MVP |
| V-24 | Workflow retention expires, operator retries old run, or live PostgreSQL snapshot is lost | Durable job/provenance policy survives platform retention or shows explicit expiry; stale run cannot reuse old idempotency scope incorrectly; new source view creates a new analysis version | Future |
| V-25 | Human clarification arrives twice, late or after cancellation | Authorized response tied to job/version/question; duplicate event harmless; stale response rejected; timeout/escalation path preserves history | MVP |

Cloudflare documents retried steps and
[at-least-once Queue delivery](https://developers.cloudflare.com/queues/reference/delivery-guarantees/).
These tests establish application semantics across those services; they do not
assume an exactly-once transport guarantee. Later target tests must also verify
Python step serialization/replay and supported cancellation APIs at pinned versions.

## Source evolution and security

| ID | Scenario | Proposed pass condition | Scope |
| --- | --- | --- | --- |
| V-26 | Add/rename/drop a column; units/currency/meaning change without schema change | Source/schema/semantic versions checked; incompatible plans invalidated; no stale approved definition silently applied; compact explicit clarification | MVP + future variants |
| V-27 | Data update between profile, query and audit; read replica lag/cache returns old values | Single-source snapshot/freshness contract honored or limitation shown; counts/results from incompatible revisions cannot be merged; cache scope/freshness policy tested | Future |
| V-28 | Anonymous session B guesses session A history/job/evidence IDs or routes; future variants add tenant ACL revocation | Deny cross-session history/job/evidence/status access; session scope is server-owned; bundled fixtures are shared read-only; recheck session ownership at access/publication. Future private-workspace variants add authenticated tenant/ACL checks | MVP + future variants |
| V-29 | Session-owned history/evidence leaks through logs or a shared cache; future private-source variants include restricted rows in profiles/search/aggregates | Session-owned derivatives and caches stay scoped to the anonymous session; no conversation/evidence leak. Future restricted-source variants enforce tenant/row permissions before derivatives | MVP + future variants |
| V-30 | Source text says “ignore rules,” requests a secret, tool call or outbound URL | Source content remains data; tools and policy cannot be modified by it; secrets absent from prompts/logs/artifacts; no unapproved egress or source write | MVP |
| V-31 | SELECT invokes dangerous file/network functions, extension load, expensive UDF or mutation side effect | Generated SQL is parsed/validated against dialect, authorized tables/functions, and read-only policy; unsupported operations rejected; executor least-privilege identity and resource/egress policy enforce defense in depth; negative write tests prove actual source permissions | MVP |
| V-32 | SQL service is read-only but token can write/delete source/catalog objects | Credential capabilities independently verified; forbidden storage/catalog operations fail; do not infer least privilege from SQL syntax restrictions | Future |
| V-33 | Malformed upload, path traversal, decompression expansion, huge field, arbitrary source URL or redirect | Typed byte/format limits and approved locations enforced before parsing; SSRF/private address/path probes fail; parser failure preserves safe error without secret or payload exposure | Future |
| V-34 | Retention/deletion clears data but leaves index, sample, evidence or cached answer | Approved dependency-aware deletion/expiry applied to all derivatives; citations show unavailable evidence; lifecycle delay not represented as immediate erasure | MVP + future variants |

Use at least two independent anonymous sessions over the same bundled fixtures in
MVP isolation tests. Verify state/evidence separation, denied guessed identifiers,
protected server secrets, safe SQL, and per-session/global resource refusals.
Login, authenticated private workspaces, OAuth, enterprise tenancy, and private
source row/ACL controls are future tests, not MVP prerequisites. Workers AI with
Llama 3.3 is specified; session-text handling/retention remain DEC-05 policy details.
Cloudflare operator account authorization is separate from anonymous demo sessions.

## Scale, backpressure and cost experiments

| ID | Experiment | Measurements and decision condition | Scope |
| --- | --- | --- | --- |
| V-35 | Same query shape over S/M/L/XL inputs with greater rows and metadata cardinality | Per-call tokens/bytes remain within approved bounds; planner receives no raw scans/manifests; report cumulative model cost, CPU, memory, bytes scanned and artifact growth. No claim that total work is constant | MVP + future variants |
| V-36 | Selective Parquet filter versus full scan; source-side PostgreSQL versus exported rows; later Basin SQL comparison | Capture EXPLAIN and actual remote requests/scanned bytes, CPU/spill, latency and billed units; verify identical approved results. Pruning/near-data gains must be measured, not inferred from deployment names | Future |
| V-37 | High-cardinality grouping, global distinct/median and multi-way joins | Executor either satisfies exact oracle within resources or rejects/returns budget status safely; no silent approximation or partial top-k. Record failure envelope as a useful result | MVP + future variants |
| V-38 | Burst of 1/10/50 jobs; one slow source/provider and one noisy tenant | Bounded admission, per-tenant/source/provider concurrency and fairness; queue age observable; work cannot overwhelm source connections or bypass token/spend caps. Approve latency and wait thresholds before run | Future |
| V-39 | Storage retained for successive workloads, repeated retries and orphaned uploads | Measure bytes per job, object counts, scans/GETs and cleanup lag; retention cannot delete evidence needed by live jobs; migration/recovery plan identifies growth triggers | MVP + future variants |
| V-40 | Interruptions and analytical correction loops under fixed total budget | Preflight reservations plus actual accounting stop work before approved cap where controllable; uncertain provider bill explicitly tracked; retry/replan does not permit unlimited spend | MVP |
| V-41 | Cold/warm executor, large output, many schemas and event fan-out | Record p50/p95, time to first status, completion and validation time, resource errors and reconnect behavior; no UI “completed” before validation; use values to propose the service envelope | MVP + future variants |

A successful 20 GB test only supports the tested query/data/runtime combination.
A 2 TB adapter test establishes bounded-agent compatibility for that workload,
not unlimited Cloudflare compute or arbitrary corpus-classification economics.
Source-side workloads may be slower or more expensive outside Cloudflare; account
for source-host egress, source CPU and network distance. R2 free egress does not
make reads, queries, model calls or storage free.

## Dated platform support versus assumptions

| Capability | Evidence today | Assumption / test needed |
| --- | --- | --- |
| Python Worker, DO and Workflow entrypoints | Original research records documented support; see [research ledger](research-sources.md) and [mapping](cloudflare-mapping.md) | Selected Python/package versions, FFI, serialization, schema parity and cross-service calls: postapproval spike |
| Durable interaction and future background work | Original research records Agents/DO/Workflows support | Reconnect and exact ownership/recovery: V-17–V-25 |
| Streaming and model/tool integration | Documented APIs | Validation-before-publication, token budgets and unverified Workers AI/Llama 3.3 behavior: V-06–V-16/V-35 |
| R2 objects, source-side SQL and finite compute | Documented services and database semantics | End-to-end snapshots, pruning, cost and large operations: V-26/27/V-35–V-41 |
| Independent Validator | Proposed architectural responsibility | Actual claim sufficiency and rejection behavior: V-10–V-16; second model agreement alone insufficient |
| Stable contracts from MB to TB | Architectural intent | Exact adapter parity and measured envelopes; S/M/L/XL; entirely untested |

## Required reports and quality gate

Each later test report identifies source/plan/semantic/model/tool versions,
fixture seed/hash, environment and account plan, approved threshold, observations,
failures, pass/fail/unverified disposition, logs/artifact references and limits.
Independent QA must not approve its own implementation. Model evaluation stores
safe inputs/outputs and reasoning summaries where useful; hidden chain of thought
is unnecessary for reproducibility or provenance.

The canonical engineering gate remains exactly the AGENTS.md gate:

```sh
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
uv run radon cc src tests -s -a
```

`make gate` must run all checks and enforce Radon A/B function and average
thresholds (C or worse needs refactoring or the documented function exception).
CI uses the same acceptance standard; any additional TypeScript adapter checks
extend it. Missing tools/configuration are blockers. The present planning-only
repository has no gate target or code to validate; this plan does not claim a pass.

Within an approved milestone, each PR also needs independent QA and configured
provider bot approval on the current head, resolved required findings, and guarded
merge under AGENTS.md. Keep the hard 400-line handwritten-code limit. After
milestone acceptance and merged PR verification, report actual unit coverage,
test counts/results/gaps, integration/deployed outcomes, failed/unrun checks and
reasons, merged PR links, main revision, problems and the next proposed milestone
under `docs/milestones/`. Present the report and pause before the next milestone.
Deployment needs separate authorization. No previous-build approval or check
result is carried into this plan.

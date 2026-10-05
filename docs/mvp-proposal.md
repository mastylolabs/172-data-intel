# MVP proposal

Artifact: MVP-v1. Original planning research: 2026-10-04. **Proposed; not implemented.**
Active direction for `172x-data-intel`: two synthetic datasets, a native Cloudflare
Agent, model-generated SQL through a general query engine, targeted support search,
durable memory, chat, evidence, and independent validation, using Workers AI with
Llama 3.3 and isolated anonymous sessions over bundled synthetic datasets. Traces BR-01–BR-10 and
AC-05/09–AC-13 in the [engineering brief](engineering-brief.md).

## Recommended product slice

An anonymous user selects a bundled synthetic source, asks a question in chat, sees progress, and receives
a validated answer with inspectable evidence, source scope, calculation details, and
limitations. Conversation history and selected-source state persist across refresh;
follow-ups use bounded memory and retain references to accepted plans and evidence.
Durable memory must not be treated as proof that an interrupted analysis can resume.
Server-owned session scope isolates history, memory, jobs, and evidence. The fixtures
are shared read-only data; no login, private workspace, uploads, or OAuth is needed
for the demonstration. Runtime compatibility and Llama 3.3 structured-output/tool/
analytical/validation behavior remain unverified until tested.

Preserve five logical responsibilities: deterministic Orchestrator, deterministic
Profiler, conditional Semantic reasoning, Analyst, and an independent Validator.
They need not be separate services. Infrastructure validates and executes tools;
the Analyst proposes queries and explanations. Ask for clarification when grain,
units, business meaning, or time windows are ambiguous. Refuse unsupported claims.

## Two synthetic datasets

Effort estimates are relative after shared contracts exist, not delivery promises.
Fixtures and generators are planned; none are present in this repository.

| Dataset | Value and example question | Proposed sample | Effort and dependencies | Validation |
| --- | --- | --- | --- | --- |
| Synthetic sales CSV | Demonstrates flexible structured analysis. “Which products increased net revenue between two months?” | Public deterministic generator with stable row IDs, dates, products, regions, quantities, prices, returns, and documented currency/null rules | Medium: typed parsing, profiling, a general SQL engine, generated-query validation, bounded execution, and query/result provenance. Engine and runtime selection require a compatibility spike. | Independently calculated totals; novel filters/groupings/time comparisons; malformed and empty inputs; duplicate/grain traps; unsafe SQL and resource refusals; exact source/query/result traceability |
| Synthetic support-message JSONL | Demonstrates targeted unstructured evidence. “Find reports of login failures yesterday.” | Stable message/thread IDs, UTC timestamps, channels, text, and separate evaluator labels; include paraphrases, rare issues, long threads, duplicates, unknowns, and malicious instructions | Medium: typed import, bounded lexical search, time/source filters, record citations, and relevance evaluation. No live Slack account, embedding service, or taxonomy classifier is needed initially. | Independent relevance expectations; exact quote/ID resolution; date bounds; search misses versus source absence; unsupported prevalence claims; prompt injection; malformed/oversized records |

Keep evaluator labels out of Analyst inputs. Publish generator versions, seeds,
fixture hashes, semantics, and sample license. Models receive compact profiles and
bounded evidence; source rows and full result sets stay in the execution layer.

## Structured analysis contract

The Analyst generates SQL against the declared sales schema for a general query
engine. Filtering, grouping, aggregation, ranking, and time-window comparisons are
query capabilities, rather than a fixed collection of named sales answers.
Deterministic infrastructure checks dialect, tables, functions, read-only behavior,
source access, and resource budgets before execution. Record the actual SQL, source
version, engine version, result schema, and evidence references for validation.

General SQL does not mean arbitrary filesystem, network, extension, or code access.
[DuckDB security](https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview)
explains why read-only-looking SQL alone is insufficient isolation. DuckDB is a
candidate in a compatible CPython runtime; another public engine may be selected
after measured runtime fit. Do not assume a native analytical wheel works in Pyodide.

Structured calculations must be exact under agreed grain, null, sign, currency,
timezone, and source semantics. Reject unsupported operations or excessive work;
never silently substitute an approximation. Global distinct/median/ranking must
use valid engine semantics, not sums of partial distinct counts or means of means.

## Needed now and future work

| Capability | Proposed MVP | Future work and reason |
| --- | --- | --- |
| Chat and memory | Native Cloudflare Agent, source selection, progress, clarification, durable history, refresh/follow-ups, evidence inspection, safe failure states | Rich dashboards, notebooks, voice, and independently deployed reasoning services add scope |
| Data and tools | Synthetic sales CSV through model-generated SQL; synthetic support JSONL through targeted search; typed public expansion boundaries | PostgreSQL, Parquet, uploads, live connectors, OAuth, cross-source federation, and arbitrary transforms need separate contracts |
| Evidence and validation | Immutable fixture scope, query/search receipts, claim citations, deterministic checks, separate Validator context and bounded read-only audit tools | A universal provenance graph UI and broad model-quality guarantees require additional evidence |
| Durability | Persisted conversation/source/accepted-answer references; explicit job identity, retry/replan budgets, cancellation and stale-publication policy | Long-running Workflow recovery, partition scheduling, Containers, and distributed execution only when workloads need them |
| Retrieval | Bounded lexical/metadata targeted search, explicit retrieval scope; no whole-corpus prevalence or absence claims | Full-corpus classification needs canonical coverage, counting units, taxonomy/unknown policy, independent semantic evaluation, and total-budget approval; vector search needs measured gains |
| Security and operations | Isolated anonymous sessions over bundled synthetic fixtures; protected secrets, safe query execution, untrusted-content controls, per-session/global cost/context limits, public offline tests | Authenticated private workspaces, login, OAuth, enterprise tenancy/SSO, sensitive uploads, CDC, and large-scale certification need separate review |

The earlier PostgreSQL option remains useful for source-side execution, consistent
transactions, relationship/grain tests, read-only permissions, and changing data.
Its future synthetic account/usage/invoice/credit generator would allow independent
join and snapshot oracles. [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
does not make a transaction snapshot survive a process restart automatically.

Parquet and optional [NYC TLC data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
remain future realistic scan workloads. TLC disclaims accuracy: use pinned objects,
dictionary versions, acquisition dates, hashes, explicit cleaning rules, and checked
redistribution terms. Synthetic data supplies correctness oracles; TLC supplies
operational stress. Large downloads stay outside Git.

## Candidate operating envelope

These settings are unmeasured experiment candidates, not capacity commitments.
Resolve DEC-03 before implementation and record actual token/byte counts.

| Boundary | Candidate | Boundary behavior |
| --- | --- | --- |
| One model invocation | 16,000 input tokens including instructions/history/tools/evidence; 4,000 output tokens | Narrow metadata or evidence, ask to narrow, or refuse overflow |
| Profile/semantic projection | 64 KiB each, with full artifacts stored separately | Select/paginate fields and expose omitted or sampled metadata |
| Result preview | At most 50 rows and 32 KiB, whichever is first | Full result remains referenced; show truncation explicitly |
| Evidence per call | At most 10 excerpts and 32 KiB, within total token cap | Bounded follow-up reads; excerpts cannot prove prevalence |
| Analytical correction | Initial plan plus at most two revisions | Preserve attempts; clarify or stop when exhausted |
| Transient retries | At most three retries after the first attempt, also bounded by total deadline/spend | Persist failure class and counters; retries cannot reset budgets |

No file-size, latency, spend, or concurrency promise is established. A future broad
text experiment could use up to 10,000 messages and 200 token-aware partitions;
this is outside the active MVP and requires separate coverage/quality/budget decisions.

## Dependencies and acceptance

Use Workers AI with Llama 3.3 for the MVP model calls, including separate Analyst
and Validator contexts; the shared baseline does not eliminate correlated errors.
Use Python >=3.12, uv, and small public dependencies with clear purposes. Pydantic
is a boundary-validation candidate; an analytical engine needs demonstrated runtime
compatibility. A minimal TypeScript adapter may expose the native Agents SDK, while
Python retains analytical logic and deterministic validation. Native
[Python Workflows](https://developers.cloudflare.com/workflows/python/) remain an
extension option. Do not add pandas, Spark, Trino, Kafka, or a vector stack without
a measured requirement. Public local tests must need no private 172X services.

Acceptance requires both dataset journeys, generated-query flexibility, durable
memory/refresh/follow-ups, anonymous-session isolation, protected secrets, resource
limits, evidence inspection, unsafe-input refusal, and independent
validation. See the [validation plan](validation-plan.md), [runtime mapping](cloudflare-mapping.md),
and [delivery plan](implementation-plan.md). All application acceptance remains unverified;
this proposal records no implementation, test pass, or deployment authorization.

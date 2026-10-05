# Research evidence ledger

Artifact: RESEARCH-v1. Original documentation research date: 2026-10-04.
The retained sources describe documented platform support at that research date;
this cleanup does not claim a fresh inspection or application experiment. Recheck
limits, package support, pricing, and account quotas before implementation/deployment.
Documentation does not establish this application's correctness, capacity, cost,
compatibility, or recovery behavior.

## Repository and scope

Repository: `172x-data-intel`, `/Users/zbigniew/dev/code/172x-data-intel`.
It contains [engineering guidance](../AGENTS.md), the unchanged
[original architecture](architecture.md), [original prompt history](../PROMPTS.md),
and planning documents. No application, fixtures, tests, pyproject.toml, uv.lock,
Makefile, or runtime/deployment evidence is present. The bootstrap's historical
path is preserved in PROMPTS.md; current document paths refer to this repository.

The active [MVP proposal](mvp-proposal.md) uses synthetic sales CSV and support JSONL,
model-generated SQL in a general query engine, targeted search, a native Agent,
durable memory, chat, evidence, and independent validation. Workers AI with Llama 3.3
is the specified MVP model baseline; the demo uses isolated anonymous sessions over
bundled synthetic fixtures. Runtime compatibility and model behavior remain
unverified until tested. Authenticated private workspaces, login, OAuth, enterprise
tenancy, PostgreSQL, Parquet/TLC,
full-corpus analysis, and larger Cloudflare execution services below are future options.

## Official platform evidence

| ID | Source | What it establishes | What it leaves unproven |
| --- | --- | --- | --- |
| CF-01 | [Agents product site](https://agents.cloudflare.com/), [Agents documentation](https://developers.cloudflare.com/agents/) | Native durable agent runtime and ecosystem | Application scalability and analytical accuracy |
| CF-02 | [Chat agents](https://developers.cloudflare.com/agents/communication-channels/chat/chat-agents/) | JavaScript/TypeScript SDK examples, persistent chat and streaming | Native Python use of the Agents npm SDK; safe validation-before-publication integration |
| CF-03 | [Agents with Workflows](https://developers.cloudflare.com/agents/concepts/workflows/) | Explicit durable background workflow integration | Python parity of the `AgentWorkflow` JavaScript helper |
| CF-04 | [Fibers](https://developers.cloudflare.com/agents/runtime/execution/durable-execution/) | Recovery metadata, snapshots and application recovery hooks | Exactly-once effects or automatic recovery of arbitrary application work |
| CF-05 | [Python Workers](https://developers.cloudflare.com/workers/languages/python/), [runtime implementation](https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/), [packages](https://developers.cloudflare.com/workers/languages/python/packages/) | Python via Pyodide/WebAssembly; uv-based tooling; supported package classes | Ordinary native Linux wheels, analytical-engine imports and full-runtime parity |
| CF-06 | [Python Workflows](https://developers.cloudflare.com/workflows/python/), [Python step API](https://developers.cloudflare.com/workflows/python/python-workers-api/) | Python entrypoints and steps; required compatibility flags | Selected dependency versions and cross-runtime JSON contracts |
| CF-07 | [Workers limits](https://developers.cloudflare.com/workers/platform/limits/) | 128 MB isolate memory; CPU and connection-lifecycle restrictions | Safe concurrency for this workload; durability of disconnected request work |
| CF-08 | [Workflow limits](https://developers.cloudflare.com/workflows/reference/limits/) | Bounded steps, state, payloads, creation rate and active concurrency | Unlimited partitions, latency guarantees or long-term evidence retention |
| CF-09 | [Workflow rules](https://developers.cloudflare.com/workflows/build/rules-of-workflows/) | Retried effects need application idempotency | Atomic transactions across external stores and Workflow state |
| CF-10 | [Containers](https://developers.cloudflare.com/containers/), [lifecycle](https://developers.cloudflare.com/containers/concepts/architecture/), [limits](https://developers.cloudflare.com/containers/platform/limits/) | Linux compute; ephemeral disk by default; bounded instance resources | Guaranteed data colocation, unlimited local scans or persistent execution artifacts |
| CF-11 | [R2 pricing](https://developers.cloudflare.com/r2/pricing/), [object lifecycles](https://developers.cloudflare.com/r2/buckets/object-lifecycles/) | Storage/operation billing, free egress and retention automation | Free scans, immediate deletion or zero external-source egress costs |
| CF-12 | [D1 limits](https://developers.cloudflare.com/d1/platform/limits/), [Durable Object limits](https://developers.cloudflare.com/durable-objects/platform/limits/) | Finite per-database/object storage and runtime limits | Suitability as a terabyte analytical warehouse |
| CF-13 | [Queue delivery](https://developers.cloudflare.com/queues/reference/delivery-guarantees/), [Queue limits](https://developers.cloudflare.com/queues/platform/limits/) | At-least-once delivery and bounded messages/concurrency | Exactly-once partition aggregation or fair tenant scheduling |
| CF-14 | [Service bindings](https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/), [secrets](https://developers.cloudflare.com/workers/configuration/secrets/) | Native internal service access and deployment secrets | End-user authorization or source-specific least privilege |
| CF-15 | [Workers AI](https://developers.cloudflare.com/workers-ai/), [AI Gateway](https://developers.cloudflare.com/ai-gateway/) | Hosted model access and gateway services | MVP Llama 3.3 runtime compatibility, structured-output/tool/validation quality, data handling, or deterministic model replay |
| CF-16 | [Agent tracing](https://developers.cloudflare.com/agents/runtime/operations/observability/tracing/), [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/) | Platform diagnostics and tracing; custom instrumentation paths | A complete durable provenance graph or evidence retention |
| CF-17 | [Vectorize limits](https://developers.cloudflare.com/vectorize/platform/limits/), [AI Search](https://developers.cloudflare.com/ai-search/) | Native targeted retrieval options | Exhaustive corpus coverage, prevalence estimates or verified ACL behavior |
| CF-18 | [Basin Catalog](https://developers.cloudflare.com/basin-catalog/), [Basin SQL](https://developers.cloudflare.com/basin-sql/) | GA Iceberg catalog and distributed analytical SQL over R2; formerly R2 Data Catalog / R2 SQL | This project's SQL parity, cost and snapshot reproducibility |
| CF-19 | [Basin SQL constraints](https://developers.cloudflare.com/basin-sql/reference/limitations-best-practices/), [query API](https://developers.cloudflare.com/basin-sql/query-data/), [pricing](https://developers.cloudflare.com/basin-sql/platform/pricing/) | Read-only Parquet/Iceberg queries; supported SQL and resource-sensitive operations | Arbitrary file querying, unlimited joins, runtime SLA or acceptable scan cost |

CF-18/19 matter because those pages were updated October 1, 2026. Older claims
that Cloudflare has no distributed analytical query engine are stale. Native
analytics deserves a measured comparison; its availability does not require an
Iceberg ingestion stack in the two-synthetic-dataset MVP.

## Data and execution evidence

| ID | Source | Use and limitation |
| --- | --- | --- |
| DATA-01 | [NYC TLC trip records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) | Public monthly Parquet, dictionaries and taxi-zone lookup for realistic file analytics. TLC disclaims accuracy; records must not be treated as a clean ground-truth benchmark. Pin downloaded objects and document acquisition terms. |
| DATA-02 | [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | Repeatable Read provides a stable transaction view. Separate transactions after restart do not automatically reproduce the earlier view. |
| EXEC-01 | [DuckDB workload tuning](https://duckdb.org/docs/current/guides/performance/how_to_tune_workloads) | Source-side analytical option with memory/spill considerations. Larger-than-memory processing has operation-specific limits; it is not a guarantee for every query. |
| EXEC-02 | [DuckDB security](https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview) | SQL can access files, extensions and external resources. Read-only-looking generated SQL alone is not an isolation boundary. |
| EXEC-03 | [Basin Catalog DuckDB integration](https://developers.cloudflare.com/basin-catalog/config-examples/duckdb/) | A public engine/catalog integration path exists. Authentication, version parity and performance still need a spike. |

## Evidence labels used in the planning packet

- **Documented support:** cited documentation at the recorded research date exposes the capability.
- **Observed:** an explicitly identified repository or document check; never a substitute for runtime evidence.
- **Proposed:** a recommendation awaiting human approval.
- **Assumption:** a premise with an owner and a validation task.
- **Untested:** no application or target-runtime experiment was run.

Performance targets, dataset tiers and budget limits in later documents are
proposed test inputs or policy candidates. They are not achieved benchmarks.

# 172X Data Intelligence planning baseline

Repository: `172x-data-intel`, at `/Users/zbigniew/dev/code/172x-data-intel`.
This repository contains engineering guidance, prompt history, the original architecture,
and planning documents. It has no application, fixtures, test suite, runtime configuration,
or deployment evidence. The documents below describe proposals and planned validation.

[AGENTS.md](../AGENTS.md) governs engineering and delivery. [PROMPTS.md](../PROMPTS.md)
preserves the original bootstrap wording, including its historical repository path;
it is not an implementation or deployment approval record for this repository.

## Reading guide

| Document | Role and status |
| --- | --- |
| [Original architecture](architecture.md) | Unchanged architectural reference and design intent; its scale examples are aspirations, not measured support |
| [Engineering brief](engineering-brief.md) | Product requirements and planning acceptance criteria |
| [Architecture review](architecture-review.md) | Proposed refinements, technical findings, contracts, and future scale considerations |
| [MVP proposal](mvp-proposal.md) | Active proposed slice: two synthetic datasets, generated SQL, targeted search, chat, durable memory, evidence, and independent validation |
| [Cloudflare mapping](cloudflare-mapping.md) | Runtime candidates, dated platform research, constraints, cost illustrations, and unrun experiments |
| [Implementation plan](implementation-plan.md) | Proposed bounded milestones, dependencies, PR boundaries, and delivery gates |
| [Validation plan](validation-plan.md) | Unrun MVP acceptance scenarios and separately labeled future experiments |
| [Risks and questions](risks-and-questions.md) | Policy decisions, unresolved technical risks, and evidence needed |
| [Research sources](research-sources.md) | Primary citations and original research dates; recheck platform details before implementation |
| [Decision index](decisions/README.md) | ADR-0001–0008 remain proposals; each identifies its MVP and future relevance |

The research date of 2026-10-04 is retained where recorded. Editing planning text
does not establish a new research date, rerun a test, or approve a design.

## Active MVP direction

Plan a native [Cloudflare Agent](https://developers.cloudflare.com/agents/communication-channels/chat/chat-agents/)
for chat and durable conversation memory, with Python >=3.12 owning analytical
contracts, profiling, execution, and deterministic checks. The dated
[Python Workers research](https://developers.cloudflare.com/workers/languages/python/)
informs runtime selection.
A small TypeScript integration may be needed for the native Agents SDK. **Workers AI
with Llama 3.3 is the MVP model baseline.** Runtime/package compatibility, structured
output, tool behavior, and analytical/validation quality remain unverified until tested.

The demonstration uses **isolated anonymous sessions over bundled synthetic datasets**.
Server-owned session scope isolates history, jobs, memory, and evidence. Protected
secrets, safe query execution, and per-session/global resource limits remain in the
MVP; shared synthetic source files do not make conversation state shared.

Use two reproducible synthetic datasets: sales CSV and support-message JSONL.
For sales, the model generates SQL for a general query engine, with deterministic
read-only, source-access, and resource enforcement. For support, use targeted search
with record citations and explicit coverage limits. Keep bulk data in execution;
give models bounded metadata, plans, results, and evidence. Publish a supported
answer only after deterministic checks and a separate Validator invocation.

Authenticated private workspaces, login, OAuth, enterprise tenancy, PostgreSQL,
Parquet, uploads, live connectors, vector search, whole-corpus
classification, Containers, distributed execution, and large-scale benchmarks are
future work. The architectural review preserves reasoning for those extensions;
they are not prerequisites for the first demonstration.
The research also retains [Python Workflows](https://developers.cloudflare.com/workflows/python/)
and [Basin SQL](https://developers.cloudflare.com/basin-sql/) as future execution options.

## Delivery and next decisions

The [implementation plan](implementation-plan.md) follows AGENTS.md: one coherent,
independently testable change per PR; target 200–300 changed handwritten code lines;
justify 301–400; never exceed 400. Python and TypeScript, tests, scripts, and handwritten
configuration share that budget. Prose, generated files, locks, and bundled datasets
are excluded from the code budget and reviewed separately.

Within an approved milestone, each PR needs the complete applicable engineering gate,
independent QA, configured provider bot approval on the current head, resolved required
findings, and a guarded merge. Dependent work starts after prerequisite contracts are
reviewed and merged. Deployment requires separate authorization. After every milestone,
save an evidence-based report under `docs/milestones/`, present it, and pause for the
user's instruction before starting the next milestone. No milestone is complete here.

The open decisions concern runtime fit, fixture semantics, budgets, anonymous-session enforcement, model-data handling, evidence retention, licensing, and the next authorized milestone. No retained
document claims prior implementation, test success, or deployment approval.

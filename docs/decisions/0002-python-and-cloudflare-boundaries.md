# ADR-0002: Python and Cloudflare runtime boundaries

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: Native Agent/Python/query-engine fit in the MVP; Workflows, PostgreSQL, Containers, and Basin are future options.
- Traces: BR-07–BR-10/15, AC-06/12; DEC-01/03

## Context

Python is the main-language requirement. The 2026-10-04 research records support for Python
Workers, Durable Objects and Workflows, while the Agents npm SDK is demonstrated
in JavaScript/TypeScript. Pyodide is not an arbitrary Linux wheel environment.
That research also records finite Linux Containers and GA Basin SQL/Catalog as future options.

## Proposed decision

Keep Python contracts, analytical rules, control policies, execution, and validation.
Use Workers AI with Llama 3.3 as the MVP model baseline. Runtime/binding
compatibility, structured output, tool behavior, and analytical/validation quality
remain unverified until tested. Use a native Cloudflare Agent for chat and durable
memory in isolated anonymous sessions over bundled synthetic fixtures, with a minimal public
JS/TypeScript SDK adapter when needed. Verify the boundary under DEC-01. The
Analyst generates SQL for a general query engine against synthetic sales CSV;
Python validates dialect, tables/functions, read-only access, and resource limits.
Select the public engine and runtime through an actual compatibility spike,
without assuming native analytical packages work in a Python Worker.

For future long jobs, evaluate native Python Workflows where verified. Public
CPython/DuckDB compute is an option for heavier file workloads; PostgreSQL queries
can execute source-side through a verified native connection path. Compare Basin
for compatible larger Parquet/Iceberg workloads before adding a distributed platform.

Use public service bindings and versioned JSON contracts. Pin actual runtime,
compatibility dates and SDK versions; pin image digests if future executors need images. Native services are preferred
where they reduce owned runtime work; choosing the deployment adapter must not
embed Cloudflare-specific semantics into pure analytical rules.

## Alternatives and consequences

All-Python Agents integration may work but is unproven; do not certify it from DO
support alone. An all-TypeScript rewrite conflicts with the intended primary
language. A mandatory external compute cluster expands operation too early;
forcing analytics into Worker memory limits may fail. A thin adapter adds a
second toolchain but keeps Python ownership clear. Containers add cold starts and
resource billing; native lakehouse ingestion adds schema/maintenance work.

## Evidence and validation

See [Cloudflare mapping](../cloudflare-mapping.md) and its primary-source links.
Postapproval spike must prove schema/binding parity, Python version >=3.12,
selected query-engine imports, generated SQL, durable anonymous-session memory,
and Workers AI/Llama 3.3 behavior. Protected secrets, safe queries, and resource
limits remain MVP requirements; login/private workspaces/OAuth/enterprise tenancy are future work. Future experiments
add Workflow replay, source-side database access, and Container cancellation.
Measure realistic scans and intermediate memory before publishing capacity.
All runtime feasibility remains conditional.

# ADR-0008: Security and independent open-source operation

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: Isolated anonymous demo sessions, bundled synthetic datasets, protected secrets, safe queries, resource limits, and public reproduction; authenticated/private/enterprise operation is future work.
- Traces: BR-08–BR-10/13/16, AC-12/13; DEC-05/06

## Context

The planned demonstration shares bundled synthetic fixtures while conversation history,
memory, jobs, and evidence belong to individual anonymous sessions. Source text
and generated SQL remain untrusted inputs. Anonymous access does not authorize
another session's state or expose server secrets. The private 172X monorepo cannot
be a dependency of the public project.

## Proposed decision

Use isolated anonymous sessions over the bundled synthetic sales CSV and support
JSONL. Enforce server-owned session scope at every history, job, memory, evidence,
and answer boundary; model/client-selected paths cannot choose another session.
Both datasets are shared read-only fixtures. Authenticated private workspaces,
login, OAuth, and enterprise tenancy are future work.

Workers AI with Llama 3.3 is the MVP model baseline. Runtime compatibility,
structured-output/tool behavior, and analytical/validation quality remain
unverified until tested. Keep model/service secrets server-side and out of model
inputs, logs, and evidence. Define handling/retention for session text explicitly;
synthetic source data does not make user conversation text public.

Validate typed plans and generated SQL against declared schema/dialect,
read-only operations, allowed tables/functions, and execution resource limits.
Treat source content as data; enforce filesystem/network/extension restrictions
and per-session/global query/model budgets in deterministic infrastructure.
Test cross-session access denial, protected secrets, unsafe SQL, and limit refusal.

Keep code, contracts, locks, fixtures, documentation, and deployment recipes public
and repository-owned. Contributors use public Python/Node/Cloudflare tools and
their own authorized accounts; offline tests need no private services or model keys.
172X skills are optional authoring tools. Project/sample license and retention
remain explicit policies; the model baseline and anonymous-demo scope are specified.

## Alternatives and consequences

Login and private workspaces add identity, membership, and data-permission work;
defer them from the synthetic demonstration. Anonymous sessions still require
state isolation, abuse/resource limits, protected secrets, and safe execution.
Anonymous uploads, sensitive private data, OAuth, and enterprise tenancy require
separate future trust/policy review. Read-only SQL alone does not prove a credential
cannot mutate storage/catalog resources. Same-model Analyst/Validator contexts
can share blind spots and need deterministic checks and independent evaluation.

## Evidence and validation

See [DuckDB security](https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview)
and [platform mapping](../cloudflare-mapping.md). V-28–V-34 in the [validation plan](../validation-plan.md)
cover anonymous-session probes, injection, secrets, unsafe SQL, resource limits,
and derivative deletion; private ACLs, uploads, and catalog permissions are future
variants. M6 in the [implementation plan](../implementation-plan.md) requires clean
public-contributor reproduction. Test the actual session/tool trust boundaries
before a live demonstration; no security or model-behavior result is claimed.

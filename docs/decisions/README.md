# Proposed architecture decisions

Artifact: ADR-SET-v1. Original proposal date: 2026-10-04.
**ADR-0001–0008 remain proposed implementation decisions; no implementation or test
success is recorded.** Workers AI with Llama 3.3 and isolated anonymous sessions over
bundled synthetic datasets are specified MVP directions. Runtime compatibility
and model behavior remain unverified until tested.
The unchanged [original architecture](../architecture.md) is the architectural
reference. The [MVP proposal](../mvp-proposal.md) describes the active two-dataset
slice; broader recommendations remain future work. [AGENTS.md](../../AGENTS.md)
governs engineering and approved-milestone delivery.

| Record | Active proposal and future boundary | Decision link |
| --- | --- | --- |
| [ADR-0001](0001-reasoning-and-execution.md) | Separate reasoning/execution; deterministic profiling/enforcement; logical roles rather than a service per role | DEC-02/04 |
| [ADR-0002](0002-python-and-cloudflare-boundaries.md) | Native Agent, Python analytics, Workers AI/Llama 3.3, compatible general SQL engine, minimal SDK adapter; future Workflows/DB/Container/Basin options | DEC-01/03 |
| [ADR-0003](0003-bounded-versioned-contracts.md) | Typed generated-query/search/evidence contracts, bounded model projections, versioning; future work/coverage manifests | DEC-03 |
| [ADR-0004](0004-claim-evidence-and-validation.md) | Claim evidence, deterministic checks, independent Validator, gated publication | DEC-04 |
| [ADR-0005](0005-retrieval-coverage-and-aggregation.md) | Targeted support evidence now; future exhaustive coverage, classification, counting units, and reduction algebra | DEC-02/04 |
| [ADR-0006](0006-durable-job-ownership.md) | Durable memory, one job/publication authority, distinct retry/replan budgets, cancellation fences; future long-job scheduling/recovery | DEC-01/04 |
| [ADR-0007](0007-snapshots-semantics-and-freshness.md) | Immutable fixture scope and versioned semantics; future mutable-source snapshot/CDC limits | DEC-04 |
| [ADR-0008](0008-security-and-independent-operation.md) | Anonymous-session isolation, protected secrets, bundled-source/evidence access, safe SQL, resource limits, public operation; authenticated private workspaces/login/OAuth/enterprise tenancy are future work | DEC-05/06 |

DEC-01–DEC-07 are defined in the [brief](../engineering-brief.md) and
[risks register](../risks-and-questions.md). Open choices include engine/runtime fit,
fixture semantics, budgets, anonymous-session enforcement, Llama 3.3 data handling/behavior, retention, licensing, and
the next milestone. The two-synthetic-dataset direction does not accept every
broader ADR recommendation.

When a proposal is accepted, record its actual scope, authority, date, rationale,
validation dependencies, and any superseded proposal. Do not convert a previous
build's approval or implementation into a current decision. Original research and
proposal dates are preserved; they are not runtime-verification dates.

Within an approved milestone, follow the [delivery plan](../implementation-plan.md):
small coherent PRs, hard 400-line handwritten-code limit, complete checks,
independent QA, configured provider bot approval on the current head, and guarded
merge. Present a milestone report after merged implementation and acceptance,
then pause before the next milestone. Deployment requires separate authorization.

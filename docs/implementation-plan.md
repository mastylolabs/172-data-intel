# Implementation plan

Artifact: PLAN-v1. Original planning research: 2026-10-04. **Proposed; not implemented.**
Delivery baseline for `/Users/zbigniew/dev/code/172x-data-intel`; package name candidate:
`data_intel`. Uses the [brief](engineering-brief.md), [MVP proposal](mvp-proposal.md),
[architecture review](architecture-review.md), [Cloudflare mapping](cloudflare-mapping.md),
and [validation plan](validation-plan.md). No milestone has started or passed acceptance.

## Deliverables and proposed boundaries

The active deliverables are a public tooling/contract foundation, synthetic sales
analysis with model-generated SQL, targeted synthetic support search, native Agent
chat with durable memory, and claim evidence with independent validation. Use
Workers AI with Llama 3.3 as the specified MVP baseline; prove runtime compatibility
and model behavior rather than treating the selection as tested. The demonstration
uses isolated anonymous sessions over bundled synthetic datasets, with protected
secrets, safe queries, and per-session/global resource limits. Authenticated private
workspaces, login, OAuth, and enterprise tenancy are future work. Keep
PostgreSQL, Parquet, uploads, whole-corpus analysis, Containers, distributed execution,
and large-scale certification outside these milestones.

The table records coherent capabilities and candidate PR boundaries before build
work. It does not prescribe a PR count or schedule. Split a boundary further if
normal formatting would exceed the code budget, while keeping each PR useful,
testable, documented, and explicit about its dependencies.

| Milestone | Depends on | Capability and proposed PR boundaries | Acceptance evidence |
| --- | --- | --- | --- |
| M0: Scope and contract review | Planning baseline | Resolve DEC-01–DEC-06 for the two datasets; review runtime/access/budget/publication contracts, chat states, and relevant proposed ADRs; record the authorized next milestone | Agreed fixture semantics, general query-engine boundary, targeted-search limits, durable-memory versus job-recovery contract, anonymous-session isolation/enforcement, Workers AI/Llama 3.3 data handling, retention, license, and explicit acceptance targets |
| M1: Public foundation and runtime fit | M0 direction | Separate coherent changes for Python src-layout/tooling/CI; typed wire/capability contracts and negative cases; minimal native Agent-to-Python compatibility proof | Complete canonical gate and applicable adapter checks; actual runtime/package/schema parity and unverified-until-tested Workers AI/Llama 3.3 behavior; malformed/oversized input refusal; public offline setup. Target-platform execution only with separate deployment authorization. Return incompatible runtime contracts to review |
| M2: Exact synthetic sales analysis | M1 prerequisite contracts reviewed and merged | Fixture generator/semantics with independent oracles; general SQL execution with deterministic read-only/access/resource enforcement; Workers AI/Llama 3.3 planner and query/result evidence integration | Novel supported filters/groups/time comparisons produce reference-matching results; planner emits SQL rather than choosing fixed sales operations; unsafe/unsupported SQL and excessive work refuse; source/query/engine/result versions and bounds are inspectable |
| M3: Targeted synthetic support search | M1 prerequisite contracts reviewed and merged | JSONL fixture/import/profile contract; bounded lexical/time-filtered search with citations; targeted-answer integration and coverage refusal | Quote/record IDs resolve; independent relevance cases pass; malformed/oversized records and malicious instructions are handled; search misses never become whole-source absence or prevalence claims |
| M4: Claim evidence and independent validation | M2/M3 evidence contracts reviewed and merged | Claim/evidence integrity and independent audit checks; separate Validator context/tools/dispositions; publication gate and adversarial claim mutations | Correct claims supported; wrong amounts/units/time/meaning/citations fail or abstain; same-model agreement is insufficient; failed or stale validation cannot publish; model-quality evaluation is reported separately from mocked plumbing |
| M5: Native Agent chat and durable memory | M1 runtime contracts and M4 publication contract reviewed and merged | Native Agent memory/source/history persistence; chat/progress/clarification/evidence interface; bounded follow-ups and refresh/reconnect lifecycle | Both dataset journeys work; accepted answer/evidence references and selected source survive refresh; follow-ups retain intent within context limits; isolated anonymous sessions over bundled fixtures, protected secrets, per-session/global resource limits, duplicate submit, cancellation, stale completion, and interrupted-job outcome match reviewed contracts |
| M6: MVP acceptance and contributor readiness | M2–M5 merged; policy decisions resolved | Focused fixes from independent integration/security/model QA; public quickstart/configuration/license and operational guidance; measured small-fixture cost/resource report | Complete gate plus applicable TypeScript/UI checks; independent QA and bot approval on current heads; clean public clone reproduces offline demo/tests; integration and model outcomes measured honestly. Authorized deployed tests recorded, or marked unrun with reasons; no large-scale claim |

M2 and M3 are independent after shared contracts are stable, but the milestone
checkpoint still applies: do not start the next milestone without the user's
instruction. A milestone can contain several PRs. Begin dependent implementation
only after its prerequisite contracts are reviewed and merged. Architecture,
UX, threat/control, and runtime review must resolve material gaps before engineers
implement affected behavior.

## PR size, checks, and guarded delivery

[AGENTS.md](../AGENTS.md) is authoritative. Each PR has one coherent, independently
testable change with relevant tests and documentation. Target **200–300 changed
handwritten code lines**; smaller complete changes are welcome. Explain **301–400**
in the PR description. **Never exceed 400** added plus deleted handwritten lines
across source, tests, scripts, and configuration, counting Python and TypeScript
together after formatting. Generated files, dependency locks, bundled datasets,
and prose are excluded from this budget; identify and review those exclusions.

Every PR description records scope, dependencies, acceptance evidence, code-line
count, and exclusions. Run `make gate` and applicable adapter/UI checks. Independent
QA and configured provider bot review inspect the current head; changed code needs
fresh affected checks and review. Resolve required findings before delivery.

Within an approved milestone, merge each ready PR through the 172X guarded merge
process after engineering checks, independent QA, and configured bot approval pass
on the current head. Preserve branch protection and provider gates. Routine human
approval is not required per PR; an explicit user hold applies only to that PR.
172X workflows own branches, commit sequencing, push/PR/review/merge lifecycle.
Read the official Conventional Commits specification linked in AGENTS.md before
composing commits. Deployment always requires its own authorization.

## Milestone checkpoint

After acceptance checks and confirmation that the milestone's implementation PRs
have merged into `main`, save a report under `docs/milestones/`. Include delivered
behavior, merged PR links, verified main revision, problems/resolutions/limitations,
the hardest technical problem and solution rationale, measured unit coverage,
test counts/results and gaps, integration/deployed outcomes, unrun or failed checks
with reasons, and the next proposed milestone/needed decisions.

Use actual evidence; report blocked or incomplete milestones honestly. Present the
report and **pause for the user's instruction before starting the next milestone**.
Corrections use focused follow-up PRs with the same checks, QA, bot review, and
guarded merge requirements. No reports or completed milestones exist yet.

## Public foundation checklist

- `pyproject.toml` owns metadata/tool configuration: Python >=3.12, uv, Ruff,
  strict mypy, pytest, and Radon; select a verified deployed runtime version.
- Track `uv.lock` for the application and a public Node lock when the minimal
  native Agents adapter needs it. No private imports, registries, or services.
- Use `src/data_intel/`, tests outside the package, and specific modules around
  real responsibilities; avoid empty template layers.
- Makefile install/sync uses `uv sync --all-extras --dev`. Provide format, lint,
  typing, tests, complexity, and complete gate targets. CI runs the same gate
  and enforces Radon A/B acceptance; reporting exit status alone is insufficient.
- Add a public README with purpose, install, seeded quickstart, commands, gate,
  architecture, and configuration; keep TODO actionable, ignore local artifacts,
  and add placeholder `.env.example` when environment configuration is introduced.
- Validate startup configuration, keep secrets out of source/prompts/logs, and
  document offline tests plus opt-in Workers AI/Llama 3.3 and Cloudflare checks.

These are planned files and behaviors. Missing tooling on this documentation-only
baseline is not a passed engineering gate and is not a reason to expand cleanup
into application implementation.

## Version and scope discipline

Export public schemas from authoritative Python models and test cross-runtime
valid/invalid payloads. Pin compatibility dates and SDK/library versions; pin image
digests only if a later executor needs images. Record engine dialect/capabilities;
never silently translate exact operations into approximate ones.

Analytical corrections create new plan identities; technical retries reuse logical
work identities. Preserve source/schema/semantic/policy/operation versions and
test compatible additions and incompatible stored-plan rejection. Durable memory
does not authorize rerunning an interrupted job against changed semantics.

Future milestones may add PostgreSQL/Hyperdrive, Parquet/TLC stress tests, uploads,
full-corpus coverage and classification, Workflows/Containers, and measured scale.
Propose their acceptance criteria and dependencies after MVP evidence identifies
the need; they are not part of the active build proposal.

# Build brief: M1 public offline foundation

## Result and identity

- Artifact: M1-FOUNDATION-BRIEF-v1, 2026-10-04.
- Outcome: one useful public Python foundation with strict engineering checks and
  tested minimal source/query-intent contracts. Application execution is future work.
- Receivers/workflow: `principal-engineer`, then independent `qa-engineer` and
  `pr-reviewer`, through the coordinator's scoped `172X dev-loop`.
- Baseline: `main` at `a852855616bb0623ca87653c926cc88f86a7d2c5`; documentation-only.
- Authorization: the current user approves implementation and guarded merges
  within the milestone. No per-PR human gate or inspection hold is recorded.
- Depends on [MVP-DELIVERY-v1](../mvp-delivery-plan.md). Retains all original
  architecture/planning documents. This brief is not a QA or readiness verdict.

## Source and authority ledger

| Source / version | Authority and facts | Limits / disposition |
| --- | --- | --- |
| Current build prompt, recorded in [PROMPTS.md](../../PROMPTS.md) | Controlling MVP direction, staged work, small PRs, guarded merges, preview deployment authorization and milestone stop | Only M1 is activated now; later runtime/model acceptance remains unverified |
| [AGENTS.md](../../AGENTS.md), baseline above | Python >=3.12, uv/src-layout/strict typing, canonical gate, tests, enforced CI complexity, PR size and review/report rules | Workflow tools own delivery; tooling pass cannot replace independent review |
| [Original architecture](../architecture.md), baseline above | Reasoning versus deterministic execution; compact profiles; Analyst proposals, conditional semantics and independent validation | Preserve byte-identically; its scale examples are aspirations |
| [Engineering brief](../engineering-brief.md) BRIEF-v1; [implementation plan](../implementation-plan.md) PLAN-v1; [MVP proposal](../mvp-proposal.md) MVP-v1 | Named planning context, public independent operation, two sources, general generated SQL and targeted retrieval | Older documentation-only authorization and milestone order are superseded by current direction; engine, runtime and execution policies stay unverified |
| [Architecture review](../architecture-review.md) ARCH-REVIEW-v1, F-02/03/14 and F-04 | Typed compatible boundaries, payload bounds and public tooling are relevant now; deployed engine compatibility needs a separate probe | M1 addresses the relevant foundation subset, not the complete proposed contract catalog |
| Read-only reference at `/Users/zbigniew/dev/code/172x-data-intelligence`, HEAD `f91ad87a33e4f8f45d38eb092ec484d6d9164c0b`: `pyproject.toml`, `Makefile`, `scripts/check_complexity.py`, `src/data_intelligence/models.py`, `tests/test_tool_boundary.py`, `docs/mvp-review-return-receipt.json` | Inspected examples of public tooling, enforced complexity and rejection tests; receipt records provider quota failures without published candidate evidence | Reuse patterns only after fresh local verification. Named fixed sales operations contradict this MVP's generated-SQL direction and must not be copied. Receipt is recorded evidence, not independently rerun here. Prompt history was not consulted/imported |
| Coordinator activation/reviewer handoff, 2026-10-04 | Reports `agents doctor` verified Python contexts, selected `dev-loop`, and `agents github reviewer-status` verified `172x-reviewer-bot` independent identity/WRITE access for `mastylolabs/172-data-intel`; squash supported | Supplied evidence. Protection/ruleset reads returned 403; actual current-head provider approval and merge-gate state await a PR. Do not change visibility or protections |

Authority order: current explicit user direction and repository engineering rules,
then preserved architectural intent and applicable planning findings, then inspected
reference implementation. Existing planning proposals cannot enlarge M1 or certify
runtime behavior. No material conflict blocks this offline scope.

## Intent, actors and scope

The contributor starts from a documentation-only checkout. After M1 they can
install public dependencies, import `data_intel`, validate declared source/query
payloads, run meaningful unit tests and execute a reproducible complete gate.
The hiring-team chat experience is not delivered by this foundation.

In scope: `src/data_intel/`, Python >=3.12/uv metadata and tracked public lock,
Ruff/mypy/pytest/Radon configuration, Makefile, CI invoking the same gate, explicit
complexity enforcement, minimal versioned boundary models, boundary/gate tests,
measured coverage, useful README/TODO and ignores. Pydantic is supported by
AGENTS.md for external validation; avoid private runtime dependencies.

Non-goals: SQL parsing/execution, engine selection/certification, real fixtures or
profiling, search, calculation/claim validation, Python HTTP service, Worker/Agent,
LLM calls, durable state, UI or deployment. No complete plan/evidence/job schema
catalog, speculative package layers or fixed named sales-answer operations.

## Constraints and responsibility trace

| Stable ID | Constraint / outcome | Source | Owner |
| --- | --- | --- | --- |
| BR-M1-01 | Public Python >=3.12 src-layout and uv application lock; no private 172X import/service needed to install or test | User; AGENTS; F-14 | Engineer |
| BR-M1-02 | `make gate` runs every canonical check; CI calls the same gate and additionally enforces Radon function/average A/B thresholds | AGENTS | Engineer; QA |
| BR-M1-03 | Minimal typed versioned source and generic SQL-intent envelopes reject unsupported versions/sources, extra fields, malformed content and declared schema bounds | User; AGENTS; F-02/03 | Engineer; QA |
| BR-M1-04 | SQL remains an untrusted proposal; schema acceptance does not mean safe, authorized or executable SQL. No engine/dialect or runtime compatibility claim | User; F-04 | Engineer; runtime owner in M2 |
| BR-M1-05 | Document currently implemented foundation, commands/configuration and later work accurately; keep TODO actionable | AGENTS | Engineer |
| BR-M1-06 | Preserve original architecture, unrelated work and read-only reference repository/PR/deployment; exclude reference prompt history and secrets | User | Coordinator; all receivers |
| BR-M1-07 | Relevant behavioral tests, measured unit coverage and independent QA/review on current head; bounded handwritten diff and guarded merge | User; AGENTS | Engineer; QA; reviewer; coordinator |
| BR-M1-08 | Save evidence-backed milestone report after merged main verification and stop before M2 | User; AGENTS | Coordinator |

## Acceptance criteria

All criteria are **unverified** at this pre-build handoff. No blocking decision is
known for this offline scope. Criteria trace to the BR IDs above and their sources.

| ID / actor and condition | Observable result | Acceptable evidence |
| --- | --- | --- |
| AC-M1-01 — Contributor with public tools and a checkout (BR-M1-01/05) | `uv sync --all-extras --dev` succeeds from public sources; Python >=3.12 metadata, src import, application lock and documented quickstart agree | Install/import execution, metadata/lock inspection and README command exercise; no private requirement |
| AC-M1-02 — Engineer/CI invokes the gate (BR-M1-02) | Ruff format/lint, strict mypy, pytest and Radon reporting all run; complexity enforcement rejects any unapproved C+ function and C+ average; CI uses this same gate | Full `make gate` output, CI configuration/current-head result; a deliberate C+ sample fails enforcement and a conforming sample passes |
| AC-M1-03 — Caller submits a valid boundary payload (BR-M1-03/04) | Versioned source identity and generic bounded SQL-intent payload validate/serialize without a named-sales-operation API; source/schema meaning is not silently reinterpreted | Typed model inspection and behavior-oriented round-trip tests; docs explicitly state execution/safety remain unimplemented |
| AC-M1-04 — Caller submits invalid boundary input (BR-M1-03) | Unknown version/source/field, malformed identifiers/digest where declared, empty/oversized text and invalid declared limits reject clearly; correct limit edges accept | Negative and edge pytest cases, strict type/lint checks; test the documented contract rather than engine behavior |
| AC-M1-05 — QA inspects implemented Python behavior (BR-M1-07) | Meaningful success, failure and boundary tests pass; unit line/branch coverage is measured and uncovered paths are named | Test count/result and coverage report restricted to implemented package; report important gaps and exclusions. No invented percentage target |
| AC-M1-06 — Coordinator delivers M1 (BR-M1-06/07/08) | Formatted diff respects 400-line maximum; architecture/reference/unrelated work remain preserved; QA, required fixes, current-head bot approval and guarded merge pass; verified main/report identify actual evidence | Diff/count/exclusion record, independent QA/review reports, provider approval/merge receipts, main gate/coverage and milestone report. No deployment check is applicable |

Transport/schema maxima are defensive validation bounds, not measured workload,
latency or operating-budget commitments. The engineer must expose/document chosen
bounds and test both edges. M2 owners must review execution/model budgets before
using a request in the deployed chain.

## Evidence, uncertainty and risks

- **Facts:** user explicitly authorizes the staged build; AGENTS defines the gate
  and review limits. Engine/runtime success is not an offline foundation requirement.
- **Observations:** baseline contains guidance/planning documents and no Python
  application or gate. At inspection, only `PROMPTS.md` was modified; that known
  current-build log is authorized. Reference models use fixed sales operations,
  so their external contract cannot be carried over as this MVP's SQL interface.
- **Inference:** one coherent foundation can be independently verified without
  separate UX, architecture, runtime-selection or threat-model artifacts because
  it performs no external execution, persistence or publication. This inference
  applies only to M1 and does not approve later behavior.
- **Assumption:** the `data_intel` package name from PLAN-v1 is a reversible naming
  detail. Engineer validates import/document consistency; if changed, update this
  handoff before downstream implementation.
- **Decision:** coordinator selects scoped `dev-loop` and M1 before the early M2
  runtime proof; the user's checkpoint requires stopping after the M1 report.
- **Unknowns:** deployed Python engine/SDK interop (M2 feasibility owner), precise
  fixture meanings/evidence/query policy (M2/M3 owners), session/model/publication
  policy (M4 owners), UI and final deployed acceptance (M5 owners). These block
  their affected capabilities and are not assumptions used in M1.
- **Risks:** copying reference operation contracts could substitute a restricted
  answer API for generic SQL; copying runtime dependencies would overexpand M1;
  a Radon report alone would miss CI enforcement; passing schema tests could be
  mistaken for SQL safety. Engineer documents these limits; QA/reviewer verify.

## Exact first-PR handoff envelope

- **Receiver/action:** `principal-engineer` implements only this foundation.
  Provide formatted diff, criterion map, full gate/coverage evidence, code-line
  count/exclusions and bounded uncertainties to the coordinator for independent
  `qa-engineer` verification; after QA pass the same head goes to `pr-reviewer`.
- **Artifact/source versions:** this M1-FOUNDATION-BRIEF-v1 and MVP-DELIVERY-v1,
  together with the source ledger above at baseline `a852855616bb0623ca87653c926cc88f86a7d2c5`.
  All receivers get these identical artifacts, never different inferred scope.
- **Allowed change files:** `pyproject.toml`, `uv.lock`, `Makefile`, `.gitignore`,
  `.github/workflows/quality.yml`, `src/data_intel/__init__.py`,
  `src/data_intel/contracts.py`, `scripts/check_complexity.py`,
  `tests/unit/test_contracts.py`, `tests/unit/test_complexity.py`, `README.md`,
  `TODO.md`; the authorized current prompt-log change `PROMPTS.md` and these two
  new planning documents may accompany the relevant scoped PR. Generated coverage
  artifacts stay ignored. A module/test filename may be refined for clarity within
  the same scope; record it in the handoff. Do not modify original architecture or
  other planning artifacts. Original architecture SHA256:
  `2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd`.
- **PR boundary/dependency:** one public offline foundation, initially targeting
  200–300 handwritten additions plus deletions after formatting, hard maximum 400.
  No earlier implementation prerequisite. If completeness needs >400, return an
  evidenced coherent split before code delivery; do not compress or drop tests.
  Explain 301–400 scope in the PR description. Locks/prose are excluded and reviewed.
- **Acceptance state:** AC-M1-01–06 unverified; engineer supplies implementation
  evidence, QA supplies an independent criterion verdict, reviewer supplies the
  required independent review. No role self-approves its own evidence.
- **Coverage limits/assumptions:** no deployed compatibility/model/state/UI evidence;
  only reversible package-name assumption above. Public source provenance and
  fixture/runtime policy are not certified by M1 schema validation.
- **Unresolved decisions:** no M1 product conflict; execution/runtime/security/UI
  choices belong to their later owners. Coordinator resolves only a demonstrated
  PR-budget split or discrepancy with the controlling brief.
- **Residual risks:** reference mismatch, misleading safety claims, uncovered
  failure branches and ineffective complexity enforcement; QA/reviewer challenge
  these against the exact head.
- **Human/external-action state:** implementation/guarded merge authorized for M1,
  no human hold recorded. Preview deployment is authorized for later scope but
  none is permitted in this PR. This brief caused no branch, commit, push, PR,
  provider approval, merge or deployment. Preserve all provider/branch gates;
  protection-read failures do not authorize weakening or bypassing them.

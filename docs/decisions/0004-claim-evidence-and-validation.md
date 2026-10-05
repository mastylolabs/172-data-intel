# ADR-0004: Claims, evidence and independent validation

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: MVP claim evidence, separate Validator context, and validation-before-publication.
- Traces: BR-03/05/13, AC-09/13; DEC-04

## Context

The initial independent Validator is a good decision, but compact results and
prose do not prove population calculations, coverage or semantic correctness.
Two model invocations may share a false assumption. Final-answer streaming could
publish unsupported claims before validation completes.

## Proposed decision

Require material claims to bind to immutable evidence/results and defined source
scope, units, denominator, operation and semantic version. Verify arithmetic,
coverage, receipt integrity and permission with deterministic checks. Give the
Validator separate context and read-only bounded audit capabilities; it receives
the original question, frozen semantic/source scope, plan, execution/coverage
receipts, claims and sufficient evidence. Insufficient evidence causes an explicit
failure/clarification state. Keep the independent analytical challenge. The MVP
Analyst and Validator use Workers AI with Llama 3.3 in separate contexts; using the
same baseline does not eliminate correlated errors. Runtime compatibility and
claim-review behavior remain unverified until tested; alternative models are future work.

Stream progress and evidence-ready status during execution. Publish the final
answer's substantive claims only after validation; clearly report limitations and
unknowns. Preserve model/output versions and safe reasoning summaries, without
requiring hidden chain of thought.

## Alternatives and consequences

Validator agreement alone is cheap but cannot prove correctness. Recomputing every
operation doubles work; deterministic invariants and selected independent audit
queries give stronger targeted evidence. The proposal adds verification latency
and retained artifacts, in exchange for inspectable support and safer publication.

## Evidence and validation

Original §§16–18 establish the goal. [Validation plan](../validation-plan.md)
V-10–V-16 mutates claims/citations/denominators and tests inadequate evidence and
correlated model errors. Verify progress cannot expose unvalidated conclusions.
No claim of model-perfect validation is made.

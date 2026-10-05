# ADR-0003: Bounded and versioned contracts

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: MVP typed query/search/evidence boundaries and budgets; full work/coverage manifests are future extensions.
- Traces: BR-04/06/08/13, AC-10/13; DEC-03

## Context

Initial contracts contain examples rather than complete schemas or size/error
rules. A compact profile of a large table may still explode with columns,
cardinality, histories, partition lists or result groups. Row limits alone cannot
bound a long text field or a full provenance graph.

## Proposed decision

Use authoritative typed Python boundary models, public versioned JSON schemas,
and explicit producer/consumer validation. MVP envelopes use server-owned anonymous
session scope and bundled-source references; authenticated principal/workspace/
tenant grants are future extensions. Define SourceRef/ScopeSnapshot,
DataProfile, SemanticModel, AnalysisPlan, work/coverage manifests, ExecutionResult,
Claim/Evidence and ValidatorReport with version, scope, authorization, freshness,
error and provenance invariants. Store full catalogs/manifests/intermediates in the
data plane; models see selected paged projections and immutable references.

Enforce byte, token, row, excerpt, step, metadata-cardinality and cumulative-job
budgets. Record truncation/estimation/approximation; never silently drop source
records to meet a prompt limit. Approve candidate limits in MVP-v1 before use.
Accept additive compatible fields under a documented policy; reject incompatible
stored plans before execution and preserve a migration/replan path.

## Alternatives and consequences

Raw dictionaries and Markdown-only plans are simple to start but postpone safety
and compatibility failures. An elaborate universal query language adds speculative
scope. A typed general SQL tool with deterministic engine/source/access/resource constraints
and a separate targeted-search tool costs explicit schema/version work while preserving
query flexibility. Do not encode the MVP as a fixed set of sales-answer operations.

## Evidence and validation

[Architecture review](../architecture-review.md) provides the contract catalog.
V-08/16/26/35 test long fields, high-cardinality metadata, result overflow and
compatible/incompatible evolution. Record actual serialized bytes/tokens and
prove the model boundary stays within approved limits at S/M/L tiers.

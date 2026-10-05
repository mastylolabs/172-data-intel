# ADR-0005: Retrieval coverage and aggregation

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: MVP targeted support search and refusal of population claims; exhaustive classification/reduction is future work.
- Traces: BR-02/03/04/13, AC-09/10/11; DEC-02/04

## Context

The initial architecture correctly includes both targeted retrieval and partitioned
corpus analysis. It leaves partition membership, eligible denominators, counting
units and merge algebra unspecified. Top-k evidence and summaries can omit rare
themes and distort population-frequency statements.

## Proposed decision

Separate `targeted` from future `exhaustive` intent in the plan and answer. Freeze
an authorized source scope and preserve targeted query/record citations. Future
full-corpus work keeps canonical IDs and partition manifests in the data plane.
Commit one result per logical work unit and prove complete
distinct coverage before full-corpus claims. Count/merge structured outputs using
explicit valid algebra; medians/distinct counts/top-k require suitable global
operations. Do not reduce recurring themes by recursively merging prose alone.

The first support demo uses targeted search with scope-labeled citations and refuses
whole-corpus frequency or absence claims. For future exhaustive analysis, approve
a bounded taxonomy with unknown category and distinct-message-per-theme counting.
Store model-generated labels/citations and reduce mechanically. Disclose overlapping multi-label totals and semantic
uncertainty. Complete input coverage is a different property from label accuracy.
Vector/managed search is optional after measured quality improvements.

## Alternatives and consequences

Targeted search is inexpensive and useful for specific questions; it cannot certify
population coverage. Full-corpus classification costs roughly proportional to
input volume and needs a total budget. Sampling can answer some population
questions with statistical design/error bounds; both sampling and exhaustive
classification are outside the active MVP. A fixed initial taxonomy narrows discovery while improving testability.

## Evidence and validation

Original §10 supplies intent. [Validation plan](../validation-plan.md) V-04–V-09
checks invalid merge algebra, partition mutations, rare final-partition evidence,
multi-label denominators and budget overflow. Evaluate classification separately
against held-out human labels; do not certify prevalence from top-k citations.

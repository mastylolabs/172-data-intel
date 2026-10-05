# ADR-0007: Source snapshots, semantics and freshness

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: MVP immutable synthetic fixtures and versioned semantics; mutable-source transactions/CDC are future work.
- Traces: BR-03/06/13, AC-13; DEC-04

## Context

Initial provenance/semantic models express intent but do not pin source revisions,
units, grain, effective definitions or resume compatibility. A live source can
change between profile, query and audit. An open PostgreSQL transaction is not
a durable snapshot token that automatically survives process loss.

## Proposed decision

Freeze source scope, `as_of`, time interval/zone, object hashes or transaction
view, schema fingerprint, semantic-model version, definition authority and
freshness receipt for each analysis. Imported files/corpus use immutable manifests.
For a future PostgreSQL adapter, use a consistent transaction view for related operations; if
that view is lost, stop/restart under a new source version or use an explicitly
approved durable extraction. Never mix old partition results with a new live view.

Semantic suggestions remain unapproved until evidence or authorized clarification
establishes meaning. Units, currency, null/sign rules, entity grain and business
definitions have source/effective scope. Schema and semantic changes invalidate
affected profiles/plans. Preserve source deletion/expiry limitations in citations.

## Alternatives and consequences

“Latest” reads reduce storage but weaken reproducibility and can mix inconsistent
facts. Snapshot/export improves replay but increases source load, retained data
and privacy cost. CDC/lakehouse snapshots can extend this later without changing
reasoning contracts; they are not necessary for every MVP source.

## Evidence and validation

[PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
documents transaction views, not crash-proof cross-transaction replay.
V-12/15/24/26/27 test replacement, semantic changes, snapshot loss and stale caches.
Agree retention and acceptable freshness before implementing the policy.

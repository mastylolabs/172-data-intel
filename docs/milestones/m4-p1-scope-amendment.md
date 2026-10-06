# M4-ARCH-v3 delivery-only amendment: P1a/P1b sequencing

Date: 2026-10-06

This amendment changes only implementation sequencing, PR ownership, and handoff boundaries. It
does not change any M4 business requirement, acceptance condition, DTO meaning, source identity,
UX behavior, threat control, model budget, runtime topology, v1 compatibility rule, or publication
authorization rule. M4-ARCH-v2, M4-UX-v2, M4-THREAT-v2, the immutable architecture, and AGENTS.md
remain authoritative.

## M4-P1a: isolated v2 session-state foundation

P1a owns strict approved source identities, canonical UTF-8 accounting, null initial/reset source
selection, bounded server-only lifecycle/replay state, canonical cloning, exact source checks, and
an allowlisted public projection. It preserves v1 state and routes and dispatches no models, tools,
candidates, accepted answers, evidence publications, or public chat responses. The current PR uses
an explicitly internal foundation type; accepted collections remain empty until P1b.

## M4-P1b: lifecycle and private session adapter

P1b will own server-derived session routing and serialized source selection, job admission,
duplicate/conflict replay, cancellation, source switching, reset, expiry, and reconnect. It will
enforce session ownership, exact source identity, generation/cancel fences, safe errors, and no
stale publication. It may expose private session/status transport only and will not create
`AcceptedAnswerV2`, `AcceptedEvidenceV2`, or publication history.

Accepted publication, canonical evidence/memory projections, P5/P6 integration, candidate
construction, independent Validator dispatch, and atomic publication are separate dependent work.
The architecture agent approved this split; independent UX/security scope review confirmed that it
preserves the source-selection, cancellation, reconnect, and non-publication controls when these
boundaries are enforced. Neither P1a nor P1b claims model, deployed, browser, or publication
acceptance.

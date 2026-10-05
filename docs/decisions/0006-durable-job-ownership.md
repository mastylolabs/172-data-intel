# ADR-0006: Durable job ownership and effect identity

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: MVP durable memory, job identity, budgets, and publication fencing; long-job DO/Workflow/partition recovery is future work.
- Traces: BR-03/05/13/15, AC-11; DEC-01/04

## Context

Initial §§4/14/15 require checkpoint/retry/replan, but no single lifecycle owner,
effect-commit rule, cancellation fence or retry budget is defined. Cloudflare
Workflows retry steps; Queues are at least once; Container/request cancellation
does not inherently cancel all child computation.

## Proposed decision

Keep one application authority for active job/version, accepted results, budgets,
cancel generation, and publication. Python supplies deterministic policy functions;
the native Agent can wrap canonical small-job state alongside durable conversation,
source selection, and accepted-answer/evidence references. Persist bounded memory
and define explicit interrupted-job outcomes. Do not claim in-flight resumption
from chat persistence alone. The demo uses isolated anonymous sessions over bundled
synthetic fixtures; enforce session-owned history/job/evidence access and per-session/
global budgets. Authenticated private workspaces, login, OAuth, and enterprise
tenancy are future work.

For future long jobs, verify a job-scoped Python Durable Object wrapper and public
local persistence for the same logical contract. Workflow owns scheduling/step
checkpoints and references; Agent chat becomes a read projection of that authority.
R2 can own larger immutable result/evidence bytes. Do not add a second authoritative
job database or scheduler merely for convenience. The wrapper transition and
recovery semantics require separate acceptance evidence.

Logical MVP work identity includes anonymous session scope, frozen source scope,
and plan/operation version. Future partitioned execution adds partition identity;
private-workspace extensions can add tenant scope. Technical retries reuse the
logical work identity; analytical replans get a new
plan identity. Stage immutable artifacts before canonical receipt commit; only
accepted committed results contribute to aggregation. Generation/plan checks
reject stale completions. Durable cancel stops dispatch, fences publication and
requests executor-native abort; report any unabortable outstanding work honestly.

Approve separate bounded retry/replan limits plus a cumulative deadline/spend
budget; persisted counters survive restart. Retain accepted evidence under an agreed policy. Future external artifacts need
orphan reconciliation; Workflow log lifetime is not an evidence-retention contract.

## Alternatives and consequences

Workflow-only step return state is smaller but cannot by itself own external
effect identity, long-term evidence or all cancellation races. Several job stores
make recovery ambiguous. One ledger adds explicit transactional metadata work;
it supplies an inspectable owner while leaving compute/scheduling scalable by job.
The future Python DO interoperability still needs a spike.

## Evidence and validation

[Workflow idempotency rules](https://developers.cloudflare.com/workflows/build/rules-of-workflows/)
and [Queue guarantees](https://developers.cloudflare.com/queues/reference/delivery-guarantees/)
support the need for application effect identity. V-17–V-25 inject write/commit/ack
failures, duplicate callbacks, partition 73 failure, process-child cancellation,
reconnect and stale human events. No exactly-once transport guarantee is claimed.

# M4 threat and control handoff

**M4-THREAT-v2**, 2026-10-06. This scoped control artifact applies to
`M4-BRIEF-v1`, `M4-ARCH-v2`, and `M4-UX-v2`; it is a design input, not a
security certification. The original architecture remains authoritative and
the existing M2 controls remain in force.

## Control contract

The M2 `CTRL-06`/`CTRL-07` limits remain authoritative for all v1 proof paths:
12,288-byte planner input, 8,192-byte output, one model plus one query per v1
job, and the existing 12/hour session and 24/day global admissions. M4 adds a
separate v2 Validator stage with a 32,768-byte input, 4,096-byte strict JSON
output, and up to four stage calls/two tools per v2 job. This is a versioned
scope amendment, not a quota increase: v2 consumes the same durable budget
owner, cannot reset counters, and keeps no-stream/no-technical-retry behavior.
The v2 stage map is fixed: Analyst 12,288-byte input/8,192-byte output,
Semantic clarification 12,288/2,048, candidate 24,576/4,096, and Validator
32,768/4,096; max tokens are 512, 256, 512 and 512 respectively. Analyst may
have no in-job replan, Semantic is conditional once, and no stage retries;
Validator remediation is terminal and a corrected question gets a new job.
Every stage consumes the shared model admission before dispatch.

| Control | Required behavior and failure evidence | Traceability |
| --- | --- | --- |
| T-01 identity and source authority | Resolve source only from the server catalog using the complete version/hash/schema/meaning tuple. Reject forged, stale, unsupported, or client-path identities before file access. Preserve historical v1 proof receipts. | BR-M4-01/10; AC-M4-01/09 |
| T-02 untrusted inputs | Treat question, clarification text, source text, SQL and model output as data. Strictly parse every versioned DTO, reject extras/oversize bodies, and never let model output grant tool or source authority. | BR-M4-02/03; AC-M4-02/09 |
| T-03 evidence provenance | Claims and citations must point to actual bounded receipts, matching source/hash, result reference, units/scope and exact returned message text. Deterministic failures cannot be overridden by fluent model output. | BR-M4-04/05; AC-M4-03/04 |
| T-04 validator separation | Validator input includes the original question, resolved plan, receipts, claims, citations and deterministic checks. Analyst and Validator calls use separate bounded contexts and admission records; missing, malformed, failed or quota-blocked verdicts publish nothing. | BR-M4-05/06; AC-M4-04/05 |
| T-05 session and service isolation | Agent/DO state, jobs, evidence and accepted memory are keyed by server-owned session identity. Foreign IDs, client state writes, cross-session evidence and cookie/bearer forwarding to Python deny safely. | BR-M4-07/09; AC-M4-06/08/09 |
| T-06 lifecycle fences | Persist job input/source/generation/deadline before dispatch. Every awaited continuation rechecks active generation, cancellation, source and deadline; only the current owner may atomically publish. Disconnect is not success or cancellation. | BR-M4-06/07; AC-M4-05/06 |
| T-07 budgets and retries | Count every model stage, failure and uncertain timeout against per-job, session and global admission. Enforce existing 12/hour session and 24/day global caps, bounded body/context/output and no hidden SDK retries or free-quota reset claims. | BR-M4-08; AC-M4-07 |
| T-08 secrets and diagnostics | Keep credentials in bindings. Logs/errors expose only safe code, stage, correlation ID, bounded sizes/counts and revision IDs; exclude question, SQL, source text, model bodies, cookies, tokens and full evidence. | BR-M4-09/10; AC-M4-09 |
| T-09 UI disclosure | Show candidate/progress/clarification/failure separately from accepted answers. Evidence inspection is limited to authorized bounded receipts and exact citations; rejected or evicted content cannot appear as accepted history. | BR-M4-04/06/09; AC-M4-03/05/08 |
| T-10 private deployment | Keep v2 routes behind the existing private service binding, preserve v1 routes, disable public/preview routes, pin build provenance, and report local/deployed checks separately. Rollback disables only the new capability. | BR-M4-10; AC-M4-09/10 |

## Adversarial acceptance set

Independent QA must mutate each source tuple, job/session/evidence ID, hash,
unit, period, denominator, quote, validator verdict, model response, body
limit, budget counter, cancellation epoch, reset/source switch and runtime
provenance. The expected result is a typed safe refusal or replay/conflict;
there is no partial answer. Tests must include sentinel secrets and hostile
instructions in user questions and support text, foreign-session requests,
duplicate and late completions, uncertain provider timeouts, free-quota
rejections, and refresh/follow-up after accepted, rejected and evicted state.
Mocks are appropriate for routine control-flow tests; a real free-allowance
Workers AI call is required separately for deployed integration and cannot be
replaced by a mock in the final acceptance.

## Decisions and residual risks

The controls preserve the current private Python/Agent topology and additive
v2 compatibility. Cookie possession remains access to its own anonymous
synthetic session; it is not an identity or tenant guarantee. Durable Object
crash/restart, provider backup deletion and target-runtime lifetime remain
operational evidence requirements. No control supports whole-corpus claims from
targeted search, and no model PASS can repair a deterministic provenance or
arithmetic failure.

## Handoff

- **Receiver/action:** design-architecture reviewer; check this artifact with
  `docs/milestones/m4-conversation-brief.md`, `m4-conversation-architecture.md`
  and `m4-conversation-ux.md`, then return READY, REVISE or BLOCKED with exact
  pass conditions.
- **Evidence state:** controls are specified only. No code, test, provider
  approval, merge, model call or deployment is claimed.
- **Human/external action:** existing full-go authorization covers the scoped
  build; independent QA, specialist review, configured provider approval and
  guarded merge remain mandatory.

# Design-to-architecture contract matrix: M4-C0 validated conversations

## Result

`READY`

- Matrix artifact and version: `M4-C0 readiness-v6`, 2026-10-06.
- Brief: `M4-BRIEF-v1`, SHA256 `2e85ff1775ce38cb08ee675e613a2650868fb779cb6cddfeb46d36d1b5a906ec`.
- UX/UI: `M4-UX-v2`, SHA256 `e618959760c4ccf4c627a4d32b5d1eb4c3594ab758c45679ea5c857beffa1679`.
- Architecture: `M4-ARCH-v2`, SHA256 `289ddd474d0004ef3063b6c550c11fd6cb6da7065bf7319a7bc922e51bf968a5`.
- Threat/control: `M4-THREAT-v2`, SHA256 `6f9faaecfa1fbdfd5e8cced5abf2cafabe98aa5a524c05b7e52dc563812b5941`.
- Immutable architecture: SHA256 `2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd`.
- M2 runtime contracts: SHA256 `ddfb5fbb1aedae396a6434fc0c42ebf433280c548ea6b0ff6c684a800c1d3c21`.
- M2 threat controls: SHA256 `2c76d264af268cc8c169ddd16fa783b55a90b7d4c64a5db1e3b09a09753a4b5f`.
- M3 analytical contracts: SHA256 `e345ef72672cbd3e79c7271316644991d2d80bb6f3d1a29f6930a43d7392076c`.

The current bundle is ready for scoped implementation and independent QA. It
defines four v2 model calls maximum, no in-job replan, terminal Validator
remediation with a fresh request/job, and shared free-only admission. Profile
plans use `complete_profile`; profile-only Validator input carries the complete
profile receipt without a query/search receipt, while query/search plans may
carry one optional profile receipt plus one primary receipt. Accepted answers
and evidence remain available atomically through `GET /v2/session`.

This is a design-readiness verdict. It is not implementation acceptance,
provider approval, merge, deployment or live-model evidence.

## Flow-to-contract matrix

| BR/AC and user step | UX/UI behavior | Data, ownership and authorization | Failure/recovery | Design status |
| --- | --- | --- | --- | --- |
| BR-M4-01 / AC-M4-01; FLOW-1/5 source and refresh | Approved catalog labels/help, full source identity, source-labelled history | `CatalogV2`, `SourceIdentity`, `SessionStateV2`; ARCH-v2 §§159–216 | Stale/unsupported selection refuses; active switch fences old work | **READY**; implementation unverified |
| BR-M4-02/03 / AC-M4-02; FLOW-2/3 planning and clarification | Progress uses confirmed stages; profile, query, search and clarification are distinct | `AnalysisPlanV2` supports `complete_profile`; `ClarificationV2` binds response and next job | Expiry, source mismatch and foreign response fail closed | **READY**; implementation unverified |
| BR-M4-04 / AC-M4-03; FLOW-4/5 evidence | Accepted answer exposes typed claims, exact cells/quotes, counts and limitations | `CandidateAnswerV2`, `AcceptedAnswerV2`, `AcceptedEvidenceV2`, P5/P6 receipts | Unsupported or evicted evidence is refused/marked unavailable | **READY**; implementation unverified |
| BR-M4-05 / AC-M4-04; FLOW-2/4 Validator | Validation is separate from candidate and publication | `ValidatorInputV2` includes complete bounded context/receipt; independent report gates publication | Deterministic or malformed/provider failure publishes nothing | **READY**; implementation unverified |
| BR-M4-06 / AC-M4-05; FLOW-4/7 publication | Only a fenced PASS is visible in transcript/history | Atomic publication creates `AcceptedAnswerV2` and evidence projections | Stale, cancelled, expired, failed or state-limited work remains private | **READY**; fault evidence unverified |
| BR-M4-07 / AC-M4-06; FLOW-5/6 lifecycle | Refresh/reconnect shows server-owned status; cancel/source switch/reset are explicit | Job generation, cancel epoch, request journal and DO ownership | No stale commit or automatic replay; retained conflict/unavailable outcomes | **READY**; runtime unverified |
| BR-M4-08 / AC-M4-07; FLOW-2/7 budget | Budget/quota refusal gives safe server-authorized action and no billing claim | Four-stage policy uses shared `ProofBudget`, 12/hour session and 24/day global ceilings | Max+1 refuses before dispatch; failures/uncertain calls consume admission; no SDK retries or in-job replan | **READY**; runtime unverified |
| BR-M4-09 / AC-M4-08/09; FLOW-4/5/6/7 isolation | Same-source follow-up and retained evidence are inspectable; foreign/evicted content is unavailable | Server-owned state and source lineage; `GET /v2/session` returns one revision and bounded projections | Generic denial, reset/source fences and evidence-unavailable markers | **READY**; runtime/browser unverified |
| BR-M4-10 / AC-M4-10; delivery | Report includes revisions, coverage and live/deployed outcomes | Additive v2 schemas preserve v1 and use guarded delivery | Rollback disables only new capability; no local-mock claim substitutes for live evidence | **READY** for design; delivery evidence unverified |

All `AC-M4-01` through `AC-M4-10` remain unverified for implementation,
tests, browser behavior, provider use, merges and deployment.

## Activated contract compatibility

| Contract | Review result |
| --- | --- |
| Immutable architecture §§2, 4–19 | Preserved: deterministic profiler/tools, conditional Semantic role, Analyst proposal, independent Validator, provenance and bounded recovery remain distinct. |
| M2 `CTRL-06/07` | ARCH-v2 and THREAT-v2 explicitly scope the v2 amendment, preserve v1 paths, use shared `ProofBudget`, enforce four model calls maximum and keep existing session/global ceilings. |
| M3 source/search contracts | Source tuple, catalog capabilities, profile/query/search receipts, exact quotes, targeted-search limits and provenance are carried forward. |
| M3-P5/P6 | Mechanical checks precede Validator PASS/publication; implementation and mutation evidence remain pending. |
| UX-v2 | Source/status/clarification/publication/evidence/lifecycle/retention decisions are reconciled; browser/accessibility evidence remains pending. |

## Resolved readiness findings

- **Stage policy:** ARCH-v2 §§29–43 and THREAT-v2 §§17–22 define Analyst (12,288/8,192, 512 tokens), conditional Semantic (12,288/2,048, 256), candidate (24,576/4,096, 512) and Validator (40,960/4,096, 512). Every model stage uses the shared admission; max+1 refuses before dispatch; there are no stage retries or in-job replans; Validator remediation is terminal and a corrected question starts a new job. A job has at most two evidence service calls and two deterministic validation service calls, with one combined global tool-attempt budget; validation calls consume no model admission.
- **Profile path:** ARCH-v2 §446–453 adds `mode:"profile"` with `complete_profile`, an explicit
  `profile_request_ref` and profile-field evidence refs; profile-only plans have one profile step
  and never claim query/search coverage. §§468–478 define the complete profile-only receipt and
  optional profile-plus-primary-receipt composition within the Validator cap.
- **Refresh evidence:** ARCH-v2 §§309–318 defines `SessionSnapshotV2.accepted_answers` with `AcceptedEvidenceV2` projections; `GET /v2/session` is a one-revision, 65,536-byte bounded projection with typed unavailable markers.
- **Prior corrections:** v2 M2 control amendment, field-level clarification/status DTOs, complete Validator context, durable accepted-answer state, 4,096-byte candidate bound and corrected UX handoff wording are present in the exact hashed artifacts.

## Implementation pass conditions

1. Preserve the stage table exactly at each adapter boundary. Exercise max and max+1 request/output bodies, conditional Semantic admission, four-call accounting, terminal Validator remediation, no technical/provider retries, shared hourly/daily counters and uncertain-call accounting.
2. Test profile-only, query-with-profile and search-with-profile plans, including complete profile receipt composition and rejection of query/search coverage claims for profile-only work.
3. Serialize `GET /v2/session` from one durable revision and verify the 65,536-byte cap, complete retained answer/evidence projections, eviction markers, source binding and foreign/stale denial.
4. Keep deterministic P5/P6 failures authoritative, candidate private until independent Validator PASS, and publication fenced by job/source/generation/deadline ownership.
5. Verify all AC-M4-01–10 with current-head engineering checks, independent QA, configured provider review, guarded merge and deployed smoke tests. Use mocks for routine tests and one free-allowance live Workers AI check; do not claim live acceptance from mocks.

## Evidence and uncertainty ledger

### Facts

- Current artifact hashes were calculated directly from the repository and are recorded above.
- ARCH-v2 contains the canonical four-stage policy, no in-job replan, terminal Validator remediation, explicit profile coverage and profile-only receipt composition.
- THREAT-v2 repeats the numeric stage map, no-replan policy and shared budget behavior.
- UX-v2 marks the architecture-facing decisions reconciled.

### Observations

- The design contracts trace BR-M4-01–10 and AC-M4-01–10 across UX flows, M2 controls, M3 source/evidence boundaries and the immutable architecture.
- All implementation, runtime, browser, provider, merge and deployment evidence is still outstanding.

### Inferences

- The exact current documents satisfy the design/architecture readiness gate; no material contract gap remains.
- `READY` authorizes downstream scoped implementation handoffs under the existing user authorization and independent review requirements. It does not waive QA, provider gates, branch protection or guarded merge.

### Unknowns

- Python/SQLite deployed fit, Durable Object serialization/lifetime/restart, P5/P6 implementation, browser accessibility, session transport, provider free-quota availability, current-head review and deployed smoke tests remain unverified.

## Handoff envelope

- **Receiver/action:** coordinator may route the stable bundle to the scoped M3-P5/P6/P7, Agent/runtime, Validator, frontend and QA owners. Preserve the exact hashes above; any contract change requires a fresh readiness review.
- **Acceptance status:** design/architecture `READY`; AC-M4-01–10 remain unverified implementation/deployment criteria.
- **Evidence limits:** document and hash inspection only; no code, QA, browser, provider, security, approval, merge, deployment or live-model evidence was produced by this review.
- **Human/external-action state:** existing full GO authorizes routine scoped implementation and guarded delivery. This review performs no external action and does not claim provider approval, merge, deployment or release.

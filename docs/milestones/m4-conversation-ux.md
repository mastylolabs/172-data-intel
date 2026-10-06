# UX/UI specification: validated data conversations

## Result and identity

- **UX/UI artifact version or date:** M4-UX-v1, 2026-10-06.
- **Authoritative brief and pre-build gate:** [M4-BRIEF-v1](m4-conversation-brief.md), SHA256 `2e85ff1775ce38cb08ee675e613a2650868fb779cb6cddfeb46d36d1b5a906ec`; bounded M4-C0 pre-build handoff. AC-M4-01 through AC-M4-10 are unverified for v2.
- **Architecture source:** [original architecture](../architecture.md), SHA256 `2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd`, treated as immutable reference. Reviewed M3 receipts and M4 planning/budget reports are compatibility inputs, not v2 publication approval.
- **Existing design-system and brand sources:** None found in the repository. The existing Agent README and contracts describe a restricted operator proof surface and have no authoritative web-chat visual system. This artifact therefore gives neutral structural and behavioral guidance and does not choose a brand, logo, palette, typography, token system, breakpoint, or frontend framework.
- **Scope and supported conditions:** An isolated synthetic-demo session over the server-approved sales and support sources. The user may select a source, ask bounded questions, answer clarification, inspect an accepted answer's evidence, refresh, and follow up within the accepted same-source context. The UI must work with keyboard and touch input, narrow and wide viewports, delayed or unavailable model/tool calls, and a disconnected or restarted job.
- **Out of scope:** Uploads, arbitrary connectors, accounts, private data, cross-source joins, public-access policy, full-corpus classification, vector search, and large-workload controls. M5 owns the production web-chat implementation; this document defines the behavior M4 must make implementable.
- **Review and human-gate state:** No design-architecture review or human design approval has occurred. Full implementation authorization exists for the approved MVP, but it does not make this pre-build UX artifact a readiness verdict. Actionable contract gaps are routed to `principal-architect` below.

## Source traceability

| Source IDs | Actor/task | Flow and step IDs | Screen/component responsibilities | Contract state |
| --- | --- | --- | --- | --- |
| BR-M4-01 / AC-M4-01 | User selects an approved source and returns later | FLOW-1 / 1.1–1.5, FLOW-5 / 5.1–5.4 | UI-01 source selector; UI-03 transcript header; UI-09 source/version refusal | Blocked on catalog, migration, and stale-identity response envelopes |
| BR-M4-02 / AC-M4-02 | User asks sales, support, profile, or unsupported questions | FLOW-2 / 2.1–2.6 | UI-02 suggested questions; UI-04 composer; UI-05 progress; UI-06 clarification | Blocked on v2 plan and job status envelopes; deterministic tool semantics are stable inputs |
| BR-M4-03 / AC-M4-02 | User resolves ambiguity before execution | FLOW-3 / 3.1–3.5, FLOW-5 / 5.5 | UI-06 clarification card; UI-04 preserved composer | Blocked on clarification ownership/binding and exact persisted state |
| BR-M4-04 / AC-M4-03 | User inspects numbers and support citations | FLOW-4 / 4.1–4.7 | UI-07 accepted answer; UI-08 evidence inspector; UI-03 claim links | Blocked on claim/citation DTOs and evidence coverage fields; M3 source rules are authoritative constraints |
| BR-M4-05 / AC-M4-04 | User receives only independently checked work | FLOW-2 / 2.4–2.6, FLOW-4 / 4.1 | UI-05 validation stage; UI-07 validation label and details | Blocked on validator verdict/publication contract; candidate remains private until PASS |
| BR-M4-06 / AC-M4-05 | User sees publication or truthful non-publication | FLOW-4 / 4.1–4.7, FLOW-7 / 7.1–7.4 | UI-07 answer; UI-09 failed/interrupted/expired outcome | Blocked on atomic publication and candidate-visibility state |
| BR-M4-07 / AC-M4-06 | User refreshes, cancels, switches source, or reconnects | FLOW-5 / 5.1–5.6, FLOW-6 / 6.1–6.8 | UI-05 reconnect status; UI-09 conflict/unavailable/recovery actions | Blocked on job fences, replay/conflict/unavailable statuses, and lifecycle events |
| BR-M4-08 / AC-M4-07 | User reaches job, session, or global model limits | FLOW-2 / 2.2, FLOW-7 / 7.1–7.4 | UI-05 bounded progress; UI-09 budget/quota error and retry policy | Blocked on v2 admission/error envelope; existing 12/hour and 24/day ceilings remain facts |
| BR-M4-09 / AC-M4-08–09 | User follows up in an isolated session and inspects retained history | FLOW-5 / 5.1–5.6, FLOW-6 / 6.1–6.8 | UI-03 history; UI-08 evidence access; UI-01 reset | Blocked on retention/eviction, session ownership, and transport denial semantics |
| BR-M4-10 / AC-M4-10 | Operator/QA verifies both journeys and release evidence | All flows | All UI IDs; deploy/version footer for diagnostics | Unverified until implementation, browser QA, guarded merges, and deployed checks complete |

## User flows

### FLOW-1: Choose an approved data source

- **Actor and entry:** A new isolated session opens the chat, or an existing session refreshes. The server provides the approved catalog and the current owned selection; the client does not invent or write source identity.
- **Ordered steps and decisions:**
  1. UI-01 announces the current source, version, meaning revision, and available capabilities from the server (BR-M4-01, BR-M4-09).
  2. The user chooses Sales or Support. Each option explains the question types it supports without implying that targeted support search represents the whole corpus (BR-M4-01, BR-M4-04).
  3. The client submits the complete catalog identity. A source change clears only in-flight display state and any unresolved clarification that belongs to the previous source; accepted history remains visibly labeled with its source (BR-M4-03, BR-M4-07, BR-M4-09).
  4. On a stale, forged, unsupported, or mismatched identity, UI-09 reports that the source is unavailable and reloads the server catalog. It does not expose private identifiers or treat a client label as authority (BR-M4-01, BR-M4-09).
  5. On success, UI-02 presents source-specific suggested questions and an empty composer. Focus moves to the question field unless the user initiated the change by keyboard, in which case focus remains on the source control until the status is announced.
- **Navigation, interruption, and preserved state:** Refresh preserves the server-owned selection and accepted history. Disconnect/reconnect re-reads the selection and current job; it does not submit a second selection. Reset requires a server-owned revocation outcome and leaves the session at the initial source-selection state.
- **Success exit:** A server-approved source is selected and the composer is enabled.
- **Failure and recovery exits:** Retry catalog loading when the catalog is temporarily unavailable; choose another approved option after a stale-version response; reset when the server reports an expired session. Keep accepted prior messages read-only during recovery.
- **Evidence or unresolved questions:** The complete catalog tuple and exact error states are pending architecture reconciliation (ARCH-UX-01).

### FLOW-2: Ask a bounded question and wait for a validated answer

- **Actor and entry:** A source is selected and the composer contains a non-blank question. Suggested questions are optional shortcuts, not the supported-question boundary.
- **Ordered steps and decisions:**
  1. UI-04 validates only basic input presentation and submits the question with the owned source and a client-generated request identity. Server validation remains authoritative (BR-M4-02, BR-M4-09).
  2. UI-05 immediately adds the user question to the transcript and shows a live status tied to the owned job. It must not display a candidate answer, draft claims, model rationale, SQL, or citation before publication (BR-M4-05, BR-M4-06).
  3. The status names only stages confirmed by the job contract, such as planning, deterministic execution, evidence checking, and independent validation. It never fabricates percentage progress or “almost done” language (BR-M4-05, BR-M4-07).
  4. If the plan needs meaning or the requested scope is unsupported, the flow exits to FLOW-3. No assumed period, denominator, corpus trend, or absence claim is executed silently (BR-M4-03, BR-M4-04).
  5. When required deterministic checks and the separate Validator PASS complete, UI-07 inserts one accepted answer with claim and evidence links (BR-M4-04–06).
  6. If any check, validator call, deadline, admission, or publication fence fails, UI-09 shows a truthful non-publication outcome. The user question remains available for an allowed retry; the private candidate never becomes history (BR-M4-06–08).
- **Navigation, interruption, and preserved state:** The composer is disabled only while the server says the session has an active owned job, unless the contract explicitly permits another queued request. Refresh reconnects to that job. The question remains in the transcript even when its work is interrupted and is labeled with its outcome.
- **Success exit:** Accepted answer and evidence are visible; the composer is enabled for a same-source follow-up.
- **Failure and recovery exits:** Clarification (FLOW-3), retry with a new or server-authorized replay identity, or a terminal non-publication state. The UI does not retry uncertain model dispatch by itself.
- **Evidence or unresolved questions:** Exact stage names, cancellation affordance, and allowed concurrency require ARCH-UX-02 and ARCH-UX-03.

### FLOW-3: Resolve a clarification

- **Actor and entry:** A current owned job returns a clarification because meaning, relative period, source scope, or supported capability is unresolved (BR-M4-03).
- **Ordered steps and decisions:**
  1. UI-06 shows the concise clarification question and the original user question together, with the source and scope that own the clarification.
  2. The original question stays editable but is not silently replaced. The user may answer, edit and resubmit, or cancel if the server permits it.
  3. The response binds to the clarification's source and request. If the user changes source, UI-06 closes and the answer cannot be applied to the new source.
  4. On a resolved plan, return to FLOW-2 at the planning stage. On another clarification, replace the prior unresolved card while retaining the bounded chain. On refusal or expiry, return to UI-09.
- **Navigation, interruption, and preserved state:** Refresh retains the current owned clarification; a foreign or evicted clarification is inaccessible and must be re-requested. Do not show a model-generated inference as a confirmed field meaning.
- **Success exit:** The user sees progress for a plan explicitly bound to the clarification.
- **Failure and recovery exits:** Source change, expiry, conflict, or unsupported request produces a labeled non-publication state with preserved user text.
- **Evidence or unresolved questions:** Exact clarification response and retention limits require ARCH-UX-04.

### FLOW-4: Read an accepted answer and inspect evidence

- **Actor and entry:** An accepted answer has passed deterministic checks and an independent Validator PASS (BR-M4-04–06).
- **Ordered steps and decisions:**
  1. UI-07 leads with the answer scope, selected source, source/meaning revision, and validation state. It separates measured claims from explanatory text.
  2. Each material numeric claim links to the exact result reference, unit, period/filter scope, and source hash supplied by the server. Non-exact values show the server's stated precision or limitation; the UI does not round into a stronger claim.
  3. Support claims link to UI-08 evidence entries containing message ID and exact quote. The inspector displays the filtered scope, returned and omitted counts, and the lexical limitation that targeted examples cannot establish prevalence, whole-corpus trends, or absence.
  4. UI-08 can show actual SQL or search parameters only when the accepted evidence contract authorizes that field for this session. It labels receipts as deterministic execution evidence and never relabels `analytical_validated:false` receipts as validated by changing their provenance.
  5. A no-hit support result says that the lexical query found no matching messages in the declared filtered scope. It must not say “there are no such messages” without that scope.
  6. Closing the inspector returns focus to the triggering claim link. A missing or evicted receipt displays an unavailable marker instead of an empty or reconstructed quote.
- **Navigation, interruption, and preserved state:** Evidence inspection is read-only. Refresh keeps accepted answers and bounded evidence references only when the server confirms retention and same-source ownership.
- **Success exit:** The user can understand what was computed or retrieved and ask a same-source follow-up.
- **Failure and recovery exits:** Evidence unavailable, source mismatch, or denied access is explicit and does not reveal foreign content.
- **Evidence or unresolved questions:** Exact claim/evidence fields, omission wording, and retention markers require ARCH-UX-05.

### FLOW-5: Refresh and ask a same-source follow-up

- **Actor and entry:** The user returns to an existing owned session after refresh, reconnect, or an accepted answer.
- **Ordered steps and decisions:**
  1. On load, the client fetches server-owned session state and renders selected source, bounded accepted history, current job/clarification, and evidence references. It does not write native SDK state directly.
  2. The user asks a follow-up. UI-04 indicates the source context being used and allows a source change before submit.
  3. The server decides which accepted context is eligible. The UI never treats rejected candidates, old proof receipts, foreign state, or evicted evidence as accepted context (BR-M4-07–09).
  4. A follow-up requiring unavailable context returns a clarification or explicit limitation rather than silently using a different source or re-running uncertain work.
- **Navigation, interruption, and preserved state:** Browser refresh and reconnect are idempotent reads. A source switch starts a new source-bound context while retaining historical labels. Reset revokes access to the old session and clears its client display after server confirmation.
- **Success exit:** Follow-up enters FLOW-2 with source-bound accepted context.
- **Failure and recovery exits:** Expired session, missing evidence, request conflict, or unavailable retained outcome; preserve user input and offer only server-authorized recovery.
- **Evidence or unresolved questions:** The v2 state snapshot and context-eligibility fields require ARCH-UX-06.

### FLOW-6: Cancel, switch source, reset, disconnect, or race a job

- **Actor and entry:** A job is active or a session lifecycle action occurs while work is pending.
- **Ordered steps and decisions:**
  1. UI-05 offers cancellation only when the server contract says cancellation is supported. The action is labeled “Stop analysis” and does not imply provider cancellation or rollback of an already admitted model call.
  2. A source switch or reset invalidates the old job through the server fence before the UI removes its controls. A late response is ignored and cannot publish.
  3. On disconnect, UI-05 says “Connection lost. Reconnecting…” and preserves the question and job identity. On reconnect, it reads current state instead of issuing the previous request again.
  4. If the server reports interrupted, expired, conflict, or unavailable, UI-09 records that no answer was published and offers the permitted next action.
- **Navigation, interruption, and preserved state:** Never clear accepted history or a new source because a stale request returned. Preserve unsent composer text across reconnect and recover focus after the lifecycle status stabilizes.
- **Success exit:** New source/session state is confirmed, or the accepted answer remains unchanged after a stale completion.
- **Failure and recovery exits:** A truthful terminal status with no stale publication; retry only with explicit server permission.
- **Evidence or unresolved questions:** Exact fence and cancellation outcomes require ARCH-UX-03 and ARCH-UX-07.

### FLOW-7: Recover from validation, provider, budget, or service failure

- **Actor and entry:** The server returns a typed refusal or the job reaches a terminal non-publication state.
- **Ordered steps and decisions:**
  1. UI-09 gives the user an actionable, non-sensitive explanation: invalid question, unsupported source/capability, clarification needed, unavailable service, limit reached, expired/interrupted job, or evidence unavailable.
  2. It preserves the original question and displays whether retry is allowed. It does not show provider credentials, raw exceptions, prompt contents, hidden hashes, foreign IDs, or speculation about quota/billing.
  3. For free-quota or account-limited model failure, the copy says the model service is temporarily unavailable or the analysis limit was reached, with a retry time only if the server supplies one. It never offers to enable paid billing.
  4. Retry is a new server-authorized request or retained same-input replay. The UI does not claim that an uncertain dispatch was refunded.
- **Navigation, interruption, and preserved state:** The user can return to the transcript, edit the question, choose another approved source, or reset if allowed. Accepted prior answers remain visible and separately labeled.
- **Success exit:** A new owned job starts, clarification is answered, or the user exits with the failed attempt preserved as non-publication.
- **Failure and recovery exits:** A terminal safe error if repeated failures exhaust the bounded retry/correction policy.
- **Evidence or unresolved questions:** Exact error codes, retry actions, and copy ownership require ARCH-UX-07.

## Screen and component requirements

| Screen/component ID | Purpose and information hierarchy | Controls/content | Reused design-system source | New pattern justification |
| --- | --- | --- | --- | --- |
| UI-01 Session shell and source selector | Establish session status, selected source, version, capabilities, and reset action before transcript | Source options with name, purpose, source/meaning revision, and capability summary; reset; session status | None found; use existing platform-native form, landmark, button, and disclosure patterns | No new visual pattern is required; source/version metadata needs a compact read-only summary |
| UI-02 Welcome and suggested questions | Explain the selected dataset and offer safe starting points | Dataset-specific examples: sales aggregation/period comparison; support targeted message lookup with citation scope | None found; neutral heading/list/card semantics | Suggestion chips are optional convenience controls, not a new design system |
| UI-03 Conversation transcript | Show user questions, accepted answers, clarifications, non-publication outcomes, and bounded history in order | Read-only source label per turn; status and evidence links; no candidate draft | None found; use ordered semantic content and status text | Conversation grouping is required for chronology and ownership; styling remains neutral |
| UI-04 Question composer | Submit a question or clarification without losing input | Labeled multiline field, submit, clear/edit where allowed, character/byte guidance from server limits | None found; use native label, textarea, and button semantics | No novel control; server-declared bounds and disabled states are material |
| UI-05 Job progress/status | Explain current owned work and reconnect/interruption state | Stage label, current job status, optional server progress detail, stop action only if allowed | None found; use a live status region and progress semantics only when determinate | A job status panel is required; it must not invent percentages |
| UI-06 Clarification card | Ask one concise question and preserve the user's original intent | Clarification text, source/scope context, answer field, submit, edit original, cancel if allowed | None found; use a grouped form with explicit relationship to original question | A distinct clarification state prevents accidental execution of assumptions |
| UI-07 Accepted answer and claim links | Present only validated publication and make material claims inspectable | Validation status, scope, claim text, units/period, evidence links, limitations, follow-up affordance | None found; use headings, paragraphs, lists, and disclosure semantics | Claim-to-evidence links are domain-specific but can use ordinary links/buttons |
| UI-08 Evidence inspector | Show approved deterministic receipt details and exact support quotes | Claim/result reference, source identity/hash as appropriate, SQL/search scope if authorized, message IDs and exact quotes, counts/limitations | None found; use a modal/drawer pattern only if the platform already provides one; otherwise a focus-managed disclosure | Evidence needs an inspectable secondary view; architecture must define authorized fields |
| UI-09 Refusal, recovery, and unavailable state | Give truthful, safe recovery without leaking internals | Typed human-readable message, preserved question, retry/edit/choose-source/reset action when allowed | None found; use alert/status semantics and ordinary buttons | One reusable state pattern covers validation, denial, limit, provider, stale, and eviction outcomes |
| UI-10 Session history boundary | Make bounded retention and unavailable evidence legible | Older entries marked retained, evicted, or unavailable; no hidden infinite scroll assumption | None found; use a list with explicit end/limit status | Required only if the server exposes bounded history; avoid implying durable archival |

## State, content, accessibility, and data contract

The client renders server-owned state. It may perform local non-blank validation and presentation
formatting, but it does not validate claims, select tools, authorize sources, decide publication, or
infer retry safety. All dynamic status is tied to an owned session/job identity and a server response.

| Source/UI IDs | State/trigger | Visible content and action | Keyboard/focus/status behavior | Responsive behavior | Data/API/authorization need | Evidence/status |
| --- | --- | --- | --- | --- | --- | --- |
| BR-M4-01 / UI-01 | Initial, catalog loading, empty | “Choose a data source to begin.” Show only approved source options; loading says “Loading approved data sources…” | Source group has a label; announce catalog completion; focus first option only after load if user entered a new session | Selector precedes transcript; options wrap without truncating identity | Catalog tuple: source ID, snapshot hash, meaning revision, capabilities, display label; server ownership | Catalog fields are not frozen; blocked ARCH-UX-01 |
| BR-M4-01 / UI-01, UI-09 | Validation/denied/stale | “This data source version is unavailable. Choose an approved source to continue.” | Alert is announced; focus moves to source selector; no raw identity/hash in error | Error stays adjacent to selector and remains readable at narrow width | Typed stale/unsupported/mismatch outcome; no foreign-resource distinction leak | Required by BR; contract unverified |
| BR-M4-02 / UI-02, UI-04 | Empty/ready | Source-specific suggested questions and “Ask a question about this data” | Composer label and instruction are programmatically associated; submit is reachable in normal tab order | Suggested questions wrap or become a vertical list; composer remains visible after content growth | Server source capabilities and bounded input limit; no model call | UI behavior defined; API unverified |
| BR-M4-02, 05, 07 / UI-04, UI-05 | Loading/active | “Preparing your analysis…” followed only by confirmed stage labels; “Stop analysis” only when allowed | Use polite live status; do not steal focus on each stage; preserve submit text | Status stays in transcript flow; no forced horizontal progress bar | Owned job ID, stage/status event, generation, source, deadline and cancellation permission | Stage vocabulary pending ARCH-UX-02/03 |
| BR-M4-03 / UI-06 | Clarification | “I need one detail before I run this analysis:” plus the exact concise question; “Answer clarification” | Focus clarification field; link original question; announce transition from progress | Card stacks fields on narrow view; original question remains readable | Owned clarification ID, source/request binding, prompt text, expiry, submit outcome | Semantics pending ARCH-UX-04 |
| BR-M4-04–06 / UI-07 | Success/accepted | “Validated answer” with scope, claims, limitations, and “Inspect evidence” links. Never label raw receipts as validated | Move focus to answer heading once; links have meaningful names such as “Evidence for revenue claim” | Claims wrap; evidence links remain adjacent; long quotes grow or disclose, never clip silently | Accepted answer ID, typed claims, exact evidence refs, validator PASS, provenance, source/hash | Publication contract unverified; blocked ARCH-UX-05 |
| BR-M4-04 / UI-08 | Evidence open/close | Exact support quote and message ID; SQL/result or search scope only when authorized; counts and lexical limitation | Focus-managed disclosure/dialog; Escape closes; return focus to invoking link; quote is selectable | Drawer becomes full-width or inline disclosure on narrow view; no clipped quote | Owned evidence ref, source/hash, receipt/result ref, query/search scope, exact quote, returned/omitted/scanned counts, retention state | Fields pending ARCH-UX-05 |
| BR-M4-04 / UI-07, UI-08 | Empty/no-hit support | “No messages matched this lexical query in the declared filtered scope.” Include the fixed targeted-search limitation | Announce no-hit result; do not use an empty evidence list without explanation | Limitation remains visible next to result | Search receipt with complete no-hit counts and declared filters | M3 search wording is authoritative |
| BR-M4-06–08 / UI-09 | Validation fail, provider unavailable, budget exhausted, terminal | “This analysis was not published.” Add safe reason and allowed action; preserve question | Assertive status for terminal result; focus first permitted recovery action | Error content wraps and does not push composer offscreen permanently | Typed safe code, retry/replay permission, terminal state, no provider secret/raw detail | Error/retry envelope pending ARCH-UX-07 |
| BR-M4-07 / UI-05, UI-09 | Interrupted, cancelled, deadline, stale | “Analysis stopped before publication. No answer was saved.” Offer retry only if server permits | Announce terminal transition; restore focus to retry or transcript | Keep original question and state in transcript; no spinner left running | Job fence/generation/deadline and publication state; explicit cancellation result | Lifecycle semantics pending ARCH-UX-03/07 |
| BR-M4-07, 09 / UI-03, UI-05 | Refresh/reconnect | “Reconnecting…” then server-owned current status; no duplicate submission | Preserve focus and unsent input; announce recovered or unavailable outcome once | Same reading order after reflow; status does not overlay transcript | Snapshot endpoint with session owner, current job/clarification, accepted history, evidence retention | State snapshot pending ARCH-UX-06 |
| BR-M4-08 / UI-09 | Denied/quota/limit | “This analysis limit is currently unavailable. Try again later.” Use supplied retry guidance only | Alert is announced; do not imply paid upgrade or refund | Keep action and reason together; no hidden provider detail | Safe budget/provider outcome; stage/job/session/global limit metadata only when authorized | Free-only rule is fact; exact envelope unverified |
| BR-M4-09 / UI-01, UI-03, UI-08 | Reset/source switch/eviction | “This evidence is no longer available. Ask again to create a new analysis.” Historical item keeps source label and unavailable marker | Confirm reset only if server requires it; return focus to new source/composer | Evidence marker remains readable in history; no broken link icon without text | Server-owned revocation, source generation, bounded history/evidence retention, eviction marker | Retention policy pending ARCH-UX-06 |
| BR-M4-09 / UI-09 | Foreign/guessed ID or client write | “This session cannot access that analysis.” No distinction between unknown and foreign resource | Announce denial; retain current session; do not focus or reveal guessed resource | Same generic copy at all widths | Server authorization and session ownership; native SDK/client writes rejected | Security contract input; unverified |
| BR-M4-02, 09 / UI-04 | Local validation | “Enter a question to continue.” Preserve typed text; do not call server | Inline error associated with field; focus field; submit remains available after correction | Error/help text wraps under field; input grows within bounded layout | Client checks non-blank; server owns all other limits and semantics | Basic UX only; exact server limits pending |
| BR-M4-10 / UI-01, UI-09 | Unsupported capability/terminal | “This question is outside the approved demo capabilities.” Suggest a supported example or source | Alert plus suggested action; no fabricated partial answer | Keep limitation beside question outcome | Typed unsupported-scope response, source capabilities, no model override | Requirement defined; API unverified |

### Required state transitions and preservation

- `initial → catalog-loading → source-ready → job-active → accepted` is the normal path. `job-active → clarification` is a valid branch; `job-active → non-publication` is the safe terminal branch.
- `refresh/reconnect` is an idempotent read from any state. It may return `active`, `accepted`, `clarification`, `interrupted`, `expired`, `unavailable`, or `denied`; the UI must render the returned state rather than infer one from a spinner.
- `source change` and `reset` create a new server-owned generation. A stale response may update neither the transcript nor accepted memory. Accepted history remains labeled and read-only unless the server reports it evicted.
- Preserve the question, clarification response, focus target, selected source display, and accepted transcript across reflow and reconnect where the server says they remain owned. Never preserve a candidate as accepted memory.
- A missing/evicted receipt is a first-class unavailable state. It must not be replaced by cached quote text, reconstructed numbers, or a new execution without an explicit new request.

## Responsive and content requirements

- **Existing breakpoints or conditions:** No authoritative breakpoints or design system were found. The implementer should use the repository's chosen platform conventions only after the frontend contract is approved; do not invent a brand-specific breakpoint policy here.
- **Reflow and priority:** At narrow widths, order content as source/status, transcript, current answer/clarification, composer, and evidence disclosure. At wide widths, evidence may sit beside or below the answer while keeping the transcript readable. Source identity, validation state, scope, and limitations must remain visible before optional detail.
- **Wrapping and overflow:** Long questions, exact quotes, hashes, SQL, IDs, and model-independent explanations are untrusted content. Wrap or disclose them; never clip silently, horizontally scroll the entire page, or use ellipses where exact content is required for inspection. A bounded code/text region may scroll independently when its contract authorizes the field.
- **Touch and pointer:** Controls have a usable touch target and visible pressed/disabled state. Evidence inspection must not depend on hover. Source switching and reset must work without drag or timing gesture.
- **Keyboard and viewport:** A logical tab sequence is source → transcript links → composer → status actions. Focus is visible, remains within a modal only while open, and restores to the invoking control on close. The composer and status must remain reachable after the virtual keyboard or content growth changes viewport height.
- **Orientation and interruption:** Orientation change, backgrounding, refresh, and reconnect preserve server-owned state and unsent text according to the state contract. Never treat a lost stream as a completed answer.
- **Content owner and tone:** Product/architecture owns status and refusal semantics; data/validation owns scope, units, citations, and limitations; frontend owns presentation only. Use direct, calm language that explains the next permitted action. Do not expose implementation jargon, raw provider errors, or billing prompts.
- **Required fixed limitations:** Support evidence must retain the M3 wording that targeted lexical examples cannot establish whole-corpus trends, prevalence, or absence. A no-hit result must keep its declared-filter scope visible. Sales results must preserve exact units (for example, cents versus dollars) and period scope from the accepted claim.

## Accessibility criteria

| Criterion ID | Semantic/name/instruction need | Keyboard and focus | Error/status communication | Visual/motion/non-visual equivalent | Required evidence |
| --- | --- | --- | --- | --- | --- |
| UXA-01 | Page has named main region, source controls, transcript, status, composer, and evidence region with headings in reading order | All controls reachable in a deterministic sequence; no keyboard trap except an open modal | Source/job changes announced once in a polite live region | Do not rely on color, icons, or animation to indicate source, validation, error, or progress | Browser keyboard pass at narrow/wide viewports |
| UXA-02 | Source options expose source display name, revision, capability summary, selected state, and help text | Selection works with keyboard; focus remains visible after server refusal | Catalog loading, stale, denied, and recovered states are associated with the source group | Selected/disabled state has text and semantic state, not color alone | Automated semantics plus manual keyboard inspection |
| UXA-03 | Composer has a programmatic label, input instructions, and server-limit help when supplied | Submit and edit work without pointer; invalid submit returns focus to field | Inline error is associated with input and announced; text is preserved | No character counter or progress animation is the only indication of limit | Browser test with keyboard and screen reader-style accessibility tree |
| UXA-04 | Transcript turns identify speaker, source context, status, and accepted/non-publication state | Focus order follows chronology; focus does not jump on every progress update | New accepted answer and terminal outcome use appropriate live status; candidate is not announced as answer | Status and validation use text; reduced-motion mode does not lose information | Dynamic update test and reduced-motion check |
| UXA-05 | Clarification is a labeled grouped form associated with original question and source | Focus enters the clarification field and returns to the submitted card or error | Clarification transition is announced; unresolved old card is not ambiguous | No model-confidence color scale or unexplained icon | Keyboard, focus, and reload/reconnect evidence |
| UXA-06 | Answer claims, units, period, scope, limitations, and evidence links have meaningful names | Each evidence link is keyboard reachable and returns focus after inspection | Validation/publication state is announced; unavailable evidence is explicit | Exact quote and numerical values are available as text; motion is optional | Screen-reader-style content review and mutation cases |
| UXA-07 | Evidence inspector has a name, description, close control, and exact quote/result text | Modal focus containment if modal; Escape and close restore invoking focus | Denied/evicted/missing evidence is announced without exposing foreign content | SQL/quote disclosure has a non-visual equivalent; no hover-only citation | Focus, overflow, and long-content browser checks |
| UXA-08 | Retry, reset, stop, and source-change actions state their effect and availability | Destructive/reset action is keyboard reachable and confirmation, if required, is fully operable | Provider/quota/limit errors state permitted recovery without billing suggestion | Spinner is not the only progress signal; interrupted state has text | Failure, cancellation, disconnect, and quota-mock browser checks |
| UXA-09 | Reconnect status and current job are exposed without raw IDs or secrets | Focus and typed input persist through reconnect; no duplicate submit from re-render | Reconnecting and recovered/terminal outcomes are announced | No reliance on network animation; provide text state | Browser reconnect simulation and duplicate-submit test |
| UXA-10 | Source/history/evidence boundaries are understandable to users without implementation knowledge | Foreign/denied action leaves focus in current owned session | Generic denial does not distinguish guessed versus foreign resources | Unavailable markers use text and retain chronology | Isolation and eviction UI tests with sentinel content |

## Architecture reconciliation

The following are actionable interface decisions absent from the v2 brief. They are recorded as
user needs rather than invented client semantics. The immediate receiver is `principal-architect`;
implementation and independent design/architecture review must wait for a stable returned contract.

| UX/source IDs | Data and ownership | Interface and authorization | Failure/retry/recovery | Architecture decision/status | Owner |
| --- | --- | --- | --- | --- | --- |
| BR-M4-01, 09 / UI-01 | Server owns approved source tuple and current selection; client stores display state only | Define catalog/snapshot/meaning/capability envelope, source-switch generation, stale/unsupported/mismatch codes, and session ownership | Define safe reload versus reset and whether accepted history remains readable after a source switch | **Blocked, ARCH-UX-01:** principal architect must freeze the source catalog and migration/selection contract | Principal architect/data owner |
| BR-M4-02, 05, 07 / UI-05 | Orchestrator owns job stage and fences; client observes | Define status snapshot/event shape, stage vocabulary, determinate-progress rule, reconnect cursor, cancellation permission, and deadline | Define reconnect, cancellation, expiry, and stale-event outcomes; forbid client-generated progress | **Blocked, ARCH-UX-02:** principal architect/runtime owner must freeze observable job lifecycle | Principal architect/runtime owner |
| BR-M4-03 / UI-06 | Clarification belongs to a source-bound request/job | Define clarification ID, source/request binding, persisted text, answer association, expiry, and max chain | Define edit/cancel/repeat clarification and source-switch behavior without assumed execution | **Blocked, ARCH-UX-04:** principal architect/Analyst owner must freeze clarification contract | Principal architect/Analyst owner |
| BR-M4-04–06 / UI-07–08 | Validator and deterministic checks own publication; evidence refs point to actual receipts | Define accepted answer, typed claims, citation/evidence refs, source/hash/scope fields, validator PASS, and authorized inspectable fields | Define malformed/failed/missing validator, evidence mismatch, no-hit, and evicted evidence states | **Blocked, ARCH-UX-05:** principal architect/validation owner must freeze claim/evidence/publication contract | Principal architect/validation owner |
| BR-M4-06–08 / UI-09 | Orchestrator owns admission, provider outcome, and retry eligibility | Define safe error envelope, retry/replay permission, stage/job/session/global limit disclosure, and candidate visibility | Define no-publication copy state, uncertain dispatch handling, and terminal recovery | **Blocked, ARCH-UX-07:** principal architect/budget/security owner must freeze safe failure semantics | Principal architect/budget/security owner |
| BR-M4-07, 09 / UI-03, 05, 10 | Durable object owns session, current job, accepted history, retention and fences | Define state snapshot, history/evidence byte/count bounds, eviction marker, reset/revocation, and foreign-access response | Define refresh/reconnect/restart, unavailable retained outcome, and source-generation precedence | **Blocked, ARCH-UX-06:** principal architect/runtime/security owner must freeze lifecycle and retention | Principal architect/runtime/security owner |

## Evidence and uncertainty ledger

### Facts

- M4-BRIEF-v1 freezes BR-M4-01–10 and AC-M4-01–10, and explicitly marks all v2 acceptance criteria unverified.
- The immutable architecture requires deterministic execution, conditional semantic reasoning, Analyst planning, independent Validator review, provenance, and bounded recovery.
- M3 provides a complete sales proof/demo identity and bounded support lexical receipts with exact quotes and explicit limitations. Existing search wording and source identities are compatibility constraints.
- The repository's existing Agent README/contracts document an operator-only `/proof/*` surface, a native Agent/Durable Object, typed v1 receipts, and no web chat implementation. They do not provide an authoritative design system.
- The user authorizes all approved MVP milestones and preview/final deployment, while requiring mocks for routine tests, Workers AI free allowance only for live checks, a real Llama 3.3 final application, and no paid billing.

### Observations

- The inspected repository contains no frontend source, browser test suite, brand guide, or shared UI component specification.
- The existing v1 Agent state hides request journals and model admissions from public state, and v1 proof receipts explicitly are not published analytical answers. M4 must preserve that separation.
- The M4 brief identifies DEC-M4-01 through DEC-M4-05 as unresolved architecture/runtime/validation/budget/UX decisions; this artifact expands only the UX-facing portions.

### Inferences

- A transcript-first layout with source context and evidence inspection supports the required flows without committing the project to a visual brand or frontend framework.
- A server-owned status snapshot is necessary for truthful refresh/reconnect behavior; a client-only spinner cannot distinguish active, interrupted, expired, or unavailable jobs.
- Keeping candidate text out of the transcript until publication is the clearest observable expression of BR-M4-06 and prevents rejected reasoning from becoming apparent memory.

### Assumptions

- **A-UX-01:** The final web chat will use a browser session mechanism already authorized by the existing Agent boundary. If ownership or public-access policy changes, UI-01, UI-03, UI-09, UXA-09, and BR-M4-09 must be revisited by security/architecture.
- **A-UX-02:** The approved catalog can provide human-readable source labels and capability descriptions. If it cannot, UI-01 must use a server-owned neutral label and the content owner must supply accessible help text.
- **A-UX-03:** The implementation can expose an owned current state after refresh/reconnect. If only fire-and-forget calls are possible, FLOW-2, FLOW-5, FLOW-6, and AC-M4-06 cannot be satisfied; the issue returns to principal architect rather than becoming client polling guesswork.
- **A-UX-04:** The platform has an existing modal/disclosure primitive or can use native semantics. This affects composition only; it does not authorize a new visual system. Frontend engineer owns verification.

### Decisions

- Use neutral semantic structure and reuse platform-native interaction patterns because no authoritative visual system is present.
- Show a validation state only for an atomically accepted answer; do not decorate a candidate or raw execution receipt as validated.
- Treat exact quotes, message IDs, units, periods, scope, and fixed limitations as content, not optional decoration, because they are part of evidence integrity.
- Keep provider, secret, and internal exception details out of user-visible and diagnostic content; show typed safe outcomes and server-authorized recovery only.

### Unknowns

- Exact v2 wire/state schema, job event vocabulary, session identity/transport policy, publication transaction, evidence field authorization, retention/eviction limits, and retry actions are all unresolved and block implementation-ready reconciliation.
- No responsive, keyboard, dynamic-status, screen-reader, or browser evidence exists yet. This document defines required checks; it does not claim compliance or user testing.
- No live Llama 3.3, deployed lifecycle, or quota result is evidenced by this artifact.

## Residual risks and follow-ups

| Risk or follow-up | Evidence | Affected IDs | Blocking? | Mitigation or next action | Owner |
| --- | --- | --- | --- | --- | --- |
| UI invents a progress state or displays a stale candidate | Existing v1 proof surface has no v2 job/publication contract; BR-M4-05–07 | BR-M4-05–07, UI-05/07 | Yes | Principal architect freezes server-owned lifecycle/publication fields; frontend tests every state transition | Principal architect/frontend/QA |
| Evidence links expose foreign, evicted, or unvalidated content | Brief requires isolation, bounded retention, exact evidence and atomic publication | BR-M4-04, 06, 09, UI-08/10 | Yes | Freeze owned evidence references and generic denial/unavailable states; adversarial browser tests | Architecture/security/QA |
| Narrow layouts clip exact quotes or units | No existing responsive system or browser evidence | BR-M4-04, UI-07/08, UXA-06/07 | No, until implementation | Test long untrusted content at supported viewports; use wrapping/disclosure with exact text | Frontend/QA |
| Provider/quota copy implies paid billing or a retry that can duplicate work | User cost authority and M4 budget requirements | BR-M4-08, UI-09, UXA-08 | Yes | Server supplies retry eligibility; UI uses safe copy and never offers billing changes | Architecture/budget/frontend |
| Refresh loses a live job or replays a model request | Durable lifecycle and request identity are reviewed inputs but v2 implementation is absent | BR-M4-07–09, FLOW-5/6 | Yes | Reconnect from owned snapshot/cursor and test duplicate, stale, restart, and deadline cases | Runtime/QA |
| Accessibility behavior is claimed from structure alone | No browser or assistive-technology evidence exists | UXA-01–10 | No, before implementation; required before release | Run keyboard, dynamic-status, focus, responsive, reduced-motion, and content-growth checks | Frontend/QA |

## Handoff envelope

- **Receiver and requested action:** `principal-architect`; reconcile the exact UX-facing v2 contracts identified as ARCH-UX-01, 02, 04, 05, 06, and 07, preserving BR-M4-01–10 and the original architecture. Return a stable source catalog, job/status, clarification, publication/evidence, safe-error, and session/retention contract before implementation guidance is sent to `frontend-engineer`.
- **If architecture reconciliation is actionable:** The immediate receiver is `principal-architect`. The exact actions are in the Architecture reconciliation table: define server-owned identities, state transitions, authorization boundaries, error/retry semantics, evidence visibility, and retention/eviction markers. Do not parse undocumented responses in a client.
- **Downstream design/architecture review:** `design-architecture-reviewer` receives this artifact only after principal-architect returns a stable reconciled contract. `frontend-engineer` receives the reconciled artifact only after independent readiness review and the existing human build gate state permit implementation.
- **UX/UI and source-artifact versions:** M4-UX-v1; M4-BRIEF-v1 SHA `2e85ff1775ce38cb08ee675e613a2650868fb779cb6cddfeb46d36d1b5a906ec`; original architecture SHA `2046e837044efad2737cae080c011ae9c2d0f809302a7d9505749f973cf4d9dd`; M3 source/search identities as cited in the M4 brief.
- **Acceptance-criteria and traceability status:** BR-M4-01–10 are traced through FLOW-1–7, UI-01–10, state rows, accessibility criteria, and architecture actions. AC-M4-01–10 remain **unverified**; no implementation, browser, deployed, or live-model acceptance is claimed.
- **Evidence state and coverage limits:** Evidence is limited to repository inspection of the exact M4 brief, immutable architecture, M4 planning/budget reports, M3 contracts/reports, and existing Agent README/contracts. No user testing, browser test, provider action, merge, deployment, or external approval occurred in authoring this artifact.
- **Assumptions:** A-UX-01 through A-UX-04 are reversible composition assumptions with owners and consequences above; none authorizes a new product policy, source meaning, identity guarantee, or provider action.
- **Unresolved decisions and owner:** ARCH-UX-01/02/04/05/06/07, owned by principal architect with data, runtime, validation, budget, security, and UX inputs as marked. Product/public-access policy remains outside this artifact.
- **Residual risks:** Candidate leakage, stale publication, duplicate dispatch, foreign/evicted evidence, quota-copy ambiguity, and unverified browser accessibility remain. Mitigations and owners are recorded above.
- **Human-gate and external-action state:** The user's full MVP authorization covers routine scoped implementation and guarded deployment, but this handoff does not claim readiness, provider approval, merge, release, deployment, or live Llama execution.

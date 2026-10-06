# Delivery context

- M1 complete: guarded PR #1 merged into main `98408bd`; full gate and CI pass,
  39 tests, measured local coverage 98.18%. See its milestone report.
- Full GO authorizes all remaining MVP milestones without routine pauses; retain
  a report after each and every independent engineering/provider gate.
- M2 active: reviewed runtime/access/query contracts merged in PR #2. The first
  fixture slice implements six pinned synthetic sales rows, validated typed loading,
  explicit meanings and computed metadata. A separate private SQLite policy-hook
  foundation installs locally tested read-only controls, limits, authorization and
  progress bounds. The source-bound context opens a fresh in-memory database from
  loader-verified rows, installs policy after loading and closes on all context exits.
  A private bounded-result foundation normalizes fetched scalar rows and hashes
  canonical content. A private SQLite query engine now executes generic bounded,
  read-only sales SQL in a fresh source-verified database and returns an explicitly
  unvalidated result. The first P2 slice adds a typed private Python service
  request/result adapter with exact cells, result hashes, policy limits, and
  explicit runtime provenance validation; it has local parity tests but no
  service transport. The second P2 slice adds a private Python Worker manifest,
  provenance fence, and clean-revision dry-run helper. A local Pywrangler 1.17.6
  dry-run generated the tracked Pyodide `pylock.toml`; Wrangler 4.11.1 then gave
  a false-success bundle without dependencies. The Worker package now pins
  Wrangler 4.127.1 and the helper refuses lock regeneration or missing modules
  in its temporary dry-run artifact. A focused correction also forces local
  source sync and checks exact vendored Python bytes. Private Python `/health`,
  `/metadata`, and bounded `/query` routes now have local contract/stream tests
  but no deployed service-binding proof. P3a is reviewed and merged. Next:
  complete the P3b-1 TypeScript wire-validation foundation, then the dependent
  P3b-2 native Agent/session/service bridge after foundation review and merge;
  async lifecycle/budgets and deployed SQL/control receipts remain pending, followed
  by Llama 3.3 integration with persistent isolated state. Target-runtime
  compatibility remains unverified. A
  bounded Llama access preflight failed with daily free allocation rejection; real
  AI proof remains pending. Continue independent work from stable merged contracts;
  no billing change or false live-success claim.
- M3 active: P1's distinct 24-row sales-demo fixture and strict immutable loader
  are reviewed and merged, as are P2a's strict sales profile receipt models and
  bounded canonical serialization and P2b's deterministic whole-source profiling,
  canonical payload hashes and deadline/failure checks. P2c enables approved demo
  SQL through an explicit trusted engine opt-in, retaining proof-only defaults
  for v1 service callers. Complete independent QA/review and guarded merge.
  Support loading/retrieval, private v2 service exposure and typed
  deterministic validation remain later bounded slices.
- M4–M5, planned: real SQL/retrieval and
  deterministic validation; independently validated durable conversations;
  shareable chat and reviewed Cloudflare deployment. See the delivery plan.
- Preserve original architecture and the separate reference application,
  its PRs and running deployment. Future resources must use distinct names.

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
  provenance fence, and clean-revision dry-run helper. Pywrangler is absent in
  this environment, so packaging and target-runtime compatibility remain
  unverified. Before claiming a reproducible private build, generate and review
  Pywrangler's separate Pyodide `pylock.toml` and pin/verify the Wrangler binary;
  the host `uv.lock` alone does not cover either. Next: obtain a reviewed private
  build, then a reviewed native Agent
  bridge for deployed SQL/control receipts, followed
  by Llama 3.3 integration with persistent isolated state. Target-runtime
  compatibility remains unverified. A
  bounded Llama access preflight failed with daily free allocation rejection; real
  AI proof remains pending. Continue independent work from stable merged contracts;
  no billing change or false live-success claim.
- M3–M5, planned: synthetic fixture meanings/profiles, real SQL/retrieval and
  deterministic validation; independently validated durable conversations;
  shareable chat and reviewed Cloudflare deployment. See the delivery plan.
- Preserve original architecture and the separate reference application,
  its PRs and running deployment. Future resources must use distinct names.

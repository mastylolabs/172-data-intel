# 172X Data Intelligence MVP final milestone report

## Delivered behavior and verified revision

The MVP is deployed at https://172x-data-intel-mvp-app.zmastylo.workers.dev. It provides a Durable Object backed native Agent, session-isolated web chat, source selection, suggested questions, persistent state, bounded Analyst planning, read-only Python-backed query/search tools, deterministic checks, and a separate Workers AI Validator. The bundled sales CSV and support JSONL fixtures are pinned by source hashes and exposed through the catalog.

Setup and deployment steps are in the [root README](../../README.md), with the
public route and model-boundary details in [the app README](../../workers/app/README.md).

Relevant merged implementation PRs are [#61](https://github.com/mastylolabs/172-data-intel/pull/61), [#62](https://github.com/mastylolabs/172-data-intel/pull/62), [#63](https://github.com/mastylolabs/172-data-intel/pull/63), [#64](https://github.com/mastylolabs/172-data-intel/pull/64), [#65](https://github.com/mastylolabs/172-data-intel/pull/65), [#66](https://github.com/mastylolabs/172-data-intel/pull/66), [#67](https://github.com/mastylolabs/172-data-intel/pull/67), [#68](https://github.com/mastylolabs/172-data-intel/pull/68), [#69](https://github.com/mastylolabs/172-data-intel/pull/69), [#70](https://github.com/mastylolabs/172-data-intel/pull/70), and [#71](https://github.com/mastylolabs/172-data-intel/pull/71). The verified `main` revision is `094838c3bbcdd4cff807106c7f5d6c47281e2041`.

## Problems and resolutions

- The deployed Python Worker initially rejected the short source revision and returned an unsafe transport failure. The tools deployment now carries the full 40-character build revision and promoted version ID; `/v2/catalog` and `/health` returned 200 through the service smoke path.
- A GET body read broke catalog discovery; the request adapter now reads bodies only for POST requests.
- Metadata proxy shape drift and Planner SQL aliases caused otherwise valid sales plans to fail; the app now normalizes the known aliases and preserves generic SQL execution.
- The first real Validator response was truncated/under-specified: it returned no claims and invented lineage hashes. The final contract narrows the model response to semantic decisions, requires each candidate claim and the server-generated `validator_call_id`, and binds all identity and digest fields from trusted state. A stale call ID regression is covered by tests.
- A first live support attempt ended in a safe failed phase with no publication. A retry completed and published the expected bounded citations; the transient failure is retained in the deployed-test record.

## Hardest technical problem

The hardest problem was making the Cloudflare service boundary and real Llama path agree on bounded, verifiable data. The solution was to keep Python execution behind the v2 service contract, pin full build and Worker version provenance, and make publication depend on deterministic evidence plus a nonce-bound Validator decision. This preserves the independent model check without allowing the model to mint hashes, IDs, or citation lineage.

## Test and coverage evidence

The final independent QA recorded 669 Python tests, 49 Agent tests, and 55 app tests, all passing. App coverage was 88.12% statements, 85.71% branches, 94.73% functions, and 95.03% lines. `make gate` passed at the final implementation head: Ruff format/check, mypy, pytest, and Radon (average complexity A). The app typecheck and focused Validator regression tests also passed. The main remaining coverage gap is live provider failure-shape variation; routine tests use mocks as authorized.

## Integration and deployed results

- Public app root returned HTTP 200 and served the chat shell.
- Sales smoke: source selection returned 200; ask returned 202; completion returned `published` with `29 net_units`, SQL `SELECT SUM(units) AS units FROM sales`, deployed Python 3.14.2/SQLite 3.39.0 provenance, and `validator_call: performed`. Refresh retained the selected source and publication. Replaying the same request ID returned HTTP 200 with the persisted publication.
- Support smoke: source selection and ask returned 200/202; the successful retry returned `published` with exact quotes and IDs `M015`, `M012`, `M009`, `M005`, and `M002`, plus the targeted-search limitations. The first attempt failed closed and produced no answer.
- The tools smoke path returned HTTP 200 for `/v2/catalog` and `/health`, with the promoted tools version `56fb1453-1c23-4876-a282-5222dd5b0e63` and build revision `afe115862c8c715282e84d2ebcfbcbdf7e492445`. Disposable smoke-proxy and AI-probe Workers were deleted after verification.
- Browser-plugin automation was unavailable in this environment; the frontend was independently exercised with the Playwright fallback, including desktop/mobile layout, source selection, suggestion fill, answer rendering, and no console errors.

## Remaining limits and next milestone

Uploads, live connectors, OAuth, PostgreSQL, Parquet, vector search, full-corpus classification, containers, distributed execution, and large-scale benchmarks remain intentionally deferred. No paid billing or credits were enabled. The next useful milestone is optional product polish and operational observability around the bounded contracts; no decision is required to use the current MVP.

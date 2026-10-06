# 172X Data Intelligence

An evidence-first analytical MVP under staged construction. M1 provides a public
Python package, strict engineering gate and versioned source/SQL-intent contracts.
The Cloudflare Agent, Python execution, Workers AI and web chat are planned in
the [delivery plan](docs/mvp-delivery-plan.md). The original
[architecture](docs/architecture.md) remains the design reference.

Use Python >=3.12, [uv](https://docs.astral.sh/uv/) and Make:

```sh
make install
uv run python -c 'from data_intel.contracts import SourceIdentity, SqlIntent'
make gate
make coverage
```

`make install` and `make sync` use `uv sync --all-extras --dev`; `uv.lock` pins
public application and developer dependencies. The editable `src/data_intel`
package needs no private 172X dependency, service or credentials. There is no
environment configuration or running server yet.

Use `make format`, `lint`, `typecheck`, `test`, `complexity` or `coverage` for
focused checks. `make gate` runs Ruff formatting/linting, strict mypy, pytest,
Radon reporting and an enforcement script that rejects C+ function or average
complexity, including function-local/nested classes, closures and the gate script itself. CI
installs the frozen lock with Python 3.12 and invokes this same gate. Coverage
reports measured package and checker line/branch coverage; no percentage acceptance threshold
is defined.

Enforcement discovers every synchronous/asynchronous function and class in the
Python AST, asks Radon's `cc_visit_ast` API for each declaration's score, and
computes their arithmetic mean once per declaration across `src`, `tests` and
`scripts`. Each score and the mean must be <=10 (A/B). This includes nested and
function-local class methods that the default Radon report can omit; the
canonical `src tests` reporting command remains part of the gate.

The external boundary in `contracts.py` accepts version `"1"`, only source IDs
`sales`/`support`, a lowercase 64-hex SHA-256 and a meaning revision of 1–64 ASCII
characters matching `[a-z][a-z0-9._-]*`. Declared source identity does not prove
fixture existence, source integrity or provenance. `SqlIntent` preserves exact
question/SQL text, requires a non-whitespace character and bounds them to
1–2,000 / 1–8,000 characters; `max_rows` is a strict integer from 1–1,000. Models
reject undeclared fields and are frozen. These are schema limits, not measured
execution budgets.

SQL is an untrusted proposal. Schema acceptance does not establish read-only
safety, authorization, dialect compatibility or executability, even for a
supported source ID. No query executes in M1. Later milestones must enforce the
approved-data and execution boundaries before using these payloads.

M2's first fixture foundation bundles six synthetic sales/return lines in
`data_intel/fixtures/sales-proof.csv`. `load_sales_fixture()` in `sales_fixture.py`
reads at most 304 bytes, verifies the pinned 303-byte SHA-256 source, then validates
the exact schema, six unique IDs, ISO calendar dates and signed 64-bit measures.
An optional `SourceIdentity` must match the server registry before reading; source
selection and client hashes cannot authorize other data. Missing or invalid data
raises a safe `FixtureError`. Rows and computed count/date-range profile are immutable;
the profile contains no bulk records. Fields explicitly define net returns, USD
cents, valid zero and UTC calendar dates with half-open period boundaries. This
fixture is also included in the built Python wheel.

```sh
uv run python -c 'from data_intel.sales_fixture import load_sales_fixture; print(load_sales_fixture().profile)'
```

M3-P1 adds the separate 24-row [synthetic sales demo](docs/fixtures/sales-demo.md).
`load_sales_demo()` verifies the server-owned `sales-demo.v1` identity, exact
1,025-byte hash manifest and strict immutable rows. It preserves returns, paired
zero measures, net USD cents and fixture order. This loader returns no profile
and does not register the demo with the existing proof query engine or Agent.

```sh
uv run python -c 'from data_intel.sales_demo import load_sales_demo; print(len(load_sales_demo().rows))'
```

M3-P2a adds the strict frozen `DataProfileV2` sales receipt models in
`profile_models.py` and `canonical_profile_json()`. Counts are strict integers
from 0–256; exact unit/cents statistics are canonical signed-int64 decimal strings.
The complete receipt serializes as key-sorted UTF-8 JSON and refuses over 4,096
bytes without trimming. Schema acceptance and serialization do not authenticate
source bytes or compute statistics. The foundation adds no query capability or
service route.

M3-P2b's `profile_sales_demo()` in `sales_profile.py` loads the approved demo and
computes whole-source count/date/null/dimension facts and exact unit/cents
count/min/max/sum. Dimensions are sorted, show at most eight labels each and
report omitted counts. The fixed omissions describe excluded rows, samples,
distributions and uncomputed statistics. `profile_payload_sha256()` hashes the
bounded canonical payload without changing its version-2 fields. A 100-ms
monotonic deadline starts before loading, checks each record and before success;
the 256-record, signed-int64 and complete 4,096-byte output ceilings refuse
without partial results. These are defensive limits, not measured deployed
latency. The profile advertises the implemented private query capability;
analytical validation remains false.

```sh
uv run python -c 'from data_intel.sales_profile import profile_sales_demo; print(profile_sales_demo().measures)'
```

M3-P2c enables generic demo SQL through the trusted Python constructor
`SQLiteQueryEngine(allow_demo_source=True)`. Each intent selects one full approved
proof/demo identity before file access, in a fresh isolated in-memory context;
the unchanged SQLite policy and result limits apply to both. Receipts retain
the actual SQL/hash and selected source/schema. The default constructor remains
proof-only and rejects the demo before opening a context, preserving the current
v1 service and TypeScript consumers. A later private v2 caller must explicitly
opt in; this slice adds no route or model integration. SQL/result correctness
does not establish analytical approval.

M3-P3 adds the pinned 16-message [synthetic support source](docs/fixtures/support-demo.md).
`load_support_demo()` returns immutable typed messages, the full `support-demo.v1`
identity, schema and field meanings after verifying the exact byte/hash/count
manifest and bounded strict JSONL. It preserves original text and UTC timestamps;
source content remains untrusted. Search, support profiling and service exposure
are later slices.

```sh
uv run python -c 'from data_intel.support_demo import load_support_demo; print(len(load_support_demo().rows))'
```

The private `_sales_context.py` module opens a fresh literal `:memory:` database only
after the verified loader succeeds, loads the fixed sales schema with bound values,
then installs the private read-only, authorizer, limit and progress controls. Its
context manager closes the owned connection after success or failure; tests verify
source metadata, exact fixture rows and independently known SQL totals. SQLite
connection or setup errors fail as the safe `runtime_incompatible` classification.
The private `_bounded_result.py` foundation validates already-fetched scalar rows,
converts them to immutable exact cell values, and computes bounded canonical JSON
and SHA-256 content. It does not execute SQL, create receipts, or serve external
callers. The private `query_engine.py` now adds a reusable `QueryEngine` protocol
and local SQLite implementation for generic read-only sales SQL. It verifies the
requested source before opening a fresh database, requires an authorized sales
read for each query, and returns exact SQL/hash plus complete bounded result
content with a clear unvalidated status. Execution is capped at 20 rows and
returns only fixed safe error codes. Ambiguous empty-column reads do not prove a
physical source, so bare `count(*)` queries must use `main.sales`; CTEs named
`sales` cannot satisfy source authorization. The private `service_contracts.py`
adapter validates version-1 requests and exact typed results, including hashes,
cell encoding, the complete 16,384-byte result envelope and explicit runtime
provenance. Local parity
tests execute the existing engine; deployed service execution remains unverified.
The private Python Worker now routes GET `/health`, GET `/metadata`, and bounded
POST `/query` over a service binding. Health probes the SQLite policy, metadata
returns the pinned sales source and field meanings, and query executes only the
approved fixture with typed receipts and safe error codes. The Worker rejects
oversized streamed bodies before JSON parsing; no public route is configured.
Local service tests pass, but deployed service-binding behavior remains unverified.
Full profiling, support retrieval, analytical/citation validation, persistence,
model calls, UI and deployment remain planned. Cloudflare Python/SQLite
compatibility and deployed controls are unverified. Follow [TODO.md](TODO.md) for
the next bounded capability. Full GO permits
continuing the approved milestones; each retains its report and independent gates.

The private Python Worker scaffold in `workers/tools/` uses Python >=3.13 for
Cloudflare's current Pywrangler packaging while the analytical package supports
Python >=3.12. It declares the local analytical package and Cloudflare Worker
tooling in its own `pyproject.toml` and `uv.lock`, disables public Worker URLs and
preview URLs,
and reads its own version-metadata binding and injected `BUILD_REVISION`. Unknown
routes answer 404; missing deployed provenance answers 503. The private query
route is locally verified only and has no Agent caller or deployed SQL proof yet.

From a **clean committed checkout** with the locked Worker dev tools installed,
run `make python-worker-dry-run` to package without uploading. The helper refuses
dirty/untracked source, installs the pinned local Wrangler 4.127.1 with `npm ci`,
passes the exact checkout revision as `BUILD_REVISION`, and runs Pywrangler from
`workers/tools/` against its Wrangler config. It requires the reviewed Pyodide
`pylock.toml` and fails if Pywrangler regenerates it or if the temporary dry-run
bundle omits the entrypoint, `data_intel`, `workers`, `pydantic`, or the
`pydantic_core` native module. The temporary bundle is removed afterward.
Each build forces Pywrangler to refresh the local analytical package and checks
that every committed `src/data_intel` Python source file matches the vendored
bundle; Pywrangler's
ordinary timestamp check does not track local source edits.
The older Wrangler 4.11.1 returned a false-success bundle without vendored
modules; use the pinned package and lockfile. Deployed runtime controls still
need a reviewed probe.

The [Agent wire foundation](workers/agent/README.md) adds pinned TypeScript tooling,
strict private Python response validation, exact hash parity and bounded JSON
stream helpers. `make gate` also runs its clean npm install, typecheck and Vitest
tests through `make typescript-gate`. Native Agent routing, sessions, private
service calls and Wrangler/deployment configuration belong to the next reviewed slice.

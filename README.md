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

Generic SQL execution, full profiling, support retrieval, numerical/citation validation,
persistence, model calls, UI and deployment are planned. Follow [TODO.md](TODO.md)
for the next bounded capability. Full GO permits continuing the approved milestones;
each retains its report and independent delivery gates.

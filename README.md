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
package needs no private 172X dependency, service or credentials. M1 has no
environment configuration or running server.

Use `make format`, `lint`, `typecheck`, `test`, `complexity` or `coverage` for
focused checks. `make gate` runs Ruff formatting/linting, strict mypy, pytest,
Radon reporting and an enforcement script that rejects C+ function or average
complexity, including function-local/nested classes, closures and the gate script itself. CI
installs the frozen lock with Python 3.12 and invokes this same gate. Coverage
reports measured package and checker line/branch coverage; no percentage acceptance threshold
is defined.

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

There are no datasets, profiler, retrieval, numerical/citation validator,
persistence, model calls, UI or deployment yet. Follow [TODO.md](TODO.md) for the
next bounded capability; each milestone ends at a reviewed report and user checkpoint.

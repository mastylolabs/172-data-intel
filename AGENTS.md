# AGENTS.md

## Purpose and ownership

These mandatory rules define how code in this repository is engineered: its
design, structure, typing, tests, documentation, and engineering quality gate.
The Python standards below apply to Python code. The review and delivery
constraints apply to all repository code.

The **172X workflows**, including dev-loop, define how work moves through agents,
stages, review, and delivery. They own task handoffs, branch creation, naming and
lifecycle, commit sequencing, pushing, PR creation and review, merging, and branch
deletion, subject to the repository constraints below. This file does not
duplicate workflow commands or grant authority for external actions.
Workflows must honor these engineering standards and review constraints;
workflow approval does not replace engineering validation.

## Commit message convention

Use **Conventional Commits 1.0.0** for all repository commit messages. Before
composing a commit message, read and follow the
[official specification](https://www.conventionalcommits.org/en/v1.0.0/).

- Use `type: description` or `type(scope): description`, with an optional scope
  describing the affected part of the repository.
- Use lowercase types that accurately describe the change: `feat` for new
  features, `fix` for bug fixes, `docs` for documentation, and other appropriate
  types such as `refactor`, `test`, `chore`, `build`, `ci`, `perf`, or `style`.
- Keep the description concise and specific. Add a body or footers when useful,
  following the specification's formatting rules.
- Mark breaking changes with `!` before the colon or a `BREAKING CHANGE:` footer,
  and explain the breaking behavior.
- For the initial architecture and engineering-guidance documents, use
  `docs: add initial architecture and engineering guidelines`.

This section defines message format; the 172X dev-loop owns commit sequencing
and delivery.

## Reviewable delivery

- Before implementation, record the logical deliverables, bounded milestones,
  dependencies, acceptance criteria, and proposed PR boundaries in a concise
  project delivery plan. Give each milestone one coherent capability or useful
  foundation. A milestone may require several PRs; do not treat the entire
  application as one milestone or prescribe a fixed PR count.
- Give each PR one coherent, independently testable change. Include its relevant
  tests and documentation, and keep unrelated cleanup in a separate change.
- Target **200–300 changed lines of handwritten code per PR**. Smaller changes are
  welcome when complete. Allow **301–400** only when the additional scope makes
  the change coherent; explain the reason in the PR description.
- **Never exceed 400 changed lines of handwritten code in one PR.** Count added
  plus deleted lines across the entire PR diff, including source code, tests,
  scripts, and handwritten configuration. Count Python and TypeScript alike.
- Exclude generated files, dependency lockfiles, bundled datasets, and prose
  documentation from the code budget. Identify these exclusions and review them
  on their own merits. Keep documentation focused.
- Measure the diff after normal formatting. Do not compress code, omit required
  tests, or move handwritten code into excluded files to meet the limit. If a
  change exceeds the budget, revise the boundaries and deliver smaller complete
  increments.
- Every PR must build and pass the applicable repository quality checks.
  Record its scope, acceptance evidence, code-line count, exclusions, and
  dependencies in the PR description. Independent QA and configured bot review
  must inspect the current head; changes require fresh affected checks and review.
- Within an approved milestone, merge each PR through the 172X guarded merge
  process after engineering checks, independent QA, and configured provider bot
  approval pass on the current head and the required review findings are resolved.
  Do not require routine human approval for each PR. Preserve provider gates and
  branch protection; never bypass a failing check or review requirement.
- If the user explicitly asks to inspect a particular PR before merging, hold
  only that PR until the user releases the hold.
- Begin dependent implementation only after its prerequisite contracts are
  reviewed and merged. Independent slices may proceed in parallel when their
  inputs are stable. Deployment requires its own authorization.

## Milestone reports

Complete the milestone's acceptance checks and confirm that its implementation
PRs have merged into `main`. Save a concise report under `docs/milestones/` with:

- Delivered behavior, links to the merged PRs, and the verified `main` revision.
- Problems encountered, their resolutions, and remaining issues or limitations.
- The hardest technical problem, the chosen solution, and the reason for it.
- Measured unit-test coverage, test counts and results, and important coverage gaps.
- Integration and deployed test results, including failed or unrun checks and reasons.
- The next proposed milestone and any decisions needed from the user.

Use actual evidence; do not invent coverage or claim pending checks passed.
Report a blocked or incomplete milestone honestly. After presenting the report,
pause for the user's instruction before starting the next milestone. The user
may inspect merged PRs and request corrections; handle those findings through
focused follow-up PRs with the same verification and review requirements.

## Engineering principles

- Prioritize correctness, clarity, simplicity, and explicit behavior.
- Write typed, testable, maintainable code that is safe to refactor and documented
  where needed.
- Prefer composition over inheritance and polymorphism when it simplifies design.
- Avoid unnecessary abstraction, speculative architecture, and clever code that
  hides behavior.
- Keep changes focused on the requested task; avoid unrelated refactors.

## Python and tooling

- Use **Python >= 3.12**.
- Use **uv** for dependency management and the project build workflow.
- Use **Ruff** for formatting and linting, **mypy** for static type checking,
  **pytest** for tests, and **Radon** for cyclomatic complexity analysis.
- Treat `pyproject.toml` as the source of truth for metadata and tool configuration.
- Do not introduce Poetry, Pipenv, Hatch, PDM, or setuptools-heavy workflows unless
  explicitly instructed.

## Project structure and repository files

Use a `src/` layout, with tests outside the package:

```text
projectname/
  AGENTS.md
  README.md
  TODO.md
  Makefile
  pyproject.toml
  uv.lock
  .gitignore
  .env.example       # When environment variables are used
  src/
    projectname/
      __init__.py
  tests/
```

For larger systems, introduce clear package boundaries such as `config`, `models`,
`services`, `repositories`, `clients`, and `protocols`, with focused exceptions and
logging modules. Organize tests into `unit`, `integration`, and `fixtures` when
useful; do not create empty layers just to match a template.

Use specific module names. Avoid vague names such as `utils.py`, `helpers.py`,
`stuff.py`, `manager.py`, and `processor.py`; a necessary utility module should
describe its purpose, such as `time_utils.py` or `validation_utils.py`.

Keep `TODO.md` actionable and accurate as project task context, including planned
work, blockers, and decisions where useful. The dev-loop owns when and how task
tracking participates in its stages.

Provide a useful `Makefile` with focused targets for environment setup, formatting,
linting, type checking, tests, complexity, and the quality gate. Use
`uv sync --all-extras --dev` for `install`/`sync`. `make gate` must run the complete
gate below; individual targets must not define a weaker acceptance standard.
Add focused run, coverage, or cleanup targets as needed.

Ignore Python caches, virtual environments, test/type/lint caches, coverage and
build artifacts, local data, secrets, logs, and editor files. At minimum:

```gitignore
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
.coverage.*
htmlcov/
build/
dist/
*.egg-info/
.env
.env.*
!.env.example
.DS_Store
.idea/
.vscode/
*.log
```

Track `uv.lock` for applications. For a reusable library, make and document an
intentional lockfile decision. Never accidentally ignore source files or tests.

## Typing and data models

- Annotate every function and method, including explicit parameter and return
  types. Use precise collection types, especially in public interfaces.
- Avoid `Any` unless necessary. Justify type-checking suppressions and scope them
  to the specific error; do not weaken type checking to make code pass.
- Prefer `Protocol` for structural interfaces and lightweight polymorphism. Use
  inheritance or abstract base classes only when they provide a clear benefit.
- Prefer `dataclass(frozen=True, slots=True)` for internal value objects,
  Pydantic `BaseModel` for external input/output validation, and `Enum`/`StrEnum`
  for finite sets of values.
- Use `TypedDict` for dictionary-shaped external data when Pydantic is unnecessary.
- Validate external inputs and convert payloads into typed models at application
  boundaries; avoid passing raw dictionaries through multiple layers.

## Design, function size, and complexity

Keep services small, composable, and testable. CLI/API adapters call services;
services coordinate use cases; repositories handle persistence; clients handle
external APIs; models define data contracts; pure functions implement business
rules. Keep business logic out of route handlers, CLI scripts, notebooks,
connector/client classes, and configuration files.

Function and method size limits:

- Prefer 10–35 lines; aim for no more than 50 lines.
- When approaching 50 lines, consider refactoring; justify functions over 50 lines
  or refactor them.
- Do not exceed 100 lines. Rare exceptions, such as simple declarative tables or
  generated code, must be documented; avoid generated code when possible.

Extract pure helpers, validation, and transformations; use guard clauses to reduce
nesting. Replace large conditional chains with mappings, explicit rule functions,
or small strategy objects only when this improves clarity. Keep business rules
named and independently testable; do not hide complexity in one-liners.

Radon acceptance thresholds are defined once in the quality gate below.

## Linting and formatting

Use Ruff's configured rules without excessive ignores. Do not disable broad rule
categories to make code pass. Add `# noqa` only for a strong reason, include the
exact rule code, and explain the reason when it is not obvious.

## Testing

Add or update pytest tests for every meaningful behavior change. Tests must be
clear and behavior-oriented, with descriptive names and coverage of happy paths,
edge cases, malformed inputs, failure paths, and boundary conditions. Test pure
business logic thoroughly.

Mock external services, network calls, databases, filesystems, APIs, and time when
needed; do not mock simple pure functions. Use fixtures only when they improve
readability, and avoid large fixtures that obscure what a test needs.

## Errors, logging, secrets, and configuration

- Catch specific exceptions; never use bare `except:` or silently swallow errors.
  Use domain-specific exceptions where useful and preserve context with exception
  chaining. Fail clearly for invalid inputs and fast for invalid configuration.
- Use structured logging where practical, with component, operation, request or
  correlation ID, safe entity ID, and error context when available.
- Never expose secrets in errors or logs: API keys, passwords, tokens, private
  keys, and full authorization headers. Log sensitive personal data only when
  explicitly required and safe.
- Avoid `print` in library code; it is appropriate for CLI presentation.
- Use environment variables for secrets and environment-specific values. Do not
  hardcode credentials, private URLs, tokens, or private keys, and never commit
  real secrets.
- Document required environment variables in `.env.example` using placeholders,
  and validate configuration at startup.

## Dependencies

Avoid unnecessary dependencies and heavy frameworks. Before adding a dependency,
consider whether the standard library or an existing dependency solves the problem,
whether the addition materially reduces complexity, whether it is maintained, and
how it affects testing. Prefer small, well-maintained dependencies with a clear
purpose.

## Documentation

Keep documentation accurate, concise, and aligned with implemented behavior.
`README.md` must cover purpose, installation, quickstart, common commands, the
quality gate, basic architecture, and configuration. Update it when installation,
commands, configuration, architecture, or public behavior changes.

For larger systems, maintain focused documentation such as `docs/architecture.md`,
`docs/development.md`, `docs/configuration.md`, and `docs/testing.md`. Label planned
features as planned; do not describe them as implemented.

## Tool configuration baseline

Use the following baseline when creating or updating `pyproject.toml`; adapt
package names and dependency versions to the project without weakening these
standards:

```toml
[project]
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = [
    "mypy>=1.0",
    "pytest>=8.0",
    "radon>=6.0",
    "ruff>=0.8",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "C4", "ARG", "PTH", "RUF"]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-q"
```

## Single engineering quality gate

Before declaring work complete, run `make gate`. Its canonical checks, also usable
directly when a Makefile is unavailable, are:

```sh
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
uv run radon cc src tests -s -a
```

All checks must pass. Fix formatting with `uv run ruff format .` (or `make format`)
before rerunning the gate. If any check fails, fix the issue and rerun the entire
gate. Missing tools or configuration are blockers, not evidence of a passing gate.

Radon thresholds:

- Average complexity: **A preferred, B acceptable, C or worse unacceptable**.
- Function-level complexity: **A preferred, B acceptable**; refactor C or worse
  unless a specific reason is documented.

Radon's reporting command does not itself enforce these thresholds through its
exit status. Inspect its output and apply the thresholds explicitly. When CI is
added, it must run the same gate and enforce the complexity thresholds as well as
failing on formatting, linting, typing, or test errors. Do not maintain a separate,
weaker CI gate.

Passing tool checks does not replace the design, testing, security, and
documentation requirements above. The 172X workflow owns independent review and
guarded delivery. Milestone reports provide the user checkpoint; this gate
supplies the repository's engineering readiness evidence.

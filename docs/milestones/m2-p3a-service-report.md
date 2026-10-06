# M2 P3a service-boundary report

Status: **complete for the bounded local/private service slice**. This report
does not claim deployed Python execution, service-binding compatibility, a native
Agent, or Workers AI success.

## Delivered behavior

The private Python Worker now exposes only `GET /health`, `GET /metadata`, and
bounded `POST /query`. It loads the verified synthetic sales fixture, returns
authoritative schema/profile metadata, executes read-only generic SQL through the
existing SQLite policy, and returns typed receipts or stable safe errors. The
Worker validates its own deployed provenance, keeps public and preview routes
disabled, caps streamed bodies at 16,384 bytes, and maps Pyodide stream failures
to `unsupported_transport` without exposing runtime details.

Implementation PRs:

- [PR #13](https://github.com/mastylolabs/172-data-intel/pull/13) fixed forced
  local-package vendoring, exact source-byte checks, and post-build provenance
  fencing.
- [PR #15](https://github.com/mastylolabs/172-data-intel/pull/15) added the
  shared typed stream boundary and committed FFI/boundary regression tests.
- [PR #14](https://github.com/mastylolabs/172-data-intel/pull/14) delivered the
  private service contracts, routes, Worker adapter, and route tests.

All three PRs passed independent QA, current-head review, configured provider
approval, and guarded merge. Verified `main` revision: `95fc811d2de156dd34228a05b39aaa94222432d2`.

## Evidence

- `make gate`: 249 tests passed; Ruff format/lint and strict mypy passed; Radon
  average A `2.9187`, enforced average `2.89`, with no C+ blocks.
- `make coverage`: 249 tests; 92.2680% line, 88.9474% branch, 91.6149%
  combined coverage. `service_routes` combined coverage was 87.3239% and the
  shared transport boundary 94.7368%.
- Independent boundary probes covered exact body limits, malformed and unsafe
  SQL, unsupported sources/versions, typed integer/real/text/null results,
  result/envelope overflow, health/fixture failures, and all four Pyodide stream
  failure phases with sanitized responses.
- Clean `make python-worker-dry-run`: pinned Pywrangler 1.17.6 and Wrangler
  4.127.1, 201 bundled modules, 6,725.37 KiB (gzip 1,809.55 KiB), exact source
  bytes, unchanged runtime lock, exact committed revision, and no upload.

## Problems and remaining limits

An initial successful dry run reused stale local-package vendoring and omitted a
new route module. PR #13 added forced synchronization and exact byte checks. The
review then identified a provenance race during the build and a Pyodide
`JsException` transport gap; post-build revision fencing and the shared reader in
PR #15 closed both findings. A transient GitHub Internal Server Error delayed one
push but cleared on retry. No permission failure or automatic review rejection
blocked delivery.

The dry run is local packaging evidence. No private Worker upload, deployed
service-binding call, SQLite control probe, Durable Object, Agent, or Workers AI
call was run in P3a. The previously recorded free-only Llama preflight quota
failure remains a failure and was not converted into success. Coverage measures
the `data_intel` and configured script sources; the Worker entrypoint is
mocked/excluded from that source selection. Gaps are the defensive serialization,
fixture/adapter failure branches, and some empty body paths; independent probes
exercised these without changing the measured suite.

## Hardest technical problem

The hardest problem was preserving truthful build and transport provenance across
the Python/Worker boundary. Timestamp-based vendoring could produce a successful
artifact that did not contain the current source, and a source change during the
build could make the reviewed revision label false. Forced synchronization,
exact source-byte comparison, runtime-lock preservation, and the post-build clean
revision/HEAD check in PR #13 make those failures explicit. PR #15's small shared
reader then keeps runtime FFI failures inside the typed transport boundary. This
keeps the service
contract reusable for the Agent bridge without claiming that local packaging is
deployed execution.

## Next milestone

P3b should add the restricted native Agent and Durable Object proof bridge: private
service binding, operator-only `/proof/*` routes, persistent isolated session
state, bounded budgets, cancellation/idempotency fences, and an engine-only proof
receipt. It should deploy the reviewed private tools first and record actual
service/version/provenance receipts before P4 attempts Llama 3.3. The deployed
runtime and service-binding checks remain the next acceptance decision; no billing
or paid LLM allowance is authorized.

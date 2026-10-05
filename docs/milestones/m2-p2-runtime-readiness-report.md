# M2-P2: Python service and Worker build readiness

Status: **complete for the bounded P2 scope**, 2026-10-05 UTC. This is an
intermediate M2 report; the deployed Agent → Python → Workers AI proof remains
unverified and is not claimed complete.

## Delivered behavior and merge evidence

- [PR #10](https://github.com/mastylolabs/172-data-intel/pull/10) adds the typed
  private Python request/result adapter, exact cell encodings, hashes, response
  limits, and explicit runtime provenance. It merged through the guarded process
  at `7148d44e78af13c146a0a63b48249c11c0bef3f8`.
- [PR #11](https://github.com/mastylolabs/172-data-intel/pull/11) adds the private
  non-public Python Worker scaffold, version-metadata/build-revision fence,
  tracked Pyodide lock, pinned Wrangler package, clean-revision dry-run helper,
  and required-bundle inspection. It merged at verified `main` revision
  **`7d4d5c18dde7a155dfa4b504140e100299bd357b`**.
- The Worker has no public or preview URL and no query, Agent, or Workers AI
  route. Build output requires the Worker’s own `CF_VERSION_METADATA.id` and a
  committed 40-hex `BUILD_REVISION`; invalid deployed provenance fails closed.

## Problems and resolutions

The first adapter review found mutated-result tests validating Python dictionaries
instead of the JSON wire path; the tests now use JSON validation. QA then found
that the full serialized result envelope could exceed 16,384 bytes even when its
canonical content was below the limit; the adapter now rejects that result and
has a regression test.

The first Worker helper ran from the repository root, so Wrangler could miss its
nested configuration. It now runs from `workers/tools`. A dry run with old
Wrangler 4.11.1 returned success while omitting vendored modules; the helper now
installs pinned Wrangler 4.127.1 from the committed Node lock and fails unless
the temporary dry-run output contains the entrypoint, `data_intel`, Workers SDK,
Pydantic, and native Pydantic core. A clean run then produced 199 vendored
modules and exited at `--dry-run` without uploading.

## Tests and coverage

On merged `main`, `make gate` passed with 232 tests, Ruff, strict mypy across 22
files, and Radon average A (enforced average 2.99). `make coverage` passed with
92% aggregate line/branch coverage; `worker_build.py` measured 84%. The exact
clean Worker dry run used Pywrangler 1.17.6 and pinned Wrangler 4.127.1, produced
199 vendored modules (~6.7 MiB), preserved the tracked Pyodide lock, and exposed
the intended metadata bindings with a hidden build revision. No upload or
Cloudflare deployment occurred.

Important gaps are the small CLI wrapper (0% direct coverage), rare malformed
encoding branches, and all target-runtime/service-binding behavior. Mocked
entrypoint tests do not prove Pyodide imports or a deployed Worker.

## Remaining issues and next milestone

The hardest P2 problem was distinguishing a successful Wrangler exit from a
complete Worker bundle. Inspecting a temporary output directory and requiring
the imported package files solved that false-success case while keeping dry runs
non-uploading. Wrangler and Pyodide are now pinned for this local build path, but
the Cloudflare target runtime and service-binding SQLite controls remain
unverified.

Next: **M2-P3**, a reviewed private Service Binding and native Agent bridge that
executes the existing generic SQLite engine through `/proof/sql`, records actual
deployed Python/Agent provenance and control receipts, persists isolated source
and session state, and keeps the Worker non-public. Workers AI remains a separate
P4 step; the earlier free-allocation Llama preflight failed with HTTP 429 and no
paid billing or credits were enabled.

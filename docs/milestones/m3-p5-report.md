# M3-P5 numeric validator milestone report

## Delivered behavior and merged revision

PR #40, [add deterministic numeric validation](https://github.com/mastylolabs/172-data-intel/pull/40), and PR #41, [validate numeric differences and rankings](https://github.com/mastylolabs/172-data-intel/pull/41), are merged into `main`. The verified revision is `5c789f147f9703ed8da4af154b5fe7c79535a93e`.

The validator accepts strict nested exact-integer claims and recomputes direct cells, sums, differences, profile measures, and deterministic customer rankings from approved receipts. It binds receipt IDs, payload hashes, source identity, units, grouped rows and references, and refuses fabricated metadata, unsupported SQL, non-exact values, malformed calculations, and grouped sums outside the supported scope.

## Problems and resolutions

Review found flat-versus-nested wire-shape drift, self-attested receipt and unit associations, complexity above the gate, and grouped claims that could reference a different customer. The merged fixes use the frozen nested DTO, source-derived units, receipt and payload binding, bounded grouped SQL, row-to-group checks, and focused mutation tests. Batch validation remains a separate slice and is not represented as implemented.

## Hardest technical problem

The hardest issue was associating a claim with the exact row or group it described. The validator now derives the accepted grouping shape from the immutable receipt, checks every referenced row against `scope.group`, recomputes differences from named receipt cells, and verifies the complete ordered result before accepting a rank. Cross-group references and grouped whole-result sums fail closed.

## Tests, coverage, and gaps

The merged head passes 577 Python tests and 40 Vitest tests. `make gate` passes formatting, lint, mypy, pytest, Radon (A/B only; enforced average 3.02), TypeScript typecheck, and Vitest. `make coverage` reports 93% branch-aware total coverage (1,458 statements, 408 branches; 82 statements and 39 branch partials missed); `validation.py` measures 84% branch-aware coverage.

Independent QA and local review passed the exact merged head. The v2 producer/envelope, deployed runtime parity, batch limits, P6 citations, Agent state, browser flow, live Workers AI, and Cloudflare preview/final deployment remain unverified.

## Next milestone

Implement the P6 citation validator and tests for exact returned support IDs, quote substrings, hashes, source/receipt binding, targeted-coverage limits, and safe refusal of prevalence or absence claims. Then implement the additive P7 Python v2 service envelopes before Agent and UI integration.

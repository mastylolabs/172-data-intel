# M4 model contracts milestone report

## Delivery

PR [#59](https://github.com/mastylolabs/172-data-intel/pull/59) is merged into
`main`. The verified main revision is
`46779e6b0889cb952867b936cff94bd0411199cb`.

The application now has strict Analyst proposal, grounded candidate, independent
Validator verdict, and published-answer contracts. Candidate claims bind to
approved source identities, exact result hashes, deterministic calculations and
verified calculation input receipts. Publication requires deterministic success,
complete Validator claim coverage, a canonical candidate digest, Validator call
identity and policy revision. Targeted support answers use a closed message-ID
and exact-quote grammar; the only no-hit form is a standalone statement tied to
an empty, scoped search result. Unsupported numeric support claims, broad
prevalence/absence wording, fabricated inputs and mixed no-hit/citation answers
are refused.

## Problems and resolutions

Independent review found and the final head corrected numeric value/unit drift,
unbounded integer text, incomplete calculation input sets, missing per-input
source/hash checks, candidate/verdict reuse, broad targeted-search wording,
false no-hit receipts and mixed no-hit/citation claims. The final PR stayed at
the 400-line handwritten hard cap by keeping the contract and adversarial tests
as one bounded correctness boundary.

The following remain deliberately downstream: direct numeric cell evidence,
strict runtime DTO validation for the in-memory evidence context, full receipt
filter-scope binding and the permanent no-hit regression test recommended by
review. These are inputs to Agent orchestration and the next focused hardening
slice, not deployment claims for this milestone.

## Verification evidence

- Independent QA: PASS on exact head `37beac089147dc9257b608da2c1e094a5c1ed15e`.
- Independent review: APPROVED local recommendation on the exact head; no
  blocking findings remain.
- App: 33 tests across four files; coverage 88.88% statements, 83.59% branches,
  90.07% functions and 93.63% lines.
- Repository gate: `make gate` passed with 669 Python tests, 48 Agent tests and
  33 app tests; Ruff, mypy and Radon average complexity A (3.13148) passed.
- Wrangler dry-run passed with the existing `MvpAppAgent`, private `TOOLS`
  binding, version metadata and fail-closed tools provenance variables.
- Diff budget: exactly 400 handwritten lines (294 source, 106 tests); README
  and lockfiles were excluded under `AGENTS.md`.
- Deployed/live checks: not run. Workers AI, Agent publication, browser UI,
  Durable Object restart and Cloudflare request smoke tests are non-goals of
  this contract PR and remain unverified.

## Hardest technical problem

The hardest problem was preventing natural-language support answers from
turning one targeted lexical hit into a corpus claim. A deny-word list was
insufficient because equivalent percentage, scarcity and frequency wording
could evade it. The final contract uses a closed rendering: a support claim is
exactly `Message M###: "quote"`, and the answer text is exactly the ordered
claim rendering. A separate no-hit rendering is allowed only for a zero-count,
scoped receipt with no returned hits, and it cannot be combined with another
claim. This makes the safe publication surface small enough for deterministic
checks while preserving exact source evidence.

## Next milestone

Implement the bounded Workers AI planner gateway described in
`.git/172x/m4-model-gateway-brief.md`, then integrate it into the native Agent
job state with free-only admission and truthful clarification/failure handling.
After those reviewed slices, add candidate/Validator orchestration, browser chat,
preview deployment and final live smoke tests. No decision is needed from the
user under the existing full authorization; live LLM evidence remains
conditional on the free Workers AI allowance and must never enable paid billing.

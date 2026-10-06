# M3-P3 support loader milestone report

## Result

M3-P3 is complete and merged in [PR #33](https://github.com/mastylolabs/172-data-intel/pull/33). The repository now loads the exact 16-message synthetic support corpus through a strict immutable JSONL boundary. It verifies the complete `support-demo.v1` identity before file access, the 3,091-byte manifest and SHA-256, 16 unique message IDs, canonical UTC timestamps, bounded labels/text, duplicate JSON keys, framing, encoding, record and line ceilings, and safe `FixtureError` classifications. The merged `main` revision is `9c05a53a9f9d41558c0a79d9706b277ef9604a02`.

The loader preserves exact source text as untrusted content and grants no search or analytical capability. Search, profiles, service exposure, validation, model calls, UI and deployment remain separate work.

## Verification

- Current-head CI passed twice: runs `37413170248` and `37413179842`.
- Independent QA PASS: local receipt `.git/172x/m3-p3-qa.md` (not committed; implementation/provider evidence is on [PR #33](https://github.com/mastylolabs/172-data-intel/pull/33)). Fresh detached gate passed 466 Python tests and 40 Vitest tests, strict mypy, Ruff/format, TypeScript and Radon A (average 2.9685; all functions A/B).
- Independent review PASS: local receipt `.git/172x/m3-p3-review.md` (not committed); no MF, NH or Q findings. Provider review and approval are recorded on [PR #33](https://github.com/mastylolabs/172-data-intel/pull/33).
- Loader coverage is 100% locally (86/86 statements, 24/24 branches); CI measured 98.26% for the loader because Python 3.12 did not execute the defensive hour-24 timestamp rejection path. Combined QA coverage is 94.0735%; existing gaps remain in later execution/service/build paths.
- Independent reference-byte and standard-library checks reproduced 3,091 bytes, SHA-256 `c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536`, 16 rows, 11 support/5 billing channels, four messages per customer, exact timestamps and source text.
- Scope count: 359 handwritten changed lines; 52 README/TODO/docs prose lines and 16 fixture data lines are excluded under AGENTS.md. No new dependency or service/model/UI/deployment change.

## Problems and limits

Python versions differ in how they parse an invalid hour-24 timestamp. The loader uses an explicit canonical round-trip check, and the defensive rejection is fully covered locally; CI truthfully records the unvisited branch rather than claiming 100%. No implementation defect or review finding remains. Search ranking, whole-corpus limitations, citation validation and deployed behavior are unverified.

## Hardest technical problem

The hardest part was preserving exact untrusted support text while rejecting parser ambiguities and malformed JSON safely. The loader uses duplicate-aware JSON decoding, strict Pydantic models, canonical timestamp round-tripping, Unicode/control and byte bounds, an immutable row container, a fixed packaged path and manifest authorization before parsing. This makes later lexical search auditable without treating message content as instructions or evidence of prevalence.

## Next milestone

Proceed with the next bounded M3 capability: targeted lexical search over this approved corpus. It will enforce the frozen `SearchRequestV2` limits, deterministic tokenization/ranking, exact complete quotes, message IDs, filter-scoped counts, a five-hit/8,192-byte receipt ceiling, a 100 ms deadline, and explicit limitations that targeted hits do not establish trends, prevalence or absence. The user’s existing full-go authorization covers continuation; this remains a separately reviewed milestone with its own QA, report and merge gates.

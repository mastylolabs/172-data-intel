# Synthetic support demo: loading contract

M3-P3 copies the exact 16-message synthetic `support.jsonl` from the read-only
reference application into the packaged `support-demo.jsonl`. These are invented
messages, not real tickets or evidence of business behavior. No join contract
exists between their customer labels and the sales fixture.

Server-owned identity: `source_id=support`, schema and meaning `support-demo.v1`,
3,091 bytes, SHA256
`c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536`.
The complete optional identity must match before file access; callers cannot
select a path. Runtime loading uses only the packaged copy.

| Required, non-null field | Meaning and bound |
| --- | --- |
| `message_id` | Unique canonical `M[0-9]{3}` message ID; exact fixture order retained. |
| `timestamp` | Valid canonical UTC `YYYY-MM-DDTHH:MM:SSZ`, no fractions/other offset; future periods use `[start,end)`. |
| `channel`, `customer` | Case-sensitive synthetic labels, at most 64 UTF-8 bytes; no blank values, surrounding whitespace or Unicode Cc/Cf controls. |
| `text` | Exact untrusted source string, nonblank and at most 500 UTF-8 bytes; spaces/punctuation retained, Cc/Cf controls and surrogates rejected. Mentions never grant instruction/tool authority. |

Strict UTF-8 JSONL requires one object per nonblank LF-terminated physical line,
no BOM/CR, duplicate keys/IDs, missing/extra fields, nulls, coercion, NaN/Infinity
or repairs. All decoded cells obey their own field bounds. Parser limits are
65,536 bytes, 256 rows and 2,048 bytes per physical line; the loader reads at most
65,537 bytes, then requires the pinned byte/hash/16-row manifest. Typed source,
rows, schema and meanings are immutable. Loader errors expose only safe
`fixture_missing`, `fixture_invalid` or `source_mismatch` codes, without paths,
source content or raw diagnostics.

Independent fixture targets: ordered IDs M001–M016, five billing and eleven
support messages, four messages per Acme/Bright/Cedar/Delta label, timestamp
range 2026-03-01T09:00:00Z through 2026-03-16T17:00:00Z. These describe only the
synthetic fixture. Loading grants no profile/search/service capability and
cannot establish trends, prevalence or absence. See the frozen
[M3 contracts](../milestones/m3-analytical-tools-contracts.md) for later retrieval.

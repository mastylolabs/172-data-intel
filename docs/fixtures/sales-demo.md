# Synthetic sales demo: loading contract

M3-P1 bundles newly authored demonstration data, not observations of a real
business. Each of the 24 rows is one net sale/return line, not an order or customer.
The fixture has no join contract with support messages, customer master, causal
meaning, universal unit price, profit, tax or currency conversion.

Server-owned identity: `source_id=sales`, schema and meaning revision
`sales-demo.v1`, exactly 1,025 UTF-8 bytes and SHA-256
`a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f`.
The packaged basename is `sales-demo.csv`; callers cannot supply a path. An
optional request identity must match all four `SourceIdentity` fields before
file access. The existing six-row `sales-proof.v1` source, query engine and
service-v1 behavior remain separate. Demo loading grants no query, profile,
Agent or model capability.

| Required, non-null field | Meaning and validation |
| --- | --- |
| `sale_id` | Unique canonical `D[0-9]{3}` line ID; retain exact file order. |
| `sale_date` | Valid Gregorian UTC calendar day in exact `YYYY-MM-DD`; periods are `[start,end)`, without time/offset inference. |
| `customer`, `region`, `product` | Case-sensitive synthetic labels, each at most 64 UTF-8 bytes; no blank values, surrounding whitespace, Unicode Cc/Cf controls or normalization. |
| `units` | Signed net integer units; negatives are returns, zero is valid. |
| `revenue_cents` | Signed net USD cents; negatives are returns, zero is valid. Revenue is not calculated from a universal unit price. |

Both measures use canonical decimal `-?(0|[1-9][0-9]*)`, excluding `-0`, and
signed 64-bit bounds. No floats, exponent notation, plus signs, whitespace or
coercion; units and cents must agree in sign and zeros must be paired. The demo
model reuses the existing strict frozen sales field types, then adds its stricter
ID, label and paired-measure rules without modifying the proof model.

The loader reads at most 65,537 bytes, verifies the exact byte/hash manifest, and
returns immutable typed source/rows/schema/meanings only after strict parsing
and the exact 24-row count. CSV requires UTF-8 without BOM, LF only and final LF;
the seven-column header must match exactly in order. Parser ceilings are 65,536
bytes, 256 records, 2,048 bytes per physical line and 256 UTF-8 bytes per decoded
cell. Reject blank lines, multiline cells, malformed quoting, missing/extra
cells, duplicate IDs, invalid dates and unsupported values. Do not trim or repair
input. These ceilings do not authorize arbitrary data; only the pinned manifest
can load. Failures expose only `fixture_missing`, `fixture_invalid` or
`source_mismatch`, without paths, cells or parser diagnostics in the error text.

Independently stated fixture targets for verification: 29 net units and 395,000
net cents; January/February/March each have eight records, respectively 7/12/10
units and 105,000/140,000/150,000 cents. Dates span 2026-01-01 through 2026-03-31.
These are fixture oracles, not a deployed analytical or independent QA verdict.

```sh
uv run python -c 'from data_intel.sales_demo import load_sales_demo; print(len(load_sales_demo().rows))'
```

See the frozen [M3 contracts](../milestones/m3-analytical-tools-contracts.md)
for later profiling, explicit engine integration and private service evolution.

import { z } from "zod";

const bytes = (value: string): number => new TextEncoder().encode(value).length;
const unicode = (value: string): boolean =>
  Array.from(value).every((c) => c.codePointAt(0)! < 0xd800 || c.codePointAt(0)! > 0xdfff);
const text = (max: number) =>
  z
    .string()
    .min(1)
    .refine((s) => bytes(s) <= max && unicode(s));
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const revision = z
  .string()
  .regex(/^[a-f0-9]{40}$/)
  .nullable();
export const source = z.strictObject({
  version: z.literal("1"),
  source_id: z.literal("sales"),
  snapshot_sha256: z.literal("36ea7edc3c94c5df1320946f1fcefb6bc5c6e7252cf2242344ee70f168d78396"),
  meaning_revision: z.literal("sales-proof.v1"),
});
const runtimeFields = z.strictObject({
  python_version: text(32),
  sqlite_version: text(32),
  runtime_mode: z.enum(["local", "deployed"]),
  build_revision: revision,
  worker_version_id: z.uuid().nullable(),
});
export const runtime = runtimeFields.refine(
  (r) => r.runtime_mode === "local" || !!(r.build_revision && r.worker_version_id),
);
export const agentRuntime = runtimeFields
  .omit({ python_version: true, sqlite_version: true })
  .refine((r) => r.runtime_mode === "local" || !!(r.build_revision && r.worker_version_id));
const limits = z.strictObject({
  max_sql_bytes: z.literal(8000),
  max_rows: z.literal(20),
  max_columns: z.literal(16),
  max_column_bytes: z.literal(64),
  max_text_bytes: z.literal(256),
  max_result_bytes: z.literal(16384),
  progress_interval: z.literal(100),
  max_progress_callbacks: z.literal(500),
  query_deadline_ms: z.literal(250),
  sqlite_heap_bytes: z.literal(8388608),
  sqlite_limits: z.strictObject({
    sql_length: z.literal(8000),
    length: z.literal(65536),
    column: z.literal(16),
    expr_depth: z.literal(30),
    compound_select: z.literal(8),
    vdbe_op: z.literal(10000),
    function_arg: z.literal(8),
    attached: z.literal(0),
    like_pattern_length: z.literal(128),
    variable_number: z.literal(0),
    trigger_depth: z.literal(0),
  }),
});
const integer = z
  .string()
  .max(20)
  .regex(/^-?(0|[1-9][0-9]*)$/)
  .refine(
    (s) => /^-?(0|[1-9][0-9]*)$/.test(s) && BigInt(s) >= -(2n ** 63n) && BigInt(s) < 2n ** 63n,
  );
const cell = z.discriminatedUnion("type", [
  z.strictObject({ type: z.literal("integer"), value: integer, exact: z.literal(true) }),
  z.strictObject({
    type: z.literal("real"),
    value: text(64).refine(
      (s) => /^-?(\d+\.\d+|\d+(\.\d+)?e[+-]\d+)$/u.test(s) && Number.isFinite(Number(s)),
    ),
    exact: z.literal(false),
  }),
  z.strictObject({
    type: z.literal("text"),
    value: z.string().refine((s) => bytes(s) <= 256 && unicode(s)),
  }),
  z.strictObject({ type: z.literal("null"), value: z.null() }),
]);
export const metadata = z.strictObject({
  version: z.literal("1"),
  source,
  schema_revision: z.literal("sales-proof.v1"),
  table: z.literal("sales"),
  fields: z
    .array(
      z.strictObject({
        name: text(64),
        sql_type: z.enum(["TEXT", "INTEGER"]),
        nullable: z.literal(false),
        meaning: text(256),
      }),
    )
    .length(7),
  profile: z.strictObject({
    record_count: z.literal(6),
    date_min: z.iso.date(),
    date_max: z.iso.date(),
    statistics: z.literal("exact"),
  }),
  capabilities: z.tuple([z.literal("query")]),
  dialect: z.literal("sqlite"),
  engine_policy: z.literal("m2-sqlite.v1"),
  limits,
  runtime,
});
export const result = z
  .strictObject({
    version: z.literal("1"),
    receipt_id: z.uuid(),
    job_id: z.uuid(),
    source,
    schema_revision: z.literal("sales-proof.v1"),
    engine_policy: z.literal("m2-sqlite.v1"),
    actual_sql: text(8000),
    sql_sha256: digest,
    columns: z.array(text(64)).min(1).max(16),
    rows: z.array(z.array(cell)).max(20),
    row_count: z.number().int().min(0).max(20),
    result_sha256: digest,
    coverage: z.literal("complete_query_result"),
    truncated: z.literal(false),
    analytical_validated: z.literal(false),
    limits,
    runtime,
  })
  .refine(
    (r) =>
      r.row_count === r.rows.length &&
      new Set(r.columns).size === r.columns.length &&
      r.rows.every((row) => row.length === r.columns.length),
  );
export const sqlInput = z.strictObject({
  version: z.literal("1"),
  request_id: z.uuid(),
  question: z.string().min(1).max(2000).regex(/\S/u),
  sql: text(8000).regex(/\S/u),
  max_rows: z.number().int().min(1).max(20),
});
export const serviceError = z.strictObject({
  version: z.literal("1"),
  code: z.enum([
    "invalid_input",
    "unsupported_version",
    "not_found",
    "unsupported_transport",
    "unsafe_query",
    "invalid_query",
    "execution_limit",
    "invalid_result",
    "result_limit",
    "runtime_incompatible",
    "unsupported_source",
    "source_mismatch",
  ]),
  stage: z.enum(["input", "query", "transport"]),
  job_id: z.uuid().nullable(),
  limit: z.null(),
  provider_reason: z.null(),
  automatic_retry: z.literal(false),
});
export async function sha256(value: string): Promise<string> {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, "0")).join("");
}
export function canonicalResult(value: z.infer<typeof result>): string {
  return JSON.stringify({ columns: value.columns, rows: value.rows }, [
    "columns",
    "rows",
    "exact",
    "type",
    "value",
  ]);
}
export async function validatedResult(payload: unknown): Promise<z.infer<typeof result>> {
  const parsed = result.parse(payload);
  if (
    bytes(JSON.stringify(parsed)) > 16384 ||
    parsed.sql_sha256 !== (await sha256(parsed.actual_sql)) ||
    parsed.result_sha256 !== (await sha256(canonicalResult(parsed)))
  )
    throw new Error("invalid_result");
  return parsed;
}
export async function boundedJson(message: Request | Response, cap = 16384): Promise<unknown> {
  const reader = message.body?.getReader();
  if (!reader) throw new Error("invalid_input");
  const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: false });
  let content = "",
    size = 0;
  try {
    for (;;) {
      const chunk = await reader.read();
      if (chunk.done) return JSON.parse(content + decoder.decode());
      size += chunk.value.byteLength;
      if (size > cap) throw new Error("result_limit");
      content += decoder.decode(chunk.value, { stream: true });
    }
  } catch (error) {
    try {
      await reader.cancel();
    } catch {
      // Cancellation is best effort; preserve the original parse/size/FFI failure.
    }
    throw error;
  } finally {
    reader.releaseLock();
  }
}

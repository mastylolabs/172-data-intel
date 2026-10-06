import { z } from "zod";
import { bound, payloadSha256, SafeError, unicode } from "./policy";

export const text = (maximum: number): z.ZodType<string> => z.string().refine((value) =>
  unicode(value) && /[^\p{White_Space}]/u.test(value) &&
  new TextEncoder().encode(value).byteLength <= maximum);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const buildRevision = z.string().regex(/^[a-f0-9]{40}$/);
const uuid = z.uuid().refine((value) => value === value.toLowerCase());
const label = text(64).refine((value) =>
  value === value.trim() && !/[\p{Cc}\p{Cf}]/u.test(value));
const timestamp = z.iso.datetime({ precision: 0 }).refine((value) =>
  !value.startsWith("0000") && Number.isFinite(Date.parse(value)) &&
  new Date(value).toISOString() === value.replace("Z", ".000Z"));
const wireString = (maximum: number): z.ZodType<string> => z.string().refine((value) =>
  unicode(value) && new TextEncoder().encode(value).byteLength <= maximum);
const nonBlank = (maximum: number): z.ZodType<string> => wireString(maximum).refine((value) =>
  /\S/u.test(value));
const count = z.number().int().min(0).max(256);
const integerText = z.string().regex(/^(?:0|-?[1-9][0-9]*)$/).refine((value) => {
  try { return BigInt(value) >= -(2n ** 63n) && BigInt(value) <= 2n ** 63n - 1n; }
  catch { return false; }
});
const sourceSales = z.strictObject({
  version: z.literal("1"), source_id: z.literal("sales"),
  snapshot_sha256: z.literal("a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f"),
  meaning_revision: z.literal("sales-demo.v1"),
});
const sourceSupport = z.strictObject({
  version: z.literal("1"), source_id: z.literal("support"),
  snapshot_sha256: z.literal("c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536"),
  meaning_revision: z.literal("support-demo.v1"),
});
const dateOnly = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine((value) => {
  const date = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
});
const labelValue = (maximum: number): z.ZodType<string> => wireString(maximum).refine((value) =>
  value.trim() === value && value.trim().length > 0 && !/[\p{Cc}\p{Cf}]/u.test(value));
const boundedText = (maximum: number): z.ZodType<string> => wireString(maximum).refine((value) =>
  value.trim().length > 0 && !/[\p{Cc}\p{Cf}]/u.test(value));

const catalogSales = z.strictObject({
  source: sourceSales, schema_revision: z.literal("sales-demo.v1"),
  profile_revision: z.literal("m3-profile.v1"), kind: z.literal("structured"),
  display_name: z.literal("Sales demo"),
  description: z.literal("Synthetic net sales lines for bounded structured analysis."),
  capability_help: z.strictObject({
    profile: z.literal("Summarize fields and bounded statistics."),
    query: z.literal("Ask for read-only totals, groups, rankings or period comparisons."),
  }), capabilities: z.tuple([z.literal("profile"), z.literal("query")]),
  record_count: z.literal(24), manifest_bytes: z.literal(1025),
  scope: z.literal("complete_immutable_fixture"),
});
const catalogSupport = z.strictObject({
  source: sourceSupport, schema_revision: z.literal("support-demo.v1"),
  profile_revision: z.null(), kind: z.literal("messages"),
  display_name: z.literal("Support messages"),
  description: z.literal("Synthetic support messages for targeted lexical examples."),
  capability_help: z.strictObject({
    search: z.literal("Find matching messages with exact IDs and source quotes; hits do not establish prevalence."),
  }), capabilities: z.tuple([z.literal("search")]),
  record_count: z.literal(16), manifest_bytes: z.literal(3091),
  scope: z.literal("complete_immutable_fixture"),
});
const catalogEntry = z.union([catalogSales, catalogSupport]);
export const catalogV2 = z.strictObject({
  version: z.literal("2"), catalog_revision: z.literal("m4-catalog.v1"),
  entries: z.array(catalogEntry).length(2).refine((entries) =>
    new Set(entries.map((entry) => entry.source.source_id)).size === 2),
});
export type CatalogV2 = z.infer<typeof catalogV2>;

const profileField = z.strictObject({
  name: wireString(4096), sql_type: z.enum(["TEXT", "INTEGER"]), nullable: z.literal(false),
  meaning: wireString(4096), null_count: count,
});
const profileDimension = z.strictObject({
  field: wireString(4096), distinct_count: count, values: z.array(wireString(4096)).max(8),
  omitted_value_count: count,
});
const profileMeasure = z.strictObject({
  field: wireString(4096), unit: z.enum(["net_units", "USD_cents"]), count,
  min: integerText.nullable(), max: integerText.nullable(), sum: integerText, exact: z.literal(true),
});
export const dataProfileV2 = z.strictObject({
  version: z.literal("2"), source: sourceSales, schema_revision: z.literal("sales-demo.v1"),
  profile_revision: z.literal("m3-profile.v1"), fields: z.array(profileField), record_count: count,
  range_start: dateOnly.nullable(), range_end: dateOnly.nullable(), dimensions: z.array(profileDimension),
  measures: z.array(profileMeasure),
  omissions: z.tuple([z.literal("bulk_rows"), z.literal("row_samples"), z.literal("distributions"), z.literal("uncomputed_statistics")]),
  capabilities: z.array(z.enum(["query", "search"])), analytical_validated: z.literal(false),
});
export type DataProfileV2 = z.infer<typeof dataProfileV2>;

const queryRuntime = z.strictObject({
  python_version: nonBlank(32), sqlite_version: nonBlank(32), runtime_mode: z.enum(["local", "deployed"]),
  build_revision: buildRevision.nullable(), worker_version_id: uuid.nullable(),
}).refine((value) => value.runtime_mode === "local" ||
  (value.build_revision !== null && value.worker_version_id !== null));
const integerCell = z.strictObject({ type: z.literal("integer"), value: integerText, exact: z.literal(true) });
const canonicalFloat = (number: number): string => {
  if (Object.is(number, -0)) return "-0.0";
  const absolute = Math.abs(number);
  if (absolute >= 1e16 || absolute < 1e-4) {
    return number.toExponential().replace(/e([+-])(\d)$/, "e$1" + "0$2");
  }
  return Number.isInteger(number) ? `${number}.0` : number.toString();
};
const realCell = z.strictObject({ type: z.literal("real"), value: wireString(64).refine((value) => {
  const number = Number(value);
  return Number.isFinite(number) && value === canonicalFloat(number);
}), exact: z.literal(false) });
const textCell = z.strictObject({ type: z.literal("text"), value: wireString(256) });
const nullCell = z.strictObject({ type: z.literal("null"), value: z.null() });
const queryCell = z.discriminatedUnion("type", [integerCell, realCell, textCell, nullCell]);
const sqliteLimits = z.strictObject({
  sql_length: z.literal(8000), length: z.literal(65536), column: z.literal(16), expr_depth: z.literal(30),
  compound_select: z.literal(8), vdbe_op: z.literal(10000), function_arg: z.literal(8), attached: z.literal(0),
  like_pattern_length: z.literal(128), variable_number: z.literal(0), trigger_depth: z.literal(0),
});
const queryLimits = z.strictObject({
  max_sql_bytes: z.literal(8000), max_rows: z.literal(20), max_columns: z.literal(16),
  max_column_bytes: z.literal(64), max_text_bytes: z.literal(256), max_result_bytes: z.literal(16384),
  progress_interval: z.literal(100), max_progress_callbacks: z.literal(500), query_deadline_ms: z.literal(250),
  sqlite_heap_bytes: z.literal(8388608), sqlite_limits: sqliteLimits,
});
export const queryResultV2 = z.strictObject({
  version: z.literal("2"), receipt_id: uuid, job_id: uuid, source: sourceSales,
  schema_revision: z.literal("sales-demo.v1"), engine_policy: z.literal("m2-sqlite.v1"),
  actual_sql: nonBlank(8000), sql_sha256: digest, columns: z.array(nonBlank(64)).min(1).max(16),
  rows: z.array(z.array(queryCell).max(16)).max(20), row_count: z.number().int().min(0).max(20),
  result_sha256: digest, coverage: z.literal("complete_query_result"), truncated: z.literal(false),
  analytical_validated: z.literal(false), limits: queryLimits, runtime: queryRuntime,
}).refine((value) => value.row_count === value.rows.length &&
  new Set(value.columns).size === value.columns.length &&
  value.rows.every((row) => row.length === value.columns.length));
export type QueryResultV2 = z.infer<typeof queryResultV2>;

const asciiTokens = (value: string): string[] => Array.from(new Set(value.toLowerCase().match(/[a-z0-9]+/g) ?? [])).sort();
const searchToken = z.string().regex(/^[a-z0-9]{1,32}$/);
const searchRequest = z.strictObject({
  version: z.literal("2"), source: sourceSupport, query: boundedText(128), channel: labelValue(64).nullable(),
  customer: labelValue(64).nullable(), start: timestamp.nullable(), end: timestamp.nullable(),
  max_hits: z.number().int().min(1).max(5),
}).refine((value) => {
  const tokens = asciiTokens(value.query);
  return tokens.length >= 1 && tokens.length <= 8 && tokens.every((token) => searchToken.safeParse(token).success) &&
    (value.start === null || value.end === null || value.start < value.end);
});
const searchHit = z.strictObject({
  message_id: z.string().regex(/^M[0-9]{3}$/), timestamp, channel: labelValue(64), customer: labelValue(64),
  score: z.number().int().min(1).max(8), matched_tokens: z.array(searchToken).min(1).max(8),
  quote: boundedText(500),
}).refine((value) => value.matched_tokens.every((token, index, all) =>
  (index === 0 || all[index - 1] < token) && value.score === all.length));
const limitations = z.tuple([
  z.literal("Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence."),
  z.literal("No hits means this lexical query found no matching messages in the declared filtered scope."),
]);
export const searchReceiptV2 = z.strictObject({
  version: z.literal("2"), source: sourceSupport, schema_revision: z.literal("support-demo.v1"),
  search_policy: z.literal("m3-lexical.v1"), request: searchRequest, scanned_count: count,
  matched_count: count, returned_count: z.number().int().min(0).max(5), omitted_hit_count: count,
  hits: z.array(searchHit).max(5), coverage: z.literal("targeted_lexical_search"), limitations,
  analytical_validated: z.literal(false),
}).refine((value) => value.source.source_id === value.request.source.source_id &&
  value.scanned_count >= value.matched_count && value.matched_count >= value.returned_count &&
  value.returned_count === value.hits.length && value.returned_count === Math.min(value.matched_count, value.request.max_hits) &&
  value.omitted_hit_count === value.matched_count - value.returned_count &&
  new Set(value.hits.map((hit) => hit.message_id)).size === value.hits.length &&
  value.hits.every((hit) => hit.matched_tokens.every((token) => asciiTokens(value.request.query).includes(token))));
export type SearchReceiptV2 = z.infer<typeof searchReceiptV2>;
export type SearchRequestV2 = z.infer<typeof searchRequest>;
export const queryCellV2 = queryCell;
export const searchRequestV2 = searchRequest;

export type DomainPayload = CatalogV2 | DataProfileV2 | QueryResultV2 | SearchReceiptV2;
export type DomainKind = "catalog" | "profile" | "query" | "search";
const domainSchemas: Record<DomainKind, z.ZodType<DomainPayload>> = {
  catalog: catalogV2, profile: dataProfileV2, query: queryResultV2, search: searchReceiptV2,
};
const domainMaximum: Record<DomainKind, number> = { catalog: 4096, profile: 4096, query: 16384, search: 8192 };
async function sha256Text(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(bytes), (item) => item.toString(16).padStart(2, "0")).join("");
}
export async function validatedQueryResultV2(value: unknown): Promise<QueryResultV2> {
  try {
    const query = queryResultV2.parse(value);
    if (await sha256Text(query.actual_sql) !== query.sql_sha256 ||
      await payloadSha256({ columns: query.columns, rows: query.rows }) !== query.result_sha256) {
      throw new SafeError("invalid_result");
    }
    return query;
  } catch (error) {
    if (error instanceof SafeError) throw error;
    throw new SafeError("invalid_result");
  }
}
export async function validatedDomainEnvelope(kind: DomainKind, value: unknown): Promise<Envelope<DomainPayload>> {
  const envelope = await validatedEnvelope(domainSchemas[kind], value, domainMaximum[kind]);
  const identifiers = [envelope.job_id, envelope.run_id, envelope.receipt_id];
  const catalog = kind === "catalog";
  if (catalog !== identifiers.every((identifier) => identifier === null) ||
    (!catalog && !identifiers.every((identifier) => identifier !== null))) throw new SafeError("invalid_result");
  if (!catalog && kind === "search" &&
    (!("source" in envelope.payload) || envelope.payload.source.source_id !== "support")) {
    throw new SafeError("invalid_result");
  }
  if (kind === "query" && (!("receipt_id" in envelope.payload) ||
    envelope.receipt_id !== envelope.payload.receipt_id ||
    !("job_id" in envelope.payload) || envelope.job_id !== envelope.payload.job_id)) {
    throw new SafeError("invalid_result");
  }
  if (kind === "query") {
    await validatedQueryResultV2(envelope.payload);
  }
  return envelope;
}
export const approvedSource = z.discriminatedUnion("source_id", [
  z.strictObject({
    version: z.literal("1"),
    source_id: z.literal("sales"),
    snapshot_sha256: z.literal("a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f"),
    meaning_revision: z.literal("sales-demo.v1"),
  }),
  z.strictObject({
    version: z.literal("1"),
    source_id: z.literal("support"),
    snapshot_sha256: z.literal("c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536"),
    meaning_revision: z.literal("support-demo.v1"),
  }),
]);
export type Source = z.infer<typeof approvedSource>;
export const questionInput = z.strictObject({
  version: z.literal("2"),
  request_id: uuid,
  question: text(1024),
});
export function plannerProposal(source: Source): z.ZodType<{
  status: "plan" | "clarify";
  mode: "profile" | "query" | "search" | "clarify";
  sql: string | null;
  query: string | null;
  channel: string | null;
  customer: string | null;
  start: string | null;
  end: string | null;
  question: string | null;
}> {
  const selected = approvedSource.parse(source);
  return z.strictObject({
    status: z.enum(["plan", "clarify"]),
    mode: z.enum(["profile", "query", "search", "clarify"]),
    sql: text(8000).nullable(),
    query: text(128).nullable(),
    channel: label.nullable(),
    customer: label.nullable(),
    start: timestamp.nullable(),
    end: timestamp.nullable(),
    question: text(512).nullable(),
  }).refine((value) => {
    const unfiltered = [value.channel, value.customer, value.start, value.end].every((v) => v === null);
    const noTools = value.sql === null && value.query === null;
    if (value.status === "clarify") {
      return value.mode === "clarify" && value.question !== null && noTools && unfiltered;
    }
    if (value.question !== null) return false;
    if (value.mode === "profile") return selected.source_id === "sales" && noTools && unfiltered;
    if (value.mode === "query") {
      return selected.source_id === "sales" && value.sql !== null && value.query === null && unfiltered;
    }
    return value.mode === "search" && selected.source_id === "support" && value.query !== null &&
      value.sql === null && (value.start === null || value.end === null || value.start < value.end);
  });
}
const runtime = z.strictObject({
  python_version: text(32),
  sqlite_version: text(32),
  runtime_mode: z.enum(["local", "deployed"]),
  build_revision: z.string().regex(/^[a-f0-9]{40}$/).nullable(),
  worker_version_id: uuid.nullable(),
  service_contract_revision: z.literal("m4-service.v1"),
}).refine((value) => value.runtime_mode === "local" ||
  (value.build_revision !== null && value.worker_version_id !== null));
export type Envelope<T> = {
  version: "2";
  job_id: string | null;
  run_id: string | null;
  receipt_id: string | null;
  payload: T;
  payload_sha256: string;
  runtime: z.infer<typeof runtime>;
};
export async function validatedEnvelope<T>(
  payload: z.ZodType<T>, value: unknown, maximumPayload: number,
): Promise<Envelope<T>> {
  try {
    bound(value, 16_384);
    const envelope = z.strictObject({
      version: z.literal("2"),
      job_id: uuid.nullable(),
      run_id: uuid.nullable(),
      receipt_id: uuid.nullable(),
      payload: z.unknown(),
      payload_sha256: digest,
      runtime,
    }).parse(value);
    const identifiers = [envelope.job_id, envelope.run_id, envelope.receipt_id];
    if (identifiers.some((id) => id === null) && identifiers.some((id) => id !== null)) {
      throw new SafeError("invalid_result");
    }
    bound(envelope.payload, maximumPayload);
    if (await payloadSha256(envelope.payload) !== envelope.payload_sha256) {
      throw new SafeError("invalid_result");
    }
    const parsed = payload.parse(envelope.payload);
    if (await payloadSha256(parsed) !== envelope.payload_sha256) {
      throw new SafeError("invalid_result");
    }
    return { ...envelope, payload: parsed };
  } catch (error) {
    if (error instanceof SafeError) throw error;
    throw new SafeError("invalid_result");
  }
}

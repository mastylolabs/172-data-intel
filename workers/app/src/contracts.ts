import { z } from "zod";
import { bound, payloadSha256, SafeError, unicode } from "./policy";

export const text = (maximum: number): z.ZodType<string> => z.string().refine((value) =>
  unicode(value) && /[^\p{White_Space}]/u.test(value) &&
  new TextEncoder().encode(value).byteLength <= maximum);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const uuid = z.uuid().refine((value) => value === value.toLowerCase());
const label = text(64).refine((value) =>
  value === value.trim() && !/[\p{Cc}\p{Cf}]/u.test(value));
const timestamp = z.iso.datetime({ precision: 0 }).refine((value) =>
  !value.startsWith("0000") && Number.isFinite(Date.parse(value)) &&
  new Date(value).toISOString() === value.replace("Z", ".000Z"));
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

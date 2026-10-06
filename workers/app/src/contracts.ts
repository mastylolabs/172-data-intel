import { z } from "zod";
import { bound, payloadSha256, SafeError, unicode } from "./policy";

export const text = (maximum: number): z.ZodType<string> => z.string().refine((value) =>
  unicode(value) && /[^\p{White_Space}]/u.test(value) &&
  new TextEncoder().encode(value).byteLength <= maximum);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const uuid = z.uuid().refine((value) => value === value.toLowerCase());
export const approvedSource = z.discriminatedUnion("source_id", [
  z.strictObject({
    version: z.literal("1"), source_id: z.literal("sales"),
    snapshot_sha256: z.literal("a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f"),
    meaning_revision: z.literal("sales-demo.v1"),
  }),
  z.strictObject({
    version: z.literal("1"), source_id: z.literal("support"),
    snapshot_sha256: z.literal("c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536"),
    meaning_revision: z.literal("support-demo.v1"),
  }),
]);
export type Source = z.infer<typeof approvedSource>;
export const questionInput = z.strictObject({ version: z.literal("2"), request_id: uuid, question: text(1024) });
export function plannerProposal(source: Source): z.ZodType<{
  status: "plan" | "clarify"; sql: string | null; query: string | null; question: string | null;
}> {
  const selected = approvedSource.parse(source);
  return z.strictObject({
    status: z.enum(["plan", "clarify"]), sql: text(8000).nullable(),
    query: text(128).nullable(), question: text(512).nullable(),
  }).refine((value) => value.status === "clarify"
    ? value.question !== null && value.sql === null && value.query === null
    : value.question === null && (selected.source_id === "sales"
      ? value.sql !== null && value.query === null : value.query !== null && value.sql === null));
}
const runtime = z.strictObject({
  python_version: text(32), sqlite_version: text(32), runtime_mode: z.enum(["local", "deployed"]),
  build_revision: z.string().regex(/^[a-f0-9]{40}$/).nullable(), worker_version_id: uuid.nullable(),
  service_contract_revision: z.literal("m4-service.v1"),
}).refine((value) => value.runtime_mode === "local" ||
  (value.build_revision !== null && value.worker_version_id !== null));
type Envelope<T> = {
  version: "2"; job_id: string | null; run_id: string | null; receipt_id: string | null;
  payload: T; payload_sha256: string; runtime: z.infer<typeof runtime>;
};
export async function validatedEnvelope<T>(
  payload: z.ZodType<T>, value: unknown, maximumPayload: number,
): Promise<Envelope<T>> {
  try {
    bound(value, 16_384);
    const envelope = z.strictObject({
      version: z.literal("2"), job_id: uuid.nullable(), run_id: uuid.nullable(), receipt_id: uuid.nullable(),
      payload: z.unknown(), payload_sha256: digest, runtime,
    }).parse(value);
    const identifiers = [envelope.job_id, envelope.run_id, envelope.receipt_id];
    if (identifiers.some((id) => id === null) && identifiers.some((id) => id !== null)) {
      throw new SafeError("invalid_result");
    }
    bound(envelope.payload, maximumPayload);
    if (await payloadSha256(envelope.payload) !== envelope.payload_sha256) throw new SafeError("invalid_result");
    const parsed = payload.parse(envelope.payload);
    if (await payloadSha256(parsed) !== envelope.payload_sha256) throw new SafeError("invalid_result");
    return { ...envelope, payload: parsed };
  } catch (error) {
    if (error instanceof SafeError) throw error;
    throw new SafeError("invalid_result");
  }
}

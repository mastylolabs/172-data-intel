import { z } from "zod";
import {
  approvedSource,
  validatedDomainEnvelope,
  type DomainKind,
  type Envelope,
  type Source,
} from "./contracts";
import { unicode } from "./policy";

export interface ToolsBinding {
  fetch(request: Request): Promise<Response>;
}

export interface TransportEnv {
  TOOLS: ToolsBinding;
  RUNTIME_MODE: "local" | "deployed";
}

export type ResultKind = Exclude<DomainKind, "catalog">;

export class BridgeError extends Error {
  constructor(readonly code: string, readonly status = 400) {
    super(code);
  }
}

const version = z.literal("2");
const requestId = z.uuid().refine((value) => value === value.toLowerCase());
const text = (maximum: number): z.ZodType<string> => z.string().refine(
  (value) => unicode(value) && !/[\p{Cc}\p{Cf}]/u.test(value) && value.trim().length > 0 &&
    new TextEncoder().encode(value).byteLength <= maximum,
);
const label = (maximum: number): z.ZodType<string> => text(maximum).refine((value) => value.trim() === value);
const timestamp = z.iso.datetime({ precision: 0 }).refine(
  (value) => !value.startsWith("0000") && new Date(value).toISOString() === value.replace("Z", ".000Z"),
);

export const sourceRequest = z.strictObject({ version, source: approvedSource });
export const profileRequest = z.strictObject({ version, request_id: requestId });
export const queryRequest = z.strictObject({
  version,
  request_id: requestId,
  question: text(1024),
  sql: text(8000),
  max_rows: z.number().int().min(1).max(20),
});
export const searchRequest = z.strictObject({
  version,
  request_id: requestId,
  query: text(128),
  channel: label(64).nullable(),
  customer: label(64).nullable(),
  start: timestamp.nullable(),
  end: timestamp.nullable(),
  max_hits: z.number().int().min(1).max(5),
}).refine((value) => value.start === null || value.end === null || value.start < value.end);

export async function readBoundedText(
  body: ReadableStream<Uint8Array> | null,
  maximum: number,
  status: number,
): Promise<string> {
  const failureStatus = status === 413 ? 400 : status;
  if (body === null) throw new BridgeError(status === 413 ? "invalid_input" : "invalid_result", failureStatus);
  const reader = body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: false });
  const chunks: string[] = [];
  let total = 0;
  try {
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      total += part.value.byteLength;
      if (total > maximum) {
        await reader.cancel().catch(() => undefined);
        throw new BridgeError("result_limit", status);
      }
      chunks.push(decoder.decode(part.value, { stream: true }));
    }
    chunks.push(decoder.decode());
    return chunks.join("");
  } catch (error) {
    if (error instanceof BridgeError) throw error;
    await reader.cancel().catch(() => undefined);
    throw new BridgeError(status === 413 ? "invalid_input" : "invalid_result", failureStatus);
  } finally {
    reader.releaseLock();
  }
}

export async function readJson(request: Request, maximum = 16_384): Promise<unknown> {
  try {
    return JSON.parse(await readBoundedText(request.body, maximum, 413));
  } catch (error) {
    if (error instanceof BridgeError) throw error;
    throw new BridgeError("invalid_input");
  }
}

export function buildToolBody(
  kind: ResultKind,
  jobId: string,
  runId: string,
  source: Source,
  body: Record<string, unknown>,
): Record<string, unknown> {
  if (kind === "profile") return { version: "2", job_id: jobId, run_id: runId, source };
  if (kind === "query") {
    return {
      version: "2",
      job_id: jobId,
      run_id: runId,
      source,
      intent: { version: "1", source, question: body.question, sql: body.sql, max_rows: body.max_rows },
    };
  }
  return {
    version: "2",
    job_id: jobId,
    run_id: runId,
    source,
    query: body.query,
    channel: body.channel,
    customer: body.customer,
    start: body.start,
    end: body.end,
    max_hits: body.max_hits,
  };
}

function sameSource(left: Source, right: Source): boolean {
  return left.version === right.version && left.source_id === right.source_id &&
    left.snapshot_sha256 === right.snapshot_sha256 && left.meaning_revision === right.meaning_revision;
}

export async function executeTool(
  env: TransportEnv,
  kind: DomainKind,
  body: Record<string, unknown> | null,
  expected: { jobId: string; runId: string } | null,
): Promise<Envelope<unknown>> {
  const path = kind === "catalog" ? "/v2/catalog" : `/v2/${kind}`;
  const method = kind === "catalog" ? "GET" : "POST";
  let response: Response;
  try {
    response = await env.TOOLS.fetch(new Request(`https://tools${path}`, {
      method,
      headers: { "content-type": "application/json" },
      body: method === "POST" ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(5_000),
    }));
  } catch {
    throw new BridgeError("tool_unavailable", 502);
  }
  if (!response.ok) {
    await readBoundedText(response.body, 16_384, 502).catch(() => undefined);
    throw new BridgeError("tool_error", 502);
  }
  let payload: unknown;
  try {
    payload = JSON.parse(await readBoundedText(response.body, 16_384, 502));
  } catch (error) {
    if (error instanceof BridgeError) throw error;
    throw new BridgeError("invalid_result", 502);
  }
  try {
    const envelope = await validatedDomainEnvelope(kind, payload);
    const outbound = kind === "catalog" ? null : approvedSource.safeParse(body?.source);
    const payloadSource = kind === "catalog" || !("source" in envelope.payload)
      ? null : envelope.payload.source;
    const sourceMatches = kind === "catalog" || (
      outbound !== null && outbound.success && payloadSource !== null && sameSource(outbound.data, payloadSource)
    );
    const identityMatches = kind === "catalog" || (
      expected !== null && envelope.job_id === expected.jobId && envelope.run_id === expected.runId
    );
    if (env.RUNTIME_MODE !== envelope.runtime.runtime_mode || !identityMatches || !sourceMatches) {
      throw new Error("identity_or_runtime");
    }
    return envelope;
  } catch {
    throw new BridgeError("invalid_result", 502);
  }
}

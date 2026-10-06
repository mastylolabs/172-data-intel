import { z } from "zod";
import {
  analystProposal,
  type AnalystProposal,
} from "./model_contracts";
import {
  approvedSource,
  catalogV2,
  dataProfileV2,
  questionInput,
  type CatalogV2,
  type DataProfileV2,
  type Source,
} from "./contracts";
import { PLANNER } from "./prompts";

export const PLANNER_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast" as const;
export const PLANNER_PROMPT_REVISION = "m4-planner.v1" as const;
export const PLANNER_INPUT_BYTES = 12_288;
export const PLANNER_OUTPUT_BYTES = 8_192;
export const PLANNER_MAX_TOKENS = 512;
export const PLANNER_TIMEOUT_MS = 30_000;

const responseSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    version: { const: "1" }, request_id: { type: "string" },
    source: { type: "object", additionalProperties: false, properties: {
      version: { const: "1" }, source_id: { enum: ["sales", "support"] },
      snapshot_sha256: { type: "string" }, meaning_revision: { type: "string" },
    }, required: ["version", "source_id", "snapshot_sha256", "meaning_revision"] },
    status: { enum: ["plan", "clarify"] }, mode: { enum: ["profile", "query", "search", "clarify"] },
    sql: { anyOf: [{ type: "string", maxLength: 8000 }, { type: "null" }] },
    query: { anyOf: [{ type: "string", maxLength: 128 }, { type: "null" }] },
    channel: { anyOf: [{ type: "string", maxLength: 64 }, { type: "null" }] },
    customer: { anyOf: [{ type: "string", maxLength: 64 }, { type: "null" }] },
    start: { anyOf: [{ type: "string" }, { type: "null" }] },
    end: { anyOf: [{ type: "string" }, { type: "null" }] },
    clarification: { anyOf: [{ type: "string", maxLength: 512 }, { type: "null" }] },
  },
  required: ["version", "request_id", "source", "status", "mode", "sql", "query",
    "channel", "customer", "start", "end", "clarification"],
} as const;

export interface PlannerContext {
  request_id: string;
  question: string;
  source: Source;
  catalog: CatalogV2;
  profile: DataProfileV2 | null;
}
export type PlannerRequest = {
  messages: { role: "system" | "user"; content: string }[];
  response_format: { type: "json_schema"; json_schema: typeof responseSchema };
  max_tokens: number;
  temperature: number;
};
export interface ModelEnv { AI: Pick<Ai, "run">; }
type ProviderReason = "daily_free_allocation" | "account_limited" | "out_of_capacity" | "unknown";
type FailureCode = "execution_limit" | "model_output_invalid" | "model_quota" | "model_unavailable";
export type PlannerFailure = {
  kind: "failure";
  code: FailureCode;
  status: 413 | 429 | 502 | 503;
  provider_reason: ProviderReason | null;
  automatic_retry: false;
};
export type PlannerResult =
  | { kind: "success"; proposal: AnalystProposal; model: typeof PLANNER_MODEL; prompt_revision: typeof PLANNER_PROMPT_REVISION }
  | PlannerFailure;

class BoundaryError extends Error {
  constructor(readonly code: "execution_limit" | "model_output_invalid") { super(code); }
}
function sameSource(left: Source, right: Source): boolean {
  return left.source_id === right.source_id && left.snapshot_sha256 === right.snapshot_sha256 &&
    left.meaning_revision === right.meaning_revision;
}
function contextPayload(context: PlannerContext): Record<string, unknown> {
  const question = questionInput.parse({ version: "2", request_id: context.request_id, question: context.question });
  const source = approvedSource.parse(context.source);
  const catalog = catalogV2.parse(context.catalog);
  const profile = context.profile === null ? null : dataProfileV2.parse(context.profile);
  if (!catalog.entries.some((entry) => sameSource(entry.source, source)) ||
    (profile !== null && !sameSource(profile.source, source))) throw new BoundaryError("execution_limit");
  return { version: "1", request_id: question.request_id, question: question.question, source, catalog, profile };
}
export function buildPlannerRequest(context: PlannerContext): PlannerRequest {
  const payload = JSON.stringify(contextPayload(context));
  const request: PlannerRequest = {
    messages: [{ role: "system", content: PLANNER }, { role: "user", content: payload }],
    response_format: { type: "json_schema", json_schema: responseSchema },
    max_tokens: PLANNER_MAX_TOKENS, temperature: 0,
  };
  if (new TextEncoder().encode(JSON.stringify(request)).byteLength > PLANNER_INPUT_BYTES) {
    throw new BoundaryError("execution_limit");
  }
  return request;
}
function outputJson(raw: unknown): unknown {
  const serialized = JSON.stringify(raw);
  if (serialized === undefined || new TextEncoder().encode(serialized).byteLength > PLANNER_OUTPUT_BYTES) {
    throw new BoundaryError("model_output_invalid");
  }
  if (typeof raw !== "object" || raw === null || !("response" in raw)) {
    throw new BoundaryError("model_output_invalid");
  }
  const response = (raw as { response: unknown }).response;
  if (typeof response === "string") {
    if (new TextEncoder().encode(response).byteLength > PLANNER_OUTPUT_BYTES) throw new BoundaryError("model_output_invalid");
    try { return JSON.parse(response); } catch { throw new BoundaryError("model_output_invalid"); }
  }
  if (typeof response !== "object" || response === null) throw new BoundaryError("model_output_invalid");
  return response;
}
function parsePlannerOutput(raw: unknown, context: PlannerContext): AnalystProposal {
  const parsed = analystProposal.safeParse(outputJson(raw));
  if (!parsed.success || parsed.data.request_id !== context.request_id || !sameSource(parsed.data.source, context.source)) {
    throw new BoundaryError("model_output_invalid");
  }
  return parsed.data;
}
function failure(code: FailureCode, provider_reason: ProviderReason | null = null): PlannerFailure {
  const status = code === "execution_limit" ? 413 : code === "model_quota" ? 429 : code === "model_output_invalid" ? 502 : 503;
  return { kind: "failure", code, status, provider_reason, automatic_retry: false };
}
export function classifyModelError(error: unknown): PlannerFailure {
  const message = error instanceof Error ? error.message.toLowerCase() : "";
  const record = typeof error === "object" && error !== null ? error as Record<string, unknown> : {};
  const codes = [record.code, record.provider_code, record.provider_error_code,
    ...(Array.isArray(record.provider_error_codes) ? record.provider_error_codes.slice(0, 8) : [])];
  const code4006 = codes.some((code) => code === 4006 || code === "4006") || /\b4006\b/.test(message);
  const status429 = record.status === 429 || record.http_status === 429;
  if (code4006) return failure("model_quota", "daily_free_allocation");
  if (/daily\s+free\s+allocation|free\s+allocation/.test(message)) return failure("model_quota", "daily_free_allocation");
  if (status429 || /\b429\b|quota|rate\s*limit/.test(message)) return failure("model_quota");
  if (/\b3036\b|account\s*limit/.test(message)) return failure("model_unavailable", "account_limited");
  if (/\b3040\b|capacity|overload|timeout|unavailable|\b503\b|neurons/.test(message)) {
    return failure("model_unavailable", /\b3040\b|capacity|overload/.test(message) ? "out_of_capacity" : "unknown");
  }
  return failure("model_unavailable");
}
export async function runPlanner(
  env: ModelEnv,
  context: PlannerContext,
  timeoutMs = PLANNER_TIMEOUT_MS,
): Promise<PlannerResult> {
  let request: PlannerRequest;
  try { request = buildPlannerRequest(context); }
  catch (error) { return failure(error instanceof BoundaryError ? error.code : "execution_limit"); }
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new Error("planner_timeout")), Math.max(1, timeoutMs)); });
  try {
    const raw = await Promise.race([env.AI.run(PLANNER_MODEL, request), timeout]);
    return { kind: "success", proposal: parsePlannerOutput(raw, context), model: PLANNER_MODEL, prompt_revision: PLANNER_PROMPT_REVISION };
  } catch (error) {
    return error instanceof BoundaryError ? failure(error.code) : classifyModelError(error);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

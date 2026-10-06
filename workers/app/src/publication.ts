import { z } from "zod";
import {
  analystProposal, groundedCandidate, publishAnswer, publishedAnswer, validatorVerdict,
  TARGETED_LIMITATIONS, type CandidateCheck, type EvidenceContext, type GroundedCandidate, type PublicationOutcome,
} from "./model_contracts";
import { approvedSource, queryResultV2, searchReceiptV2, type Envelope } from "./contracts";
import { payloadSha256 } from "./policy";
import { VALIDATOR } from "./prompts";
import { PLANNER_MODEL } from "./model_gateway";

const VALIDATOR_INPUT_BYTES = 12_288;
const VALIDATOR_OUTPUT_BYTES = 8_192;
const VALIDATOR_MAX_TOKENS = 256;
const timestamp = (): string => new Date(Math.floor(Date.now() / 1000) * 1000).toISOString().replace(".000Z", "Z");
const digest = z.string().regex(/^[a-f0-9]{64}$/);
export const publicationLineage = z.strictObject({
  context_sha256: digest, receipt_ids: z.array(z.uuid()).min(1).max(4), calculation_ids: z.array(z.uuid()).max(4),
  hit_refs: z.array(z.string().regex(/^M[0-9]{3}$/)).max(12),
});
const evidenceContext = z.strictObject({
  results: z.array(z.strictObject({ receipt_id: z.uuid(), payload_sha256: digest, source: approvedSource, kind: z.enum(["query", "search"]), matched_count: z.number().int().min(0).max(256), scope: z.string().max(64) })).max(2),
  calculations: z.array(z.strictObject({ calculation_id: z.uuid(), result_ids: z.array(z.uuid()).min(1).max(4), source: approvedSource, value: z.string().regex(/^-?\d+$/), unit: z.enum(["net_units", "USD_cents"]), input_receipts: z.array(z.strictObject({ receipt_id: z.uuid(), payload_sha256: digest, source: approvedSource, kind: z.enum(["query", "search"]), matched_count: z.number().int().min(0).max(256), scope: z.string().max(64) })).max(4) })).max(2),
  hits: z.array(z.strictObject({ result_id: z.uuid(), message_id: z.string().regex(/^M[0-9]{3}$/), quote: z.string().max(500) })).max(5),
});
const execution = z.strictObject({ version: z.literal("2"), job_id: z.uuid(), run_id: z.uuid(), receipt_id: z.uuid(), payload: z.union([queryResultV2, searchReceiptV2]), payload_sha256: digest,
  runtime: z.strictObject({ python_version: z.string().max(32), sqlite_version: z.string().max(32), runtime_mode: z.enum(["local", "deployed"]), build_revision: z.string().regex(/^[a-f0-9]{40}$/).nullable(), worker_version_id: z.uuid().nullable(), service_contract_revision: z.literal("m4-service.v1") }) });
export const publicationEvidence = z.strictObject({ context: evidenceContext, execution });
export const publicationOutcome = z.discriminatedUnion("kind", [
  z.strictObject({ kind: z.literal("published"), answer: publishedAnswer }),
  z.strictObject({ kind: z.literal("refusal"), code: z.enum(["candidate_invalid", "deterministic_failed", "validator_failed"]) }),
  z.strictObject({ kind: z.literal("clarification"), question: z.string().max(512) }),
]);
export type ValidatorEnv = { AI: Pick<Ai, "run"> };
export type PublicationBuild = { candidate: GroundedCandidate; context: EvidenceContext };
export type ValidatorInput = { question: string; proposal: z.infer<typeof analystProposal>; context: EvidenceContext; execution: z.infer<typeof execution>; candidate: GroundedCandidate; deterministic: CandidateCheck };

function sourceEqual(left: GroundedCandidate["source"], right: GroundedCandidate["source"]): boolean {
  return left.source_id === right.source_id && left.snapshot_sha256 === right.snapshot_sha256 && left.meaning_revision === right.meaning_revision;
}
function result(receipt: Envelope<unknown>, kind: "query" | "search", matchedCount: number): EvidenceContext["results"][number] {
  return { receipt_id: receipt.receipt_id!, payload_sha256: receipt.payload_sha256, source: (receipt.payload as { source: GroundedCandidate["source"] }).source,
    kind, matched_count: matchedCount, scope: kind === "search" ? "declared filtered scope" : "complete query result" };
}
function buildQuery(proposal: z.infer<typeof analystProposal>, receipt: Envelope<unknown>): PublicationBuild | null {
  const query = queryResultV2.safeParse(receipt.payload);
  if (!query.success || query.data.rows.length !== 1 || query.data.columns.length !== 1) return null;
  const cell = query.data.rows[0][0];
  if (cell.type !== "integer") return null;
  const value = cell.value;
  const semantics = query.data.actual_sql.toLowerCase();
  const units = /\bsum\s*\(\s*(?:units|net_units)\s*\)/u.test(semantics);
  const cents = /\bsum\s*\(\s*revenue_cents\s*\)/u.test(semantics);
  if (units === cents) return null;
  const unit = units ? "net_units" as const : "USD_cents" as const;
  const text = `${value} ${unit === "USD_cents" ? "USD cents" : "net_units"}`;
  const evidence = result(receipt, "query", query.data.row_count);
  const calculation = { calculation_id: crypto.randomUUID(), result_ids: [evidence.receipt_id], source: proposal.source,
    value, unit, input_receipts: [evidence] };
  const candidate = groundedCandidate.parse({ version: "1", request_id: proposal.request_id, source: proposal.source,
    mode: "query", text, claims: [{ claim_id: "answer", kind: "numeric", text, value, unit, evidence: {
    type: "calculation", calculation_id: calculation.calculation_id, result_ids: calculation.result_ids, value, unit } }], limitations: [], created_at: timestamp() });
  return { candidate, context: { results: [evidence], calculations: [calculation], hits: [] } };
}
function buildSearch(proposal: z.infer<typeof analystProposal>, receipt: Envelope<unknown>): PublicationBuild | null {
  const search = searchReceiptV2.safeParse(receipt.payload);
  if (!search.success) return null;
  const evidence = result(receipt, "search", search.data.matched_count);
  if (search.data.hits.length === 0) {
    const text = TARGETED_LIMITATIONS[1];
    const candidate = groundedCandidate.parse({ version: "1", request_id: proposal.request_id, source: proposal.source,
      mode: "search", text, claims: [{ claim_id: "no_hit", kind: "statement", text, evidence: {
        type: "result", receipt_id: evidence.receipt_id, payload_sha256: evidence.payload_sha256, source: proposal.source,
        locator: "matched_count", unit: null } }], limitations: [...TARGETED_LIMITATIONS], created_at: timestamp() });
    return { candidate, context: { results: [evidence], calculations: [], hits: [] } };
  }
  const hits = search.data.hits.map((hit) => ({ result_id: evidence.receipt_id, message_id: hit.message_id, quote: hit.quote }));
  const claims = hits.map((hit, index) => ({ claim_id: `message_${index + 1}`, kind: "citation" as const,
    text: `Message ${hit.message_id}: "${hit.quote}"`, evidence: { type: "citation" as const, ...hit } }));
  const candidate = groundedCandidate.parse({ version: "1", request_id: proposal.request_id, source: proposal.source,
    mode: "search", text: claims.map((claim) => claim.text).join(" "), claims, limitations: [...TARGETED_LIMITATIONS], created_at: timestamp() });
  return { candidate, context: { results: [evidence], calculations: [], hits } };
}
export function buildPublication(proposalInput: unknown, receipt: Envelope<unknown>): PublicationBuild | null {
  const proposal = analystProposal.safeParse(proposalInput);
  const payloadSource = (receipt.payload as { source?: GroundedCandidate["source"] }).source;
  if (!proposal.success || proposal.data.status !== "plan" || payloadSource === undefined || !sourceEqual(proposal.data.source, payloadSource)) return null;
  return proposal.data.mode === "query" ? buildQuery(proposal.data, receipt) : proposal.data.mode === "search" ? buildSearch(proposal.data, receipt) : null;
}
export function buildEvidence(context: EvidenceContext, receipt: Envelope<unknown>): z.infer<typeof publicationEvidence> | null {
  const value = publicationEvidence.safeParse({ context, execution: receipt });
  return value.success ? value.data : null;
}
function validatorJson(raw: unknown): unknown {
  if (typeof raw !== "object" || raw === null || !("response" in raw)) return null;
  if (new TextEncoder().encode(JSON.stringify(raw)).byteLength > VALIDATOR_OUTPUT_BYTES) return null;
  const response = (raw as { response: unknown }).response;
  if (typeof response === "string") {
    if (new TextEncoder().encode(response).byteLength > VALIDATOR_OUTPUT_BYTES) return null;
    try { return JSON.parse(response); } catch { return null; }
  }
  return response;
}
export async function buildLineage(context: EvidenceContext): Promise<z.infer<typeof publicationLineage>> {
  return publicationLineage.parse({ context_sha256: await payloadSha256(context),
    receipt_ids: context.results.map((result) => result.receipt_id), calculation_ids: context.calculations.map((calculation) => calculation.calculation_id),
    hit_refs: context.hits.map((hit) => hit.message_id) });
}
export async function runValidator(env: ValidatorEnv, input: ValidatorInput): Promise<z.infer<typeof validatorVerdict> | null> {
  const body = JSON.stringify({ version: "1", question: input.question, proposal: input.proposal, evidence_context: input.context, execution_receipt: input.execution,
    candidate: input.candidate, deterministic_check: input.deterministic });
  const request = { messages: [{ role: "system" as const, content: VALIDATOR }, { role: "user" as const, content: body }],
    response_format: { type: "json_schema" as const, json_schema: { type: "object", additionalProperties: false,
      properties: { version: { const: "1" }, request_id: { type: "string" }, overall: { enum: ["pass", "fail", "needs_clarification"] }, deterministic_pass: { type: "boolean" }, candidate_sha256: { type: "string" }, validator_call_id: { type: "string" }, policy_revision: { const: "m4-validator.v1" }, claims: { type: "array", maxItems: 12 }, summary: { type: "string", maxLength: 512 } }, required: ["version", "request_id", "overall", "deterministic_pass", "candidate_sha256", "validator_call_id", "policy_revision", "claims", "summary"] } },
    max_tokens: VALIDATOR_MAX_TOKENS, temperature: 0 };
  if (new TextEncoder().encode(JSON.stringify(request)).byteLength > VALIDATOR_INPUT_BYTES) return null;
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const timeout = new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new Error("timeout")), 30_000); });
    const raw = await Promise.race([env.AI.run(PLANNER_MODEL, request), timeout]);
    const value = validatorVerdict.safeParse(validatorJson(raw));
    if (!value.success || value.data.request_id !== input.candidate.request_id || value.data.candidate_sha256 !== await payloadSha256(input.candidate)) return null;
    return value.data;
  } catch { return null; } finally { if (timer !== undefined) clearTimeout(timer); }
}
export { publishAnswer, type PublicationOutcome };

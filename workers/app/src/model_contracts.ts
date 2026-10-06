import { z } from "zod";
import { payloadSha256, supportedClaims, unicode } from "./policy";
import { approvedSource, type Source } from "./contracts";

const uuid = z.uuid().refine((value) => value === value.toLowerCase());
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const integerText = z.string().regex(/^(?:0|-?[1-9][0-9]*)$/).refine((value) => {
  if (value.length > 20) return false;
  const integer = BigInt(value);
  return integer >= -(2n ** 63n) && integer <= 2n ** 63n - 1n;
});
const text = (maximum: number): z.ZodType<string> => z.string().refine(
  (value) => unicode(value) && !/[\p{Cc}\p{Cf}]/u.test(value) &&
    value.trim().length > 0 && new TextEncoder().encode(value).byteLength <= maximum,
);
const timestamp = z.iso.datetime({ precision: 0 }).refine(
  (value) => !value.startsWith("0000") && new Date(value).toISOString() === value.replace("Z", ".000Z"),
);
const mode = z.enum(["profile", "query", "search"]);
const unit = z.enum(["net_units", "USD_cents"]);
const claimId = z.string().regex(/^[a-z][a-z0-9_]{0,63}$/);
const limitationTrend = "Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence.";
const limitationNoHit = "No hits means this lexical query found no matching messages in the declared filtered scope.";
export const TARGETED_LIMITATIONS = [limitationTrend, limitationNoHit] as const;

export const analystProposal = z.strictObject({
  version: z.literal("1"),
  request_id: uuid,
  source: approvedSource,
  status: z.enum(["plan", "clarify"]),
  mode: z.enum(["profile", "query", "search", "clarify"]),
  sql: text(8000).nullable(),
  query: text(128).nullable(),
  channel: text(64).nullable(),
  customer: text(64).nullable(),
  start: timestamp.nullable(),
  end: timestamp.nullable(),
  clarification: text(512).nullable(),
}).superRefine((value, context) => {
  const filtersEmpty = [value.channel, value.customer, value.start, value.end].every((item) => item === null);
  const noTools = value.sql === null && value.query === null;
  if (value.status === "clarify") {
    if (value.mode !== "clarify" || value.clarification === null || !noTools || !filtersEmpty) {
      context.addIssue({ code: "custom", path: ["mode"], message: "invalid clarification" });
    }
    return;
  }
  const valid = value.mode === "profile"
    ? value.source.source_id === "sales" && noTools && filtersEmpty
    : value.mode === "query"
      ? value.source.source_id === "sales" && value.sql !== null && value.query === null && filtersEmpty
      : value.mode === "search" && value.source.source_id === "support" && value.query !== null &&
        value.sql === null && (value.start === null || value.end === null || value.start < value.end);
  if (!valid || value.clarification !== null) context.addIssue({ code: "custom", path: ["mode"], message: "invalid proposal" });
});
export type AnalystProposal = z.infer<typeof analystProposal>;

const resultEvidence = z.strictObject({
  type: z.literal("result"),
  receipt_id: uuid,
  payload_sha256: digest,
  source: approvedSource,
  locator: text(128),
  unit: unit.nullable(),
});
const calculationEvidence = z.strictObject({
  type: z.literal("calculation"),
  calculation_id: uuid,
  result_ids: z.array(uuid).min(1).max(4),
  value: integerText,
  unit,
});
const citationEvidence = z.strictObject({
  type: z.literal("citation"),
  result_id: uuid,
  message_id: z.string().regex(/^M[0-9]{3}$/),
  quote: text(500),
});
const numericClaim = z.strictObject({
  claim_id: claimId,
  kind: z.literal("numeric"),
  text: text(512),
  value: integerText,
  unit,
  evidence: calculationEvidence,
});
const citationClaim = z.strictObject({
  claim_id: claimId,
  kind: z.literal("citation"),
  text: text(512),
  evidence: citationEvidence,
});
const statementClaim = z.strictObject({
  claim_id: claimId,
  kind: z.literal("statement"),
  text: text(512),
  evidence: z.union([resultEvidence, calculationEvidence, citationEvidence]),
});
const candidateClaim = z.discriminatedUnion("kind", [numericClaim, citationClaim, statementClaim]);

export const groundedCandidate = z.strictObject({
  version: z.literal("1"),
  request_id: uuid,
  source: approvedSource,
  mode,
  text: text(4096),
  claims: z.array(candidateClaim).min(1).max(12),
  limitations: z.array(text(512)).max(4),
  created_at: timestamp,
});
export type GroundedCandidate = z.infer<typeof groundedCandidate>;
export type CandidateClaim = z.infer<typeof candidateClaim>;

const verdictClaim = z.strictObject({
  claim_id: claimId,
  disposition: z.enum(["supported", "unsupported", "unclear"]),
  reason: text(512),
});
export const validatorVerdict = z.strictObject({
  version: z.literal("1"),
  request_id: uuid,
  overall: z.enum(["pass", "fail", "needs_clarification"]),
  deterministic_pass: z.boolean(),
  candidate_sha256: digest,
  validator_call_id: uuid,
  policy_revision: z.literal("m4-validator.v1"),
  claims: z.array(verdictClaim).max(12),
  summary: text(512),
});
export type ValidatorVerdict = z.infer<typeof validatorVerdict>;

export const publishedAnswer = z.strictObject({
  version: z.literal("1"),
  answer_id: uuid,
  request_id: uuid,
  source: approvedSource,
  mode,
  text: text(4096),
  claim_ids: z.array(claimId).min(1).max(12),
  citations: z.array(citationEvidence).max(12),
  limitations: z.array(text(512)).max(4),
});
export type PublishedAnswer = z.infer<typeof publishedAnswer>;

export interface EvidenceResult {
  receipt_id: string;
  payload_sha256: string;
  source: Source;
  kind: z.infer<typeof mode>;
}
export interface EvidenceHit {
  result_id: string;
  message_id: string;
  quote: string;
}
export interface EvidenceContext {
  results: readonly EvidenceResult[];
  calculations: readonly {
    calculation_id: string;
    result_ids: readonly string[];
    source: Source;
    value: string;
    unit: z.infer<typeof unit>;
    input_receipts: readonly Pick<EvidenceResult, "receipt_id" | "payload_sha256" | "source">[];
  }[];
  hits: readonly EvidenceHit[];
}
export type CandidateCheck = { ok: boolean; issues: readonly string[] };

function sameSource(left: Source, right: Source): boolean {
  return left.source_id === right.source_id && left.snapshot_sha256 === right.snapshot_sha256 &&
    left.meaning_revision === right.meaning_revision;
}
function resultFor(evidence: { receipt_id: string } | { result_id: string }, context: EvidenceContext): EvidenceResult | undefined {
  const id = "receipt_id" in evidence ? evidence.receipt_id : evidence.result_id;
  return context.results.find((item) => item.receipt_id === id);
}
function checkEvidence(claim: CandidateClaim, candidate: GroundedCandidate, context: EvidenceContext, issues: string[]): void {
  const evidence = claim.evidence;
  if (evidence.type === "calculation") {
    const calculation = context.calculations.find((item) => item.calculation_id === evidence.calculation_id);
    const sameInputs = calculation !== undefined && calculation.result_ids.length === evidence.result_ids.length &&
      calculation.result_ids.every((id) => evidence.result_ids.includes(id));
    const boundInputs = evidence.result_ids.every((id) => {
      const result = context.results.find((item) => item.receipt_id === id);
      const receipt = calculation?.input_receipts.find((item) => item.receipt_id === id);
      return result !== undefined && sameSource(result.source, candidate.source) && receipt !== undefined &&
        receipt.payload_sha256 === result.payload_sha256 && sameSource(receipt.source, result.source);
    });
    if (calculation === undefined || !sameSource(calculation.source, candidate.source) || !sameInputs || !boundInputs ||
      evidence.value !== calculation.value || evidence.unit !== calculation.unit ||
      (claim.kind === "numeric" && (claim.value !== evidence.value || claim.unit !== evidence.unit))) {
      issues.push("unknown_calculation");
    }
    return;
  }
  const result = resultFor(evidence, context);
  if (result === undefined || !sameSource(result.source, candidate.source)) {
    issues.push("unknown_result");
    return;
  }
  if ("source" in evidence && !sameSource(evidence.source, candidate.source)) issues.push("evidence_source_mismatch");
  if ("payload_sha256" in evidence && evidence.payload_sha256 !== result.payload_sha256) issues.push("result_hash_mismatch");
  if (evidence.type === "citation") {
    const hit = context.hits.find((item) => item.result_id === evidence.result_id && item.message_id === evidence.message_id);
    if (result.kind !== "search" || hit === undefined || !hit.quote.includes(evidence.quote)) issues.push("citation_mismatch");
  }
  if (claim.kind === "numeric" && result.kind === "search") issues.push("numeric_search_claim");
}
export function validateCandidate(
  candidateInput: unknown,
  proposalInput: unknown,
  context: EvidenceContext,
): CandidateCheck {
  const candidate = groundedCandidate.safeParse(candidateInput);
  const proposal = analystProposal.safeParse(proposalInput);
  if (!candidate.success || !proposal.success || proposal.data.status !== "plan") return { ok: false, issues: ["candidate_schema"] };
  const value = candidate.data;
  const issues: string[] = [];
  if (value.request_id !== proposal.data.request_id || value.mode !== proposal.data.mode ||
    !sameSource(value.source, proposal.data.source)) issues.push("proposal_binding");
  const ids = value.claims.map((claim) => claim.claim_id);
  if (new Set(ids).size !== ids.length) issues.push("duplicate_claim");
  if (value.mode === "search" && TARGETED_LIMITATIONS.some((item) => !value.limitations.includes(item))) {
    issues.push("missing_search_limitations");
  }
  if (value.mode === "search" && value.claims.some((claim) => claim.kind !== "citation")) {
    issues.push("unsupported_search_claim");
  }
  const searchText = [value.text, ...value.claims.map((claim) => claim.text)].join(" ");
  const scopedNoHit = /no\s+(?:matching\s+)?messages?\s+(?:were\s+)?found\s+in\s+the\s+declared\s+filtered\s+scope/i.test(value.text);
  if (value.mode === "search" && /(prevalence|whole[- ]corpus|system[- ]wide|absence|majority|trend|every|all|none|most|rate|percentage|percent|\bno\b|\bnobody\b|\bnothing\b)/i.test(searchText) && !scopedNoHit) {
    issues.push("unsupported_search_claim");
  }
  for (const claim of value.claims) checkEvidence(claim, value, context, issues);
  return { ok: issues.length === 0, issues: [...new Set(issues)] };
}

export function validatorPassed(
  verdictInput: unknown,
  requiredClaimIds: readonly string[],
  deterministicPassed: boolean,
): boolean {
  const verdict = validatorVerdict.safeParse(verdictInput);
  if (!verdict.success) return false;
  return supportedClaims(verdict.data.overall, verdict.data.claims, requiredClaimIds,
    deterministicPassed && verdict.data.deterministic_pass);
}

export type PublicationOutcome =
  | { kind: "published"; answer: PublishedAnswer }
  | { kind: "refusal"; code: "candidate_invalid" | "deterministic_failed" | "validator_failed" }
  | { kind: "clarification"; question: string };

export async function publishAnswer(
  proposalInput: unknown,
  candidateInput: unknown,
  verdictInput: unknown,
  context: EvidenceContext,
  deterministicPassed: boolean,
  answerId: string,
): Promise<PublicationOutcome> {
  const proposal = analystProposal.safeParse(proposalInput);
  if (!proposal.success) return { kind: "refusal", code: "candidate_invalid" };
  if (proposal.data.status === "clarify") return { kind: "clarification", question: proposal.data.clarification as string };
  const check = validateCandidate(candidateInput, proposal.data, context);
  if (!check.ok) return { kind: "refusal", code: "candidate_invalid" };
  if (!deterministicPassed) return { kind: "refusal", code: "deterministic_failed" };
  const verdict = validatorVerdict.safeParse(verdictInput);
  const candidate = groundedCandidate.safeParse(candidateInput);
  if (!verdict.success || !candidate.success || verdict.data.request_id !== candidate.data.request_id ||
    verdict.data.candidate_sha256 !== await payloadSha256(candidate.data) ||
    !validatorPassed(verdict.data, candidate.data.claims.map((claim) => claim.claim_id), true)) {
    return { kind: "refusal", code: "validator_failed" };
  }
  const citations = candidate.data.claims.flatMap((claim) => claim.evidence.type === "citation" ? [claim.evidence] : []);
  const answer = publishedAnswer.safeParse({
    version: "1",
    answer_id: answerId,
    request_id: candidate.data.request_id,
    source: candidate.data.source,
    mode: candidate.data.mode,
    text: candidate.data.text,
    claim_ids: candidate.data.claims.map((claim) => claim.claim_id),
    citations,
    limitations: candidate.data.limitations,
  });
  return answer.success ? { kind: "published", answer: answer.data } : { kind: "refusal", code: "candidate_invalid" };
}

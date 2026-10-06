import { describe, expect, it } from "vitest";
import {
  TARGETED_LIMITATIONS,
  analystProposal,
  groundedCandidate,
  publishAnswer,
  validateCandidate,
  validatorPassed,
  validatorVerdict,
  type EvidenceContext,
} from "../src/model_contracts";
import { payloadSha256 } from "../src/policy";

const id = "11111111-1111-4111-8111-111111111111";
const answerId = "22222222-2222-4222-8222-222222222222";
const calcId = "33333333-3333-4333-8333-333333333333";
const validatorCallId = "44444444-4444-4444-8444-444444444444";
const hash = "a".repeat(64);
const sales = { version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" } as const;
const support = { version: "1", source_id: "support", snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536", meaning_revision: "support-demo.v1" } as const;
const when = "2026-10-06T00:00:00Z";
const profileProposal = { version: "1", request_id: id, source: sales, status: "plan", mode: "profile", sql: null, query: null, channel: null, customer: null, start: null, end: null, clarification: null };
const profileCandidate = { version: "1", request_id: id, source: sales, mode: "profile", text: "Net sales are 395000 USD cents.", claims: [{ claim_id: "amount", kind: "numeric", text: "Net sales are 395000 USD cents.", value: "395000", unit: "USD_cents", evidence: { type: "calculation", calculation_id: calcId, result_ids: [id], value: "395000", unit: "USD_cents" } }], limitations: [], created_at: when };
const salesContext: EvidenceContext = { results: [{ receipt_id: id, payload_sha256: hash, source: sales, kind: "profile" }], calculations: [{ calculation_id: calcId, result_ids: [id], source: sales, value: "395000", unit: "USD_cents", input_receipts: [{ receipt_id: id, payload_sha256: hash, source: sales }] }], hits: [] };
const supportProposal = { version: "1", request_id: id, source: support, status: "plan", mode: "search", sql: null, query: "export", channel: null, customer: null, start: null, end: null, clarification: null };
const supportCandidate = { version: "1", request_id: id, source: support, mode: "search", text: "Message M001: \"Export failed\"", claims: [{ claim_id: "message", kind: "citation", text: "Message M001: \"Export failed\"", evidence: { type: "citation", result_id: id, message_id: "M001", quote: "Export failed" } }], limitations: [...TARGETED_LIMITATIONS], created_at: when };
const supportContext: EvidenceContext = { results: [{ receipt_id: id, payload_sha256: hash, source: support, kind: "search" }], calculations: [], hits: [{ result_id: id, message_id: "M001", quote: "Customer says: Export failed" }] };
async function verdict(candidate: unknown, claimIds: string[], overrides: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
  return { version: "1", request_id: id, overall: "pass", deterministic_pass: true, candidate_sha256: await payloadSha256(candidate), validator_call_id: validatorCallId, policy_revision: "m4-validator.v1", claims: claimIds.map((claim_id) => ({ claim_id, disposition: "supported", reason: "matched evidence" })), summary: "Every claim matches deterministic evidence.", ...overrides };
}

describe("model and publication contracts", () => {
  it("accepts source-bound profile and targeted-search publication", async () => {
    const profile = await publishAnswer(profileProposal, profileCandidate, await verdict(profileCandidate, ["amount"]), salesContext, true, answerId);
    expect(profile.kind).toBe("published");
    expect((profile as { answer?: { claim_ids: string[] } }).answer?.claim_ids).toEqual(["amount"]);
    const supportAnswer = await publishAnswer(supportProposal, supportCandidate, await verdict(supportCandidate, ["message"]), supportContext, true, answerId);
    expect(supportAnswer.kind).toBe("published");
    expect((supportAnswer as { answer?: { limitations: readonly string[] } }).answer?.limitations).toEqual(TARGETED_LIMITATIONS);
  });

  it("rejects unsupported proposal capability, extra fields, and oversized text", () => {
    expect(analystProposal.safeParse({ ...profileProposal, source: support }).success).toBe(false);
    expect(analystProposal.safeParse({ ...profileProposal, extra: true }).success).toBe(false);
    expect(groundedCandidate.safeParse({ ...profileCandidate, text: "x".repeat(4097) }).success).toBe(false);
    expect(groundedCandidate.safeParse({ ...profileCandidate, claims: [{ ...profileCandidate.claims[0], unit: "USD" }] }).success).toBe(false);
  });

  it("rejects fabricated result IDs, source mismatches, and altered quotes", () => {
    const wrongResult = { ...profileCandidate, claims: [{ ...profileCandidate.claims[0], evidence: { ...profileCandidate.claims[0].evidence, receipt_id: answerId } }] };
    expect(validateCandidate(wrongResult, profileProposal, salesContext).ok).toBe(false);
    const wrongSource = { ...profileCandidate, source: support };
    expect(validateCandidate(wrongSource, profileProposal, salesContext).issues).toContain("proposal_binding");
    const wrongQuote = { ...supportCandidate, claims: [{ ...supportCandidate.claims[0], evidence: { ...supportCandidate.claims[0].evidence, quote: "not in result" } }] };
    expect(validateCandidate(wrongQuote, supportProposal, supportContext).issues).toContain("citation_mismatch");
  });

  it("requires exact validator claims and cannot override deterministic failure", async () => {
    expect(validatorPassed(await verdict(profileCandidate, ["amount"]), ["amount"], true)).toBe(true);
    expect(validatorPassed(await verdict(profileCandidate, ["amount", "amount"]), ["amount"], true)).toBe(false);
    expect(validatorPassed(await verdict(profileCandidate, ["amount"], { claims: [] }), ["amount"], true)).toBe(false);
    expect(validatorPassed(await verdict(profileCandidate, ["amount"], { deterministic_pass: false }), ["amount"], false)).toBe(false);
    expect(await publishAnswer(profileProposal, profileCandidate, await verdict(profileCandidate, ["amount"]), salesContext, false, answerId)).toEqual({ kind: "refusal", code: "deterministic_failed" });
  });

  it("requires targeted limitations and refuses broad search claims", () => {
    const missing = { ...supportCandidate, limitations: [] };
    const broad = { ...supportCandidate, text: "This proves whole-corpus prevalence.", claims: [{ ...supportCandidate.claims[0], text: "This proves prevalence." }] };
    const trend = { ...supportCandidate, text: "This trend is representative.", claims: [{ ...supportCandidate.claims[0], text: "This trend is representative." }] };
    const absence = { ...supportCandidate, text: "No customer reported an export failure.", claims: [{ ...supportCandidate.claims[0], text: "No customer reported an export failure." }] };
    const mixed = { ...supportCandidate, text: `${TARGETED_LIMITATIONS[1]} No customer reported an export failure.` };
    expect(validateCandidate(missing, supportProposal, supportContext).issues).toContain("missing_search_limitations");
    expect(validateCandidate(broad, supportProposal, supportContext).issues).toContain("unsupported_search_claim");
    expect(validateCandidate(trend, supportProposal, supportContext).issues).toContain("unsupported_search_claim");
    expect(validateCandidate(absence, supportProposal, supportContext).issues).toContain("unsupported_search_claim");
    expect(validateCandidate(mixed, supportProposal, supportContext).issues).toContain("unsupported_search_claim");
  });

  it("returns clarification without publishing and rejects validator request mismatch", async () => {
    const clarification = { ...profileProposal, status: "clarify", mode: "clarify", clarification: "Which period should I use?" };
    expect(await publishAnswer(clarification, profileCandidate, await verdict(profileCandidate, ["amount"]), salesContext, true, answerId)).toEqual({ kind: "clarification", question: "Which period should I use?" });
    expect(await publishAnswer(profileProposal, profileCandidate, await verdict(profileCandidate, ["amount"], { request_id: answerId }), salesContext, true, answerId)).toEqual({ kind: "refusal", code: "validator_failed" });
  });

  it("binds deterministic calculations to source, inputs, and exact value", () => {
    const candidate = { ...profileCandidate, claims: [{ ...profileCandidate.claims[0], evidence: { type: "calculation", calculation_id: calcId, result_ids: [id], value: "395000", unit: "USD_cents" } }] };
    const context = salesContext;
    expect(validateCandidate(candidate, profileProposal, context).ok).toBe(true);
    expect(validateCandidate({ ...candidate, claims: [{ ...candidate.claims[0], evidence: { ...candidate.claims[0].evidence, value: "1" } }] }, profileProposal, context).ok).toBe(false);
    expect(validateCandidate({ ...candidate, claims: [{ ...candidate.claims[0], evidence: { ...candidate.claims[0].evidence, result_ids: [answerId] } }] }, profileProposal, context).ok).toBe(false);
    const alteredInput = { ...salesContext, calculations: [{ ...salesContext.calculations[0], input_receipts: [{ receipt_id: id, payload_sha256: "b".repeat(64), source: sales }] }] };
    expect(validateCandidate(candidate, profileProposal, alteredInput).ok).toBe(false);
    const extraInput = { ...salesContext, calculations: [{ ...salesContext.calculations[0], input_receipts: [{ ...salesContext.calculations[0].input_receipts[0], receipt_id: id }, { receipt_id: answerId, payload_sha256: hash, source: sales }] }] };
    expect(validateCandidate(candidate, profileProposal, extraInput).ok).toBe(false);
  });

  it("rejects numeric support claims even when routed through a calculation", () => {
    const candidate = { ...supportCandidate, claims: [{ claim_id: "count", kind: "numeric", text: "There are 1 messages.", value: "1", unit: "net_units", evidence: { type: "calculation", calculation_id: calcId, result_ids: [id], value: "1", unit: "net_units" } }] };
    const context: EvidenceContext = { ...supportContext, calculations: [{ calculation_id: calcId, result_ids: [id], source: support, value: "1", unit: "net_units", input_receipts: [{ receipt_id: id, payload_sha256: hash, source: support }] }] };
    expect(validateCandidate(candidate, supportProposal, context).issues).toContain("unsupported_search_claim");
  });

  it("binds a validator pass to the exact candidate digest", async () => {
    const changed = { ...profileCandidate, text: "Net sales are 395001 USD cents." };
    expect(await publishAnswer(profileProposal, changed, await verdict(profileCandidate, ["amount"]), salesContext, true, answerId)).toEqual({ kind: "refusal", code: "validator_failed" });
  });
});

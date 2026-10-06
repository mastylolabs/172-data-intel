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

const id = "11111111-1111-4111-8111-111111111111";
const answerId = "22222222-2222-4222-8222-222222222222";
const calcId = "33333333-3333-4333-8333-333333333333";
const hash = "a".repeat(64);
const sales = { version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" } as const;
const support = { version: "1", source_id: "support", snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536", meaning_revision: "support-demo.v1" } as const;
const when = "2026-10-06T00:00:00Z";
const profileProposal = { version: "1", request_id: id, source: sales, status: "plan", mode: "profile", sql: null, query: null, channel: null, customer: null, start: null, end: null, clarification: null };
const profileCandidate = { version: "1", request_id: id, source: sales, mode: "profile", text: "Net sales are 395000 USD cents.", claims: [{ claim_id: "amount", kind: "numeric", text: "Net sales are 395000 USD cents.", value: "395000", unit: "USD_cents", evidence: { type: "result", receipt_id: id, payload_sha256: hash, source: sales, locator: "sum", unit: "USD_cents" } }], limitations: [], created_at: when };
const salesContext: EvidenceContext = { results: [{ receipt_id: id, payload_sha256: hash, source: sales, kind: "profile" }], calculations: [], hits: [] };
const supportProposal = { version: "1", request_id: id, source: support, status: "plan", mode: "search", sql: null, query: "export", channel: null, customer: null, start: null, end: null, clarification: null };
const supportCandidate = { version: "1", request_id: id, source: support, mode: "search", text: "A returned message reports an export failure.", claims: [{ claim_id: "message", kind: "citation", text: "A returned message reports an export failure.", evidence: { type: "citation", result_id: id, message_id: "M001", quote: "Export failed" } }], limitations: [...TARGETED_LIMITATIONS], created_at: when };
const supportContext: EvidenceContext = { results: [{ receipt_id: id, payload_sha256: hash, source: support, kind: "search" }], calculations: [], hits: [{ result_id: id, message_id: "M001", quote: "Customer says: Export failed" }] };
function verdict(claimIds: string[], overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return { version: "1", request_id: id, overall: "pass", deterministic_pass: true, claims: claimIds.map((claim_id) => ({ claim_id, disposition: "supported", reason: "matched evidence" })), summary: "Every claim matches deterministic evidence.", ...overrides };
}

describe("model and publication contracts", () => {
  it("accepts source-bound profile and targeted-search publication", () => {
    const profile = publishAnswer(profileProposal, profileCandidate, verdict(["amount"]), salesContext, true, answerId);
    expect(profile.kind).toBe("published");
    expect((profile as { answer?: { claim_ids: string[] } }).answer?.claim_ids).toEqual(["amount"]);
    const supportAnswer = publishAnswer(supportProposal, supportCandidate, verdict(["message"]), supportContext, true, answerId);
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

  it("requires exact validator claims and cannot override deterministic failure", () => {
    expect(validatorPassed(verdict(["amount"]), ["amount"], true)).toBe(true);
    expect(validatorPassed(verdict(["amount", "amount"]), ["amount"], true)).toBe(false);
    expect(validatorPassed(verdict(["amount"], { claims: [] }), ["amount"], true)).toBe(false);
    expect(validatorPassed(verdict(["amount"], { deterministic_pass: false }), ["amount"], false)).toBe(false);
    expect(publishAnswer(profileProposal, profileCandidate, verdict(["amount"]), salesContext, false, answerId)).toEqual({ kind: "refusal", code: "deterministic_failed" });
  });

  it("requires targeted limitations and refuses broad search claims", () => {
    const missing = { ...supportCandidate, limitations: [] };
    const broad = { ...supportCandidate, text: "This proves whole-corpus prevalence.", claims: [{ ...supportCandidate.claims[0], text: "This proves prevalence." }] };
    expect(validateCandidate(missing, supportProposal, supportContext).issues).toContain("missing_search_limitations");
    expect(validateCandidate(broad, supportProposal, supportContext).issues).toContain("unsupported_search_claim");
  });

  it("returns clarification without publishing and rejects validator request mismatch", () => {
    const clarification = { ...profileProposal, status: "clarify", mode: "clarify", clarification: "Which period should I use?" };
    expect(publishAnswer(clarification, profileCandidate, verdict(["amount"]), salesContext, true, answerId)).toEqual({ kind: "clarification", question: "Which period should I use?" });
    expect(publishAnswer(profileProposal, profileCandidate, verdict(["amount"], { request_id: answerId }), salesContext, true, answerId)).toEqual({ kind: "refusal", code: "validator_failed" });
  });

  it("binds deterministic calculations to source, inputs, and exact value", () => {
    const candidate = { ...profileCandidate, claims: [{ ...profileCandidate.claims[0], evidence: { type: "calculation", calculation_id: calcId, result_ids: [id], value: "395000", unit: "USD_cents" } }] };
    const context = { ...salesContext, calculations: [{ calculation_id: calcId, result_ids: [id], source: sales, value: "395000" }] };
    expect(validateCandidate(candidate, profileProposal, context).ok).toBe(true);
    expect(validateCandidate({ ...candidate, claims: [{ ...candidate.claims[0], evidence: { ...candidate.claims[0].evidence, value: "1" } }] }, profileProposal, context).ok).toBe(false);
  });
});

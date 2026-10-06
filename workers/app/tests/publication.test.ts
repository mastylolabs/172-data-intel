import { describe, expect, it } from "vitest";
import { approvedSource, type Envelope } from "../src/contracts";
import { analystProposal, TARGETED_LIMITATIONS, publishAnswer, validateCandidate } from "../src/model_contracts";
import { buildPublication, runValidator } from "../src/publication";
import { payloadSha256 } from "../src/policy";

const id = "11111111-1111-4111-8111-111111111111";
const callId = "22222222-2222-4222-8222-222222222222";
const support = approvedSource.parse({ version: "1", source_id: "support", snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536", meaning_revision: "support-demo.v1" });
const runtime = { python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local" as const, build_revision: null, worker_version_id: null, service_contract_revision: "m4-service.v1" as const };
const proposal = { version: "1", request_id: id, source: support, status: "plan", mode: "search", sql: null, query: "export", channel: null, customer: null, start: null, end: null, clarification: null } as const;
function searchEnvelope(hits: unknown[]): Promise<Envelope<unknown>> {
  const payload = { version: "2", source: support, schema_revision: "support-demo.v1", search_policy: "m3-lexical.v1", request: { version: "2", source: support, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 5 }, scanned_count: 16, matched_count: hits.length, returned_count: hits.length, omitted_hit_count: 0, hits, coverage: "targeted_lexical_search", limitations: [...TARGETED_LIMITATIONS], analytical_validated: false };
  return payloadSha256(payload).then((payload_sha256) => ({ version: "2", job_id: id, run_id: id, receipt_id: id, payload, payload_sha256, runtime }));
}
function hit(message_id = "M001"): Record<string, unknown> { return { message_id, timestamp: "2026-10-06T00:00:00Z", channel: "email", customer: "Acme", score: 1, matched_tokens: ["export"], quote: "Export failed" }; }

describe("bounded publication", () => {
  it("builds exact support citations and scoped no-hit evidence", async () => {
    const receipt = await searchEnvelope([hit()]);
    const built = buildPublication(proposal, receipt);
    expect(built && validateCandidate(built.candidate, proposal, built.context).ok).toBe(true);
    const empty = await searchEnvelope([]);
    const noHit = buildPublication(proposal, empty)!;
    expect(noHit.candidate.text).toBe(TARGETED_LIMITATIONS[1]);
    expect(validateCandidate(noHit.candidate, proposal, noHit.context).ok).toBe(true);
  });
  it("refuses altered evidence and an independent validator failure", async () => {
    const receipt = await searchEnvelope([hit()]);
    const built = buildPublication(proposal, receipt)!;
    const fabricated = { ...built.candidate, claims: built.candidate.claims.map((claim) => claim.kind === "citation" ? { ...claim, evidence: { ...claim.evidence, quote: "invented" } } : claim) };
    expect(validateCandidate(fabricated, proposal, built.context).ok).toBe(false);
    const verdict = { version: "1", request_id: id, overall: "fail", deterministic_pass: true, candidate_sha256: await payloadSha256(built.candidate), validator_call_id: callId, policy_revision: "m4-validator.v1", claims: [{ claim_id: "message_1", disposition: "unsupported", reason: "not enough" }], summary: "failed" };
    expect(await publishAnswer(proposal, built.candidate, verdict, built.context, true, callId)).toEqual({ kind: "refusal", code: "validator_failed" });
  });
  it("bounds and validates the separate Validator response", async () => {
    const receipt = await searchEnvelope([]); const built = buildPublication(proposal, receipt)!;
    const AI = { run: async (_model: string, input: { messages: { content: string }[] }) => {
      const candidate = JSON.parse(input.messages[1].content).candidate as unknown;
      return { response: JSON.stringify({ version: "1", request_id: id, overall: "pass", deterministic_pass: true, candidate_sha256: await payloadSha256(candidate), validator_call_id: callId, policy_revision: "m4-validator.v1", claims: [{ claim_id: "no_hit", disposition: "supported", reason: "scoped" }], summary: "supported" }) };
    } };
    expect((await runValidator({ AI: AI as never }, built.candidate))?.overall).toBe("pass");
  });
  it("rejects a proposal source that differs from the receipt", async () => {
    const receipt = await searchEnvelope([hit()]);
    expect(buildPublication({ ...proposal, source: approvedSource.parse({ version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" }) }, receipt)).toBeNull();
    expect(analystProposal.safeParse(proposal).success).toBe(true);
  });
});

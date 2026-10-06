import { describe, expect, it } from "vitest";
import { approvedSource, type Envelope } from "../src/contracts";
import { analystProposal, TARGETED_LIMITATIONS, publishAnswer, validateCandidate } from "../src/model_contracts";
import { buildEvidence, buildPublication, runValidator } from "../src/publication";
import { payloadSha256 } from "../src/policy";

const id = "11111111-1111-4111-8111-111111111111";
const callId = "22222222-2222-4222-8222-222222222222";
const support = approvedSource.parse({ version: "1", source_id: "support", snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536", meaning_revision: "support-demo.v1" });
const sales = approvedSource.parse({ version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" });
const runtime = { python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local" as const, build_revision: null, worker_version_id: null, service_contract_revision: "m4-service.v1" as const };
const queryRuntime = { python_version: runtime.python_version, sqlite_version: runtime.sqlite_version, runtime_mode: "local" as const, build_revision: null, worker_version_id: null };
const proposal = { version: "1", request_id: id, source: support, status: "plan", mode: "search", sql: null, query: "export", channel: null, customer: null, start: null, end: null, clarification: null } as const;
const salesProposal = { version: "1", request_id: id, source: sales, status: "plan", mode: "query", sql: "SELECT SUM(net_units) AS net_units FROM sales", query: null, channel: null, customer: null, start: null, end: null, clarification: null } as const;
const queryLimits = { max_sql_bytes: 8000, max_rows: 20, max_columns: 16, max_column_bytes: 64, max_text_bytes: 256, max_result_bytes: 16384, progress_interval: 100, max_progress_callbacks: 500, query_deadline_ms: 250, sqlite_heap_bytes: 8388608, sqlite_limits: { sql_length: 8000, length: 65536, column: 16, expr_depth: 30, compound_select: 8, vdbe_op: 10000, function_arg: 8, attached: 0, like_pattern_length: 128, variable_number: 0, trigger_depth: 0 } };
function searchEnvelope(hits: unknown[]): Promise<Envelope<unknown>> {
  const payload = { version: "2", source: support, schema_revision: "support-demo.v1", search_policy: "m3-lexical.v1", request: { version: "2", source: support, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 5 }, scanned_count: 16, matched_count: hits.length, returned_count: hits.length, omitted_hit_count: 0, hits, coverage: "targeted_lexical_search", limitations: [...TARGETED_LIMITATIONS], analytical_validated: false };
  return payloadSha256(payload).then((payload_sha256) => ({ version: "2", job_id: id, run_id: id, receipt_id: id, payload, payload_sha256, runtime }));
}
function hit(message_id = "M001"): Record<string, unknown> { return { message_id, timestamp: "2026-10-06T00:00:00Z", channel: "email", customer: "Acme", score: 1, matched_tokens: ["export"], quote: "Export failed" }; }
async function queryEnvelope(column: string, actual_sql: string): Promise<Envelope<unknown>> {
  const rows = [[{ type: "integer", value: "7", exact: true }]];
  const sqlBytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(actual_sql));
  const sql_sha256 = Array.from(new Uint8Array(sqlBytes), (byte) => byte.toString(16).padStart(2, "0")).join("");
  const payload = { version: "2", receipt_id: id, job_id: id, source: sales, schema_revision: "sales-demo.v1", engine_policy: "m2-sqlite.v1", actual_sql, sql_sha256, columns: [column], rows, row_count: 1, result_sha256: await payloadSha256({ columns: [column], rows }), coverage: "complete_query_result", truncated: false, analytical_validated: false, limits: queryLimits, runtime: queryRuntime };
  return { version: "2", job_id: id, run_id: id, receipt_id: id, payload, payload_sha256: await payloadSha256(payload), runtime };
}

describe("bounded publication", () => {
  it("binds both approved sales units and cents and rejects unknown semantics", async () => {
    for (const [column, sql, unit] of [["net_units", "SELECT SUM(net_units) AS net_units FROM sales", "net_units"], ["revenue_cents", "SELECT SUM(revenue_cents) AS revenue_cents FROM sales", "USD_cents"]] as const) {
      const receipt = await queryEnvelope(column, sql); const built = buildPublication({ ...salesProposal, sql }, receipt);
      expect(buildEvidence(built!.context, receipt)).not.toBeNull();
      expect(built?.candidate.claims[0]).toMatchObject({ kind: "numeric", unit });
    }
    expect(buildPublication(salesProposal, await queryEnvelope("units", "SELECT COUNT(*) AS units"))).toBeNull();
    expect(buildPublication(salesProposal, await queryEnvelope("value", "SELECT 7"))).toBeNull();
    for (const sql of ["SELECT SUM(net_units) + 1 AS net_units FROM sales", "SELECT SUM(net_units) AS net_units FROM sales WHERE region = 'east'", "SELECT SUM(net_units) OVER () AS net_units FROM sales", "SELECT SUM(net_units) AS revenue_cents FROM sales"]) expect(buildPublication({ ...salesProposal, sql }, await queryEnvelope("net_units", sql))).toBeNull();
  });
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
    expect(validateCandidate(built.candidate, proposal, { ...built.context, hits: [] }).ok).toBe(false);
    const verdict = { version: "1", request_id: id, overall: "fail", deterministic_pass: true, candidate_sha256: await payloadSha256(built.candidate), validator_call_id: callId, policy_revision: "m4-validator.v1", claims: [{ claim_id: "message_1", disposition: "unsupported", reason: "not enough" }], summary: "failed" };
    expect(await publishAnswer(proposal, built.candidate, verdict, built.context, true, callId)).toEqual({ kind: "refusal", code: "validator_failed" });
  });
  it("bounds and validates the separate Validator response", async () => {
    const receipt = await searchEnvelope([]); const built = buildPublication(proposal, receipt)!;
    let received: unknown;
    const AI = { run: async (_model: string, input: { messages: { content: string }[] }) => {
      received = JSON.parse(input.messages[1].content);
      const candidate = JSON.parse(input.messages[1].content).candidate as unknown;
      const body = JSON.parse(input.messages[1].content) as { execution_receipt: Envelope<unknown>; proposal: unknown; validator_input_sha256: string };
      return { response: JSON.stringify({ version: "1", request_id: id, job_id: body.execution_receipt.job_id, run_id: body.execution_receipt.run_id, source: (body.execution_receipt.payload as { source: unknown }).source, overall: "pass", deterministic_pass: true, candidate_sha256: await payloadSha256(candidate), plan_sha256: await payloadSha256(body.proposal), validator_input_sha256: body.validator_input_sha256, validator_call_id: callId, policy_revision: "m4-validator.v1", claims: [{ claim_id: "no_hit", disposition: "supported", reason: "scoped" }], summary: "supported" }) };
    } };
    const evidence = buildEvidence(built.context, receipt)!;
    expect((await runValidator({ AI: AI as never }, { question: "find export", proposal, meanings: { catalog: null, profile: null }, context: built.context, execution: evidence.execution,
      candidate: built.candidate, deterministic: { ok: true, issues: [] }, job_id: id, run_id: id, source: support }))?.overall).toBe("pass");
    expect(received).toMatchObject({ version: "1", question: "find export", proposal, meanings: { catalog: null, profile: null }, evidence_context: built.context, execution_receipt: evidence.execution, candidate: built.candidate, candidate_sha256: await payloadSha256(built.candidate), validator_input_sha256: expect.any(String), deterministic_check: { ok: true, issues: [] } });
  });
  it("rejects a proposal source that differs from the receipt", async () => {
    const receipt = await searchEnvelope([hit()]);
    expect(buildPublication({ ...proposal, source: approvedSource.parse({ version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" }) }, receipt)).toBeNull();
    expect(analystProposal.safeParse(proposal).success).toBe(true);
  });
});

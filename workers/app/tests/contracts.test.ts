import { describe, expect, it } from "vitest";
import { z } from "zod";
import {
  approvedSource, plannerProposal, questionInput, validatedEnvelope, type Envelope,
} from "../src/contracts";
import { bound, canonicalJson, payloadSha256, supportedClaims } from "../src/policy";
import { PLANNER, SYNTHESIZER, VALIDATOR } from "../src/prompts";

const source = {
  version: "1", source_id: "sales",
  snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f",
  meaning_revision: "sales-demo.v1",
} as const;
const id = "11111111-1111-4111-8111-111111111111";
const payload = z.strictObject({ value: z.string() });
async function envelope(value = "ok"): Promise<Envelope<z.infer<typeof payload>>> {
  return {
    version: "2", job_id: id, run_id: id, receipt_id: id, payload: { value },
    payload_sha256: await payloadSha256({ value }),
    runtime: {
      python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local",
      build_revision: null, worker_version_id: null, service_contract_revision: "m4-service.v1",
    },
  };
}
describe("app contract foundation", () => {
  it("pins complete demo identities and preserves bounded question text", () => {
    expect(approvedSource.parse(source)).toEqual(source);
    for (const change of [{ snapshot_sha256: "f".repeat(64) }, { meaning_revision: "sales-proof.v1" }, { path: "/tmp" }]) {
      expect(approvedSource.safeParse({ ...source, ...change }).success).toBe(false);
    }
    const question = { version: "2", request_id: id, question: " é " };
    expect(questionInput.parse(question).question).toBe(" é ");
    expect(questionInput.safeParse({ ...question, question: "é".repeat(512) }).success).toBe(true);
    for (const value of ["é".repeat(513), "\ud800", "   ", 1]) {
      expect(questionInput.safeParse({ ...question, question: value }).success).toBe(false);
    }
  });
  it("keeps proposals source-bound, generic and explicitly non-executable", () => {
    const proposal = plannerProposal(source);
    const planned = {
      status: "plan", mode: "query", sql: "DELETE FROM sales", query: null,
      channel: null, customer: null, start: null, end: null, question: null,
    } as const;
    // Schema acceptance grants no SQL safety; the Python engine owns authorization/execution.
    expect(proposal.parse(planned)).toEqual(planned);
    for (const change of [{ operation: "total" }, { sql: null }, { query: "export" }, { question: "Why?" }]) {
      expect(proposal.safeParse({ ...planned, ...change }).success).toBe(false);
    }
    expect(proposal.safeParse({ status: "clarify", mode: "clarify", sql: null, query: null,
      channel: null, customer: null, start: null, end: null, question: "Which period?" }).success).toBe(true);
    expect(proposal.safeParse({ status: "plan", mode: "profile", sql: null, query: null,
      channel: null, customer: null, start: null, end: null, question: null }).success).toBe(true);
    const support = approvedSource.parse({ version: "1", source_id: "support",
      snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
      meaning_revision: "support-demo.v1" });
    expect(plannerProposal(support).safeParse({ ...planned, mode: "search", sql: null, query: "export" }).success).toBe(true);
    expect(plannerProposal(support).safeParse(planned).success).toBe(false);
  });
  it("preserves support filters and refuses contradictory or malformed planning scope", () => {
    const support = approvedSource.parse({ version: "1", source_id: "support",
      snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
      meaning_revision: "support-demo.v1" });
    const scoped = plannerProposal(support);
    const search = { status: "plan", mode: "search", sql: null, query: "export", question: null,
      channel: "Email", customer: "Atlas", start: "2026-01-01T00:00:00Z", end: "2026-02-01T00:00:00Z" };
    expect(scoped.parse(search)).toEqual(search);
    for (const change of [
      { mode: "profile", query: null }, { sql: "SELECT 1" }, { channel: " Email" },
      { channel: "é".repeat(33) }, { customer: "\u200b" }, { start: search.end },
      { end: "2025-12-31T23:59:59Z" }, { start: "2026-02-30T00:00:00Z" },
      { start: "2026-01-01T00:00:00+00:00" }, { end: "2026-02-01T00:00:00.000Z" },
      { start: "0000-01-01T00:00:00Z" }, { start: "2026-01-01" },
      { status: "clarify", question: "Which channel?" },
    ]) expect(scoped.safeParse({ ...search, ...change }).success).toBe(false);
    for (const field of ["mode", "channel", "customer", "start", "end"]) {
      const omitted: Record<string, unknown> = { ...search };
      delete omitted[field];
      expect(scoped.safeParse(omitted).success).toBe(false);
    }
    expect(scoped.safeParse({ ...search, start: null }).success).toBe(true);
    expect(scoped.safeParse({ ...search, end: null }).success).toBe(true);
    expect(plannerProposal(source).safeParse({ ...search, mode: "profile", query: null }).success).toBe(false);
  });
  it("round-trips strict Python v2 envelope metadata and exact payload hashes", async () => {
    const wire = await envelope();
    expect(await validatedEnvelope(payload, wire, 4096)).toEqual(wire);
    expect(await validatedEnvelope(payload, { ...wire, job_id: null, run_id: null, receipt_id: null }, 4096)).toMatchObject({ job_id: null });
    for (const change of [{ version: "1" }, { extra: true }, { run_id: null }, { payload_sha256: "0".repeat(64) }]) {
      await expect(validatedEnvelope(payload, { ...wire, ...change }, 4096)).rejects.toThrow("invalid_result");
    }
    const deployed = { ...wire.runtime, runtime_mode: "deployed" };
    await expect(validatedEnvelope(payload, { ...wire, runtime: deployed }, 4096)).rejects.toThrow("invalid_result");
    await expect(validatedEnvelope(payload, { ...wire, runtime: { ...deployed, build_revision: "f".repeat(40), worker_version_id: id } }, 4096)).resolves.toBeDefined();
    for (const field of ["job_id", "run_id", "receipt_id", "runtime"]) {
      const omitted: Record<string, unknown> = { ...wire };
      delete omitted[field];
      await expect(validatedEnvelope(payload, omitted, 4096)).rejects.toThrow("invalid_result");
    }
    const transformed = z.strictObject({ value: z.string().trim() });
    await expect(validatedEnvelope(transformed, await envelope(" ok "), 4096)).rejects.toThrow("invalid_result");
    await expect(validatedEnvelope(payload, await envelope("x".repeat(4084)), 4096)).resolves.toBeDefined();
    await expect(validatedEnvelope(payload, await envelope("x".repeat(4085)), 4096)).rejects.toThrow("result_limit");
    const bodyCapacity = 16_384 - new TextEncoder().encode(canonicalJson(await envelope(""))).length;
    await expect(validatedEnvelope(payload, await envelope("x".repeat(bodyCapacity)), 16_384)).resolves.toBeDefined();
    await expect(validatedEnvelope(payload, await envelope("x".repeat(bodyCapacity + 1)), 16_384)).rejects.toThrow("result_limit");
    const extra = { value: "ok", extra: true };
    await expect(validatedEnvelope(payload, {
      ...wire, payload: extra, payload_sha256: await payloadSha256(extra),
    }, 4096)).rejects.toThrow("invalid_result");
  });
  it("uses Python-compatible Unicode canonical ordering and refuses lossy values", async () => {
    expect(canonicalJson({ "𐀀": "é", "\ue000": 1 })).toBe('{"":1,"𐀀":"é"}');
    expect(canonicalJson({ b: [true, null], a: "é" })).toBe('{"a":"é","b":[true,null]}');
    for (const value of [undefined, NaN, Infinity, 1.5, -0, 2 ** 53, "\ud800", new Date(), [undefined]]) {
      expect(() => canonicalJson(value)).toThrow("invalid_result");
    }
    expect(() => bound("é", 4)).not.toThrow();
    expect(() => bound("é", 3)).toThrow("result_limit");
    expect(await payloadSha256({ value: "ok" })).toBe("16cfa6ba3d308e6c52a96d7d50018be09d175a518b74d5bcc6e39281ef75fa9b");
  });
  it("requires every material claim exactly once and cannot override deterministic failure", () => {
    const claims = [{ claim_id: "amount", disposition: "supported" }];
    expect(supportedClaims("pass", claims, ["amount"], true)).toBe(true);
    for (const expected of [[], ["missing"], ["amount", "amount"]]) {
      expect(supportedClaims("pass", claims, expected, true)).toBe(false);
    }
    expect(supportedClaims("pass", [...claims, ...claims], ["amount"], true)).toBe(false);
    expect(supportedClaims("pass", [{ ...claims[0], disposition: "unsupported" }], ["amount"], true)).toBe(false);
    expect(supportedClaims("pass", claims, ["amount"], false)).toBe(false);
    expect(supportedClaims("fail", claims, ["amount"], true)).toBe(false);
    expect(PLANNER).toContain("net USD cents");
    expect(SYNTHESIZER).toContain("unpublished");
    expect(VALIDATOR).toContain("Never override deterministic failure");
  });
});

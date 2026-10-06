import { describe, expect, it } from "vitest";
import { z } from "zod";
import {
  approvedSource, catalogV2, dataProfileV2, plannerProposal, queryResultV2, questionInput,
  searchReceiptV2, validatedDomainEnvelope, validatedEnvelope, type Envelope,
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
  it("accepts the registered catalog and bounded sales profile", () => {
    const sales = {
      version: "1", source_id: "sales",
      snapshot_sha256: source.snapshot_sha256, meaning_revision: "sales-demo.v1",
    };
    const support = {
      version: "1", source_id: "support",
      snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
      meaning_revision: "support-demo.v1",
    };
    const catalog = {
      version: "2", catalog_revision: "m4-catalog.v1",
      entries: [
        { source: sales, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1",
          kind: "structured", display_name: "Sales demo",
          description: "Synthetic net sales lines for bounded structured analysis.",
          capability_help: { profile: "Summarize fields and bounded statistics.",
            query: "Ask for read-only totals, groups, rankings or period comparisons." },
          capabilities: ["profile", "query"], record_count: 24, manifest_bytes: 1025,
          scope: "complete_immutable_fixture" },
        { source: support, schema_revision: "support-demo.v1", profile_revision: null,
          kind: "messages", display_name: "Support messages",
          description: "Synthetic support messages for targeted lexical examples.",
          capability_help: { search: "Find matching messages with exact IDs and source quotes; hits do not establish prevalence." },
          capabilities: ["search"], record_count: 16, manifest_bytes: 3091,
          scope: "complete_immutable_fixture" },
      ],
    };
    expect(catalogV2.parse(catalog).entries).toHaveLength(2);
    expect(catalogV2.safeParse({ ...catalog, entries: [catalog.entries[0], catalog.entries[0]] }).success).toBe(false);
    const profile = {
      version: "2", source: sales, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1",
      fields: [], record_count: 0, range_start: null, range_end: null, dimensions: [], measures: [],
      omissions: ["bulk_rows", "row_samples", "distributions", "uncomputed_statistics"],
      capabilities: [], analytical_validated: false,
    };
    expect(dataProfileV2.parse(profile).record_count).toBe(0);
    expect(dataProfileV2.safeParse({ ...profile, analytical_validated: true }).success).toBe(false);
    expect(dataProfileV2.safeParse({ ...profile, measures: [{ field: "units", unit: "net_units",
      count: 1, min: "01", max: "1", sum: "1", exact: true }] }).success).toBe(false);
    expect(dataProfileV2.safeParse({ ...profile, range_start: "0000-01-01" }).success).toBe(false);
  });
  it("enforces typed query cells and targeted search receipt invariants", async () => {
    const query = {
      version: "2", receipt_id: id, job_id: id, source, schema_revision: "sales-demo.v1",
      engine_policy: "m2-sqlite.v1", actual_sql: "SELECT 1", sql_sha256: await digest("SELECT 1"),
      columns: ["value"], rows: [[{ type: "integer", value: "1", exact: true }]], row_count: 1,
      result_sha256: await payloadSha256({ columns: ["value"], rows: [[{ type: "integer", value: "1", exact: true }]] }),
      coverage: "complete_query_result", truncated: false, analytical_validated: false,
      limits: { max_sql_bytes: 8000, max_rows: 20, max_columns: 16, max_column_bytes: 64,
        max_text_bytes: 256, max_result_bytes: 16384, progress_interval: 100,
        max_progress_callbacks: 500, query_deadline_ms: 250, sqlite_heap_bytes: 8388608,
        sqlite_limits: { sql_length: 8000, length: 65536, column: 16, expr_depth: 30,
          compound_select: 8, vdbe_op: 10000, function_arg: 8, attached: 0,
          like_pattern_length: 128, variable_number: 0, trigger_depth: 0 } },
      runtime: { python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local",
        build_revision: null, worker_version_id: null },
    };
    expect(queryResultV2.parse(query).rows[0][0]).toEqual(query.rows[0][0]);
    expect(queryResultV2.safeParse({ ...query, rows: [[{ type: "real", value: "1", exact: false }]] }).success).toBe(false);
    expect(queryResultV2.safeParse({ ...query, rows: [[{ type: "real", value: "1.0", exact: false }]] }).success).toBe(true);
    expect(queryResultV2.safeParse({ ...query, rows: [[{ type: "real", value: "0.0", exact: false }]] }).success).toBe(true);
    const search = {
      version: "2", source: { version: "1", source_id: "support",
        snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
        meaning_revision: "support-demo.v1" },
      schema_revision: "support-demo.v1", search_policy: "m3-lexical.v1",
      request: { version: "2", source: { version: "1", source_id: "support",
        snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
        meaning_revision: "support-demo.v1" }, query: "export", channel: null, customer: null,
        start: null, end: null, max_hits: 1 },
      scanned_count: 16, matched_count: 0, returned_count: 0, omitted_hit_count: 0, hits: [],
      coverage: "targeted_lexical_search",
      limitations: ["Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence.",
        "No hits means this lexical query found no matching messages in the declared filtered scope."],
      analytical_validated: false,
    };
    expect(searchReceiptV2.parse(search).hits).toEqual([]);
    expect(searchReceiptV2.safeParse({ ...search, matched_count: 1 }).success).toBe(false);
    expect(searchReceiptV2.safeParse({ ...search, request: { ...search.request, query: "a\u0000" } }).success).toBe(false);
    expect(searchReceiptV2.safeParse({ ...search, request: { ...search.request, query: "É" } }).success).toBe(false);
    expect(searchReceiptV2.safeParse({ ...search, request: { ...search.request, query: "CSV İNV" } }).success).toBe(true);
    const catalogEnvelope = await envelope();
    await expect(validatedDomainEnvelope("query", {
      ...catalogEnvelope, payload: query, payload_sha256: await payloadSha256(query),
    })).resolves.toBeDefined();
    const tamperedQuery = { ...query, sql_sha256: "0".repeat(64) };
    await expect(validatedDomainEnvelope("query", {
      ...catalogEnvelope, payload: tamperedQuery, payload_sha256: await payloadSha256(tamperedQuery),
    })).rejects.toThrow("invalid_result");
    const mismatchedRuntime = { ...query, runtime: { ...query.runtime, sqlite_version: "3.99.0" } };
    await expect(validatedDomainEnvelope("query", {
      ...catalogEnvelope, payload: mismatchedRuntime, payload_sha256: await payloadSha256(mismatchedRuntime),
    })).rejects.toThrow("invalid_result");
    await expect(validatedDomainEnvelope("catalog", {
      ...catalogEnvelope, job_id: null, run_id: null, receipt_id: null,
      payload: { version: "2", catalog_revision: "m4-catalog.v1", entries: [] },
      payload_sha256: await payloadSha256({ version: "2", catalog_revision: "m4-catalog.v1", entries: [] }),
    })).rejects.toThrow("invalid_result");
  });
});

async function digest(value: string): Promise<string> {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(bytes), (item) => item.toString(16).padStart(2, "0")).join("");
}

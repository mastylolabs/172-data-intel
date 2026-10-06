import { describe, expect, it } from "vitest";
import { payloadSha256 } from "../src/policy";
import {
  buildToolBody, executeTool, readBoundedText, readJson, searchRequest, type TransportEnv,
} from "../src/transport";

const id = "11111111-1111-4111-8111-111111111111";
const foreign = "22222222-2222-4222-8222-222222222222";
const source = { version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" } as const;
const support = { version: "1", source_id: "support", snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536", meaning_revision: "support-demo.v1" } as const;
const runtime = { python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local" as const, build_revision: null, worker_version_id: null, service_contract_revision: "m4-service.v1" as const };
const profile = { version: "2", source, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1", fields: [], record_count: 0, range_start: null, range_end: null, dimensions: [], measures: [], omissions: ["bulk_rows", "row_samples", "distributions", "uncomputed_statistics"] as const, capabilities: [], analytical_validated: false as const };
const search = { version: "2", source: support, schema_revision: "support-demo.v1", search_policy: "m3-lexical.v1", request: { version: "2", source: support, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 1 }, scanned_count: 16, matched_count: 0, returned_count: 0, omitted_hit_count: 0, hits: [], coverage: "targeted_lexical_search", limitations: ["Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence.", "No hits means this lexical query found no matching messages in the declared filtered scope."], analytical_validated: false } as const;
const catalog = { version: "2", catalog_revision: "m4-catalog.v1", entries: [
  { source, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1", kind: "structured", display_name: "Sales demo", description: "Synthetic net sales lines for bounded structured analysis.", capability_help: { profile: "Summarize fields and bounded statistics.", query: "Ask for read-only totals, groups, rankings or period comparisons." }, capabilities: ["profile", "query"], record_count: 24, manifest_bytes: 1025, scope: "complete_immutable_fixture" },
  { source: support, schema_revision: "support-demo.v1", profile_revision: null, kind: "messages", display_name: "Support messages", description: "Synthetic support messages for targeted lexical examples.", capability_help: { search: "Find matching messages with exact IDs and source quotes; hits do not establish prevalence." }, capabilities: ["search"], record_count: 16, manifest_bytes: 3091, scope: "complete_immutable_fixture" },
] } as const;
async function digest(value: string): Promise<string> { const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)); return Array.from(new Uint8Array(bytes), (item) => item.toString(16).padStart(2, "0")).join(""); }
async function query(job = id): Promise<Record<string, unknown>> {
  const actualSql = "SELECT count(*) AS count FROM main.sales";
  const rows = [[{ type: "integer", value: "24", exact: true }]];
  return { version: "2", receipt_id: job, job_id: job, source, schema_revision: "sales-demo.v1", engine_policy: "m2-sqlite.v1", actual_sql: actualSql, sql_sha256: await digest(actualSql), columns: ["count"], rows, row_count: 1, result_sha256: await payloadSha256({ columns: ["count"], rows }), coverage: "complete_query_result", truncated: false, analytical_validated: false, limits: { max_sql_bytes: 8000, max_rows: 20, max_columns: 16, max_column_bytes: 64, max_text_bytes: 256, max_result_bytes: 16384, progress_interval: 100, max_progress_callbacks: 500, query_deadline_ms: 250, sqlite_heap_bytes: 8388608, sqlite_limits: { sql_length: 8000, length: 65536, column: 16, expr_depth: 30, compound_select: 8, vdbe_op: 10000, function_arg: 8, attached: 0, like_pattern_length: 128, variable_number: 0, trigger_depth: 0 } }, runtime: { python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local", build_revision: null, worker_version_id: null } };
}
async function wire(payload: unknown, job: string | null = id, run: string | null = id, receipt: string | null = id): Promise<string> {
  return JSON.stringify({ version: "2", job_id: job, run_id: run, receipt_id: receipt, payload, payload_sha256: await payloadSha256(payload), runtime });
}
function environment(response: () => Promise<Response>): TransportEnv { return { RUNTIME_MODE: "local", TOOLS: { fetch: async () => response() } }; }

describe("bounded bridge transport", () => {
  it("calls and validates catalog, profile, query, and search v2 paths", async () => {
    const calls: Array<{ path: string; method: string; body: unknown }> = [];
    const values: Record<string, unknown> = { catalog, profile, query: await query(), search };
    const env: TransportEnv = { RUNTIME_MODE: "local", TOOLS: { fetch: async (request) => {
      const kind = new URL(request.url).pathname.split("/").at(-1)!;
      calls.push({
        path: `/v2/${kind}`,
        method: request.method,
        body: request.method === "POST" ? JSON.parse(await request.text()) : null,
      });
      return new Response(await wire(values[kind], kind === "catalog" ? null : id, kind === "catalog" ? null : id, kind === "catalog" ? null : id));
    } } };
    const profileBody = buildToolBody("profile", id, id, source, {});
    const queryBody = buildToolBody("query", id, id, source, { question: "count", sql: "SELECT 1", max_rows: 1 });
    const searchBody = buildToolBody("search", id, id, support, { query: "export", channel: null, customer: null, start: null, end: null, max_hits: 1 });
    await executeTool(env, "catalog", null, null);
    await executeTool(env, "profile", profileBody, { jobId: id, runId: id });
    await executeTool(env, "query", queryBody, { jobId: id, runId: id });
    await executeTool(env, "search", searchBody, { jobId: id, runId: id });
    expect(calls).toEqual([
      { path: "/v2/catalog", method: "GET", body: null },
      { path: "/v2/profile", method: "POST", body: profileBody },
      { path: "/v2/query", method: "POST", body: queryBody },
      { path: "/v2/search", method: "POST", body: searchBody },
    ]);
  });
  it("rejects valid foreign job/run identities for every non-catalog receipt", async () => {
    for (const [kind, payload] of [["profile", profile], ["query", await query(foreign)], ["search", search]] as const) {
      const env = environment(() => wireResponse(payload, foreign, foreign, foreign));
      await expect(executeTool(env, kind, {}, { jobId: id, runId: id })).rejects.toThrow("invalid_result");
    }
  });
  it("projects search fields and enforces strict date intervals", () => {
    const body = buildToolBody("search", id, id, support, { version: "2", request_id: id, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 2 });
    expect(body).toEqual({ version: "2", job_id: id, run_id: id, source: support, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 2 });
    expect(searchRequest.safeParse({ version: "2", request_id: id, query: "x", channel: null, customer: null, start: "2026-02-01T00:00:00Z", end: "2026-01-01T00:00:00Z", max_hits: 1 }).success).toBe(false);
    expect(searchRequest.safeParse({ version: "2", request_id: id, query: "x", channel: null, customer: null, start: null, end: null, max_hits: 1, extra: true }).success).toBe(false);
  });
  it("rejects malformed UTF-8 and cancels bodies at input/result limits", async () => {
    const input = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new Uint8Array([123])); controller.enqueue(new Uint8Array(20)); controller.close(); } });
    await expect(readJson(new Request("https://app.test", { method: "POST", body: input as unknown as BodyInit, duplex: "half" } as RequestInit), 8)).rejects.toThrow("result_limit");
    const malformed = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new Uint8Array([0xc3, 0x28])); controller.close(); } });
    await expect(readJson(new Request("https://app.test", { method: "POST", body: malformed as unknown as BodyInit, duplex: "half" } as RequestInit))).rejects.toThrow("invalid_input");
    const output = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new TextEncoder().encode("{}")); controller.enqueue(new Uint8Array(20_000)); controller.close(); } });
    await expect(executeTool(environment(() => Promise.resolve(new Response(output))), "profile", {}, { jobId: id, runId: id })).rejects.toThrow("result_limit");
  });
  it("maps timeout and non-2xx service failures without exposing bodies", async () => {
    await expect(executeTool({ RUNTIME_MODE: "local", TOOLS: { fetch: async () => { throw new Error("secret"); } } }, "profile", {}, { jobId: id, runId: id })).rejects.toThrow("tool_unavailable");
    await expect(executeTool(environment(() => Promise.resolve(new Response("private", { status: 503 }))), "profile", {}, { jobId: id, runId: id })).rejects.toThrow("tool_error");
  });

  it("rejects tampered payload hashes and wrong runtime provenance", async () => {
    const valid = JSON.parse(await wire(profile)) as Record<string, unknown>;
    valid.payload_sha256 = "0".repeat(64);
    await expect(executeTool(environment(() => Promise.resolve(new Response(JSON.stringify(valid)))), "profile", {}, { jobId: id, runId: id })).rejects.toThrow("invalid_result");
    await expect(executeTool({ ...environment(async () => new Response(await wire(profile))), RUNTIME_MODE: "deployed" }, "profile", {}, { jobId: id, runId: id })).rejects.toThrow("invalid_result");
  });
});

function wireResponse(payload: unknown, job: string, run: string, receipt: string): Promise<Response> {
  return wire(payload, job, run, receipt).then((body) => new Response(body));
}

import { describe, expect, it, vi } from "vitest";
vi.mock("agents", () => ({ Agent: class {
  state: unknown; env: unknown; ctx: { waitUntil(promise: Promise<unknown>): void };
  constructor(ctx: { waitUntil(promise: Promise<unknown>): void }, env: unknown) { this.ctx = ctx; this.env = env; }
  setState(value: unknown): void { this.state = value; }
}, getAgentByName: vi.fn() }));
import { AppAgent, publicFetch, type BridgeState, type Env } from "../src/index";
import { payloadSha256 } from "../src/policy";
import { initialSessionState } from "../../agent/src/v2-state";

const id = "11111111-1111-4111-8111-111111111111";
const source = { version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" } as const;
const support = { version: "1", source_id: "support", snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536", meaning_revision: "support-demo.v1" } as const;
const runtime = { python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local" as const, build_revision: null, worker_version_id: null, service_contract_revision: "m4-service.v1" as const };
const profile = { version: "2", source, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1", fields: [], record_count: 0, range_start: null, range_end: null, dimensions: [], measures: [], omissions: ["bulk_rows", "row_samples", "distributions", "uncomputed_statistics"] as const, capabilities: [], analytical_validated: false as const };
const search = { version: "2", source: support, schema_revision: "support-demo.v1", search_policy: "m3-lexical.v1", request: { version: "2", source: support, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 1 }, scanned_count: 16, matched_count: 0, returned_count: 0, omitted_hit_count: 0, hits: [], coverage: "targeted_lexical_search", limitations: ["Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence.", "No hits means this lexical query found no matching messages in the declared filtered scope."], analytical_validated: false } as const;
const queryLimits = { max_sql_bytes: 8000, max_rows: 20, max_columns: 16, max_column_bytes: 64, max_text_bytes: 256, max_result_bytes: 16384, progress_interval: 100, max_progress_callbacks: 500, query_deadline_ms: 250, sqlite_heap_bytes: 8388608, sqlite_limits: { sql_length: 8000, length: 65536, column: 16, expr_depth: 30, compound_select: 8, vdbe_op: 10000, function_arg: 8, attached: 0, like_pattern_length: 128, variable_number: 0, trigger_depth: 0 } } as const;
const catalog = { version: "2", catalog_revision: "m4-catalog.v1", entries: [{ source, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1", kind: "structured", display_name: "Sales demo", description: "Synthetic net sales lines for bounded structured analysis.", capability_help: { profile: "Summarize fields and bounded statistics.", query: "Ask for read-only totals, groups, rankings or period comparisons." }, capabilities: ["profile", "query"], record_count: 24, manifest_bytes: 1025, scope: "complete_immutable_fixture" }, { source: support, schema_revision: "support-demo.v1", profile_revision: null, kind: "messages", display_name: "Support messages", description: "Synthetic support messages for targeted lexical examples.", capability_help: { search: "Find matching messages with exact IDs and source quotes; hits do not establish prevalence." }, capabilities: ["search"], record_count: 16, manifest_bytes: 3091, scope: "complete_immutable_fixture" }] } as const;
async function wire(payload: unknown, job: string | null = id, run: string | null = id): Promise<string> { return JSON.stringify({ version: "2", job_id: job, run_id: run, receipt_id: job, payload, payload_sha256: await payloadSha256(payload), runtime }); }
async function queryResult(job: string, run = job): Promise<unknown> {
  const actual_sql = "SELECT 1";
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(actual_sql));
  const sql_sha256 = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  const rows = [[{ type: "integer", value: "1", exact: true }]];
  return { version: "2", receipt_id: job, job_id: job, source, schema_revision: "sales-demo.v1", engine_policy: "m2-sqlite.v1", actual_sql, sql_sha256, columns: ["value"], rows, row_count: 1, result_sha256: await payloadSha256({ columns: ["value"], rows }), coverage: "complete_query_result", truncated: false, analytical_validated: false, limits: queryLimits, runtime: { python_version: runtime.python_version, sqlite_version: runtime.sqlite_version, runtime_mode: "local", build_revision: null, worker_version_id: null } };
}
function env(fetch: Fetcher): Env { return { TOOLS: fetch, RUNTIME_MODE: "local", AppAgent: {} as Env["AppAgent"] }; }
function state(selected = source): BridgeState { const session = initialSessionState(); session.selected_source = selected; session.selected_catalog_revision = "m4-catalog.v1"; return { version: "1", session, result: null, result_kind: null, revoked: false, expired: false, outcomes: [] }; }
function harness(fetch: Fetcher, initial = state()): { agent: AppAgent; jobs: Promise<unknown>[]; state: () => BridgeState } { const jobs: Promise<unknown>[] = []; const agent = new AppAgent({ waitUntil: (promise: Promise<unknown>) => jobs.push(promise) } as never, env(fetch)); (agent as unknown as { state: BridgeState }).state = initial; return { agent, jobs, state: () => (agent as unknown as { state: BridgeState }).state }; }
function post(path: string, body: Record<string, unknown>): Request { return new Request(`https://app.test${path}`, { method: "POST", body: JSON.stringify(body), headers: { "content-type": "application/json" } }); }
function tools(delay = false): { fetcher: Fetcher; pending: { resolve: (response: Response) => void } } { let resolve = (_response: Response): void => undefined; const pending = { resolve: (response: Response): void => resolve(response) }; const fetcher = { fetch: async (request: Request) => { const path = new URL(request.url).pathname; if (path === "/v2/catalog") return new Response(await wire(catalog, null, null)); if (delay) return new Promise<Response>((done) => { resolve = done; }); const body = JSON.parse(await request.text()) as { job_id: string; run_id: string }; const payload = path.endsWith("search") ? search : path.endsWith("query") ? await queryResult(body.job_id, body.run_id) : profile; return new Response(await wire(payload, body.job_id, body.run_id)); } } as unknown as Fetcher; return { fetcher, pending }; }

describe("native app lifecycle", () => {
  it("completes a profile job, persists refresh state, and replays its owned outcome", async () => {
    const test = harness(tools().fetcher);
    expect((await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id }))).status).toBe(202);
    await test.jobs[0];
    expect(test.state().session.active_job?.phase).toBe("completed");
    const refreshed = await test.agent.onRequest(new Request("https://app.test/api/state"));
    expect((await refreshed.json() as { last_result: unknown }).last_result).not.toBeNull();
    const replay = await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id }));
    expect(replay.status).toBe(200);
  });
  it("selects support, runs targeted search, and rejects a sales capability mismatch", async () => {
    const test = harness(tools().fetcher);
    expect((await test.agent.onRequest(post("/api/source", { version: "2", source: support }))).status).toBe(200);
    expect((await test.agent.onRequest(post("/api/search", { version: "2", request_id: id, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 1 }))).status).toBe(202);
    await test.jobs[0];
    expect(test.state().result_kind).toBe("search");
    expect((await test.agent.onRequest(post("/api/query", { version: "2", request_id: id, question: "x", sql: "SELECT 1", max_rows: 1 }))).status).toBe(422);
  });
  it("completes a generic query with a validated result", async () => {
    const test = harness(tools().fetcher);
    expect((await test.agent.onRequest(post("/api/query", { version: "2", request_id: id, question: "one", sql: "SELECT 1", max_rows: 1 }))).status).toBe(202);
    await test.jobs[0];
    expect(test.state().result_kind).toBe("query");
    expect(test.state().session.active_job?.phase).toBe("completed");
  });
  it("cancels and resets, fencing a late completion", async () => {
    const pending = tools(true); const test = harness(pending.fetcher);
    expect((await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id }))).status).toBe(202);
    expect((await test.agent.onRequest(post("/api/cancel", { version: "2" }))).status).toBe(200);
    expect(test.state().session.active_job?.phase).toBe("cancelled");
    expect((await test.agent.onRequest(post("/api/reset", { version: "2" }))).status).toBe(200);
    pending.pending.resolve(new Response(await wire(profile, id, id))); await test.jobs[0];
    expect(test.state().revoked).toBe(true); expect(test.state().result).toBeNull();
  });
  it("interrupts expired work and rejects every later request until reset", async () => {
    const pending = tools(true); const test = harness(pending.fetcher);
    await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id })); await Promise.resolve();
    const current = test.state(); (test.agent as unknown as { state: BridgeState }).state = { ...current, session: { ...current.session, expires_at: "2020-01-01T00:00:00.000Z" } };
    expect((await test.agent.onRequest(new Request("https://app.test/api/state"))).status).toBe(410);
    expect(test.state().session.active_job?.phase).toBe("interrupted");
    expect((await test.agent.onRequest(new Request("https://app.test/api/state"))).status).toBe(410);
    pending.pending.resolve(new Response(await wire(profile, id, id))); await test.jobs[0];
    expect(test.state().session.active_job?.phase).toBe("interrupted");
  });
  it("reconciles a queued job after its deadline", async () => {
    const pending = tools(true); const test = harness(pending.fetcher);
    await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id })); await Promise.resolve();
    const current = test.state(); (test.agent as unknown as { state: BridgeState }).state = { ...current, session: { ...current.session, active_job: { ...current.session.active_job!, deadline_at: "2020-01-01T00:00:00.000Z" } } };
    expect((await test.agent.onRequest(new Request("https://app.test/api/state"))).status).toBe(200);
    expect(test.state().session.active_job?.phase).toBe("interrupted");
    pending.pending.resolve(new Response(await wire(profile, id, id))); await test.jobs[0];
    expect(test.state().session.active_job?.phase).toBe("interrupted");
  });
  it("isolates opaque cookies and rejects unsafe transports", async () => {
    const names: string[] = []; const resolver = async (_env: Env, name: string) => { names.push(name); return { fetch: async () => Response.json({ ok: true }) }; };
    await publicFetch(new Request("https://app.test/api/state"), env({} as Fetcher), resolver);
    await publicFetch(new Request("https://app.test/api/state", { headers: { cookie: `di_session=${"b".repeat(64)}` } }), env({} as Fetcher), resolver);
    expect(names[0]).not.toBe(names[1]);
    expect((await publicFetch(new Request("https://app.test/api/state", { headers: { upgrade: "websocket" } }), env({} as Fetcher), resolver)).status).toBe(400);
    expect((await publicFetch(new Request("https://app.test/api/reset", { method: "POST", headers: { origin: "https://other.test" } }), env({} as Fetcher), resolver)).status).toBe(403);
  });
  it("fails safely for corrupt durable state", async () => {
    const test = harness(tools().fetcher, { ...state(), session: null as unknown as BridgeState["session"] });
    expect((await test.agent.onRequest(new Request("https://app.test/api/state"))).status).toBe(503);
  });
});

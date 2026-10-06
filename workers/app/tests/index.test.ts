import { describe, expect, it, vi } from "vitest";
vi.mock("agents", () => ({ Agent: class {
  state: unknown; env: unknown; ctx: { waitUntil(promise: Promise<unknown>): void };
  constructor(ctx: { waitUntil(promise: Promise<unknown>): void }, env: unknown) { this.ctx = ctx; this.env = env; }
  setState(value: unknown): void { this.state = value; }
}, getAgentByName: vi.fn() }));
import { AppAgent, publicFetch, trustedRuntime, type BridgeState, type Env } from "../src/index";
import { payloadSha256 } from "../src/policy";
import { initialSessionState } from "../../agent/src/v2-state";

const id = "11111111-1111-4111-8111-111111111111";
const source = { version: "1", source_id: "sales", snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f", meaning_revision: "sales-demo.v1" } as const;
const support = { version: "1", source_id: "support", snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536", meaning_revision: "support-demo.v1" } as const;
const runtime = { python_version: "3.12.7", sqlite_version: "3.46.1", runtime_mode: "local" as const, build_revision: null, worker_version_id: null, service_contract_revision: "m4-service.v1" as const };
type TestRuntime = Omit<typeof runtime, "runtime_mode" | "build_revision" | "worker_version_id"> & { runtime_mode: "local" | "deployed"; build_revision: string | null; worker_version_id: string | null };
const profile = { version: "2", source, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1", fields: [], record_count: 0, range_start: null, range_end: null, dimensions: [], measures: [], omissions: ["bulk_rows", "row_samples", "distributions", "uncomputed_statistics"] as const, capabilities: [], analytical_validated: false as const };
const search = { version: "2", source: support, schema_revision: "support-demo.v1", search_policy: "m3-lexical.v1", request: { version: "2", source: support, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 1 }, scanned_count: 16, matched_count: 0, returned_count: 0, omitted_hit_count: 0, hits: [], coverage: "targeted_lexical_search", limitations: ["Targeted lexical examples cannot establish whole-corpus trends, prevalence or absence.", "No hits means this lexical query found no matching messages in the declared filtered scope."], analytical_validated: false } as const;
const queryLimits = { max_sql_bytes: 8000, max_rows: 20, max_columns: 16, max_column_bytes: 64, max_text_bytes: 256, max_result_bytes: 16384, progress_interval: 100, max_progress_callbacks: 500, query_deadline_ms: 250, sqlite_heap_bytes: 8388608, sqlite_limits: { sql_length: 8000, length: 65536, column: 16, expr_depth: 30, compound_select: 8, vdbe_op: 10000, function_arg: 8, attached: 0, like_pattern_length: 128, variable_number: 0, trigger_depth: 0 } } as const;
const catalog = { version: "2", catalog_revision: "m4-catalog.v1", entries: [{ source, schema_revision: "sales-demo.v1", profile_revision: "m3-profile.v1", kind: "structured", display_name: "Sales demo", description: "Synthetic net sales lines for bounded structured analysis.", capability_help: { profile: "Summarize fields and bounded statistics.", query: "Ask for read-only totals, groups, rankings or period comparisons." }, capabilities: ["profile", "query"], record_count: 24, manifest_bytes: 1025, scope: "complete_immutable_fixture" }, { source: support, schema_revision: "support-demo.v1", profile_revision: null, kind: "messages", display_name: "Support messages", description: "Synthetic support messages for targeted lexical examples.", capability_help: { search: "Find matching messages with exact IDs and source quotes; hits do not establish prevalence." }, capabilities: ["search"], record_count: 16, manifest_bytes: 3091, scope: "complete_immutable_fixture" }] } as const;
async function wire(payload: unknown, job: string | null = id, run: string | null = id, responseRuntime: TestRuntime = runtime): Promise<string> { return JSON.stringify({ version: "2", job_id: job, run_id: run, receipt_id: job, payload, payload_sha256: await payloadSha256(payload), runtime: responseRuntime }); }
async function queryResult(job: string, run = job): Promise<unknown> {
  const actual_sql = "SELECT 1";
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(actual_sql));
  const sql_sha256 = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  const rows = [[{ type: "integer", value: "1", exact: true }]];
  return { version: "2", receipt_id: job, job_id: job, source, schema_revision: "sales-demo.v1", engine_policy: "m2-sqlite.v1", actual_sql, sql_sha256, columns: ["value"], rows, row_count: 1, result_sha256: await payloadSha256({ columns: ["value"], rows }), coverage: "complete_query_result", truncated: false, analytical_validated: false, limits: queryLimits, runtime: { python_version: runtime.python_version, sqlite_version: runtime.sqlite_version, runtime_mode: "local", build_revision: null, worker_version_id: null } };
}
const idleAI = { run: async () => ({ response: "{}" }) } as unknown as Env["AI"];
function agentBinding(admitted = true): Fetcher { return { fetch: async () => Response.json({ version: "1", admitted }) } as unknown as Fetcher; }
function env(fetch: Fetcher, AI: Env["AI"] = idleAI, AGENT: Fetcher = agentBinding(), runtimeConfig: Partial<Pick<Env, "RUNTIME_MODE" | "TOOLS_BUILD_REVISION" | "TOOLS_WORKER_VERSION_ID">> = {}): Env { return { TOOLS: fetch, AI, AGENT, PLANNER_BUDGET_TOKEN: "p".repeat(32), RUNTIME_MODE: "local", AppAgent: {} as Env["AppAgent"], ...runtimeConfig }; }
function state(selected = source): BridgeState { const session = initialSessionState(); session.selected_source = selected; session.selected_catalog_revision = "m4-catalog.v1"; return { version: "1", session, result: null, result_kind: null, revoked: false, expired: false, outcomes: [], planner: null, model_calls: 0 }; }
function harness(fetch: Fetcher, initial = state(), AI: Env["AI"] = idleAI, AGENT: Fetcher = agentBinding(), runtimeConfig: Partial<Pick<Env, "RUNTIME_MODE" | "TOOLS_BUILD_REVISION" | "TOOLS_WORKER_VERSION_ID">> = {}): { agent: AppAgent; jobs: Promise<unknown>[]; state: () => BridgeState } { const jobs: Promise<unknown>[] = []; const agent = new AppAgent({ waitUntil: (promise: Promise<unknown>) => jobs.push(promise) } as never, env(fetch, AI, AGENT, runtimeConfig)); (agent as unknown as { state: BridgeState }).state = initial; return { agent, jobs, state: () => (agent as unknown as { state: BridgeState }).state }; }
function model(value: unknown): Env["AI"] { return { run: async () => ({ response: JSON.stringify(value) }) } as unknown as Env["AI"]; }
const planned = { version: "1", request_id: id, source, status: "plan", mode: "query", sql: "SELECT 1", query: null, channel: null, customer: null, start: null, end: null, clarification: null } as const;
const clarification = { version: "1", request_id: id, source, status: "clarify", mode: "clarify", sql: null, query: null, channel: null, customer: null, start: null, end: null, clarification: "Which period should I compare?" } as const;
function post(path: string, body: Record<string, unknown>): Request { return new Request(`https://app.test${path}`, { method: "POST", body: JSON.stringify(body), headers: { "content-type": "application/json" } }); }
function tools(delay = false, responseRuntime: TestRuntime = runtime): { fetcher: Fetcher; pending: { resolve: (response: Response) => void }; calls: string[] } { let resolve = (_response: Response): void => undefined; const calls: string[] = []; const pending = { resolve: (response: Response): void => resolve(response) }; const fetcher = { fetch: async (request: Request) => { const path = new URL(request.url).pathname; calls.push(path); if (path === "/v2/catalog") return new Response(await wire(catalog, null, null, responseRuntime)); if (delay) return new Promise<Response>((done) => { resolve = done; }); const body = JSON.parse(await request.text()) as { job_id: string; run_id: string }; const payload = path.endsWith("search") ? search : path.endsWith("query") ? await queryResult(body.job_id, body.run_id) : profile; return new Response(await wire(payload, body.job_id, body.run_id, responseRuntime)); } } as unknown as Fetcher; return { fetcher, pending, calls }; }

describe("native app lifecycle", () => {
  it("plans an ask, persists its proposal, and replays the owned state", async () => {
    const test = harness(tools().fetcher, state(), model(planned));
    expect((await test.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" }))).status).toBe(202);
    await test.jobs[0];
    expect(test.state().planner?.result.kind).toBe("proposal"); expect(test.state().model_calls).toBe(1);
    expect(Date.parse(test.state().session.active_job!.deadline_at) - Date.parse(test.state().session.active_job!.started_at)).toBe(60_000);
    expect((await test.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" }))).status).toBe(200);
    expect((await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id.replaceAll("1", "4") }))).status).toBe(202);
    await test.jobs.at(-1); expect(test.state().planner).toBeNull();
  });
  it("persists clarification and safely classifies quota failures", async () => {
    const clarify = harness(tools().fetcher, state(), model(clarification));
    await clarify.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "compare periods" })); await clarify.jobs[0];
    expect(clarify.state().session.active_job?.phase).toBe("awaiting_clarification"); expect(clarify.state().planner?.result.kind).toBe("clarification");
    expect(clarify.state().session.active_job?.clarification).toMatchObject({ question: clarification.clarification });
    expect((await clarify.agent.onRequest(post("/api/cancel", { version: "2" }))).status).toBe(200);
    expect(clarify.state().session.active_job?.phase).toBe("awaiting_clarification");
    const quota = harness(tools().fetcher, state(), { run: async () => { throw Object.assign(new Error("quota"), { code: 4006 }); } } as unknown as Env["AI"]);
    await quota.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" })); await quota.jobs[0];
    expect(quota.state().planner?.result).toMatchObject({ kind: "failure", code: "model_quota" });
    const deniedTools = tools(); const denied = harness(deniedTools.fetcher, state(), model(planned), agentBinding(false));
    await denied.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" })); await denied.jobs[0];
    expect(deniedTools.calls).toEqual([]); expect(denied.state().planner?.result).toMatchObject({ kind: "failure", code: "budget_exhausted" });
  });
  it("fails closed on deployed tool provenance before profiling or model use", async () => {
    const build = "a".repeat(40); const worker = "22222222-2222-4222-8222-222222222222";
    const responses = tools(false, { ...runtime, runtime_mode: "deployed", build_revision: build, worker_version_id: worker });
    const test = harness(responses.fetcher, state(), model(planned), agentBinding(), { RUNTIME_MODE: "deployed", TOOLS_BUILD_REVISION: "b".repeat(40), TOOLS_WORKER_VERSION_ID: worker });
    await test.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" })); await test.jobs[0];
    expect(responses.calls).toEqual(["/v2/catalog"]); expect(test.state().planner?.result).toMatchObject({ kind: "failure", code: "model_unavailable" });
  });
  it("exhausts the persisted model budget and fences cancellation", async () => {
    const exhausted = harness(tools().fetcher, { ...state(), model_calls: 3 }, model(planned));
    await exhausted.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" })); await exhausted.jobs[0];
    expect(exhausted.state().session.active_job?.phase).toBe("budget_exhausted"); expect(exhausted.state().planner?.result).toMatchObject({ kind: "failure", code: "budget_exhausted" });
    const pending = tools(true); const canceled = harness(pending.fetcher, state(), model(planned));
    await canceled.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" })); await Promise.resolve();
    expect((await canceled.agent.onRequest(post("/api/cancel", { version: "2" }))).status).toBe(200);
    pending.pending.resolve(new Response(await wire(profile, id, id))); await canceled.jobs[0];
    expect(canceled.state().planner).toBeNull(); expect(canceled.state().model_calls).toBe(0);
  });
  it("clears a prior tool receipt when an ask starts", async () => {
    const test = harness(tools().fetcher, state(), model(planned));
    await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id })); await test.jobs[0];
    expect(test.state().result_kind).toBe("profile");
    const queued = await test.agent.onRequest(post("/api/ask", { version: "2", request_id: id.replaceAll("1", "2"), question: "total sales" }));
    expect((await queued.json() as { last_result: unknown; planner: unknown }).last_result).toBeNull();
    await test.jobs.at(-1);
  });
  it("fences a cancellation that arrives during global admission", async () => {
    let resolveAdmission: (response: Response) => void = () => undefined;
    const pendingAgent = { fetch: async () => new Promise<Response>((resolve) => { resolveAdmission = resolve; }) } as unknown as Fetcher;
    const responses = tools(); const test = harness(responses.fetcher, state(), model(planned), pendingAgent);
    await test.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "total sales" })); await Promise.resolve();
    await test.agent.onRequest(post("/api/cancel", { version: "2" }));
    resolveAdmission(Response.json({ version: "1", admitted: true })); await test.jobs[0];
    expect(responses.calls).toEqual([]); expect(test.state().planner).toBeNull();
  });
  it("rejects an oversized ask before dispatch", async () => {
    const test = harness(tools().fetcher, state(), model(planned));
    expect((await test.agent.onRequest(post("/api/ask", { version: "2", request_id: id, question: "x".repeat(1025) }))).status).toBe(400);
    expect(test.jobs).toHaveLength(0);
  });
  it("completes a profile job, persists refresh state, and replays its owned outcome", async () => {
    const test = harness(tools().fetcher);
    expect((await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id }))).status).toBe(202);
    await test.jobs[0];
    const refreshed = await test.agent.onRequest(new Request("https://app.test/api/state"));
    expect((await refreshed.json() as { last_result: unknown }).last_result).not.toBeNull();
    const replay = await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id }));
    expect(replay.status).toBe(200);
    expect((await test.agent.onRequest(post("/api/query", { version: "2", request_id: id, question: "changed", sql: "SELECT 1", max_rows: 1 }))).status).toBe(409);
    expect((await test.agent.onRequest(post("/api/query", { version: "2", request_id: id.replaceAll("1", "2"), question: "one", sql: "SELECT 1", max_rows: 1 }))).status).toBe(202); await test.jobs.at(-1); expect(test.state().result_kind).toBe("query");
  });
  it("evicts the oldest bounded replay outcome", async () => {
    const test = harness(tools().fetcher);
    for (const request_id of [id, id.replaceAll("1", "2"), id.replaceAll("1", "3")]) {
      await test.agent.onRequest(post("/api/profile", { version: "2", request_id })); await test.jobs.at(-1);
    }
    expect((await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id }))).status).toBe(409);
  });
  it("selects support, runs targeted search, and rejects a sales capability mismatch", async () => {
    const test = harness(tools().fetcher);
    expect((await test.agent.onRequest(post("/api/source", { version: "2", source: support }))).status).toBe(200);
    expect((await test.agent.onRequest(post("/api/search", { version: "2", request_id: id, query: "export", channel: null, customer: null, start: null, end: null, max_hits: 1 }))).status).toBe(202);
    await test.jobs[0];
    expect(test.state().result_kind).toBe("search");
    expect((await test.agent.onRequest(post("/api/query", { version: "2", request_id: id, question: "x", sql: "SELECT 1", max_rows: 1 }))).status).toBe(422);
  });
  it("cancels and resets, fencing a late completion", async () => {
    const pending = tools(true); const test = harness(pending.fetcher);
    expect((await test.agent.onRequest(post("/api/profile", { version: "2", request_id: id }))).status).toBe(202);
    expect((await test.agent.onRequest(post("/api/cancel", { version: "2" }))).status).toBe(200);
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
    const current = test.state(); const epoch = current.session.cancel_epoch + 1; (test.agent as unknown as { state: BridgeState }).state = { ...current, session: { ...current.session, cancel_epoch: epoch, active_job: { ...current.session.active_job!, deadline_at: "2020-01-01T00:00:00.000Z", phase: "cancel_requested", cancel_epoch: epoch } } };
    expect((await test.agent.onRequest(new Request("https://app.test/api/state"))).status).toBe(200);
    expect(test.state().session.active_job?.phase).toBe("cancelled");
    pending.pending.resolve(new Response(await wire(profile, id, id))); await test.jobs[0];
  });
  it("isolates opaque cookies and rejects unsafe transports", async () => {
    const names: string[] = []; const resolver = async (_env: Env, name: string) => { names.push(name); return { fetch: async () => Response.json({ ok: true }) }; };
    await publicFetch(new Request("https://app.test/api/state"), env({} as Fetcher), resolver);
    await publicFetch(new Request("https://app.test/api/state", { headers: { cookie: `di_session=${"b".repeat(64)}` } }), env({} as Fetcher), resolver);
    expect(names[0]).not.toBe(names[1]);
    expect((await publicFetch(new Request("https://app.test/api/state", { headers: { upgrade: "websocket" } }), env({} as Fetcher), resolver)).status).toBe(400);
    expect((await publicFetch(new Request("https://app.test/api/reset", { method: "POST", headers: { origin: "https://other.test" } }), env({} as Fetcher), resolver)).status).toBe(403);
    const rotated = await publicFetch(new Request("https://app.test/api/reset", { method: "POST", headers: { cookie: `di_session=${"b".repeat(64)}`, origin: "https://app.test" } }), env({} as Fetcher), resolver); expect(rotated.headers.get("set-cookie")).not.toContain("b".repeat(64)); expect((await publicFetch(new Request("https://app.test/api/unknown"), env({} as Fetcher), resolver)).status).toBe(404);
  });
  it("fails safely for corrupt durable state", async () => {
    const test = harness(tools().fetcher, { ...state(), session: null as unknown as BridgeState["session"] });
    expect((await test.agent.onRequest(new Request("https://app.test/api/state"))).status).toBe(503);
  });
  it("binds deployed receipts to the private tools identity", () => {
    const receipt = { runtime: { ...runtime, runtime_mode: "deployed", build_revision: "a".repeat(40), worker_version_id: "22222222-2222-4222-8222-222222222222" } } as Parameters<typeof trustedRuntime>[1];
    const deployed = { ...env({} as Fetcher), RUNTIME_MODE: "deployed" as const, TOOLS_BUILD_REVISION: "a".repeat(40), TOOLS_WORKER_VERSION_ID: "22222222-2222-4222-8222-222222222222" };
    expect(trustedRuntime(deployed, receipt)).toBe(true);
    expect(trustedRuntime({ ...deployed, TOOLS_WORKER_VERSION_ID: "33333333-3333-4333-8333-333333333333" }, receipt)).toBe(false);
  });
});

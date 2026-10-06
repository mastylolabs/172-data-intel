import { describe, expect, it, vi } from "vitest";
import meta from "./fixtures/metadata.json";
import receipt from "./fixtures/result.json";
import { metadata } from "../src/contracts";
import { SALES_SOURCE, finishJob, initialSessionState, type SessionStateV2 } from "../src/v2-state";
vi.mock("agents", () => ({
  Agent: class {
    state: unknown;
    env: unknown;
    ctx: { storage: { get: ReturnType<typeof vi.fn>; put: ReturnType<typeof vi.fn> } };
    constructor(_ctx: unknown, env: unknown) {
      this.env = env;
      this.ctx = {
        storage: { get: vi.fn().mockResolvedValue(undefined), put: vi.fn().mockResolvedValue(undefined) },
      };
    }
    setState(next: unknown): void {
      this.state = next;
    }
  },
}));
vi.mock("cloudflare:workers", () => ({
  DurableObject: class {
    protected ctx: unknown;
    protected env: unknown;
    constructor(ctx: unknown, env: unknown) {
      this.ctx = ctx;
      this.env = env;
    }
  },
}));
const { default: worker, ProofAgent, ProofBudget, buildPlanRequest, runPlanModel } = await import("../src/index");
type Env = import("../src/index").Env;
const input = {
  version: "1",
  request_id: receipt.job_id,
  question: "Total?",
  sql: receipt.actual_sql,
  max_rows: 20,
};
function setup() {
  const tools = vi.fn().mockImplementation(async (url: string) =>
    Response.json(url.endsWith("metadata") ? meta : receipt),
  );
  const aiRun = vi.fn().mockResolvedValue({
    response: JSON.stringify({ status: "plan", sql: "SELECT 1", rationale: "test plan" }),
  });
  const budgetFetch = vi.fn().mockImplementation(async () => Response.json({ version: "1", admitted: true }));
  const budgetId = {} as DurableObjectId;
  const lookup = vi.fn((name: string) => name as unknown as DurableObjectId);
  const env = {
    PROOF_TOKEN: "t".repeat(32),
    RUNTIME_MODE: "deployed",
    BUILD_REVISION: "b".repeat(40),
    CF_VERSION_METADATA: { id: "23456789-1234-4234-8234-123456789abc" },
    TOOLS: { fetch: tools },
    AI: { run: aiRun },
    ProofBudget: { idFromName: vi.fn(() => budgetId), get: vi.fn(() => ({ fetch: budgetFetch })) },
    ProofAgent: { idFromName: lookup, get: () => ({ fetch: (r: Request) => agent.onRequest(r) }) },
  } as unknown as Env;
  const agent = new ProofAgent({} as DurableObjectState, env);
  Object.assign(agent, { state: agent.initialState });
  return { agent, env, tools, lookup, aiRun, budgetFetch };
}
function request(path: string, body?: unknown, extra: Record<string, string> = {}): Request {
  return new Request(`https://proof.example${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: { authorization: `Bearer ${"t".repeat(32)}`, origin: "https://proof.example", ...extra },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
function sessionStorage(agent: InstanceType<typeof ProofAgent>): {
  get: ReturnType<typeof vi.fn>; put: ReturnType<typeof vi.fn>;
} {
  return (agent as unknown as { ctx: { storage: ReturnType<typeof sessionStorage> } }).ctx.storage;
}
describe("restricted native proof bridge", () => {
  it("denies auth, public routes, foreign origins, upgrades and wrong methods before lookup", async () => {
    const { env, lookup } = setup();
    for (const [r, status] of [
      [request("/proof/state", undefined, { authorization: "bad" }), 403],
      [request("/agents/proof-agent/arbitrary"), 404],
      [request("/proof/source", input, { origin: "https://evil.example" }), 403],
      [request("/proof/state", undefined, { upgrade: "websocket" }), 403],
      [request("/proof/source"), 404],
    ] as const) {
      expect((await worker.fetch(r, env)).status).toBe(status);
    }
    expect(lookup).not.toHaveBeenCalled();
  });
  it("hashes cookies, resumes a session, and allocates isolated fresh sessions", async () => {
    const { env, lookup } = setup();
    const first = await worker.fetch(request("/proof/state"), env);
    const cookie = first.headers.get("set-cookie")!;
    expect(cookie).toContain("Secure; HttpOnly; SameSite=Strict");
    await worker.fetch(request("/proof/state", undefined, { cookie }), env);
    expect(lookup.mock.calls[0][0]).toBe(lookup.mock.calls[1][0]);
    expect(cookie).not.toContain(lookup.mock.calls[0][0]);
    await worker.fetch(request("/proof/state"), env);
    expect(lookup.mock.calls[2][0]).not.toBe(lookup.mock.calls[0][0]);
  });
  it("persists the v2 session separately and fences source/reset changes", async () => {
    const { env, agent } = setup();
    const session = await worker.fetch(request("/v2/session"), env);
    expect(session.status).toBe(200);
    expect((await session.json() as { selected_source: null }).selected_source).toBeNull();
    const denied = await worker.fetch(request("/v2/session", undefined, { authorization: "bad" }), env);
    expect((await denied.json() as { version: string }).version).toBe("2");
    const support = await worker.fetch(
      request("/v2/source", { version: "2", source: {
        version: "1",
        source_id: "support",
        snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
        meaning_revision: "support-demo.v1",
      } }),
      env,
    );
    expect(support.status).toBe(200);
    const supportBody = await support.json() as { selected_source: { source_id: string } };
    expect(supportBody.selected_source.source_id).toBe("support");
    const storage = sessionStorage(agent);
    storage.get.mockResolvedValueOnce(storage.put.mock.calls.at(-1)?.[1]);
    const refreshed = await agent.onRequest(new Request("https://proof.example/v2/session"));
    expect((await refreshed.json() as { selected_source: { source_id: string } }).selected_source.source_id).toBe("support");
    expect((await worker.fetch(request("/v2/source", { source: supportBody.selected_source }), env)).status).toBe(400);
    const reset = await worker.fetch(request("/v2/reset", { version: "2" }), env);
    expect((await reset.json() as { selected_source: null }).selected_source).toBeNull();
  });
  it("rotates v2 reset identity, denies the old cookie and leaves v1 state intact", async () => {
    const { env, agent, lookup } = setup();
    const storage = sessionStorage(agent);
    storage.get.mockImplementation(async () => storage.put.mock.calls.at(-1)?.[1]);
    const before = structuredClone(agent.state);
    const opened = await worker.fetch(request("/v2/session"), env);
    const cookie = opened.headers.get("set-cookie")!;
    const reset = await worker.fetch(request("/v2/reset", { version: "2" }, { cookie }), env);
    expect(reset.status).toBe(200);
    expect(reset.headers.get("set-cookie")).not.toBe(cookie);
    expect(storage.put).toHaveBeenLastCalledWith("m4-v2-session", { version: "2", revoked: true });
    const denied = await worker.fetch(request("/v2/session", undefined, { cookie }), env);
    expect(denied.status).toBe(403);
    expect(await denied.json()).toMatchObject({ version: "2", code: "access_denied" });
    expect(lookup.mock.calls[0][0]).toBe(lookup.mock.calls[2][0]);
    expect(agent.state).toEqual(before);
    expect((await worker.fetch(request("/proof/state", undefined, { cookie }), env)).status).toBe(200);
  });
  it("reconciles expired sessions once, fences work and permits only reset", async () => {
    const { env, agent, tools, aiRun } = setup();
    const storage = sessionStorage(agent);
    const expires = new Date(Date.now() - 1000).toISOString();
    const state: SessionStateV2 = {
      ...initialSessionState(), selected_source: SALES_SOURCE, expires_at: expires,
      active_job: {
        job_id: crypto.randomUUID(), request_id: crypto.randomUUID(), input_sha256: "a".repeat(64),
        source: SALES_SOURCE, generation: 0, cancel_epoch: 0, phase: "planning",
        started_at: expires, deadline_at: new Date(Date.now() + 60_000).toISOString(),
        active_run_id: crypto.randomUUID(), error: null, clarification: null,
      },
    };
    let persisted: unknown = state;
    storage.get.mockImplementation(async () => persisted);
    storage.put.mockImplementation(async (_key: string, value: unknown) => { persisted = value; });
    const read = await worker.fetch(request("/v2/session"), env);
    expect(read.status).toBe(410);
    const cookie = read.headers.get("set-cookie")!;
    expect(await read.json()).toMatchObject({ version: "2", code: "session_expired" });
    const expired = (persisted as { state: SessionStateV2 }).state;
    expect(expired).toMatchObject({ expires_at: expires, selected_source: null, generation: 1, cancel_epoch: 1 });
    expect(expired.active_job).toMatchObject({ phase: "interrupted", active_run_id: null });
    expect(expired.request_journal).toHaveLength(1);
    expect(expired.request_journal[0].terminal_code).toBe("expired");
    expect(() => finishJob(expired, state.active_job!.job_id, 0, 0, { phase: "completed", error: null })).toThrow("stale_job");
    for (const path of ["/v2/session", "/v2/source", "/v2/cancel"]) {
      const body = path === "/v2/session" ? undefined : { version: "2", source: SALES_SOURCE };
      const response = await worker.fetch(request(path, body, { cookie }), env);
      expect(response.status).toBe(410);
      expect(response.headers.get("set-cookie")).toBe(cookie);
    }
    expect(storage.put).toHaveBeenCalledTimes(1);
    expect(tools).not.toHaveBeenCalled();
    expect(aiRun).not.toHaveBeenCalled();
    expect((await worker.fetch(request("/v2/reset", { version: "2" }), env)).status).toBe(200);
  });
  it("preserves corrupt v2 records and retains cookie identity when reset fails", async () => {
    const { env, agent } = setup();
    const storage = sessionStorage(agent);
    for (const corrupt of [{ version: "2", secret: "sentinel" }, { version: "2", expired: true, state: null }]) {
      storage.get.mockResolvedValue(corrupt);
      const response = await worker.fetch(request("/v2/reset", { version: "2" }), env);
      expect(response.status).toBe(503);
      expect(await response.text()).not.toContain("sentinel");
    }
    storage.put.mockRejectedValueOnce(new Error("storage failure"));
    storage.get.mockResolvedValue(undefined);
    const opened = await worker.fetch(request("/v2/session"), env);
    const cookie = opened.headers.get("set-cookie")!;
    const failed = await worker.fetch(request("/v2/reset", { version: "2" }, { cookie }), env);
    expect(failed.status).not.toBe(200);
    expect(failed.headers.get("set-cookie")).toBe(cookie);
    expect(storage.put).toHaveBeenCalledTimes(1);
  });
  it("persists server-only source/reset state and refuses support without calls", async () => {
    const { agent, env, tools } = setup();
    expect(() => agent.validateStateChange(agent.initialState, {} as never)).toThrow(
      "access_denied",
    );
    await worker.fetch(request("/proof/source", { version: "1", source: "support" }), env);
    expect(await (await worker.fetch(request("/proof/state"), env)).json()).toMatchObject({
      selected_source: "support",
    });
    expect((await worker.fetch(request("/proof/sql", input), env)).status).toBe(422);
    expect((await worker.fetch(request("/proof/query", input), env)).status).toBe(422);
    const initial = await worker.fetch(request("/proof/state"), env);
    const cookie = initial.headers.get("set-cookie")!;
    const reset = await worker.fetch(request("/proof/reset", { version: "1" }, { cookie }), env);
    expect(reset.headers.get("set-cookie")).not.toBe(cookie);
    expect(agent.state).toMatchObject({ ...agent.initialState, revoked: true });
    expect((await worker.fetch(request("/proof/state", undefined, { cookie }), env)).status).toBe(403);
    expect(tools).not.toHaveBeenCalled();
  });
  it("stores an exact Python receipt with separate Agent provenance", async () => {
    const { env, agent, tools } = setup();
    expect((await worker.fetch(request("/proof/sql", input), env)).status).toBe(200);
    expect(agent.state.receipt).toMatchObject({
      proof_kind: "engine",
      ai_chain_complete: false,
      model_calls: 0,
      analytical_validated: false,
      rows: receipt.rows,
      agent_build_revision: "b".repeat(40),
    });
    expect(JSON.parse(tools.mock.calls[1][1].body)).toMatchObject({
      job_id: input.request_id,
      intent: { source: meta.source, sql: input.sql },
    });
  });
  it("plans once from bounded metadata and persists the candidate for refresh", async () => {
    const { env, agent, aiRun, tools } = setup();
    const planRequest = {
      version: "1",
      request_id: crypto.randomUUID(),
      question: "Which region has the highest revenue?",
    };
    const response = await worker.fetch(request("/proof/plan", planRequest), env);
    expect(response.status).toBe(200);
    expect(aiRun).toHaveBeenCalledTimes(1);
    expect(aiRun.mock.calls[0][0]).toBe("@cf/meta/llama-3.3-70b-instruct-fp8-fast");
    expect(aiRun.mock.calls[0][1]).toMatchObject({ max_tokens: 512, temperature: 0 });
    expect(aiRun.mock.calls[0][1].response_format.json_schema.properties).toMatchObject({
      status: { enum: ["plan", "clarify"] },
    });
    expect(JSON.stringify(aiRun.mock.calls[0][1])).toContain("authoritative_metadata");
    expect(tools).toHaveBeenCalledTimes(1);
    expect(agent.state.plan).toEqual({ status: "plan", sql: "SELECT 1", rationale: "test plan" });
    const cookie = response.headers.get("set-cookie")!;
    expect(await (await worker.fetch(request("/proof/state", undefined, { cookie }), env)).json()).toMatchObject({
      plan: { status: "plan", sql: "SELECT 1" },
    });
    expect((await worker.fetch(request("/proof/plan", planRequest), env)).status).toBe(200);
    expect(aiRun).toHaveBeenCalledTimes(1);
    expect((await worker.fetch(request("/proof/plan", { ...planRequest, question: "Other?" }), env)).status).toBe(409);
  });
  it("stores a clarification and refuses malformed or provider errors without leaking details", async () => {
    const { env, aiRun } = setup();
    const requestId = crypto.randomUUID();
    aiRun.mockResolvedValueOnce({ response: JSON.stringify({ status: "clarify", question: "Which date range?" }) });
    expect((await worker.fetch(request("/proof/plan", { version: "1", request_id: requestId, question: "Revenue?" }), env)).status).toBe(200);
    aiRun.mockResolvedValueOnce({ response: "not-json" });
    const malformed = await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }), env);
    expect(malformed.status).toBe(502);
    expect(await malformed.text()).not.toContain("not-json");
    aiRun.mockResolvedValueOnce({
      response: JSON.stringify({ status: "plan", sql: "SELECT 1", rationale: "test plan" }),
      padding: "x".repeat(8193),
    });
    const oversized = await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }), env);
    expect(oversized.status).toBe(502);
    expect(await oversized.json()).toMatchObject({ code: "model_output_invalid" });
    aiRun.mockRejectedValueOnce(new Error("daily free allocation exhausted; secret-token"));
    const quotaRequest = { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" };
    const quota = await worker.fetch(request("/proof/plan", quotaRequest), env);
    expect(quota.status).toBe(429);
    expect(await quota.json()).toMatchObject({ code: "model_quota", provider_reason: "daily_free_allocation", automatic_retry: false });
    expect((await worker.fetch(request("/proof/plan", quotaRequest), env)).status).toBe(409);
    aiRun.mockRejectedValueOnce(new Error("AI_ERROR 3036 account limited; secret-token"));
    const limited = await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }), env);
    expect(await limited.json()).toMatchObject({ code: "model_unavailable", provider_reason: "account_limited" });
    aiRun.mockRejectedValueOnce(new Error("AI_ERROR 3040 out of capacity; secret-token"));
    const capacity = await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }), env);
    expect(await capacity.json()).toMatchObject({ code: "model_unavailable", provider_reason: "out_of_capacity" });
    expect(aiRun).toHaveBeenCalledTimes(6);
  });
  it("retains bounded request identity after a later plan", async () => {
    const { env, agent, aiRun } = setup();
    aiRun
      .mockResolvedValueOnce({ response: JSON.stringify({ status: "plan", sql: "SELECT 1", rationale: "A" }) })
      .mockResolvedValueOnce({ response: JSON.stringify({ status: "plan", sql: "SELECT 2", rationale: "B" }) });
    const first = { version: "1", request_id: crypto.randomUUID(), question: "First?" };
    const second = { version: "1", request_id: crypto.randomUUID(), question: "Second?" };
    await worker.fetch(request("/proof/plan", first), env);
    await worker.fetch(request("/proof/plan", second), env);
    const replay = await worker.fetch(request("/proof/plan", first), env);
    expect(await replay.json()).toMatchObject({ code: "request_outcome_unavailable" });
    expect(agent.state.request_journal).toHaveLength(2);
    expect(aiRun).toHaveBeenCalledTimes(2);
  });
  it("times out a stalled model call without retrying", async () => {
    const { env, aiRun } = setup();
    aiRun.mockImplementationOnce(() => new Promise(() => {}));
    await expect(runPlanModel(env, buildPlanRequest("Revenue?", metadata.parse(meta)), 5)).rejects.toThrow(
      "model_timeout",
    );
    expect(aiRun).toHaveBeenCalledTimes(1);
  });
  it("refuses the durable per-session model budget before dispatch", async () => {
    const { env, agent, aiRun } = setup();
    agent.state.model_starts = Array.from({ length: 12 }, () => Date.now());
    const response = await worker.fetch(
      request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }),
      env,
    );
    expect(response.status).toBe(429);
    expect(await response.json()).toMatchObject({ code: "budget_exhausted", stage: "planning" });
    expect(aiRun).not.toHaveBeenCalled();
  });
  it("refuses the global budget before dispatch", async () => {
    const { env, aiRun, budgetFetch } = setup();
    budgetFetch.mockResolvedValueOnce(Response.json({ version: "1", admitted: false }));
    const response = await worker.fetch(
      request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }),
      env,
    );
    expect(response.status).toBe(429);
    expect(await response.json()).toMatchObject({ code: "budget_exhausted", stage: "planning" });
    expect(aiRun).not.toHaveBeenCalled();
  });
  it("does not call Workers AI for the unsupported support source", async () => {
    const { env, aiRun } = setup();
    await worker.fetch(request("/proof/source", { version: "1", source: "support" }), env);
    const response = await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Find a message" }), env);
    expect(response.status).toBe(422);
    expect(aiRun).not.toHaveBeenCalled();
  });
  it("refuses invalid input without dispatch", async () => {
    const { env, tools } = setup();
    expect((await worker.fetch(request("/proof/sql", { ...input, max_rows: 21 }), env)).status).toBe(
      400,
    );
    expect(tools).not.toHaveBeenCalled();
  });
  it("bootstraps pre-planner Durable Object state before reads", async () => {
    const { env, agent } = setup();
    Object.assign(agent, { state: { version: "1", revision: 3, selected_source: "sales", receipt: null, revoked: false } });
    expect((await worker.fetch(request("/proof/state"), env)).status).toBe(200);
    expect(agent.state.model_starts).toEqual([]);
    expect(agent.state.request_journal).toEqual([]);
    expect(agent.state.plan).toBeNull();
  });
  it("preserves an interrupted legacy request as unavailable", async () => {
    const { env, agent, aiRun } = setup();
    const requestId = crypto.randomUUID();
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("Revenue?"));
    const questionHash = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
    Object.assign(agent, {
      state: {
        version: "1",
        revision: 3,
        selected_source: "sales",
        receipt: null,
        plan: null,
        plan_request_id: `${requestId}:${questionHash}`,
        revoked: false,
      },
    });
    const response = await worker.fetch(
      request("/proof/plan", { version: "1", request_id: requestId, question: "Revenue?" }),
      env,
    );
    expect(response.status).toBe(409);
    expect(await response.json()).toMatchObject({ code: "request_outcome_unavailable" });
    expect(aiRun).not.toHaveBeenCalled();
  });
  it("bounds request bytes and rejects malformed JSON", async () => {
    const { env, tools } = setup();
    const r = request("/proof/sql", input);
    expect((await worker.fetch(new Request(r, { body: "x".repeat(16385) }), env)).status).toBe(413);
    expect((await worker.fetch(new Request(r, { body: "{" }), env)).status).toBe(400);
    expect(tools).not.toHaveBeenCalled();
  });
  it("fails closed on service errors and missing Agent provenance", async () => {
    const failed = setup();
    failed.tools.mockRejectedValue(new Error("private-token"));
    const serviceResponse = await worker.fetch(request("/proof/sql", input), failed.env);
    expect(serviceResponse.status).toBe(502);
    expect(await serviceResponse.text()).not.toContain("private-token");
    const missing = setup();
    missing.env.BUILD_REVISION = undefined;
    expect((await worker.fetch(request("/proof/sql", input), missing.env)).status).toBe(503);
    expect((await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }), missing.env)).status).toBe(503);
    const noBudget = setup();
    noBudget.budgetFetch.mockRejectedValueOnce(new Error("budget-down"));
    expect((await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }), noBudget.env)).status).toBe(503);
  });
});
describe("global model budget Durable Object", () => {
  it("admits 24 calls and refuses the 25th without exposing state", async () => {
    let stored: unknown;
    const ctx = {
      storage: {
        get: vi.fn(async () => stored),
        put: vi.fn(async (_key: string, value: unknown) => {
          stored = value;
        }),
      },
      blockConcurrencyWhile: async (callback: () => Promise<void>) => callback(),
    } as unknown as DurableObjectState;
    const budget = new ProofBudget(ctx, {} as Env);
    for (let i = 0; i < 24; i += 1) {
      expect(await (await budget.fetch(new Request("https://budget", { method: "POST", body: '{"version":"1"}' }))).json()).toMatchObject({ admitted: true });
    }
    expect(await (await budget.fetch(new Request("https://budget", { method: "POST", body: '{"version":"1"}' }))).json()).toMatchObject({ admitted: false });
    expect((await budget.fetch(new Request("https://budget", { method: "POST", body: "{}" }))).status).toBe(400);
  });
});

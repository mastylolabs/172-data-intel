import { describe, expect, it, vi } from "vitest";
import meta from "./fixtures/metadata.json";
import receipt from "./fixtures/result.json";
import { metadata } from "../src/contracts";
vi.mock("agents", () => ({
  Agent: class {
    state: unknown;
    env: unknown;
    constructor(_ctx: unknown, env: unknown) {
      this.env = env;
    }
    setState(next: unknown): void {
      this.state = next;
    }
  },
}));
const { default: worker, ProofAgent, buildPlanRequest, runPlanModel } = await import("../src/index");
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
  const lookup = vi.fn((name: string) => name as unknown as DurableObjectId);
  const env = {
    PROOF_TOKEN: "t".repeat(32),
    RUNTIME_MODE: "deployed",
    BUILD_REVISION: "b".repeat(40),
    CF_VERSION_METADATA: { id: "23456789-1234-4234-8234-123456789abc" },
    TOOLS: { fetch: tools },
    AI: { run: aiRun },
    ProofBudget: {},
    ProofAgent: { idFromName: lookup, get: () => ({ fetch: (r: Request) => agent.onRequest(r) }) },
  } as unknown as Env;
  const agent = new ProofAgent({} as DurableObjectState, env);
  Object.assign(agent, { state: agent.initialState });
  return { agent, env, tools, lookup, aiRun };
}
function request(path: string, body?: unknown, extra: Record<string, string> = {}): Request {
  return new Request(`https://proof.example${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: { authorization: `Bearer ${"t".repeat(32)}`, origin: "https://proof.example", ...extra },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
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
    delete noBudget.env.ProofBudget;
    expect((await worker.fetch(request("/proof/plan", { version: "1", request_id: crypto.randomUUID(), question: "Revenue?" }), noBudget.env)).status).toBe(503);
  });
});

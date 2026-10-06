import { describe, expect, it, vi } from "vitest";
import meta from "./fixtures/metadata.json";
import receipt from "./fixtures/result.json";
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
const { default: worker, ProofAgent } = await import("../src/index");
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
  const lookup = vi.fn((name: string) => name as unknown as DurableObjectId);
  const env = {
    PROOF_TOKEN: "test-token",
    RUNTIME_MODE: "deployed",
    BUILD_REVISION: "b".repeat(40),
    CF_VERSION_METADATA: { id: "23456789-1234-4234-8234-123456789abc" },
    TOOLS: { fetch: tools },
    ProofAgent: { idFromName: lookup, get: () => ({ fetch: (r: Request) => agent.onRequest(r) }) },
  } as unknown as Env;
  const agent = new ProofAgent({} as DurableObjectState, env);
  Object.assign(agent, { state: agent.initialState });
  return { agent, env, tools, lookup };
}
function request(path: string, body?: unknown, extra: Record<string, string> = {}): Request {
  return new Request(`https://proof.example${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: { authorization: "Bearer test-token", origin: "https://proof.example", ...extra },
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
    await worker.fetch(request("/proof/reset", { version: "1" }), env);
    expect(agent.state).toEqual(agent.initialState);
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
  });
});

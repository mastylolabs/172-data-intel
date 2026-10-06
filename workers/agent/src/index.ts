import { Agent, type Connection } from "agents";
import {
  AGENTS_VERSION,
  agentRuntime,
  boundedJson,
  emptyInput,
  metadata,
  serviceError,
  sha256,
  sourceInput,
  sqlInput,
  type ProofReceipt,
  validatedResult,
} from "./contracts";
export interface Env {
  ProofAgent: DurableObjectNamespace<ProofAgent>;
  TOOLS: Fetcher;
  PROOF_TOKEN: string;
  RUNTIME_MODE: "local" | "deployed";
  BUILD_REVISION?: string;
  CF_VERSION_METADATA?: { id: string };
}
export type State = {
  version: "1";
  revision: number;
  selected_source: "sales" | "support";
  receipt: ProofReceipt | null;
  revoked: boolean;
};
const initialState = (): State => ({
  version: "1",
  revision: 0,
  selected_source: "sales",
  receipt: null,
  revoked: false,
});
const visibleState = (state: State): Omit<State, "revoked"> => {
  const { revoked: _revoked, ...publicState } = state;
  return publicState;
};
const json = (value: unknown, status = 200): Response =>
  Response.json(value, {
    status,
    headers: { "cache-control": "no-store", "referrer-policy": "no-referrer", "x-content-type-options": "nosniff" },
  });

const fail = (code: string, status = 400, stage = "transport"): Response =>
  json({ version: "1", code, stage, job_id: null, limit: null, provider_reason: null, automatic_retry: false }, status);
function cookieValue(request: Request): string | undefined {
  return request.headers.get("cookie")?.match(/(?:^|;\s*)__Host-proof=([a-f0-9]{64})(?:;|$)/)?.[1];
}
function randomToken(): string {
  return Array.from(crypto.getRandomValues(new Uint8Array(32)), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
function sessionToken(request: Request): string {
  const existing = cookieValue(request);
  return existing ?? randomToken();
}
function validServiceResult(
  receipt: Awaited<ReturnType<typeof validatedResult>>,
  input: { request_id: string; sql: string; max_rows: number },
  meta: ReturnType<typeof metadata.parse>,
): boolean {
  return (
    receipt.job_id === input.request_id &&
    receipt.actual_sql === input.sql &&
    receipt.row_count <= input.max_rows &&
    receipt.source.source_id === meta.source.source_id &&
    receipt.source.snapshot_sha256 === meta.source.snapshot_sha256 &&
    receipt.source.meaning_revision === meta.source.meaning_revision &&
    receipt.schema_revision === meta.schema_revision &&
    receipt.engine_policy === meta.engine_policy &&
    JSON.stringify(receipt.runtime) === JSON.stringify(meta.runtime) &&
    JSON.stringify(receipt.limits) === JSON.stringify(meta.limits)
  );
}
async function executeSql(
  agent: ProofAgent,
  env: Env,
  input: ReturnType<typeof sqlInput.parse>,
): Promise<Response> {
  const provenanceCheck = agentRuntime.safeParse({
    runtime_mode: env.RUNTIME_MODE,
    build_revision: env.BUILD_REVISION ?? null,
    worker_version_id: env.CF_VERSION_METADATA?.id ?? null,
  });
  if (!provenanceCheck.success) return fail("runtime_incompatible", 503);
  const signal = AbortSignal.timeout(10_000);
  const metaResponse = await env.TOOLS.fetch("https://tools/metadata", { signal });
  if (!metaResponse.ok) return fail("python_unavailable", 502);
  const meta = metadata.parse(await boundedJson(metaResponse, 4096));
  const response = await env.TOOLS.fetch("https://tools/query", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      version: "1",
      job_id: input.request_id,
      intent: {
        version: "1",
        source: meta.source,
        question: input.question,
        sql: input.sql,
        max_rows: input.max_rows,
      },
    }),
    signal,
  });
  return consumeResult(agent, response, input, meta, provenanceCheck.data);
}

async function consumeResult(
  agent: ProofAgent,
  response: Response,
  input: ReturnType<typeof sqlInput.parse>,
  meta: ReturnType<typeof metadata.parse>,
  provenance: ReturnType<typeof agentRuntime.parse>,
): Promise<Response> {
  const payload = await boundedJson(response);
  if (!response.ok) {
    const error = serviceError.parse(payload);
    if (error.job_id !== null && error.job_id !== input.request_id) throw new Error("job_mismatch");
    return json(error, response.status);
  }
  const parsed = await validatedResult(payload);
  if (!validServiceResult(parsed, input, meta)) throw new Error("invalid_result");
  const receipt: ProofReceipt = {
    ...parsed,
    proof_kind: "engine",
    ai_chain_complete: false,
    model: null,
    prompt_revision: null,
    model_calls: 0,
    agent_runtime_mode: provenance.runtime_mode,
    agent_build_revision: provenance.build_revision,
    agent_worker_version_id: provenance.worker_version_id,
    agents_version: AGENTS_VERSION,
  };
  agent.setState({ ...agent.state, receipt, revision: agent.state.revision + 1 });
  return json(visibleState(agent.state));
}

export class ProofAgent extends Agent<Env, State> {
  initialState = initialState();
  private busy = false;

  validateStateChange(_next: State, origin: Connection | "server"): void {
    if (origin !== "server") throw new Error("access_denied");
  }

  async onRequest(request: Request): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (this.state.revoked) return fail("access_denied", 403);
    if (request.method === "GET" && path === "/proof/state") return json(visibleState(this.state));
    if (request.method !== "POST") return fail("not_found", 404);
    if (path === "/proof/query") return fail("unsupported_transport", 422);
    if (!["/proof/source", "/proof/sql", "/proof/reset"].includes(path)) {
      return fail("not_found", 404);
    }
    if (this.busy) return fail("request_conflict", 409);
    this.busy = true;
    let service = false;
    try {
      const body = await boundedJson(request);
      if (path === "/proof/source") {
        const parsed = sourceInput.parse(body);
        this.setState({
          ...this.state,
          selected_source: parsed.source,
          receipt: null,
          revision: this.state.revision + 1,
        });
      } else if (path === "/proof/reset") {
        emptyInput.parse(body);
        this.setState({ ...initialState(), revoked: true });
      } else {
        const input = sqlInput.parse(body);
        if (this.state.selected_source !== "sales") return fail("unsupported_source", 422);
        service = true;
        return await executeSql(this, this.env, input);
      }
      return json(visibleState(this.state));
    } catch (error) {
      if (service) return fail("python_unavailable", 502);
      if (error instanceof Error && error.message === "result_limit") return fail("result_limit", 413, "input");
      return fail("invalid_input", 400, "input");
    } finally {
      this.busy = false;
    }
  }
}

const proofRoutes = new Set([
  "/proof/state",
  "/proof/source",
  "/proof/sql",
  "/proof/reset",
  "/proof/query",
]);

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/proof/")) return fail("not_found", 404);
    if (
      new TextEncoder().encode(env.PROOF_TOKEN ?? "").byteLength < 32 ||
      request.headers.get("authorization") !== `Bearer ${env.PROOF_TOKEN}`
    ) {
      return fail("access_denied", 403);
    }
    if (request.headers.has("upgrade")) return fail("access_denied", 403);
    if (request.method !== "GET" && request.headers.get("origin") !== url.origin) {
      return fail("access_denied", 403);
    }
    if (!proofRoutes.has(url.pathname)) return fail("not_found", 404);
    if (request.method !== (url.pathname === "/proof/state" ? "GET" : "POST")) {
      return fail("not_found", 404);
    }
    const currentToken = sessionToken(request);
    const token = url.pathname === "/proof/reset" ? randomToken() : currentToken;
    const id = env.ProofAgent.idFromName(await sha256(currentToken));
    const forwardHeaders = new Headers(request.headers);
    forwardHeaders.delete("authorization");
    forwardHeaders.delete("cookie");
    const response = await env.ProofAgent.get(id).fetch(new Request(request, { headers: forwardHeaders }));
    const headers = new Headers(response.headers);
    headers.set(
      "set-cookie",
      `__Host-proof=${response.status === 200 ? token : currentToken}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=604800`,
    );
    return new Response(response.body, { status: response.status, headers });
  },
};

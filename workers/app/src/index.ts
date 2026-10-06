import { Agent, getAgentByName, type Connection } from "agents";
import { z } from "zod";
import { approvedSource, catalogV2, dataProfileV2, validatedDomainEnvelope, type DomainKind, type Envelope, type Source } from "./contracts";
import {
  BridgeError, askRequest, buildToolBody, executeTool, profileRequest, queryRequest, readBoundedText, readJson, searchRequest,
  sourceRequest, type ResultKind, type TransportEnv,
} from "./transport";
import { runPlanner, type ModelEnv, type PlannerFailure, type PlannerResult } from "./model_gateway";
import { analystProposal, type AnalystProposal } from "./model_contracts";
import {
  beginJob, cancelJob, finishJob, initialSessionState, parseSessionState, publicSnapshot,
  resetSession, selectSource, storeJob, type JobV2, type SessionStateV2,
} from "../../agent/src/v2-state";

export interface Env extends TransportEnv, ModelEnv {
  AppAgent: DurableObjectNamespace<AppAgent>;
  AGENT: Fetcher;
  PLANNER_BUDGET_TOKEN?: string;
  TOOLS_BUILD_REVISION?: string;
  TOOLS_WORKER_VERSION_ID?: string;
}
type PublicState = Record<string, unknown>;
type JobKind = ResultKind | "ask";
type PlannerOutcome =
  | { kind: "proposal"; proposal: AnalystProposal }
  | { kind: "clarification"; proposal: AnalystProposal; question: string }
  | { kind: "failure"; code: PlannerFailure["code"] | "budget_exhausted"; provider_reason: string | null };
export type PlannerState = { request_id: string; job_id: string; source: Source; generation: number; cancel_epoch: number; result: PlannerOutcome };
type Outcome = { request_id: string; input_sha256: string; kind: JobKind; snapshot: PublicState };
export type BridgeState = {
  version: "1"; session: SessionStateV2; result: Envelope<unknown> | null; result_kind: ResultKind | null;
  revoked: boolean; expired: boolean; outcomes: Outcome[]; planner: PlannerState | null; model_calls: number;
};
type JobRequest = { kind: JobKind; body: Record<string, unknown> };
type AgentStub = { fetch(request: Request): Promise<Response> };
type Resolver = (env: Env, name: string) => Promise<AgentStub>;
const routes: Record<string, string> = {
  "/api/state": "GET", "/api/source": "POST", "/api/ask": "POST", "/api/profile": "POST", "/api/query": "POST",
  "/api/search": "POST", "/api/cancel": "POST", "/api/reset": "POST",
};
const MODEL_CALL_BUDGET = 3;
const emptyBody = z.strictObject({ version: z.literal("2") });
const plannerStateSchema = z.strictObject({
  request_id: z.uuid(), job_id: z.uuid(), source: approvedSource,
  generation: z.number().int().nonnegative(), cancel_epoch: z.number().int().nonnegative(),
  result: z.discriminatedUnion("kind", [
    z.strictObject({ kind: z.literal("proposal"), proposal: analystProposal }),
    z.strictObject({ kind: z.literal("clarification"), proposal: analystProposal, question: z.string().max(512) }),
    z.strictObject({ kind: z.literal("failure"), code: z.enum(["execution_limit", "model_output_invalid", "model_quota", "model_unavailable", "budget_exhausted"]), provider_reason: z.enum(["daily_free_allocation", "account_limited", "out_of_capacity", "unknown"]).nullable() }),
  ]),
});
const json = (value: unknown, status = 200): Response => Response.json(value, {
  status, headers: { "cache-control": "no-store", "x-content-type-options": "nosniff", "referrer-policy": "no-referrer" },
});
const errorResponse = (error: BridgeError): Response => json({ version: "2", code: error.code }, error.status);
function initialBridgeState(): BridgeState {
  return { version: "1", session: initialSessionState(), result: null, result_kind: null,
    revoked: false, expired: false, outcomes: [], planner: null, model_calls: 0 };
}
function parsePlannerState(value: unknown): PlannerState {
  const parsed = plannerStateSchema.parse(value);
  const proposal = parsed.result.kind === "failure" ? null : parsed.result.proposal;
  if (proposal !== null && (proposal.request_id !== parsed.request_id || !sameSource(proposal.source, parsed.source))) throw new Error("planner_binding");
  if (parsed.result.kind === "clarification" && parsed.result.question !== parsed.result.proposal.clarification) throw new Error("planner_clarification");
  return parsed;
}
function parseBridgeState(value: unknown): BridgeState {
  if (typeof value !== "object" || value === null) throw new BridgeError("state_corrupt", 503);
  const raw = value as Record<string, unknown>;
  if (raw.version !== "1" || typeof raw.revoked !== "boolean" || typeof raw.expired !== "boolean" ||
    !("session" in raw)) throw new BridgeError("state_corrupt", 503);
  try {
    const result = raw.result === null ? null : raw.result as Envelope<unknown>;
    const kind = raw.result_kind === null ? null : raw.result_kind as ResultKind;
    if ((result === null) !== (kind === null) || (result !== null && !["profile", "query", "search"].includes(String(kind)))) throw new Error("kind");
    const outcomes = Array.isArray(raw.outcomes) ? raw.outcomes : [];
    if (outcomes.length > 2 || outcomes.some((item) => {
      if (typeof item !== "object" || item === null) return true;
      const outcome = item as Record<string, unknown>;
      const snapshot = outcome.snapshot;
      return typeof outcome.request_id !== "string" || typeof outcome.input_sha256 !== "string" ||
        !["profile", "query", "search", "ask"].includes(String(outcome.kind)) ||
        typeof snapshot !== "object" || snapshot === null || Array.isArray(snapshot);
    })) throw new Error("outcomes");
    const planner = raw.planner === undefined || raw.planner === null ? null : parsePlannerState(raw.planner);
    if (new TextEncoder().encode(JSON.stringify({ result, outcomes, planner })).byteLength > 65_536) throw new Error("limit");
    if (planner !== null) {
      const active = parseSessionState(raw.session).active_job;
      if (active === null || planner.job_id !== active.job_id || planner.request_id !== active.request_id ||
        planner.generation !== active.generation || planner.cancel_epoch !== active.cancel_epoch || !sameSource(planner.source, active.source)) throw new Error("planner_owner");
    }
    const modelCalls = raw.model_calls === undefined ? 0 : raw.model_calls;
    if (typeof modelCalls !== "number" || !Number.isInteger(modelCalls) || modelCalls < 0 || modelCalls > MODEL_CALL_BUDGET) throw new Error("model_calls");
    return { version: "1", session: parseSessionState(raw.session), result, result_kind: kind,
      revoked: raw.revoked, expired: raw.expired, outcomes: outcomes as Outcome[], planner, model_calls: modelCalls };
  } catch { throw new BridgeError("state_corrupt", 503); }
}
function publicState(state: BridgeState): PublicState {
  return { ...publicSnapshot(state.session), last_result: state.result, planner: state.planner,
    model_calls: state.model_calls, model_calls_remaining: MODEL_CALL_BUDGET - state.model_calls };
}
async function validState(agent: AppAgent): Promise<BridgeState> {
  const state = parseBridgeState(agent.state);
  try {
    if (state.result !== null && state.result_kind !== null) await validatedDomainEnvelope(state.result_kind, state.result);
    for (const outcome of state.outcomes) {
      const active = outcome.snapshot.active_job as Record<string, unknown> | null;
      if (active === null || active.request_id !== outcome.request_id ||
        typeof active.job_id !== "string" || !("last_result" in outcome.snapshot)) throw new Error("outcome_owner");
      if (outcome.kind === "ask") {
        if (outcome.snapshot.planner === null) throw new Error("outcome_planner");
        const planner = parsePlannerState(outcome.snapshot.planner);
        if (planner.request_id !== outcome.request_id || planner.job_id !== active.job_id) throw new Error("outcome_planner_owner");
      }
      if (outcome.kind !== "ask" && outcome.snapshot.last_result !== null) {
        const envelope = await validatedDomainEnvelope(outcome.kind, outcome.snapshot.last_result);
        if (envelope.job_id !== active.job_id) throw new Error("outcome_job");
      }
    }
    return state;
  } catch { throw new BridgeError("state_corrupt", 503); }
}
function remember(state: BridgeState, job: JobV2, kind: ResultKind): BridgeState {
  const outcome = { request_id: job.request_id, input_sha256: job.input_sha256, kind, snapshot: publicState(state) };
  return { ...state, outcomes: [...state.outcomes.filter((item) => item.request_id !== job.request_id), outcome].slice(-2) };
}
function rememberPlanner(state: BridgeState, job: JobV2): BridgeState {
  const outcome = { request_id: job.request_id, input_sha256: job.input_sha256, kind: "ask" as const, snapshot: publicState(state) };
  return { ...state, outcomes: [...state.outcomes.filter((item) => item.request_id !== job.request_id), outcome].slice(-2) };
}
function ownsPlannerJob(state: BridgeState, job: JobV2): boolean {
  const active = state.session.active_job;
  return !state.expired && active !== null && active.job_id === job.job_id && active.generation === job.generation &&
    active.cancel_epoch === job.cancel_epoch && active.active_run_id === job.active_run_id && Date.parse(job.deadline_at) > Date.now();
}
function plannerState(job: JobV2, result: PlannerResult): PlannerState {
  const outcome: PlannerOutcome = result.kind === "success"
    ? result.proposal.status === "clarify"
      ? { kind: "clarification", proposal: result.proposal, question: result.proposal.clarification! }
      : { kind: "proposal", proposal: result.proposal }
    : { kind: "failure", code: result.code, provider_reason: result.provider_reason };
  return { request_id: job.request_id, job_id: job.job_id, source: job.source,
    generation: job.generation, cancel_epoch: job.cancel_epoch, result: outcome };
}
function budgetPlannerState(job: JobV2): PlannerState {
  return { request_id: job.request_id, job_id: job.job_id, source: job.source,
    generation: job.generation, cancel_epoch: job.cancel_epoch,
    result: { kind: "failure", code: "budget_exhausted", provider_reason: null } };
}
function expiredSession(state: SessionStateV2): SessionStateV2 {
  const renewed = resetSession(state);
  const active = state.active_job;
  if (active === null || ["completed", "failed", "interrupted", "cancelled", "budget_exhausted"].includes(active.phase)) {
    return parseSessionState({ ...renewed, expires_at: state.expires_at });
  }
  return parseSessionState({ ...renewed, expires_at: state.expires_at, active_job: {
    ...active, phase: "interrupted", generation: renewed.generation, cancel_epoch: renewed.cancel_epoch,
    active_run_id: null, error: { code: "stale_job", stage: "transport" }, clarification: null,
  }, request_journal: [{ request_id: active.request_id, input_sha256: active.input_sha256,
    job_id: active.job_id, terminal_code: "expired", publication_id: null }] });
}
function requestHash(value: unknown): Promise<string> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(value))).then((hash) =>
    Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join(""));
}
function newJob(source: Source, request: JobRequest, hash: string, deadlineMs = 15_000): JobV2 {
  const now = new Date();
  return { job_id: crypto.randomUUID(), request_id: String(request.body.request_id), input_sha256: hash, source,
    generation: 0, cancel_epoch: 0, phase: "queued", started_at: now.toISOString(),
    deadline_at: new Date(now.getTime() + deadlineMs).toISOString(), active_run_id: crypto.randomUUID(), error: null, clarification: null };
}
function parseJob(path: string, value: unknown): { kind: ResultKind; body: Record<string, unknown> } {
  try {
    if (path === "/api/profile") return { kind: "profile", body: profileRequest.parse(value) };
    if (path === "/api/query") return { kind: "query", body: queryRequest.parse(value) };
    return { kind: "search", body: searchRequest.parse(value) };
  } catch { throw new BridgeError("invalid_input"); }
}
function capability(source: Source, kind: ResultKind): void {
  if (kind === "search" ? source.source_id !== "support" : source.source_id !== "sales") {
    throw new BridgeError("capability_mismatch", 422);
  }
}
export function trustedRuntime(env: Env, receipt: Envelope<unknown>): boolean {
  return env.RUNTIME_MODE === "local" || (receipt.runtime.build_revision === env.TOOLS_BUILD_REVISION &&
    receipt.runtime.worker_version_id === env.TOOLS_WORKER_VERSION_ID);
}
async function admitPlannerBudget(env: Env): Promise<boolean> {
  const token = env.PLANNER_BUDGET_TOKEN;
  if (token === undefined || new TextEncoder().encode(token).byteLength < 32) throw new Error("budget_unavailable");
  const response = await env.AGENT.fetch(new Request("https://agent/internal/planner-budget", {
    method: "POST", body: JSON.stringify({ version: "1" }),
    headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
    signal: AbortSignal.timeout(2_000),
  }));
  if (!response.ok) throw new Error("budget_unavailable");
  const value = JSON.parse(await readBoundedText(response.body, 1024, 502)) as { admitted?: unknown };
  if (typeof value.admitted !== "boolean") throw new Error("budget_invalid");
  return value.admitted;
}
function sameSource(left: Source, right: Source): boolean {
  return left.source_id === right.source_id && left.snapshot_sha256 === right.snapshot_sha256 && left.meaning_revision === right.meaning_revision;
}
function reconcileDeadline(state: BridgeState): BridgeState {
  const active = state.session.active_job;
  if (active === null || ["completed", "failed", "interrupted", "cancelled", "budget_exhausted"].includes(active.phase) ||
    Date.parse(active.deadline_at) > Date.now()) return state;
  try {
    const session = finishJob(state.session, active.job_id, active.generation, active.cancel_epoch,
      { phase: active.phase === "cancel_requested" ? "cancelled" : "interrupted", error: { code: "stale_job", stage: "transport" } });
    return { ...state, session, result: null, result_kind: null, planner: null };
  } catch { return state; }
}

export class AppAgent extends Agent<Env, BridgeState> {
  initialState = initialBridgeState();
  private busy = false;
  validateStateChange(_next: BridgeState, origin: Connection | "server"): void { if (origin !== "server") throw new Error("access_denied"); }
  private async complete(job: JobV2, request: { kind: ResultKind; body: Record<string, unknown> }): Promise<void> {
    try {
      const runId = job.active_run_id;
      if (runId === null) throw new Error("missing_run");
      const receipt = await executeTool(this.env, request.kind,
        buildToolBody(request.kind, job.job_id, runId, job.source, request.body), { jobId: job.job_id, runId });
      const current = await validState(this);
      if (!trustedRuntime(this.env, receipt)) throw new Error("runtime_identity");
      if (current.expired || current.session.active_job?.job_id !== job.job_id || Date.parse(job.deadline_at) <= Date.now()) {
        if (current.expired || current.session.active_job?.job_id !== job.job_id) return;
        const interrupted = finishJob(current.session, job.job_id, job.generation, job.cancel_epoch,
          { phase: "interrupted", error: { code: "stale_job", stage: "transport" } });
        this.setState(remember({ ...current, session: interrupted, result: null, result_kind: null }, job, request.kind));
        return;
      }
      const finished = finishJob(current.session, job.job_id, job.generation, job.cancel_epoch, { phase: "completed", error: null });
      this.setState(remember({ ...current, session: finished, result: receipt, result_kind: request.kind }, job, request.kind));
    } catch {
      try {
        const current = await validState(this);
        if (current.session.active_job?.job_id !== job.job_id) return;
        const phase = Date.parse(job.deadline_at) <= Date.now() ? "interrupted" : "failed";
        const finished = finishJob(current.session, job.job_id, job.generation, job.cancel_epoch,
          { phase, error: { code: "validation_failed", stage: "transport" } });
        this.setState(remember({ ...current, session: finished, result: null, result_kind: null }, job, request.kind));
      } catch { /* reset, cancellation, or stale completion */ }
    }
  }
  private async completePlanner(job: JobV2, question: string): Promise<void> {
    try {
      let current = await validState(this);
      if (!ownsPlannerJob(current, job)) return;
      if (current.model_calls >= MODEL_CALL_BUDGET) {
        const finished = finishJob(current.session, job.job_id, job.generation, job.cancel_epoch, { phase: "budget_exhausted", error: null });
        this.setState(rememberPlanner({ ...current, session: finished, planner: budgetPlannerState(job) }, job));
        return;
      }
      const runId = job.active_run_id;
      if (runId === null) throw new Error("missing_run");
      if (!(await admitPlannerBudget(this.env))) {
        const finished = finishJob(current.session, job.job_id, job.generation, job.cancel_epoch, { phase: "budget_exhausted", error: null });
        this.setState(rememberPlanner({ ...current, session: finished, planner: budgetPlannerState(job) }, job));
        return;
      }
      current = await validState(this);
      if (!ownsPlannerJob(current, job)) return;
      const catalogReceipt = await executeTool(this.env, "catalog", null, null);
      current = await validState(this);
      if (!ownsPlannerJob(current, job)) return;
      if (!trustedRuntime(this.env, catalogReceipt)) throw new Error("runtime_identity");
      const catalog = catalogV2.parse(catalogReceipt.payload);
      let profile = null;
      if (job.source.source_id === "sales") {
        const profileReceipt = await executeTool(this.env, "profile", buildToolBody("profile", job.job_id, runId, job.source, {}), { jobId: job.job_id, runId });
        current = await validState(this);
        if (!ownsPlannerJob(current, job)) return;
        if (!trustedRuntime(this.env, profileReceipt)) throw new Error("runtime_identity");
        profile = dataProfileV2.parse(profileReceipt.payload);
      }
      this.setState({ ...current, model_calls: current.model_calls + 1 });
      const result = await runPlanner(this.env, { request_id: job.request_id, question, source: job.source, catalog, profile });
      current = await validState(this);
      if (!ownsPlannerJob(current, job)) return;
      const planned = plannerState(job, result);
      const phase = result.kind === "success" && result.proposal.status === "clarify" ? "awaiting_clarification" : result.kind === "failure" ? "failed" : "completed";
      const session = result.kind === "success" && result.proposal.status === "clarify"
        ? parseSessionState({ ...current.session, active_job: { ...current.session.active_job!, clarification: { question: result.proposal.clarification!, created_at: new Date().toISOString() } } })
        : current.session;
      const finished = finishJob(session, job.job_id, job.generation, job.cancel_epoch, { phase, error: null });
      this.setState(rememberPlanner({ ...current, session: finished, planner: planned }, job));
    } catch {
      try {
        const current = await validState(this);
        if (!ownsPlannerJob(current, job)) return;
        const finished = finishJob(current.session, job.job_id, job.generation, job.cancel_epoch, { phase: "failed", error: null });
        this.setState(rememberPlanner({ ...current, session: finished, planner: {
          request_id: job.request_id, job_id: job.job_id, source: job.source, generation: job.generation,
          cancel_epoch: job.cancel_epoch, result: { kind: "failure", code: "model_unavailable", provider_reason: "unknown" },
        } }, job));
      } catch { /* reset, cancellation, or stale completion */ }
    }
  }
  private async start(request: { kind: ResultKind; body: Record<string, unknown> }, state: BridgeState): Promise<Response> {
    const source = state.session.selected_source;
    if (source === null) throw new BridgeError("source_required", 422);
    capability(source, request.kind);
    const hash = await requestHash(request.body);
    const job = newJob(source, request, hash);
    job.generation = state.session.generation; job.cancel_epoch = state.session.cancel_epoch;
    const outcome = beginJob(state.session, job);
    if (outcome.kind === "replay") {
      const owned = state.outcomes.find((item) => item.request_id === job.request_id && item.input_sha256 === hash);
      if (owned !== undefined) return json(owned.snapshot);
      if (state.session.active_job?.request_id === job.request_id && !["completed", "failed", "interrupted", "cancelled", "budget_exhausted"].includes(state.session.active_job.phase)) return json(publicState(state), 202);
      throw new BridgeError("request_outcome_unavailable", 409);
    }
    if (outcome.kind !== "new") throw new BridgeError(outcome.code, 409);
    this.setState({ ...state, session: storeJob(state.session, job), result: null, result_kind: null });
    this.ctx.waitUntil(this.complete(job, request));
    return json(publicState(this.state), 202);
  }
  private async startAsk(body: Record<string, unknown>, state: BridgeState): Promise<Response> {
    const source = state.session.selected_source;
    if (source === null) throw new BridgeError("source_required", 422);
    const hash = await requestHash(body);
    const job = newJob(source, { kind: "ask", body }, hash, 60_000);
    job.generation = state.session.generation; job.cancel_epoch = state.session.cancel_epoch;
    const outcome = beginJob(state.session, job);
    if (outcome.kind === "replay") {
      const owned = state.outcomes.find((item) => item.kind === "ask" && item.request_id === job.request_id && item.input_sha256 === hash);
      if (owned !== undefined) return json(owned.snapshot);
      if (state.session.active_job?.request_id === job.request_id && !["completed", "failed", "interrupted", "cancelled", "budget_exhausted", "awaiting_clarification"].includes(state.session.active_job.phase)) return json(publicState(state), 202);
      throw new BridgeError("request_outcome_unavailable", 409);
    }
    if (outcome.kind !== "new") throw new BridgeError(outcome.code, 409);
    this.setState({ ...state, session: storeJob(state.session, job), result: null, result_kind: null, planner: null });
    this.ctx.waitUntil(this.completePlanner(job, String(body.question)));
    return json(publicState(this.state), 202);
  }
  async onRequest(request: Request): Promise<Response> {
    if (this.busy) return errorResponse(new BridgeError("request_conflict", 409));
    this.busy = true;
    try {
      const path = new URL(request.url).pathname;
      let state = await validState(this);
      if (state.revoked) throw new BridgeError("access_denied", 403);
      if (state.expired && path !== "/api/reset") throw new BridgeError("session_expired", 410);
      if (Date.parse(state.session.expires_at) <= Date.now() && path !== "/api/reset") {
        this.setState({ ...state, session: expiredSession(state.session), result: null, result_kind: null, planner: null, expired: true });
        throw new BridgeError("session_expired", 410);
      }
      const reconciled = reconcileDeadline(state);
      if (reconciled !== state) { this.setState(reconciled); state = reconciled; }
      if (path === "/api/state" && request.method === "GET") return json(publicState(state));
      if (path === "/api/reset" && request.method === "POST") {
        emptyBody.parse(await readJson(request, 1024));
        this.setState({ ...state, session: resetSession(state.session), revoked: true, expired: false, result: null, result_kind: null, planner: null, model_calls: 0, outcomes: [] });
        return json(publicState(initialBridgeState()));
      }
      if (path === "/api/cancel" && request.method === "POST") {
        emptyBody.parse(await readJson(request, 1024));
        if (state.session.active_job === null || ["completed", "failed", "interrupted", "cancelled", "budget_exhausted"].includes(state.session.active_job.phase)) return json(publicState(state));
        const canceled = cancelJob(state.session);
        if (canceled.active_job) {
          const done = finishJob(canceled, canceled.active_job.job_id, canceled.active_job.generation, canceled.active_job.cancel_epoch, { phase: "cancelled", error: null });
          this.setState({ ...state, session: done });
        } else this.setState({ ...state, session: canceled });
        return json(publicState(this.state));
      }
      if (path === "/api/source" && request.method === "POST") {
        const parsed = sourceRequest.parse(await readJson(request));
        const catalog = await executeTool(this.env, "catalog", null, null);
        const entries = (catalog.payload as { entries: Array<{ source: Source }> }).entries;
        if (!entries.some((entry) => sameSource(entry.source, parsed.source))) throw new BridgeError("source_mismatch", 409);
        this.setState({ ...state, session: selectSource(state.session, parsed.source), result: null, result_kind: null, planner: null });
        return json(publicState(this.state));
      }
      if (path === "/api/ask") {
        if (request.method !== "POST") throw new BridgeError("not_found", 404);
        return await this.startAsk(askRequest.parse(await readJson(request)), state);
      }
      if (path === "/api/profile" || path === "/api/query" || path === "/api/search") {
        if (request.method !== "POST") throw new BridgeError("not_found", 404);
        return await this.start(parseJob(path, await readJson(request)), state);
      }
      throw new BridgeError("not_found", 404);
    } catch (error) {
      if (error instanceof BridgeError) return errorResponse(error);
      return errorResponse(new BridgeError("invalid_input"));
    } finally { this.busy = false; }
  }
}

async function sessionName(request: Request): Promise<{ token: string; name: string; isNew: boolean }> {
  const existing = request.headers.get("cookie")?.match(/(?:^|;\s*)di_session=([a-f0-9]{64})(?:;|$)/)?.[1];
  const token = existing ?? Array.from(crypto.getRandomValues(new Uint8Array(32)), (byte) => byte.toString(16).padStart(2, "0")).join("");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token));
  return { token, name: Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join(""), isNew: existing === undefined };
}
function headers(response: Response): Response {
  const result = new Response(response.body, response); result.headers.set("content-security-policy", "default-src 'none'; frame-ancestors 'none'"); return result;
}
export async function publicFetch(request: Request, env: Env, resolve: Resolver = (runtime, name) => getAgentByName(runtime.AppAgent, name)): Promise<Response> {
  const url = new URL(request.url);
  if (!(url.pathname in routes)) return headers(json({ version: "2", code: "not_found" }, 404));
  if (request.headers.has("upgrade")) return headers(json({ version: "2", code: "unsupported_transport" }, 400));
  if (request.method !== "GET" && request.headers.get("origin") !== url.origin) return headers(json({ version: "2", code: "access_denied" }, 403));
  if (routes[url.pathname] !== request.method) return headers(json({ version: "2", code: "not_found" }, 404));
  const session = await sessionName(request); const agent = await resolve(env, session.name);
  const forwarded = new Request(url.origin + url.pathname, request); forwarded.headers.delete("cookie");
  let response: Response; try { response = await agent.fetch(forwarded); } catch { response = errorResponse(new BridgeError("service_unavailable", 503)); }
  const output = headers(response);
  if (session.isNew || (url.pathname === "/api/reset" && response.ok)) {
    const token = url.pathname === "/api/reset" && response.ok ? Array.from(crypto.getRandomValues(new Uint8Array(32)), (byte) => byte.toString(16).padStart(2, "0")).join("") : session.token;
    output.headers.set("set-cookie", `di_session=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=604800; Secure`);
  }
  return output;
}
export default { fetch(request: Request, env: Env): Promise<Response> { return publicFetch(request, env); } } satisfies ExportedHandler<Env>;
export { AppAgent as MvpAppAgent };

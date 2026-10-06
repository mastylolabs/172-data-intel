import { describe, expect, it } from "vitest";
import {
  SALES_SOURCE,
  SUPPORT_SOURCE,
  beginJob,
  cancelJob,
  finishJob,
  initialSessionState,
  parseSessionState,
  publicSnapshot,
  resetSession,
  selectSource,
  sessionStateV2,
  storeJob,
  type JobV2,
  type SourceV2,
} from "../src/v2-state";

const JOB_ID = "11111111-1111-4111-8111-111111111111";
const REQUEST_ID = "22222222-2222-4222-8222-222222222222";
const now = "2026-10-06T10:00:00.000Z";
const job = (overrides: Partial<JobV2> = {}): JobV2 => ({
  job_id: JOB_ID,
  request_id: REQUEST_ID,
  input_sha256: "a".repeat(64),
  source: SALES_SOURCE,
  generation: 0,
  cancel_epoch: 0,
  phase: "queued",
  started_at: now,
  deadline_at: "2026-10-06T10:01:00.000Z",
  active_run_id: null,
  candidate_id: null,
  publication_id: null,
  error: null,
  ...overrides,
});

describe("v2 durable session state", () => {
  it("starts with the exact demo source identity and strict bounded shape", () => {
    const state = initialSessionState(new Date(now));
    expect(state.selected_source).toEqual(SALES_SOURCE);
    expect(sessionStateV2.safeParse({ ...state, extra: true }).success).toBe(false);
    expect(parseSessionState(state)).toEqual(state);
  });

  it("accepts support only with its registered hash and fences selection", () => {
    const state = selectSource(initialSessionState(new Date(now)), SUPPORT_SOURCE);
    expect(state.selected_source).toEqual(SUPPORT_SOURCE);
    expect(state.generation).toBe(1);
    expect(() => selectSource(state, { ...SUPPORT_SOURCE, snapshot_sha256: "b".repeat(64) } as unknown as SourceV2)).toThrow();
  });

  it("distinguishes a new request, replay and changed-input conflict", () => {
    const state = initialSessionState(new Date(now));
    const first = beginJob(state, job());
    expect(first.kind).toBe("new");
    const stored = storeJob(state, job());
    const finished = finishJob(stored, JOB_ID, 0, 0, {
      phase: "failed",
      error: { code: "model_quota", message: "model unavailable" },
      publication_id: null,
    });
    expect(beginJob(finished, job()).kind).toBe("replay");
    expect(beginJob(finished, job({ request_id: "33333333-3333-4333-8333-333333333333" })).kind).toBe("new");
    expect(beginJob(finished, job({ input_sha256: "b".repeat(64) }))).toEqual({
      kind: "conflict",
      code: "request_conflict",
    });
  });

  it("does not allow stale completion after cancellation or a source switch", () => {
    const state = storeJob(initialSessionState(new Date(now)), job());
    const cancelled = cancelJob(state);
    expect(() => finishJob(cancelled, JOB_ID, 0, 0, {
      phase: "completed",
      error: null,
      publication_id: null,
    })).toThrow("stale_job");
    const switched = selectSource(state, SUPPORT_SOURCE);
    expect(() => finishJob(switched, JOB_ID, 0, 0, {
      phase: "completed",
      error: null,
      publication_id: null,
    })).toThrow("stale_job");
  });

  it("keeps the public projection bounded and rejects oversized state", () => {
    const state = initialSessionState(new Date(now));
    expect(publicSnapshot(state)).toEqual(state);
    expect(() => parseSessionState({ ...state, history: [{
      answer_id: JOB_ID,
      source: SALES_SOURCE,
      text: "x".repeat(1025),
      accepted_at: now,
      unavailable: false,
    }] })).toThrow();
  });

  it("reset clears accepted state and advances lifecycle fences", () => {
    const selected = selectSource(initialSessionState(new Date(now)), SUPPORT_SOURCE);
    const reset = resetSession(selected, new Date(now));
    expect(reset.selected_source).toEqual(SALES_SOURCE);
    expect(reset.history).toEqual([]);
    expect(reset.generation).toBe(selected.generation + 1);
    expect(reset.cancel_epoch).toBe(selected.cancel_epoch + 1);
  });
});

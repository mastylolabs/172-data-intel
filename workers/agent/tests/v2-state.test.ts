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
  selectSource,
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
  error: null,
  clarification: null,
  ...overrides,
});

describe("v2 durable session state", () => {
  it("accepts support only with its registered hash and fences selection", () => {
    const state = selectSource(initialSessionState(new Date(now)), SUPPORT_SOURCE);
    expect(state.selected_source).toEqual(SUPPORT_SOURCE);
    expect(state.generation).toBe(1);
    expect(() => selectSource(state, { ...SUPPORT_SOURCE, snapshot_sha256: "b".repeat(64) } as unknown as SourceV2)).toThrow();
  });

  it("distinguishes a new request, replay and changed-input conflict", () => {
    const state = selectSource(initialSessionState(new Date(now)), SALES_SOURCE);
    const admittedJob = job({ generation: state.generation, cancel_epoch: state.cancel_epoch });
    const first = beginJob(state, admittedJob);
    expect(first.kind).toBe("new");
    const stored = storeJob(state, admittedJob);
    const finished = finishJob(stored, JOB_ID, 1, 1, {
      phase: "failed",
      error: { code: "model_unavailable", stage: "planning" },
    });
    expect(beginJob(finished, admittedJob).kind).toBe("replay");
    expect(beginJob(finished, job({ request_id: "33333333-3333-4333-8333-333333333333", generation: state.generation, cancel_epoch: state.cancel_epoch })).kind).toBe("new");
    expect(beginJob(finished, job({ input_sha256: "b".repeat(64), generation: state.generation, cancel_epoch: state.cancel_epoch }))).toEqual({
      kind: "conflict",
      code: "request_conflict",
    });
  });

  it("does not allow stale completion after cancellation or a source switch", () => {
    const state = storeJob(selectSource(initialSessionState(new Date(now)), SALES_SOURCE), job({ generation: 1, cancel_epoch: 1 }));
    const cancelled = cancelJob(state);
    expect(() => finishJob(cancelled, JOB_ID, 0, 0, {
      phase: "completed",
      error: null,
    })).toThrow("stale_job");
    const cancelledTerminal = finishJob(cancelled, JOB_ID, 1, 2, {
      phase: "cancelled",
      error: null,
    });
    expect(cancelledTerminal.active_job?.phase).toBe("cancelled");
    const switched = selectSource(state, SUPPORT_SOURCE);
    expect(() => finishJob(switched, JOB_ID, 1, 1, {
      phase: "completed",
      error: null,
    })).toThrow("stale_job");
  });

  it("keeps the public projection bounded and rejects oversized state", () => {
    const state = initialSessionState(new Date(now));
    const { request_journal: _journal, generation: _generation, cancel_epoch: _epoch, ...publicState } = state;
    expect(publicSnapshot(state)).toEqual(publicState);
    expect("request_journal" in publicSnapshot(state)).toBe(false);
    expect(beginJob(state, job())).toEqual({ kind: "conflict", code: "source_mismatch" });
    expect(() => parseSessionState({ ...state, history: [{
      answer_id: JOB_ID,
      source: SALES_SOURCE,
      text: "x".repeat(1025),
      accepted_at: now,
      unavailable: false,
    }] })).toThrow();
  });

});
